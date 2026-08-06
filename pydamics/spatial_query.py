"""
Spatial query API -- "give me every entity within this radius/rect,"
distinct from raycasting ("what's the first thing a ray hits"). Needed
for AOE damage, radar/minimap logic, aggro range, proximity puzzles.

    nearby = world.query_radius(center=(0,0), radius=50)
    in_box = world.query_rect(min_point=(0,0), max_point=(100,100))

Uses the existing SpatialHash to avoid an O(n) scan over every entity.
"""
from __future__ import annotations
from .vector import Vec2
from .spatial_hash import SpatialHash


def query_radius(entities, center, radius: float):
    center = center if isinstance(center, Vec2) else Vec2(*center)
    if not entities:
        return []

    grid = SpatialHash(cell_size=max(radius, 1e-6))
    grid.rebuild(entities)

    seen = set()
    results = []
    for candidate in grid.query_neighbors(center):
        if id(candidate) in seen:
            continue
        seen.add(id(candidate))
        if (candidate.position - center).length() <= radius:
            results.append(candidate)
    return results


def query_rect(entities, min_point, max_point):
    min_point = min_point if isinstance(min_point, Vec2) else Vec2(*min_point)
    max_point = max_point if isinstance(max_point, Vec2) else Vec2(*max_point)
    if not entities:
        return []

    width = max(max_point.x - min_point.x, 1e-6)
    height = max(max_point.y - min_point.y, 1e-6)
    cell_size = max(width, height)
    grid = SpatialHash(cell_size=cell_size)
    grid.rebuild(entities)

    center = Vec2((min_point.x + max_point.x) / 2.0, (min_point.y + max_point.y) / 2.0)

    seen = set()
    results = []
    for candidate in grid.query_neighbors(center):
        if id(candidate) in seen:
            continue
        seen.add(id(candidate))
        pos = candidate.position
        if min_point.x <= pos.x <= max_point.x and min_point.y <= pos.y <= max_point.y:
            results.append(candidate)
    return results
