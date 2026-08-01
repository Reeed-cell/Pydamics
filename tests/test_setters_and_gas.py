import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pydamics import Entity, World, Vec2, GasZone


# --- chainable setters ---

def test_mass_setter_updates_and_chains():
    ball = Entity(mass=1.0, position=(0, 0))
    result = ball.physics2d.mass(9)
    assert ball.mass == 9
    assert result is ball.physics2d  # returns self for chaining


def test_position_setter_updates_and_chains():
    ball = Entity(mass=1.0, position=(0, 0))
    ball.physics2d.position(3, 4)
    assert ball.position.x == 3 and ball.position.y == 4


def test_velocity_setter_updates_and_chains():
    ball = Entity(mass=1.0, position=(0, 0))
    ball.physics2d.velocity(5, -2)
    assert ball.velocity.x == 5 and ball.velocity.y == -2


def test_setters_chain_together():
    ball = Entity(mass=1.0, position=(0, 0))
    ball.physics2d.mass(9).velocity(1, 2).position(3, 4)
    assert ball.mass == 9
    assert ball.velocity.x == 1 and ball.velocity.y == 2
    assert ball.position.x == 3 and ball.position.y == 4


# --- collider-dependent setters: require .collider() first ---

def test_restitution_setter_requires_collider():
    ball = Entity(mass=1.0, position=(0, 0))
    with pytest.raises(RuntimeError):
        ball.physics2d.restitution(0.5)


def test_restitution_setter_works_after_collider():
    ball = Entity(mass=1.0, position=(0, 0))
    ball.physics2d.collider(radius=0.4, restitution=0.3)
    ball.physics2d.restitution(0.9)
    assert ball._collider.restitution == 0.9


def test_radius_setter_requires_collider():
    ball = Entity(mass=1.0, position=(0, 0))
    with pytest.raises(RuntimeError):
        ball.physics2d.radius(1.0)


def test_radius_setter_works_after_collider():
    ball = Entity(mass=1.0, position=(0, 0))
    ball.physics2d.collider(radius=0.4)
    ball.physics2d.radius(0.8)
    assert ball._collider.radius == 0.8


def test_static_setter_requires_collider():
    ball = Entity(mass=1.0, position=(0, 0))
    with pytest.raises(RuntimeError):
        ball.physics2d.static(True)


def test_static_setter_works_after_collider():
    ball = Entity(mass=1.0, position=(0, 0))
    ball.physics2d.collider(radius=0.4, static=False)
    ball.physics2d.static(True)
    assert ball._collider.static is True


# --- GasZone / GasPush ---

def test_gas_push_moves_object_inside_zone_along_x_only():
    zone = GasZone(min_point=(-5, -5), max_point=(5, 5), force=10.0)
    puff = Entity(mass=1.0, position=(0, 0))
    puff.physics2d.gas(zone)

    world = World()
    world.add(puff)
    for _ in range(30):
        world.step(1 / 60)

    assert puff.position.x > 0
    assert puff.position.y == 0  # gas push is x-only, no y-component


def test_gas_push_does_nothing_outside_zone():
    zone = GasZone(min_point=(-5, -5), max_point=(5, 5), force=10.0)
    outside = Entity(mass=1.0, position=(100, 0))
    outside.physics2d.gas(zone)

    world = World()
    world.add(outside)
    for _ in range(30):
        world.step(1 / 60)

    assert outside.position.x == 100  # untouched, never entered the zone
    assert outside.position.y == 0
