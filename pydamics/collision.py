"""
Collision detection and impulse-based response -- circles and oriented
(rotated) boxes.

Unlike Force (which computes a per-entity acceleration independently),
collision needs to compare PAIRS of objects, so it's handled as an extra
phase in World.step() rather than through the physics2d Force system.

Two kinds of collision are handled here:
  1. entity vs entity  -- both have a collider (`.physics2d.collider()`),
                            circle or box, any combination
  2. entity vs solid    -- an entity with a collider against an SEO
                            object (`.seo.solid()`), box or circle, which
                            may itself be physics-capable ("physicsified")
                            or purely static

Box collision uses SAT (separating axis theorem, see sat.py) -- correct
for oriented (rotated) boxes, not just axis-aligned ones. A physicsified
SEO box uses its own `.angle` if it has one; a purely static SEO box has
no angle at all and is treated as axis-aligned.

Uses a spatial hash for the entity-entity broad-phase (see
spatial_hash.py) instead of a naive O(n^2) scan. Entity-vs-solid checks
stay a simple scan against the (usually much shorter) solids list.

resolve_all_collisions() returns a list of CollisionEvent for whatever
was actually resolved this step -- World.step() uses this to dispatch
on_collision callbacks, apply torque from off-center impulses, and wake
sleeping objects that got hit.
"""
from __future__ import annotations
import math
from .vector import Vec2
from .physics_core import compute_total_acceleration, has_physics
from .seo import SEOShapeBox, SEOShapeCircle
from .spatial_hash import SpatialHash
from .physics2d.box_collider import BoxCollider
from .sat import sat_box_vs_box, closest_point_on_box, box_axes


class CollisionEvent:
    """A single resolved collision. `normal` points from `a` to `b`.
    For world.on_collision(fn), fn is called as
    fn(a, b, contact_point, normal, impulse). For per-object
    .physics2d.on_collision(fn), World.step() derives a per-side normal
    (pointing away from the other object) -- see World.step()."""
    __slots__ = ("a", "b", "contact_point", "normal", "impulse")

    def __init__(self, a, b, contact_point, normal, impulse):
        self.a = a
        self.b = b
        self.contact_point = contact_point
        self.normal = normal
        self.impulse = impulse


def should_collide(a, b) -> bool:
    """Symmetric-AND layer filter: a pair only collides if EACH side's
    collides_with (when set) includes the other's layer. Works on
    anything with .layer/.collides_with (CircleCollider, BoxCollider, or SEO)."""
    if a.collides_with is not None and b.layer not in a.collides_with:
        return False
    if b.collides_with is not None and a.layer not in b.collides_with:
        return False
    return True


def _wake(obj) -> None:
    if getattr(obj, "_is_sleeping", False):
        obj._is_sleeping = False
        obj._sleep_still_time = 0.0


def _apply_torque_from_impulse(entity, contact_point: Vec2, impulse_applied: Vec2) -> None:
    """impulse_applied is the impulse actually added to this entity's
    velocity (mind the sign -- the two sides of a collision get opposite
    impulses)."""
    moi = getattr(entity, "moment_of_inertia", None)
    if not moi:
        return
    lever_arm = contact_point - entity.position
    torque = lever_arm.cross(impulse_applied)
    entity.angular_velocity += torque / moi


def _bounding_radius(collider) -> float:
    """Conservative bounding-circle radius, used only for spatial-hash
    cell sizing -- safe (never too small) for either shape."""
    if isinstance(collider, BoxCollider):
        return math.hypot(collider.width / 2.0, collider.height / 2.0)
    return collider.radius


def resolve_all_collisions(entities, solids) -> list:
    """entities: physics-capable objects (may or may not have a collider).
    solids: SEO objects to check entities against (may or may not be
    physics-capable themselves -- "physicsified" solids)."""
    events = []
    colliders = [e for e in entities if getattr(e, "_collider", None) is not None]

    _resolve_entity_entity_collisions(colliders, events)

    for entity in colliders:
        for solid in solids:
            if solid is entity:
                continue
            if not hasattr(solid, "seo") or solid.seo.shape is None:
                continue
            if not should_collide(entity._collider, solid.seo):
                continue
            entity_is_box = isinstance(entity._collider, BoxCollider)
            solid_is_box = isinstance(solid.seo.shape, SEOShapeBox)
            if entity_is_box and solid_is_box:
                _resolve_box_vs_seo_box(entity, solid, events)
            elif entity_is_box and not solid_is_box:
                _resolve_box_vs_seo_circle(entity, solid, events)
            elif not entity_is_box and solid_is_box:
                _resolve_circle_vs_box(entity, solid, events)
            else:
                _resolve_circle_vs_circle_solid(entity, solid, events)

    return events


def _resolve_entity_entity_collisions(colliders, events) -> None:
    n = len(colliders)
    if n < 2:
        return

    max_radius = max(_bounding_radius(c._collider) for c in colliders)
    grid = SpatialHash(cell_size=max(max_radius * 2.0, 1e-6))
    grid.rebuild(colliders)

    index_of = {id(c): i for i, c in enumerate(colliders)}
    seen = set()
    for i, a in enumerate(colliders):
        for b in grid.query_neighbors(a.position):
            j = index_of[id(b)]
            if j <= i or (i, j) in seen:
                continue
            seen.add((i, j))
            if not should_collide(a._collider, b._collider):
                continue
            a_is_box = isinstance(a._collider, BoxCollider)
            b_is_box = isinstance(b._collider, BoxCollider)
            if a_is_box and b_is_box:
                _resolve_box_vs_box_pair(a, b, events)
            elif a_is_box and not b_is_box:
                _resolve_circle_vs_box_pair(b, a, events)  # (circle, box) order
            elif not a_is_box and b_is_box:
                _resolve_circle_vs_box_pair(a, b, events)
            else:
                _resolve_entity_pair(a, b, events)


# --- shared impulse/correction core, used by every pairing below ---

def _apply_pair_impulse(a, b, normal: Vec2, overlap: float, contact_point: Vec2,
                         events, restitution_a=None, restitution_b=None) -> None:
    """normal points from a to b. Used for entity-entity pairs (both
    always physics-capable, from the `colliders` list)."""
    ca, cb = a._collider, b._collider
    ra = ca.restitution if restitution_a is None else restitution_a
    rb = cb.restitution if restitution_b is None else restitution_b

    inv_mass_a = 0.0 if ca.static else 1.0 / max(a.mass, 1e-9)
    inv_mass_b = 0.0 if cb.static else 1.0 / max(b.mass, 1e-9)
    total_inv_mass = inv_mass_a + inv_mass_b
    if total_inv_mass == 0:
        return

    _wake(a)
    _wake(b)

    correction = normal * (overlap / total_inv_mass)
    if not ca.static:
        a.position -= correction * inv_mass_a
    if not cb.static:
        b.position += correction * inv_mass_b

    impulse = Vec2.zero()
    rel_vel = b.velocity - a.velocity
    vel_along_normal = rel_vel.dot(normal)
    if vel_along_normal <= 0:
        restitution = min(ra, rb)
        impulse_mag = -(1 + restitution) * vel_along_normal / total_inv_mass
        impulse = normal * impulse_mag
        if not ca.static:
            a.velocity -= impulse * inv_mass_a
        if not cb.static:
            b.velocity += impulse * inv_mass_b

    if not ca.static:
        a._prev_accel = compute_total_acceleration(a)
    if not cb.static:
        b._prev_accel = compute_total_acceleration(b)

    if not ca.static:
        _apply_torque_from_impulse(a, contact_point, -impulse)
    if not cb.static:
        _apply_torque_from_impulse(b, contact_point, impulse)

    events.append(CollisionEvent(a, b, contact_point, normal, impulse))


def _resolve_entity_pair(a, b, events) -> None:
    """circle vs circle (entity-entity)."""
    ca, cb = a._collider, b._collider
    delta = b.position - a.position
    dist = delta.length()
    min_dist = ca.radius + cb.radius
    if dist >= min_dist:
        return
    if dist == 0:
        delta = Vec2(1e-4, 0.0)
        dist = delta.length()

    normal = delta / dist
    overlap = min_dist - dist
    contact_point = (a.position + b.position) * 0.5
    _apply_pair_impulse(a, b, normal, overlap, contact_point, events)


def _resolve_box_vs_box_pair(a, b, events) -> None:
    """box vs box (entity-entity), oriented via each entity's .angle."""
    ca, cb = a._collider, b._collider
    result = sat_box_vs_box(a.position, a.angle, ca.width / 2.0, ca.height / 2.0,
                             b.position, b.angle, cb.width / 2.0, cb.height / 2.0)
    if result is None:
        return
    normal, overlap = result  # points from a to b
    contact_point = (a.position + b.position) * 0.5
    _apply_pair_impulse(a, b, normal, overlap, contact_point, events)


def _resolve_circle_vs_box_pair(circle_entity, box_entity, events) -> None:
    """circle vs box (entity-entity). Event/impulse convention: normal
    points from circle_entity (a) to box_entity (b), matching the
    (a, b) argument order used everywhere else."""
    circle_c = circle_entity._collider
    box_c = box_entity._collider
    hw, hh = box_c.width / 2.0, box_c.height / 2.0

    closest, inside, local_x, local_y = closest_point_on_box(
        circle_entity.position, box_entity.position, box_entity.angle, hw, hh)

    if inside:
        ax, ay = box_axes(box_entity.angle)
        dx = hw - abs(local_x)
        dy = hh - abs(local_y)
        if dx < dy:
            normal = ax * (-1.0 if local_x >= 0 else 1.0)  # points box->circle = a->b
            overlap = dx + circle_c.radius
        else:
            normal = ay * (-1.0 if local_y >= 0 else 1.0)
            overlap = dy + circle_c.radius
        contact_point = closest
    else:
        delta = circle_entity.position - closest
        dist = delta.length()
        if dist >= circle_c.radius:
            return
        normal = delta / dist  # points box->circle = a->b
        overlap = circle_c.radius - dist
        contact_point = closest

    _apply_pair_impulse(circle_entity, box_entity, normal, overlap, contact_point, events)


# --- entity vs SEO solid (existing circle-vs-* cases, plus new box-vs-*) ---

def _resolve_circle_vs_box(circle_entity, box_obj, events) -> None:
    collider = circle_entity._collider
    shape = box_obj.seo.shape
    solid_angle = getattr(box_obj, "angle", 0.0)
    hw, hh = shape.width / 2.0, shape.height / 2.0

    closest, inside, local_x, local_y = closest_point_on_box(
        circle_entity.position, box_obj.position, solid_angle, hw, hh)

    if inside:
        ax, ay = box_axes(solid_angle)
        dx = hw - abs(local_x)
        dy = hh - abs(local_y)
        if dx < dy:
            normal = ax * (1.0 if local_x >= 0 else -1.0)
            overlap = dx + collider.radius
        else:
            normal = ay * (1.0 if local_y >= 0 else -1.0)
            overlap = dy + collider.radius
    else:
        delta = circle_entity.position - closest
        dist = delta.length()
        if dist >= collider.radius:
            return
        normal = delta / dist
        overlap = collider.radius - dist

    _apply_solid_impulse(circle_entity, box_obj, normal, overlap, closest, events)


def _resolve_circle_vs_circle_solid(circle_entity, solid_obj, events) -> None:
    shape = solid_obj.seo.shape
    delta = circle_entity.position - solid_obj.position
    dist = delta.length()
    min_dist = circle_entity._collider.radius + shape.radius
    if dist >= min_dist:
        return
    if dist == 0:
        delta = Vec2(1e-4, 0.0)
        dist = delta.length()
    normal = delta / dist
    overlap = min_dist - dist
    contact_point = solid_obj.position + normal * shape.radius
    _apply_solid_impulse(circle_entity, solid_obj, normal, overlap, contact_point, events)


def _resolve_box_vs_seo_box(box_entity, seo_obj, events) -> None:
    collider = box_entity._collider
    shape = seo_obj.seo.shape
    seo_angle = getattr(seo_obj, "angle", 0.0)
    result = sat_box_vs_box(box_entity.position, box_entity.angle,
                             collider.width / 2.0, collider.height / 2.0,
                             seo_obj.position, seo_angle,
                             shape.width / 2.0, shape.height / 2.0)
    if result is None:
        return
    normal, overlap = result  # points from box_entity to seo_obj (entity->solid)
    contact_point = (box_entity.position + seo_obj.position) * 0.5
    # _apply_solid_impulse wants solid->entity, so flip
    _apply_solid_impulse(box_entity, seo_obj, normal * -1.0, overlap, contact_point, events)


def _resolve_box_vs_seo_circle(box_entity, seo_obj, events) -> None:
    collider = box_entity._collider
    shape = seo_obj.seo.shape
    hw, hh = collider.width / 2.0, collider.height / 2.0
    closest, inside, local_x, local_y = closest_point_on_box(
        seo_obj.position, box_entity.position, box_entity.angle, hw, hh)

    if inside:
        ax, ay = box_axes(box_entity.angle)
        dx = hw - abs(local_x)
        dy = hh - abs(local_y)
        if dx < dy:
            normal = ax * (1.0 if local_x >= 0 else -1.0)
            overlap = dx + shape.radius
        else:
            normal = ay * (1.0 if local_y >= 0 else -1.0)
            overlap = dy + shape.radius
        contact_point = closest
    else:
        delta = closest - seo_obj.position  # points from circle center to box surface = solid->entity
        dist = delta.length()
        if dist >= shape.radius:
            return
        normal = delta / dist
        overlap = shape.radius - dist
        contact_point = closest

    _apply_solid_impulse(box_entity, seo_obj, normal, overlap, contact_point, events)


def _apply_solid_impulse(entity, solid_obj, normal: Vec2, overlap: float,
                          contact_point: Vec2, events) -> None:
    """Shared impulse/positional-correction math for entity-vs-SEO
    collisions. `normal` points from the solid toward the entity.
    Shape-agnostic -- works for circle or box entities identically,
    since it only reads entity._collider.restitution (both shapes have it)."""
    solid_is_movable = has_physics(solid_obj)

    inv_mass_a = 1.0 / max(entity.mass, 1e-9)
    inv_mass_b = (1.0 / max(solid_obj.mass, 1e-9)) if solid_is_movable else 0.0
    total_inv_mass = inv_mass_a + inv_mass_b
    if total_inv_mass == 0:
        return

    _wake(entity)
    if solid_is_movable:
        _wake(solid_obj)

    correction = normal * (overlap / total_inv_mass)
    entity.position += correction * inv_mass_a
    if solid_is_movable:
        solid_obj.position -= correction * inv_mass_b

    solid_velocity = solid_obj.velocity if solid_is_movable else Vec2.zero()
    impulse = Vec2.zero()
    rel_vel = entity.velocity - solid_velocity
    vel_along_normal = rel_vel.dot(normal)
    if vel_along_normal <= 0:
        entity_restitution = entity._collider.restitution
        solid_restitution = solid_obj.seo.restitution
        restitution = min(entity_restitution, solid_restitution)
        impulse_mag = -(1 + restitution) * vel_along_normal / total_inv_mass
        impulse = normal * impulse_mag
        entity.velocity += impulse * inv_mass_a
        if solid_is_movable:
            solid_obj.velocity -= impulse * inv_mass_b

    entity._prev_accel = compute_total_acceleration(entity)
    if solid_is_movable:
        solid_obj._prev_accel = compute_total_acceleration(solid_obj)

    _apply_torque_from_impulse(entity, contact_point, impulse)
    if solid_is_movable:
        _apply_torque_from_impulse(solid_obj, contact_point, -impulse)

    # event convention is "normal points from a to b" (a=entity, b=solid);
    # the physics math above uses "normal points from solid to entity",
    # so flip it here to keep the event's documented contract consistent
    events.append(CollisionEvent(entity, solid_obj, contact_point, -normal, impulse))
