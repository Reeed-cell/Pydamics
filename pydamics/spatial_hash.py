"""
Uniform grid spatial hash for broad-phase neighbor queries.

Splits space into square cells of a given size; objects are bucketed by
the cell their position falls in. If cell_size >= your search radius,
querying neighbors only needs to check an object's own cell plus its 8
surrounding cells, instead of comparing against every other object --
turns O(n^2) into roughly O(n) for reasonably uniform distributions.

Used internally by collision.py (entity-entity broad-phase) and sph.py
(SPH neighbor search) -- rebuilt fresh each step, since it's cheap
relative to the O(n^2) it replaces.
"""
from __future__ import annotations
import math
from .vector import Vec2


class SpatialHash:
    def __init__(self, cell_size: float):
        self.cell_size = max(cell_size, 1e-6)
        self._buckets: dict[tuple[int, int], list] = {}

    def _cell_of(self, position: Vec2) -> tuple[int, int]:
        return (math.floor(position.x / self.cell_size), math.floor(position.y / self.cell_size))

    def clear(self) -> None:
        self._buckets.clear()

    def insert(self, obj, position: Vec2) -> None:
        cell = self._cell_of(position)
        self._buckets.setdefault(cell, []).append(obj)

    def rebuild(self, objects, position_of=lambda o: o.position) -> None:
        self.clear()
        for obj in objects:
            self.insert(obj, position_of(obj))

    def query_neighbors(self, position: Vec2):
        """Yield every object bucketed in the same cell as `position` or
        one of its 8 surrounding cells (candidates only -- caller still
        needs to check actual distance, since this is a broad-phase)."""
        cx, cy = self._cell_of(position)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                bucket = self._buckets.get((cx + dx, cy + dy))
                if bucket:
                    yield from bucket
