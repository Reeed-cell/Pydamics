"""
FluidZone -- a rectangular region of fluid (a pool, a tank, an ocean
surface). Doesn't do anything on its own; attach `.physics2d.buoyancy(zone)`
to an entity to make it respond to a zone (Archimedes-style buoyancy +
extra drag while submerged).
"""
from __future__ import annotations
from .vector import Vec2


class FluidZone:
    def __init__(self, min_point, max_point, density: float = 1.0, drag: float = 2.0):
        """
        min_point/max_point: opposite corners of the rectangular zone
                              (world y-up coords). max_point.y is the
                              waterline/surface.
        density: fluid density RELATIVE to your entities' own effective
                 density (mass / (pi * radius^2), a 2D area-based analog
                 of density) -- NOT meant as a literal real-world kg/m^3
                 value. If an entity's mass/radius gives it an effective
                 density of ~1.0 and this zone is density=2.0, that
                 entity floats (roughly twice as buoyant as its weight);
                 density=0.5 and it sinks. Pick values relative to what
                 your entities' mass/radius actually imply.
        drag:    extra velocity-proportional drag applied while submerged,
                 scaled by how much of the entity is underwater.
        """
        self.min_point = min_point if isinstance(min_point, Vec2) else Vec2(*min_point)
        self.max_point = max_point if isinstance(max_point, Vec2) else Vec2(*max_point)
        self.density = density
        self.drag = drag

    def contains_x(self, position: Vec2) -> bool:
        return self.min_point.x <= position.x <= self.max_point.x

    def submerged_fraction(self, position: Vec2, radius: float) -> float:
        """Rough linear estimate (not exact circle-segment area) of how
        much of a circle of `radius` centered at `position` is below the
        zone's waterline (max_point.y) and above its floor (min_point.y).
        Good enough for game-like buoyancy, not for scientific accuracy."""
        if not self.contains_x(position):
            return 0.0

        top_surface = self.max_point.y
        floor = self.min_point.y
        bottom_of_circle = position.y - radius
        top_of_circle = position.y + radius

        if bottom_of_circle >= top_surface or top_of_circle <= floor:
            return 0.0

        submerged_top = min(top_of_circle, top_surface)
        submerged_bottom = max(bottom_of_circle, floor)
        submerged_height = max(0.0, submerged_top - submerged_bottom)
        full_height = 2 * radius
        if full_height == 0:
            return 0.0
        return max(0.0, min(1.0, submerged_height / full_height))
