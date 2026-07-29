"""
pydamics -- a small, chainable-syntax 2D physics engine.

    from pydamics import Entity, World

    ball = Entity(mass=2.0, position=(0, 10))
    ball.physics2d.gravity(force=9.8)
    ball.physics2d.fluid(density=1.2, drag=0.3)

    world = World()
    world.add(ball)

    # manual stepping:
    world.step(dt=1/60)

    # OR let the engine run itself:
    world.run(dt=1/60)
    ...
    world.stop()
"""
from .entity import Entity
from .world import World
from .vector import Vec2
from .physics2d import Physics2D, Gravity, Fluid, Friction, Force

__all__ = [
    "Entity",
    "World",
    "Vec2",
    "Physics2D",
    "Gravity",
    "Fluid",
    "Friction",
    "Force",
]

__version__ = "0.1.0"
