"""
GasZone -- a stripped-down cousin of FluidZone for simple ambient air
current effects. Structurally the same idea (a rectangular region), but
deliberately missing everything FluidZone has: no buoyancy, no
pressure/SPH, no drag, no gust, no y-component or direction vector to
configure. Just a constant push along x for anything inside.

If you need buoyancy, drag, or genuine fluid-like behavior, use
FluidZone or FluidSystem instead -- GasZone is intentionally minimal.
"""
from __future__ import annotations
from .vector import Vec2


class GasZone:
    def __init__(self, min_point, max_point, force: float = 1.0):
        """
        min_point/max_point: opposite corners of the rectangular zone.
        force: constant push magnitude along +x for anything inside
               (negative values push in -x).
        """
        self.min_point = min_point.copy() if isinstance(min_point, Vec2) else Vec2(*min_point)
        self.max_point = max_point.copy() if isinstance(max_point, Vec2) else Vec2(*max_point)
        self.force = force

    def contains(self, position: Vec2) -> bool:
        return (self.min_point.x <= position.x <= self.max_point.x and
                self.min_point.y <= position.y <= self.max_point.y)
