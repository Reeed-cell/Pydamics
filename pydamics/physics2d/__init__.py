"""
The Physics2D namespace -- this is what you get from `obj.physics2d`
after pydamics.attach() (or Entity.__init__, or pydamics.classify()
with kind including "rigid"/"gas").

Usage:
    ball.physics2d.gravity(force=9.8)
    ball.physics2d.fluid(density=1.2, drag=0.3)
    ball.physics2d.spring(anchor=Vec2(0, 10), stiffness=15.0)
    ball.physics2d.wind(force=3.0, gust=1.0)
    ball.physics2d.attractor(target=sun, strength=200.0)
    ball.physics2d.vortex(center=Vec2(0, 0), strength=20.0)
    ball.physics2d.buoyancy(zone=pool, radius=0.4)
    ball.physics2d.gas(zone=air_current)
    ball.physics2d.collider(radius=0.4, restitution=0.7)

Chainable setters (each returns self, so they stack):
    ball.physics2d.mass(9).velocity(0, 0).position(0, 10)
"""
from __future__ import annotations
from ..vector import Vec2
from .forces import (
    Force, Gravity, Fluid, Friction, Spring, Wind, Attractor, Buoyancy,
    Vortex, GasPush, Torque, ConstantTorque,
)
from .collider import CircleCollider
from .box_collider import BoxCollider


class Physics2D:
    """Attached to any physics-capable object (via attach() or Entity).
    Each force-attaching method call creates a Force and registers it on
    the owning object, then returns the Force object so it can be
    removed or tweaked later. `.collider()` is separate -- it's not a
    force, it's a shape used by the World's collision pass. The plain
    setters (`.mass()`, `.position()`, etc.) return `self` (the Physics2D
    namespace) instead, so they can be chained together."""

    def __init__(self, entity):
        self._entity = entity

    # --- forces ---

    def gravity(self, force: float = 9.8, direction=None) -> Gravity:
        f = Gravity(force=force, direction=direction)
        self._entity._add_force(f)
        return f

    def fluid(self, density: float = 1.0, drag: float = 0.1) -> Fluid:
        f = Fluid(density=density, drag=drag)
        self._entity._add_force(f)
        return f

    def friction(self, coefficient: float = 0.3, normal_force: float = 9.8) -> Friction:
        f = Friction(coefficient=coefficient, normal_force=normal_force)
        self._entity._add_force(f)
        return f

    def spring(self, anchor, stiffness: float = 10.0, rest_length: float = 1.0,
               damping: float = 0.1) -> Spring:
        f = Spring(anchor=anchor, stiffness=stiffness, rest_length=rest_length,
                   damping=damping)
        self._entity._add_force(f)
        return f

    def wind(self, force: float = 2.0, direction=None, gust: float = 0.0) -> Wind:
        f = Wind(force=force, direction=direction, gust=gust)
        self._entity._add_force(f)
        return f

    def attractor(self, target, strength: float = 50.0, min_distance: float = 0.1) -> Attractor:
        f = Attractor(target=target, strength=strength, min_distance=min_distance)
        self._entity._add_force(f)
        return f

    def vortex(self, center, strength: float = 20.0, min_distance: float = 0.1) -> Vortex:
        f = Vortex(center=center, strength=strength, min_distance=min_distance)
        self._entity._add_force(f)
        return f

    def buoyancy(self, zone, radius: float = 0.4, gravity: float = 9.8) -> Buoyancy:
        f = Buoyancy(zone=zone, radius=radius, gravity=gravity)
        self._entity._add_force(f)
        return f

    def gas(self, zone) -> GasPush:
        """Constant x-only push while inside a GasZone -- the deliberately
        minimal 'gas' counterpart to .buoyancy(). See GasZone/GasPush for
        what's intentionally NOT here (no drag, gust, y-component)."""
        f = GasPush(zone=zone)
        self._entity._add_force(f)
        return f

    def custom(self, force: Force) -> Force:
        """Attach any custom Force subclass."""
        self._entity._add_force(force)
        return force

    def remove(self, force: Force) -> None:
        self._entity._remove_force(force)

    def clear(self) -> None:
        self._entity._clear_forces()

    # --- collider shape ---

    def collider(self, radius: float = 0.5, restitution: float = 0.6,
                 static: bool = False, layer: str = "default", collides_with=None,
                 shape: str = "circle", width: float = 1.0, height: float = 1.0):
        """Give this object a collision shape -- the World's step() will
        detect and resolve overlaps with other colliders (and with SEO
        solids) automatically. `layer`/`collides_with` filter which
        other colliders/solids this one actually interacts with
        (symmetric-AND -- see CircleCollider for details).

        shape="circle" (default, uses radius) or shape="box" (uses
        width/height, oriented by the entity's `.angle` -- rotate it by
        setting angle/angular_velocity/torque like anything else)."""
        if shape == "box":
            c = BoxCollider(width=width, height=height, restitution=restitution,
                             static=static, layer=layer, collides_with=collides_with)
        else:
            c = CircleCollider(radius=radius, restitution=restitution, static=static,
                                layer=layer, collides_with=collides_with)
        self._entity._collider = c
        return c

    # --- chainable setters (each returns self, not the underlying value) ---

    def mass(self, value: float) -> "Physics2D":
        """Update mass after construction. Returns self for chaining."""
        self._entity.mass = float(value)
        return self

    def position(self, x: float, y: float) -> "Physics2D":
        """Update position after construction. Returns self for chaining."""
        self._entity.position = Vec2(x, y)
        return self

    def velocity(self, x: float, y: float) -> "Physics2D":
        """Update velocity after construction. Returns self for chaining."""
        self._entity.velocity = Vec2(x, y)
        return self

    def _require_collider(self, setter_name: str) -> CircleCollider:
        if self._entity._collider is None:
            raise RuntimeError(
                f"{type(self._entity).__name__} has no collider yet -- "
                f"call .physics2d.collider(...) before "
                f".physics2d.{setter_name}(...). Setting collider-only "
                f"properties on an object that isn't a collider is an "
                f"incorrect-properties-for-this-kind error."
            )
        return self._entity._collider

    def restitution(self, value: float) -> "Physics2D":
        """Update collider bounciness after the fact. Requires
        .collider(...) to have been called first -- raises RuntimeError
        otherwise. Returns self for chaining."""
        self._require_collider("restitution").restitution = value
        return self

    def radius(self, value: float) -> "Physics2D":
        """Update collider size after the fact. Requires .collider(...)
        to have been called first -- raises RuntimeError otherwise.
        Returns self for chaining."""
        self._require_collider("radius").radius = value
        return self

    def static(self, value: bool) -> "Physics2D":
        """Toggle whether a collider is static after the fact. Requires
        .collider(...) to have been called first -- raises RuntimeError
        otherwise. Returns self for chaining."""
        self._require_collider("static").static = bool(value)
        return self

    # --- torque (rotational analog of forces) ---

    def torque(self, magnitude: float = 5.0) -> ConstantTorque:
        """Attach a steady torque (applied every step until removed).
        Returns the Torque object so it can be held onto and removed
        later, same pattern as the force-attaching methods."""
        t = ConstantTorque(magnitude=magnitude)
        self._entity._add_torque(t)
        return t

    def custom_torque(self, torque: Torque) -> Torque:
        """Attach any custom Torque subclass (implement compute_torque(entity))."""
        self._entity._add_torque(torque)
        return torque

    def remove_torque(self, torque: Torque) -> None:
        if torque in self._entity._torques:
            self._entity._torques.remove(torque)

    # --- collision events ---

    def on_collision(self, callback) -> None:
        """Register callback(other, contact_point, normal, impulse) --
        called every step this object is involved in a resolved
        collision. `normal` points away from `other` (i.e. "the
        direction I got pushed")."""
        self._entity._collision_callbacks.append(callback)

    # --- sleep / deactivation ---

    @property
    def sleep_threshold(self):
        """Velocity magnitude below which this object can fall asleep
        (skipped by force computation/integration until woken). None
        (the default) disables sleeping entirely -- opt-in only."""
        return self._entity._sleep_threshold

    @sleep_threshold.setter
    def sleep_threshold(self, value) -> None:
        self._entity._sleep_threshold = value
        if value is None:
            self._entity._is_sleeping = False
            self._entity._sleep_still_time = 0.0

    @property
    def is_sleeping(self) -> bool:
        return self._entity._is_sleeping

    def wake(self) -> None:
        """Wake this object up immediately (e.g. after being hit) and
        reset its still-time counter."""
        self._entity._is_sleeping = False
        self._entity._sleep_still_time = 0.0


__all__ = [
    "Physics2D", "Force", "Gravity", "Fluid", "Friction", "Spring", "Wind",
    "Attractor", "Vortex", "Buoyancy", "GasPush", "CircleCollider", "BoxCollider",
    "Torque", "ConstantTorque",
]
