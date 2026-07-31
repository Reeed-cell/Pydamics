"""
The Physics2D namespace -- this is what you get from `obj.physics2d`
after pydamics.attach() (or Entity.__init__, which calls attach() for you).

Usage:
    ball.physics2d.gravity(force=9.8)
    ball.physics2d.fluid(density=1.2, drag=0.3)
    ball.physics2d.spring(anchor=Vec2(0, 10), stiffness=15.0)
    ball.physics2d.wind(force=3.0, gust=1.0)
    ball.physics2d.attractor(target=sun, strength=200.0)
    ball.physics2d.vortex(center=Vec2(0, 0), strength=20.0)
    ball.physics2d.buoyancy(zone=pool, radius=0.4)
    ball.physics2d.collider(radius=0.4, restitution=0.7)
"""
from __future__ import annotations
from .forces import Force, Gravity, Fluid, Friction, Spring, Wind, Attractor, Buoyancy, Vortex
from .collider import CircleCollider


class Physics2D:
    """Attached to any physics-capable object (via attach() or Entity).
    Each force-attaching method call creates a Force and registers it on
    the owning object, then returns the Force object so it can be
    removed or tweaked later. `.collider()` is separate -- it's not a
    force, it's a shape used by the World's collision pass."""

    def __init__(self, entity):
        self._entity = entity

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

    def collider(self, radius: float = 0.5, restitution: float = 0.6,
                 static: bool = False) -> CircleCollider:
        """Give this object a circular collision shape -- the World's
        step() will detect and resolve overlaps with other colliders
        (and with SEO solids) automatically."""
        c = CircleCollider(radius=radius, restitution=restitution, static=static)
        self._entity._collider = c
        return c

    def custom(self, force: Force) -> Force:
        """Attach any custom Force subclass."""
        self._entity._add_force(force)
        return force

    def remove(self, force: Force) -> None:
        self._entity._remove_force(force)

    def clear(self) -> None:
        self._entity._clear_forces()


__all__ = [
    "Physics2D", "Force", "Gravity", "Fluid", "Friction", "Spring", "Wind",
    "Attractor", "Vortex", "Buoyancy", "CircleCollider",
]
