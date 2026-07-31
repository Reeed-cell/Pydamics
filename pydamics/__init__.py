"""
pydamics -- a small, chainable-syntax 2D physics engine.

Core usage:

    from pydamics import Entity, World

    ball = Entity(mass=2.0, position=(0, 10))
    ball.physics2d.gravity(force=9.8)
    ball.physics2d.collider(radius=0.4, restitution=0.7)

    world = World()
    world.add(ball)
    world.step(dt=1/60)

Or attach physics to YOUR OWN class instead of using Entity:

    import pydamics
    ship = pydamics.attach(MyShipClass(), mass=1500.0, position=(0, 20))
    ship.physics2d.gravity(force=9.8)

Solid, static or movable geometry (platforms, walls, floors) uses `.seo`
instead of `.physics2d` -- works with or without also being physics-capable:

    platform = pydamics.solidify(MyPlatform(), position=(0, 0))
    platform.seo.solid(width=8, height=1)
    world.add_solid(platform)

Full SPH fluid particle simulation is a separate system (pairwise forces
don't fit the per-object physics2d model):

    from pydamics import FluidSystem
    fluid = FluidSystem()
    fluid.add_particle(position=(0, 5))
    world.add_fluid_system(fluid)
"""
from .entity import Entity
from .world import World
from .vector import Vec2
from .physics_core import attach, has_physics, compute_total_acceleration
from .physics2d import (
    Physics2D, Gravity, Fluid, Friction, Spring, Wind, Attractor, Vortex,
    Buoyancy, CircleCollider, Force,
)
from .fluid_zone import FluidZone
from .seo import SEO, SEOShapeBox, SEOShapeCircle, solidify, is_solid
from .sph import FluidParticle, FluidSystem
from .collision import resolve_all_collisions

__all__ = [
    "Entity", "World", "Vec2",
    "attach", "has_physics", "compute_total_acceleration",
    "Physics2D", "Gravity", "Fluid", "Friction", "Spring", "Wind",
    "Attractor", "Vortex", "Buoyancy", "CircleCollider", "Force",
    "FluidZone",
    "SEO", "SEOShapeBox", "SEOShapeCircle", "solidify", "is_solid",
    "FluidParticle", "FluidSystem",
    "resolve_all_collisions",
]

__version__ = "0.3.0"
