"""
Entity -- a convenience class for when you don't have your own object to
attach physics to. Just a thin wrapper around `pydamics.attach()`; if you
already have a class of your own, use `attach()` directly instead of
adopting this one.
"""
from __future__ import annotations
from .physics_core import attach


class Entity:
    def __init__(self, mass: float = 1.0, position=(0.0, 0.0), velocity=(0.0, 0.0)):
        attach(self, mass=mass, position=position, velocity=velocity)

    def __repr__(self) -> str:
        return f"Entity(pos={self.position}, vel={self.velocity}, mass={self.mass})"
