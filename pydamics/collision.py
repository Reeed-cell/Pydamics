"""
Circle collision detection and impulse-based response.

Unlike Force (which computes a per-entity acceleration independently),
collision needs to compare PAIRS of objects, so it's handled as an extra
phase in World.step() rather than through the physics2d Force system.

Two kinds of collision are handled here:
  1. entity vs entity  -- both have a CircleCollider (`.physics2d.collider()`)
  2. entity vs solid    -- an entity with a CircleCollider against an SEO
                            object (`.seo.solid()`), which may be a box or
                            a circle, and may itself be physics-capable
                            (a "physicsified" solid) or purely static

Uses a spatial hash for the entity-entity broad-phase (see
spatial_hash.py) instead of a naive O(n^2) scan, so this scales well
past a few dozen colliding objects. Entity-vs-solid checks stay a
simple scan against the (usually much shorter) solids list.

resolve_all_collisions() returns a list of CollisionEvent for whatever
was actually resolved this step -- World.step() uses this to dispatch
on_collision callbacks (both world.on_collision() and per-object
.physics2d.on_collision()), apply torque from off-center impulses, and
wake sleeping objects that got hit.
"""
from __future__ import annotations
from .vector import Vec2
from .physics_core import compute_total_acceleration, has_physics
from .seo import SEOShapeBox, SEOShapeCircle
from .spatial_hash import SpatialHash


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
    anything with .layer/.collides_with (CircleCollider or SEO)."""
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
            if isinstance(solid.seo.shape, SEOShapeBox):
                _resolve_circle_vs_box(entity, solid, events)
            elif isinstance(solid.seo.shape, SEOShapeCircle):
                _resolve_circle_vs_circle_solid(entity, solid, events)

    return events


def _resolve_entity_entity_collisions(colliders, events) -> None:
    n = len(colliders)
    if n < 2:
        return

    # cell size >= any possible collision distance (sum of the two
    # largest radii) guarantees no true overlap gets missed -- this only
    # reduces which pairs get checked, never which pairs actually collide
    max_radius = max(c._collider.radius for c in colliders)
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
            _resolve_entity_pair(a, b, events)


def _resolve_entity_pair(a, b, events) -> None:
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
        restitution = min(ca.restitution, cb.restitution)
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

    contact_point = (a.position + b.position) * 0.5
    if not ca.static:
        _apply_torque_from_impulse(a, contact_point, -impulse)
    if not cb.static:
        _apply_torque_from_impulse(b, contact_point, impulse)

    events.append(CollisionEvent(a, b, contact_point, normal, impulse))


def _resolve_circle_vs_box(circle_entity, box_obj, events) -> None:
    collider = circle_entity._collider
    shape = box_obj.seo.shape
    half_w = shape.width / 2.0
    half_h = shape.height / 2.0
    box_center = box_obj.position

    closest_x = max(box_center.x - half_w, min(circle_entity.position.x, box_center.x + half_w))
    closest_y = max(box_center.y - half_h, min(circle_entity.position.y, box_center.y + half_h))
    closest = Vec2(closest_x, closest_y)

    delta = circle_entity.position - closest
    dist = delta.length()

    if dist == 0:
        # circle center is inside the box -- push out along the shallowest axis
        dx = (half_w + collider.radius) - abs(circle_entity.position.x - box_center.x)
        dy = (half_h + collider.radius) - abs(circle_entity.position.y - box_center.y)
        if dx < dy:
            normal = Vec2(1.0 if circle_entity.position.x >= box_center.x else -1.0, 0.0)
            overlap = dx
        else:
            normal = Vec2(0.0, 1.0 if circle_entity.position.y >= box_center.y else -1.0)
            overlap = dy
    elif dist < collider.radius:
        normal = delta / dist
        overlap = collider.radius - dist
    else:
        return  # not overlapping

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


def _apply_solid_impulse(entity, solid_obj, normal: Vec2, overlap: float,
                          contact_point: Vec2, events) -> None:
    """Shared impulse/positional-correction math for entity-vs-SEO
    collisions. `normal` points from the solid toward the entity."""
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
