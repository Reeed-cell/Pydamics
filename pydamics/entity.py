"""
Entity -- the "object" you attach physics behaviors to.
"""
from __future__ import annotations
from .vector import Vec2
from .physics2d import Physics2D


class Entity:
    def __init__(self, mass: float = 1.0, position=(0.0, 0.0), velocity=(0.0, 0.0)):
        self.mass = float(mass)
        self.position = Vec2(*position)
        self.velocity = Vec2(*velocity)

        # last computed acceleration, needed for velocity-verlet integration
        self._prev_accel = Vec2.zero()

        self._forces = []  # list of Force objects currently attached

        # namespace access: entity.physics2d.gravity(...), etc.
        self.physics2d = Physics2D(self)

    # --- internal, called by the Physics2D namespace ---
    def _add_force(self, force) -> None:
        self._forces.append(force)

    def _remove_force(self, force) -> None:
        if force in self._forces:
            self._forces.remove(force)

    def _clear_forces(self) -> None:
        self._forces.clear()

    # --- used by the integrator ---
    def compute_total_acceleration(self) -> Vec2:
        total = Vec2.zero()
        for force in self._forces:
            total += force.compute_acceleration(self)
        return total

    def __repr__(self) -> str:
        return f"Entity(pos={self.position}, vel={self.velocity}, mass={self.mass})"
