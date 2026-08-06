"""
Raycasting -- "what's the nearest solid/entity along this line?"

    hit = world.raycast(origin=(0,0), direction=Vec2(1,0), max_distance=500)
    if hit:
        print(hit.entity, hit.point, hit.distance, hit.normal)

    hits = world.raycast_all(origin=(0,0), direction=Vec2(1,0), max_distance=500)
    # -> sorted list of all hits along the ray, nearest first

A spatial query against the world's own collision geometry (circles and
boxes, entities and SEO solids), using the existing SpatialHash for
broad-phase: instead of narrow-phase-testing every collidable object in
the scene, only objects near sample points along the ray are tested.
Explicitly NOT in scope: pathfinding built on repeated raycasts -- that's
app/AI-layer logic, not physics.
"""
from __future__ import annotations
import math
from .vector import Vec2
from .spatial_hash import SpatialHash
from .physics2d.box_collider import BoxCollider
from .seo import SEOShapeBox, SEOShapeCircle
from .sat import closest_point_on_box, box_axes


class RaycastHit:
    __slots__ = ("entity", "point", "distance", "normal")

    def __init__(self, entity, point, distance, normal):
        self.entity = entity
        self.point = point
        self.distance = distance
        self.normal = normal

    def __repr__(self) -> str:
        return f"RaycastHit(entity={self.entity!r}, distance={self.distance:.3f})"


def _ray_vs_circle(origin: Vec2, direction: Vec2, max_distance: float,
                    center: Vec2, radius: float):
    """Returns (distance, point, normal) of the nearest intersection, or None."""
    oc = origin - center
    b = oc.dot(direction)
    c = oc.dot(oc) - radius * radius
    discriminant = b * b - c
    if discriminant < 0:
        return None
    sqrt_disc = math.sqrt(discriminant)
    t1 = -b - sqrt_disc
    t2 = -b + sqrt_disc
    t = t1 if t1 >= 0 else t2
    if t < 0 or t > max_distance:
        return None
    point = origin + direction * t
    normal = (point - center).normalized()
    return t, point, normal


def _ray_vs_box(origin: Vec2, direction: Vec2, max_distance: float,
                 box_position: Vec2, angle: float, half_width: float, half_height: float):
    """Slab method in the box's local (rotated) frame. Returns
    (distance, point, normal) or None."""
    ax, ay = box_axes(angle)
    rel = origin - box_position
    local_origin_x = rel.dot(ax)
    local_origin_y = rel.dot(ay)
    local_dir_x = direction.dot(ax)
    local_dir_y = direction.dot(ay)

    t_min, t_max = 0.0, max_distance
    normal_axis = None
    normal_sign = 1.0

    for local_o, local_d, half, axis in (
        (local_origin_x, local_dir_x, half_width, ax),
        (local_origin_y, local_dir_y, half_height, ay),
    ):
        if abs(local_d) < 1e-12:
            if local_o < -half or local_o > half:
                return None  # parallel to this slab and outside it
            continue
        t1 = (-half - local_o) / local_d
        t2 = (half - local_o) / local_d
        sign1 = -1.0
        if t1 > t2:
            t1, t2 = t2, t1
            sign1 = 1.0
        if t1 > t_min:
            t_min = t1
            normal_axis = axis
            normal_sign = sign1
        t_max = min(t_max, t2)
        if t_min > t_max:
            return None

    if normal_axis is None or t_min < 0 or t_min > max_distance:
        return None

    point = origin + direction * t_min
    normal = normal_axis * normal_sign
    return t_min, point, normal


def _collect_candidates(entities, solids, origin: Vec2, direction: Vec2, max_distance: float):
    """Broad-phase: sample points along the ray, gather nearby colliders
    via the spatial hash, dedupe. Correct (never misses a true hit near a
    sampled point) as long as the sample spacing is <= the hash cell size,
    which it is by construction below."""
    collidable = [(e, e._collider) for e in entities if getattr(e, "_collider", None) is not None]
    collidable += [(s, s.seo.shape) for s in solids if hasattr(s, "seo") and s.seo.shape is not None]
    if not collidable:
        return []

    def _reach(shape):
        if isinstance(shape, (BoxCollider, SEOShapeBox)):
            return math.hypot(shape.width / 2.0, shape.height / 2.0)
        return shape.radius

    max_reach = max(_reach(shape) for _, shape in collidable)
    cell_size = max(max_reach * 2.0, 1e-6)
    grid = SpatialHash(cell_size=cell_size)
    grid.rebuild(collidable, position_of=lambda pair: pair[0].position)

    candidates = {}
    steps = max(1, int(max_distance / cell_size) + 1)
    for i in range(steps + 1):
        sample_point = origin + direction * (i * cell_size)
        for obj, shape in grid.query_neighbors(sample_point):
            candidates[id(obj)] = (obj, shape)

    return list(candidates.values())


def _raycast_hits(entities, solids, origin, direction, max_distance: float, collides_with=None):
    direction = direction.normalized()
    hits = []
    for obj, shape in _collect_candidates(entities, solids, origin, direction, max_distance):
        if collides_with is not None:
            layer = getattr(shape, "layer", "default")
            if layer not in collides_with:
                continue

        if isinstance(shape, (BoxCollider, SEOShapeBox)):
            angle = getattr(obj, "angle", 0.0)
            result = _ray_vs_box(origin, direction, max_distance, obj.position, angle,
                                  shape.width / 2.0, shape.height / 2.0)
        else:
            result = _ray_vs_circle(origin, direction, max_distance, obj.position, shape.radius)

        if result is not None:
            distance, point, normal = result
            hits.append(RaycastHit(obj, point, distance, normal))

    hits.sort(key=lambda h: h.distance)
    return hits


def raycast(entities, solids, origin, direction, max_distance: float = float("inf"),
            collides_with=None):
    """Nearest hit along the ray, or None."""
    origin = origin if isinstance(origin, Vec2) else Vec2(*origin)
    direction = direction if isinstance(direction, Vec2) else Vec2(*direction)
    hits = _raycast_hits(entities, solids, origin, direction, max_distance, collides_with)
    return hits[0] if hits else None


def raycast_all(entities, solids, origin, direction, max_distance: float = float("inf"),
                 collides_with=None):
    """All hits along the ray, nearest first."""
    origin = origin if isinstance(origin, Vec2) else Vec2(*origin)
    direction = direction if isinstance(direction, Vec2) else Vec2(*direction)
    return _raycast_hits(entities, solids, origin, direction, max_distance, collides_with)
