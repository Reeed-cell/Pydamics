import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pydamics
from pydamics import World, FluidSystem


# --- PhysicsObject mixin ---

class MixinShip(pydamics.PhysicsObject):
    def __init__(self, name, **physics_kwargs):
        super().__init__(**physics_kwargs)
        self.name = name


def test_physics_object_mixin_makes_class_physics_capable():
    ship = MixinShip("Falcon", mass=1500.0, position=(0, 20))
    assert pydamics.has_physics(ship)
    assert ship.name == "Falcon"

    ship.physics2d.gravity(force=9.8)
    world = World()
    world.add(ship)
    for _ in range(60):
        world.step(1 / 60)
    assert ship.position.y < 20


# --- physics_class decorator ---

@pydamics.physics_class(mass=2.0, position=(1, 2))
class DecoratedShip:
    def __init__(self, name):
        self.name = name


def test_physics_class_decorator_makes_class_physics_capable():
    ship = DecoratedShip("Millennium")
    assert pydamics.has_physics(ship)
    assert ship.name == "Millennium"
    assert ship.mass == 2.0
    assert ship.position.x == 1 and ship.position.y == 2


# --- SolidObject mixin ---

class MixinPlatform(pydamics.SolidObject):
    pass


def test_solid_object_mixin_makes_class_solidified():
    platform = MixinPlatform(position=(0, 0))
    assert hasattr(platform, "seo")
    assert not pydamics.is_solid(platform)  # solidified but no shape yet
    platform.seo.solid(width=4, height=1)
    assert pydamics.is_solid(platform)


# --- solid_class decorator ---

@pydamics.solid_class(position=(3, 4))
class DecoratedPlatform:
    pass


def test_solid_class_decorator_makes_class_solidified():
    platform = DecoratedPlatform()
    assert hasattr(platform, "seo")
    assert platform.position.x == 3 and platform.position.y == 4
    platform.seo.solid(radius=1.0)
    assert pydamics.is_solid(platform)


# --- fluidify() / is_fluid() / FluidObject / fluid_class ---

class WaterDroplet:
    def __init__(self, name):
        self.name = name


def test_fluidify_and_is_fluid():
    drop = WaterDroplet("drop1")
    assert not pydamics.is_fluid(drop)
    pydamics.fluidify(drop, mass=1.0, position=(0, 5))
    assert pydamics.is_fluid(drop)
    assert drop.name == "drop1"


def test_fluid_system_add_accepts_fluidified_custom_object():
    drop = pydamics.fluidify(WaterDroplet("drop2"), mass=1.0, position=(0, 5))
    fluid = FluidSystem()
    fluid.add(drop)
    assert drop in fluid.particles
    fluid.step(dt=1 / 120, gravity=9.8)
    assert drop.velocity.y < 0  # gravity pulled it down


def test_fluid_system_add_rejects_non_fluidified_object():
    import pytest
    drop = WaterDroplet("not fluidified")
    fluid = FluidSystem()
    with pytest.raises(TypeError):
        fluid.add(drop)


class MixinDroplet(pydamics.FluidObject):
    def __init__(self, name, **fluid_kwargs):
        super().__init__(**fluid_kwargs)
        self.name = name


def test_fluid_object_mixin():
    drop = MixinDroplet("mixin-drop", mass=1.0, position=(0, 5))
    assert pydamics.is_fluid(drop)
    fluid = FluidSystem()
    fluid.add(drop)
    fluid.step(dt=1 / 120, gravity=9.8)
    assert drop.velocity.y < 0


@pydamics.fluid_class(mass=1.0, position=(0, 5))
class DecoratedDroplet:
    pass


def test_fluid_class_decorator():
    drop = DecoratedDroplet()
    assert pydamics.is_fluid(drop)
    assert drop.position.y == 5


# --- regression: decorator-captured Vec2 defaults must not alias across instances ---

@pydamics.physics_class(mass=1.0, position=pydamics.Vec2(0, 10))
class DecoratedSharedDefault:
    pass


def test_physics_class_decorator_vec2_default_not_shared_across_instances():
    a = DecoratedSharedDefault()
    b = DecoratedSharedDefault()
    assert a.position is not b.position

    a.physics2d.gravity(force=9.8)
    world = World()
    world.add(a)
    world.add(b)
    for _ in range(30):
        world.step(1 / 60)

    assert a.position.y < 10
    assert b.position.y == 10  # untouched -- would fail if the decorator aliased instances
