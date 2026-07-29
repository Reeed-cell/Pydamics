import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import math
from pydamics import Entity, World, Vec2


def test_vec2_basic_ops():
    a = Vec2(1, 2)
    b = Vec2(3, 4)
    assert (a + b).x == 4 and (a + b).y == 6
    assert (b - a).x == 2 and (b - a).y == 2
    assert (a * 2).x == 2 and (a * 2).y == 4
    assert math.isclose(a.length(), math.sqrt(5))


def test_gravity_pulls_down():
    ball = Entity(mass=1.0, position=(0, 10))
    ball.physics2d.gravity(force=9.8)
    world = World()
    world.add(ball)
    for _ in range(60):  # 1 second at 60fps
        world.step(1 / 60)
    assert ball.position.y < 10  # it fell
    assert ball.velocity.y < 0   # moving downward


def test_no_forces_means_no_motion():
    e = Entity(mass=1.0, position=(0, 0), velocity=(0, 0))
    world = World()
    world.add(e)
    world.step(1 / 60)
    assert e.position.x == 0 and e.position.y == 0
    assert e.velocity.x == 0 and e.velocity.y == 0


def test_fluid_drag_reduces_speed_growth():
    # ball with only gravity should end up faster than ball with gravity+drag
    free = Entity(mass=1.0, position=(0, 100))
    free.physics2d.gravity(force=9.8)

    dragged = Entity(mass=1.0, position=(0, 100))
    dragged.physics2d.gravity(force=9.8)
    dragged.physics2d.fluid(density=1.0, drag=1.0)

    world = World()
    world.add(free)
    world.add(dragged)

    for _ in range(120):
        world.step(1 / 60)

    assert abs(dragged.velocity.y) < abs(free.velocity.y)


def test_remove_force_stops_effect():
    # Note: velocity verlet averages old+new acceleration each step, so
    # removing a force takes one extra step to fully "flush" out of the
    # velocity. We check steady-state (two steps after removal) rather
    # than the immediate next step.
    e = Entity(mass=1.0, position=(0, 10))
    g = e.physics2d.gravity(force=9.8)
    world = World()
    world.add(e)
    world.step(1 / 60)
    e.physics2d.remove(g)
    world.step(1 / 60)  # one step of lag while old acceleration flushes out
    vel_steady = e.velocity.y
    world.step(1 / 60)
    world.step(1 / 60)
    # velocity shouldn't keep dropping once gravity is fully removed
    assert math.isclose(e.velocity.y, vel_steady, abs_tol=1e-9)


def test_auto_run_and_stop():
    e = Entity(mass=1.0, position=(0, 50))
    e.physics2d.gravity(force=9.8)
    world = World()
    world.add(e)
    world.run(dt=1 / 60, real_time=False)
    import time
    time.sleep(0.05)
    world.stop()
    assert world.running is False
    assert world.time_elapsed > 0
