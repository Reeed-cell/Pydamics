"""
Force definitions for the 2D physics namespace.

Every force is a small object with a compute_acceleration(entity) method.
Forces are persistent once attached -- they get evaluated every world.step().
"""
from __future__ import annotations
import math
import random
from ..vector import Vec2
from ..fluid_zone import FluidZone
from ..gas import GasZone


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


class Spring(Force):
    """Hooke's-law spring pulling/pushing the entity toward an anchor,
    with damping. The anchor can be a fixed Vec2 point, or another
    physics-capable object -- if it's an object, its `.position` (and
    `.velocity`, for damping) are read live every step, so the spring
    follows a moving anchor."""

    name = "spring"

    def __init__(self, anchor, stiffness: float = 10.0, rest_length: float = 1.0,
                 damping: float = 0.1):
        self.anchor = anchor
        self.stiffness = stiffness
        self.rest_length = rest_length
        self.damping = damping

    def _anchor_position(self) -> Vec2:
        return self.anchor if isinstance(self.anchor, Vec2) else self.anchor.position

    def _anchor_velocity(self) -> Vec2:
        if isinstance(self.anchor, Vec2):
            return Vec2.zero()
        return getattr(self.anchor, "velocity", Vec2.zero())

    def compute_acceleration(self, entity) -> Vec2:
        delta = entity.position - self._anchor_position()
        length = delta.length()
        if length == 0:
            return Vec2.zero()
        direction = delta.normalized()
        stretch = length - self.rest_length

        spring_force_mag = -self.stiffness * stretch
        rel_vel = entity.velocity - self._anchor_velocity()
        damping_force_mag = -self.damping * rel_vel.dot(direction)

        total_force_mag = spring_force_mag + damping_force_mag
        return direction * (total_force_mag / max(entity.mass, 1e-9))


class Wind(Force):
    """A constant directional acceleration, optionally gusting (randomly
    varying in magnitude each step). Similar to Gravity but meant for
    arbitrary/horizontal directions and less "always-on" force fields."""

    name = "wind"

    def __init__(self, force: float = 2.0, direction: Vec2 | None = None, gust: float = 0.0):
        self.force = force
        self.direction = (direction or Vec2(1, 0)).normalized()
        self.gust = gust  # +/- random variation added to force each step; 0 = steady wind

    def compute_acceleration(self, entity) -> Vec2:
        magnitude = self.force
        if self.gust:
            magnitude += random.uniform(-self.gust, self.gust)
        return self.direction * magnitude


class Attractor(Force):
    """Inverse-square attraction toward a point or another physics-capable
    object -- e.g. simple orbital gravity around a planet/star, as opposed
    to Gravity's constant downward pull. `min_distance` avoids blow-up as
    distance approaches zero."""

    name = "attractor"

    def __init__(self, target, strength: float = 50.0, min_distance: float = 0.1):
        self.target = target  # Vec2 or physics-capable object
        self.strength = strength
        self.min_distance = min_distance

    def _target_position(self) -> Vec2:
        return self.target if isinstance(self.target, Vec2) else self.target.position

    def compute_acceleration(self, entity) -> Vec2:
        delta = self._target_position() - entity.position
        dist = max(delta.length(), self.min_distance)
        direction = delta / dist
        accel_mag = self.strength / (dist * dist)
        return direction * accel_mag


class Buoyancy(Force):
    """Archimedes-principle buoyancy + extra drag while inside a FluidZone,
    scaled by how submerged the entity currently is. Buoyant acceleration
    is g * fraction * (zone.density / entity_density - 1), where
    entity_density is derived from the entity's own mass and `radius`
    (treated as a 2D circle, area = pi*r^2) -- so it's the DENSITY RATIO
    that matters, not either value in isolation. Pick zone.density and
    your entities' mass/radius so that ratio is sane for your scene; a
    wildly mismatched ratio will (correctly, physically) produce a
    wildly large force, the same way a helium balloon dropped in water
    would rocket upward in real life."""

    name = "buoyancy"

    def __init__(self, zone: FluidZone, radius: float = 0.4, gravity: float = 9.8):
        self.zone = zone
        self.radius = radius
        self.gravity = gravity

    def compute_acceleration(self, entity) -> Vec2:
        fraction = self.zone.submerged_fraction(entity.position, self.radius)
        if fraction <= 0:
            return Vec2.zero()

        area = math.pi * self.radius * self.radius
        entity_density = entity.mass / max(area, 1e-9)

        buoyant_accel_mag = self.gravity * fraction * (
            self.zone.density / max(entity_density, 1e-9) - 1.0
        )
        accel = Vec2(0, buoyant_accel_mag)

        v = entity.velocity
        speed = v.length()
        if speed > 0:
            drag_accel_mag = self.zone.drag * fraction * speed
            accel -= v.normalized() * (drag_accel_mag / max(entity.mass, 1e-9))

        return accel


class Vortex(Force):
    """Tangential (perpendicular-to-radius) force around a center point --
    creates swirling/cyclone motion, distinct from Attractor's radial pull.
    Positive `strength` swirls counter-clockwise, negative clockwise."""

    name = "vortex"

    def __init__(self, center, strength: float = 20.0, min_distance: float = 0.1):
        self.center = center  # Vec2 or physics-capable object
        self.strength = strength
        self.min_distance = min_distance

    def _center_position(self) -> Vec2:
        return self.center if isinstance(self.center, Vec2) else self.center.position

    def compute_acceleration(self, entity) -> Vec2:
        delta = entity.position - self._center_position()
        dist = max(delta.length(), self.min_distance)
        radial = delta / dist
        tangent = Vec2(-radial.y, radial.x)  # perpendicular to radial, CCW
        accel_mag = self.strength / dist
        return tangent * accel_mag


class GasPush(Force):
    """Constant push along x while inside a GasZone -- the deliberately
    minimal 'gas' counterpart to Buoyancy: no y-component, no drag, no
    gust, no direction vector. Use Wind or Fluid instead if you need
    those."""

    name = "gas_push"

    def __init__(self, zone: GasZone):
        self.zone = zone

    def compute_acceleration(self, entity) -> Vec2:
        if not self.zone.contains(entity.position):
            return Vec2.zero()
        return Vec2(self.zone.force, 0.0)
