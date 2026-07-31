import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import math
from pydamics import Entity, World, Vec2


def test_two_circles_dont_overlap_after_collision():
    a = Entity(mass=1.0, position=(0, 0), velocity=(2, 0))
    a.physics2d.collider(radius=0.5, restitution=1.0)
    b = Entity(mass=1.0, position=(1.0, 0), velocity=(0, 0))
    b.physics2d.collider(radius=0.5, restitution=1.0)

    world = World()
    world.add(a)
    world.add(b)
    for _ in range(60):
        world.step(1 / 60)

    dist = (b.position - a.position).length()
    assert dist >= 1.0 - 1e-6  # no longer overlapping (radii sum to 1.0)


def test_equal_mass_elastic_collision_transfers_velocity():
    # classic equal-mass elastic collision: a stops, b moves off with a's speed
    a = Entity(mass=1.0, position=(0, 0), velocity=(3, 0))
    a.physics2d.collider(radius=0.5, restitution=1.0)
    b = Entity(mass=1.0, position=(1.0, 0), velocity=(0, 0))
    b.physics2d.collider(radius=0.5, restitution=1.0)

    world = World()
    world.add(a)
    world.add(b)
    world.step(1 / 60)  # they start touching, one step should trigger resolution

    assert b.velocity.x > 0  # b picked up speed from the impact
    assert a.velocity.x < 3  # a lost some/all speed


def test_inelastic_collision_loses_energy():
    a = Entity(mass=1.0, position=(0, 0), velocity=(3, 0))
    a.physics2d.collider(radius=0.5, restitution=0.0)
    b = Entity(mass=1.0, position=(1.0, 0), velocity=(0, 0))
    b.physics2d.collider(radius=0.5, restitution=0.0)

    world = World()
    world.add(a)
    world.add(b)
    world.step(1 / 60)

    # perfectly inelastic: both end up moving at the same (halved) velocity
    assert math.isclose(a.velocity.x, b.velocity.x, abs_tol=1e-6)


def test_static_collider_never_moves():
    wall = Entity(mass=1.0, position=(2, 0))
    wall.physics2d.collider(radius=0.5, restitution=0.8, static=True)
    ball = Entity(mass=1.0, position=(0, 0), velocity=(5, 0))
    ball.physics2d.collider(radius=0.5, restitution=0.8)

    world = World()
    world.add(wall)
    world.add(ball)
    for _ in range(60):
        world.step(1 / 60)

    assert wall.position.x == 2  # untouched
    assert ball.velocity.x < 0  # bounced back
