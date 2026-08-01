"""
pydamics -- a small, chainable-syntax 2D physics engine.

v0.4.0 adds one unified entry point over the four "make my own object
X-capable" systems below:

    pydamics.classify(obj, kind="rigid", mass=9, position=(0, 10))
    pydamics.classify(obj, kind=["rigid", "solid"])   # multiple kinds at once
    pydamics.kind_of(obj)                             # -> frozenset({"rigid"}), etc.

    with pydamics.classify(ball, kind="rigid") as cfg:
        cfg.physics2d.mass(9).velocity(0, 0)

classify() is sugar over attach()/solidify()/fluidify() -- those still
work exactly as before, unchanged:

  RIGID-BODY PHYSICS         SOLID GEOMETRY (SEO)      SPH FLUID PARTICLES
  attach(obj, ...)           solidify(obj, ...)        fluidify(obj, ...)
  has_physics(obj)           is_solid(obj)             is_fluid(obj)
  class X(PhysicsObject)     class X(SolidObject)      class X(FluidObject)
  @physics_class(...)        @solid_class(...)         @fluid_class(...)
  obj.physics2d.gravity(..)  obj.seo.solid(...)         fluid.add(obj)

"gas" is a fourth kind: a stripped-down cousin of fluid/buoyancy --
`obj.physics2d.gas(zone)` where zone is a GasZone (no drag, no gust, no
y-component, just a constant push along x). Requesting kind="gas" also
implies "rigid" under the hood, since the push is a Force like any other.

Core usage:

    from pydamics import Entity, World

    ball = Entity(mass=2.0, position=(0, 10))
    ball.physics2d.gravity(force=9.8)
    ball.physics2d.collider(radius=0.4, restitution=0.7)

    world = World()
    world.add(ball)
    world.step(dt=1/60)

Or attach physics to YOUR OWN class -- four equivalent ways, plus classify():

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

    # 4. unified classify()
    pydamics.classify(MyShipClass(), kind="rigid", mass=1500.0, position=(0, 20))

Solid, static or movable geometry (platforms, walls, floors) uses `.seo`
instead of `.physics2d`, with the same attachment styles
(solidify() / SolidObject / @solid_class / classify(kind="solid")):

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
    Buoyancy, GasPush, CircleCollider, Force,
)
from .fluid_zone import FluidZone
from .gas import GasZone
from .seo import (
    SEO, SEOShapeBox, SEOShapeCircle, solidify, is_solid, SolidObject, solid_class,
)
from .sph import (
    FluidParticle, FluidSystem, fluidify, is_fluid, FluidObject, fluid_class,
)
from .collision import resolve_all_collisions
from .spatial_hash import SpatialHash
from .classify import classify, kind_of

__all__ = [
    "Entity", "World", "Vec2",
    "attach", "has_physics", "compute_total_acceleration", "PhysicsObject", "physics_class",
    "Physics2D", "Gravity", "Fluid", "Friction", "Spring", "Wind",
    "Attractor", "Vortex", "Buoyancy", "GasPush", "CircleCollider", "Force",
    "FluidZone", "GasZone",
    "SEO", "SEOShapeBox", "SEOShapeCircle", "solidify", "is_solid", "SolidObject", "solid_class",
    "FluidParticle", "FluidSystem", "fluidify", "is_fluid", "FluidObject", "fluid_class",
    "resolve_all_collisions", "SpatialHash",
    "classify", "kind_of",
]

__version__ = "0.4.0"
