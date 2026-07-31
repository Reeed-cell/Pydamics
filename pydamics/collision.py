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

Naive O(n^2) broad-phase -- fine for tens to low hundreds of objects.
"""
from __future__ import annotations
from .vector import Vec2
from .physics_core import compute_total_acceleration, has_physics
from .seo import SEOShapeBox, SEOShapeCircle


def resolve_all_collisions(entities, solids) -> None:
    """entities: physics-capable objects (may or may not have a collider).
    solids: SEO objects to check entities against (may or may not be
    physics-capable themselves -- "physicsified" solids)."""
    colliders = [e for e in entities if getattr(e, "_collider", None) is not None]

    n = len(colliders)
    for i in range(n):
        for j in range(i + 1, n):
            _resolve_entity_pair(colliders[i], colliders[j])

    for entity in colliders:
        for solid in solids:
            if solid is entity:
                continue
            if not hasattr(solid, "seo") or solid.seo.shape is None:
                continue
            if isinstance(solid.seo.shape, SEOShapeBox):
                _resolve_circle_vs_box(entity, solid)
            elif isinstance(solid.seo.shape, SEOShapeCircle):
                _resolve_circle_vs_circle_solid(entity, solid)


def _resolve_entity_pair(a, b) -> None:
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

    correction = normal * (overlap / total_inv_mass)
    if not ca.static:
        a.position -= correction * inv_mass_a
    if not cb.static:
        b.position += correction * inv_mass_b

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


def _resolve_circle_vs_box(circle_entity, box_obj) -> None:
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

    _apply_solid_impulse(circle_entity, box_obj, normal, overlap)


def _resolve_circle_vs_circle_solid(circle_entity, solid_obj) -> None:
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
    _apply_solid_impulse(circle_entity, solid_obj, normal, overlap)


def _apply_solid_impulse(entity, solid_obj, normal: Vec2, overlap: float) -> None:
    """Shared impulse/positional-correction math for entity-vs-SEO
    collisions. `normal` points from the solid toward the entity."""
    solid_is_movable = has_physics(solid_obj)

    inv_mass_a = 1.0 / max(entity.mass, 1e-9)
    inv_mass_b = (1.0 / max(solid_obj.mass, 1e-9)) if solid_is_movable else 0.0
    total_inv_mass = inv_mass_a + inv_mass_b
    if total_inv_mass == 0:
        return

    correction = normal * (overlap / total_inv_mass)
    entity.position += correction * inv_mass_a
    if solid_is_movable:
        solid_obj.position -= correction * inv_mass_b

    solid_velocity = solid_obj.velocity if solid_is_movable else Vec2.zero()
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
