"""
The Physics2D namespace -- this is what you get from `entity.physics2d`.

Usage:
    ball.physics2d.gravity(force=9.8)
    ball.physics2d.fluid(density=1.2, drag=0.3)
    ball.physics2d.friction(coefficient=0.4)
"""
from __future__ import annotations
from .forces import Gravity, Fluid, Friction, Force


class Physics2D:
    """Attached to an Entity. Each method call creates a Force and registers
    it on the owning entity, then returns the Force object so it can be
    removed or tweaked later."""

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

    def custom(self, force: Force) -> Force:
        """Attach any custom Force subclass."""
        self._entity._add_force(force)
        return force

    def remove(self, force: Force) -> None:
        self._entity._remove_force(force)

    def clear(self) -> None:
        self._entity._clear_forces()


__all__ = ["Physics2D", "Gravity", "Fluid", "Friction", "Force"]
