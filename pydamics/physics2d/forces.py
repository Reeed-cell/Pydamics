"""
Force definitions for the 2D physics namespace.

Every force is a small object with a compute_acceleration(entity) method.
Forces are persistent once attached -- they get evaluated every world.step().
"""
from __future__ import annotations
from ..vector import Vec2


class Force:
    """Base class for all attachable forces."""

    name = "force"

    def compute_acceleration(self, entity) -> Vec2:
        """Return the acceleration (not force!) this contributes to the entity."""
        raise NotImplementedError


class Gravity(Force):
    name = "gravity"

    def __init__(self, force: float = 9.8, direction: Vec2 | None = None):
        # force is treated as an acceleration magnitude (like 9.8 m/s^2),
        # applied along `direction` (default: straight down, -y).
        self.force = force
        self.direction = (direction or Vec2(0, -1)).normalized()

    def compute_acceleration(self, entity) -> Vec2:
        return self.direction * self.force


class Fluid(Force):
    """Simple drag force proportional to velocity (air/water resistance)."""

    name = "fluid"

    def __init__(self, density: float = 1.0, drag: float = 0.1):
        self.density = density
        self.drag = drag

    def compute_acceleration(self, entity) -> Vec2:
        v = entity.velocity
        speed = v.length()
        if speed == 0:
            return Vec2.zero()
        drag_accel_mag = self.density * self.drag * speed
        # acceleration opposes velocity direction
        return v.normalized() * -drag_accel_mag / max(entity.mass, 1e-9)


class Friction(Force):
    """Kinetic friction opposing motion, proportional to a normal force magnitude."""

    name = "friction"

    def __init__(self, coefficient: float = 0.3, normal_force: float = 9.8):
        self.coefficient = coefficient
        self.normal_force = normal_force

    def compute_acceleration(self, entity) -> Vec2:
        v = entity.velocity
        if v.length() == 0:
            return Vec2.zero()
        friction_mag = self.coefficient * self.normal_force
        return v.normalized() * -friction_mag / max(entity.mass, 1e-9)
