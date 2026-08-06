import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import math
from pydamics import Entity, World


def test_angle_defaults_to_zero_no_torque():
    ball = Entity(mass=1.0, position=(0, 0))
    assert ball.angle == 0.0
    assert ball.angular_velocity == 0.0


def test_no_torque_means_no_rotation():
    ball = Entity(mass=1.0, position=(0, 10))
    ball.physics2d.gravity(force=9.8)  # linear force, no torque

    world = World()
    world.add(ball)
    for _ in range(60):
        world.step(1 / 60)

    assert ball.angle == 0.0
    assert ball.angular_velocity == 0.0
    assert ball.position.y < 10  # linear motion still works exactly as before


def test_constant_torque_increases_angular_velocity_linearly():
    ball = Entity(mass=1.0, position=(0, 0), moment_of_inertia=1.0)
    ball.physics2d.torque(magnitude=2.0)  # alpha = torque/I = 2.0

    world = World()
    world.add(ball)
    dt = 1 / 60
    for _ in range(60):  # 1 second
        world.step(dt)

    # analytic solution: angular_velocity = alpha * t = 2.0 * 1.0 = 2.0
    assert math.isclose(ball.angular_velocity, 2.0, rel_tol=0.02)
    # angle = 0.5 * alpha * t^2 = 0.5 * 2.0 * 1.0 = 1.0
    assert math.isclose(ball.angle, 1.0, rel_tol=0.05)


def test_remove_torque_stops_rotation_accelerating():
    ball = Entity(mass=1.0, position=(0, 0), moment_of_inertia=1.0)
    t = ball.physics2d.torque(magnitude=2.0)

    world = World()
    world.add(ball)
    for _ in range(30):
        world.step(1 / 60)
    ball.physics2d.remove_torque(t)
    world.step(1 / 60)  # one step of verlet lag while old torque flushes out
    vel_steady = ball.angular_velocity

    for _ in range(30):
        world.step(1 / 60)

    assert math.isclose(ball.angular_velocity, vel_steady, abs_tol=1e-9)


def test_circle_movers_get_no_self_torque_from_normal_impulse():
    # Documents a real, deliberate property: since the collision normal
    # is always computed from the contact point toward a circle's OWN
    # center, a circular mover's lever arm is always exactly parallel/
    # antiparallel to its own impulse -- cross product is always zero.
    # A frictionless circle genuinely can't pick up spin from a pure
    # normal impulse, matching real smooth (frictionless) sphere physics.
    a = Entity(mass=1.0, position=(0, 0), velocity=(3, 0), moment_of_inertia=1.0)
    a.physics2d.collider(radius=0.5, restitution=0.8)
    b = Entity(mass=1.0, position=(0.9, 0.3), moment_of_inertia=1.0)  # off-center approach
    b.physics2d.collider(radius=0.5, restitution=0.8)

    world = World()
    world.add(a)
    world.add(b)
    world.step(1 / 60)

    assert math.isclose(a.angular_velocity, 0.0, abs_tol=1e-9)
    assert math.isclose(b.angular_velocity, 0.0, abs_tol=1e-9)


def test_off_center_hit_imparts_spin_to_a_box_solid():
    # A box's geometry ISN'T radially symmetric like a circle, so a
    # physicsified box CAN pick up genuine torque when hit away from its
    # center -- this is where "off-center collision imparts spin" is
    # actually physically real in this engine. Landing on the flat top
    # away from x=0 is enough: the lever arm gets a nonzero x-component
    # while the impulse stays purely vertical, so torque = lever x impulse
    # is nonzero.
    import pydamics as pd

    class Crate:
        pass

    crate = pd.attach(Crate(), mass=20.0, position=(0, 0), moment_of_inertia=5.0)
    pd.solidify(crate)
    crate.seo.solid(width=4, height=1, restitution=0.1)  # half-width 2, half-height 0.5

    ball = Entity(mass=1.0, position=(1.5, 3))  # off-center in x, falls straight down onto it
    ball.physics2d.gravity(force=9.8)
    ball.physics2d.collider(radius=0.3, restitution=0.1)

    world = World()
    world.add(crate)
    world.add(ball)
    for _ in range(120):
        world.step(1 / 60)

    assert crate.angular_velocity != 0.0


def test_dead_center_collision_imparts_no_spin():
    # a head-on collision through both centers (same y) should NOT
    # produce spin -- the lever arm should be ~zero
    a = Entity(mass=1.0, position=(0, 0), velocity=(3, 0), moment_of_inertia=1.0)
    a.physics2d.collider(radius=0.5, restitution=0.8)
    b = Entity(mass=1.0, position=(0.9, 0), moment_of_inertia=1.0)  # same y, dead center
    b.physics2d.collider(radius=0.5, restitution=0.8)

    world = World()
    world.add(a)
    world.add(b)
    world.step(1 / 60)

    assert math.isclose(a.angular_velocity, 0.0, abs_tol=1e-9)
    assert math.isclose(b.angular_velocity, 0.0, abs_tol=1e-9)


def test_static_solid_gets_no_angular_velocity_change():
    import pydamics as pd

    class Platform:
        pass

    platform = pd.solidify(Platform(), position=(0, 0))
    platform.seo.solid(width=4, height=1, restitution=0.5)

    ball = Entity(mass=1.0, position=(1.0, 3), moment_of_inertia=1.0)  # off-center over the platform
    ball.physics2d.gravity(force=9.8)
    ball.physics2d.collider(radius=0.3, restitution=0.5)

    world = World()
    world.add(ball)
    world.add_solid(platform)
    for _ in range(120):
        world.step(1 / 60)

    # platform has no angular_velocity attribute at all (not physics-capable)
    assert not hasattr(platform, "angular_velocity")


def test_custom_moment_of_inertia_respected():
    heavy_spinner = Entity(mass=1.0, position=(0, 0), moment_of_inertia=10.0)
    light_spinner = Entity(mass=1.0, position=(5, 0), moment_of_inertia=1.0)
    heavy_spinner.physics2d.torque(magnitude=5.0)
    light_spinner.physics2d.torque(magnitude=5.0)

    world = World()
    world.add(heavy_spinner)
    world.add(light_spinner)
    for _ in range(30):
        world.step(1 / 60)

    # same torque, larger moment of inertia -> slower angular acceleration
    assert abs(light_spinner.angular_velocity) > abs(heavy_spinner.angular_velocity)


def test_default_moment_of_inertia_derived_from_mass():
    ball = Entity(mass=4.0, position=(0, 0))
    assert ball.moment_of_inertia == 4.0 * 0.5
