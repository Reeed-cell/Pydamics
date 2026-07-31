import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import math
import pytest
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


# --- extension system (attach() on a plain, non-Entity class) ---

class Spaceship:
    """A user's own class -- deliberately nothing to do with pydamics."""

    def __init__(self, name):
        self.name = name


def test_attach_makes_any_object_physics_capable():
    import pydamics
    ship = Spaceship("Falcon")
    assert not pydamics.has_physics(ship)

    pydamics.attach(ship, mass=1500.0, position=(0, 20))
    assert pydamics.has_physics(ship)
    assert ship.name == "Falcon"  # original attribute untouched

    ship.physics2d.gravity(force=9.8)
    world = World()
    world.add(ship)
    for _ in range(60):
        world.step(1 / 60)
    assert ship.position.y < 20
    assert ship.velocity.y < 0


def test_world_add_rejects_unattached_object():
    ship = Spaceship("Broken")  # forgot to attach()
    world = World()
    with pytest.raises(TypeError):
        world.add(ship)


def test_attach_returns_the_object_for_chaining():
    import pydamics
    ship = pydamics.attach(Spaceship("Chained"), mass=2.0, position=(1, 2))
    assert ship.name == "Chained"
    assert ship.mass == 2.0


# --- new force types ---

def test_spring_pulls_toward_rest_length():
    e = Entity(mass=1.0, position=(5, 0))  # stretched out to x=5
    e.physics2d.spring(anchor=Vec2(0, 0), stiffness=5.0, rest_length=1.0, damping=0.0)
    world = World()
    world.add(e)
    for _ in range(30):
        world.step(1 / 60)
    # spring should have pulled it back toward the anchor (closer than start)
    assert e.position.x < 5


def test_wind_pushes_in_its_direction():
    e = Entity(mass=1.0, position=(0, 0))
    e.physics2d.wind(force=5.0, direction=Vec2(1, 0))
    world = World()
    world.add(e)
    for _ in range(30):
        world.step(1 / 60)
    assert e.position.x > 0
    assert math.isclose(e.position.y, 0.0, abs_tol=1e-9)


def test_attractor_pulls_toward_target():
    e = Entity(mass=1.0, position=(10, 0))
    e.physics2d.attractor(target=Vec2(0, 0), strength=50.0)
    world = World()
    world.add(e)
    for _ in range(30):
        world.step(1 / 60)
    assert e.position.x < 10  # pulled toward the origin


# --- regression: two objects must never secretly share one Vec2 ---

def test_entities_sharing_a_vec2_position_dont_alias():
    shared = Vec2(0, 10)
    a = Entity(mass=1.0, position=shared)
    b = Entity(mass=1.0, position=shared)
    assert a.position is not b.position

    a.physics2d.gravity(force=9.8)  # only a falls
    world = World()
    world.add(a)
    world.add(b)
    for _ in range(30):
        world.step(1 / 60)

    assert a.position.y < 10
    assert b.position.y == 10  # untouched -- would fail if positions were aliased


def test_vec2_plus_equals_does_not_mutate_shared_original():
    original = Vec2(1, 1)
    alias = original
    original += Vec2(5, 5)
    assert alias.x == 1 and alias.y == 1  # alias untouched -- += rebinds, doesn't mutate
    assert original.x == 6 and original.y == 6


def test_vec2_times_vec2_raises_type_error():
    with pytest.raises(TypeError):
        Vec2(1, 2) * Vec2(3, 4)
