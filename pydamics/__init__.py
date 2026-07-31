"""
pydamics -- a small, chainable-syntax 2D physics engine.

Three parallel "make my own object X-capable" systems, all following the
same pattern (a plain function, a mixin class, or a decorator -- pick
whichever fits how you write your classes):

  RIGID-BODY PHYSICS         SOLID GEOMETRY (SEO)      SPH FLUID PARTICLES
  attach(obj, ...)           solidify(obj, ...)        fluidify(obj, ...)
  has_physics(obj)           is_solid(obj)             is_fluid(obj)
  class X(PhysicsObject)     class X(SolidObject)      class X(FluidObject)
  @physics_class(...)        @solid_class(...)         @fluid_class(...)
  obj.physics2d.gravity(..)  obj.seo.solid(...)         fluid.add(obj)

Core usage:

    from pydamics import Entity, World

    ball = Entity(mass=2.0, position=(0, 10))
    ball.physics2d.gravity(force=9.8)
    ball.physics2d.collider(radius=0.4, restitution=0.7)

    world = World()
    world.add(ball)
    world.step(dt=1/60)

Or attach physics to YOUR OWN class -- three equivalent ways:

    import pydamics

    # 1. function call
    ship = pydamics.attach(MyShipClass(), mass=1500.0, position=(0, 20))

    # 2. mixin
    class MyShipClass(pydamics.PhysicsObject):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    # 3. decorator
    @pydamics.physics_class(mass=1500.0, position=(0, 20))
    class MyShipClass:
        pass

Solid, static or movable geometry (platforms, walls, floors) uses `.seo`
instead of `.physics2d`, with the same three attachment styles
(solidify() / SolidObject / @solid_class):

    platform = pydamics.solidify(MyPlatform(), position=(0, 0))
    platform.seo.solid(width=8, height=1)
    world.add_solid(platform)

Full SPH fluid particle simulation is a separate system (pairwise forces
don't fit the per-object physics2d model). Use the built-in FluidParticle,
or fluidify() your own class and register it directly:

    from pydamics import FluidSystem
    fluid = FluidSystem()
    fluid.add_particle(position=(0, 5))                 # built-in particle
    fluid.add(pydamics.fluidify(MyDroplet(), position=(1, 5)))  # your own class
    world.add_fluid_system(fluid)
"""
from .entity import Entity
from .world import World
from .vector import Vec2
from .physics_core import (
    attach, has_physics, compute_total_acceleration, PhysicsObject, physics_class,
)
from .physics2d import (
    Physics2D, Gravity, Fluid, Friction, Spring, Wind, Attractor, Vortex,
    Buoyancy, CircleCollider, Force,
)
from .fluid_zone import FluidZone
from .seo import (
    SEO, SEOShapeBox, SEOShapeCircle, solidify, is_solid, SolidObject, solid_class,
)
from .sph import (
    FluidParticle, FluidSystem, fluidify, is_fluid, FluidObject, fluid_class,
)
from .collision import resolve_all_collisions
from .spatial_hash import SpatialHash

__all__ = [
    "Entity", "World", "Vec2",
    "attach", "has_physics", "compute_total_acceleration", "PhysicsObject", "physics_class",
    "Physics2D", "Gravity", "Fluid", "Friction", "Spring", "Wind",
    "Attractor", "Vortex", "Buoyancy", "CircleCollider", "Force",
    "FluidZone",
    "SEO", "SEOShapeBox", "SEOShapeCircle", "solidify", "is_solid", "SolidObject", "solid_class",
    "FluidParticle", "FluidSystem", "fluidify", "is_fluid", "FluidObject", "fluid_class",
    "resolve_all_collisions", "SpatialHash",
]

__version__ = "0.3.2"
