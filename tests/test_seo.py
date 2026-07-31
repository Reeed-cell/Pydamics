import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pydamics
from pydamics import Entity, World, Vec2


class Platform:
    """A user's own plain class -- not physics-capable, just solid geometry."""
    pass


def test_static_platform_stops_falling_ball():
    platform = Platform()
    pydamics.solidify(platform, position=(0, 0))
    platform.seo.solid(width=8, height=1, restitution=0.0)

    ball = Entity(mass=1.0, position=(0, 5))
    ball.physics2d.gravity(force=9.8)
    ball.physics2d.collider(radius=0.4, restitution=0.0)

    world = World()
    world.add(ball)
    world.add_solid(platform)

    for _ in range(200):
        world.step(1 / 60)

    # ball should rest on top of the platform (top surface at y = 0.5,
    # ball radius 0.4 -> resting center around y = 0.9), not fall through
    assert ball.position.y > 0.5
    assert ball.position.y < 2.0


def test_ball_falls_through_without_seo_registered():
    # sanity check: if we DON'T solidify+add_solid, nothing stops the ball
    platform = Platform()
    ball = Entity(mass=1.0, position=(0, 5))
    ball.physics2d.gravity(force=9.8)
    ball.physics2d.collider(radius=0.4)

    world = World()
    world.add(ball)
    # platform intentionally NOT added as a solid

    for _ in range(120):
        world.step(1 / 60)

    assert ball.position.y < 0  # fell straight through where a platform would be


def test_physicsified_solid_is_both_movable_and_solid():
    # a platform that's ALSO physics-capable: falls under gravity but
    # still blocks the ball resting on it
    platform = pydamics.attach(Platform(), mass=50.0, position=(0, 0))
    platform.physics2d.gravity(force=1.0)  # falls slowly
    pydamics.solidify(platform)  # position already set by attach()
    platform.seo.solid(width=8, height=1, restitution=0.0)

    ball = Entity(mass=1.0, position=(0, 3))
    ball.physics2d.gravity(force=9.8)
    ball.physics2d.collider(radius=0.4, restitution=0.0)

    world = World()
    world.add(platform)  # physics-capable -> goes through world.add()
    world.add(ball)

    for _ in range(180):
        world.step(1 / 60)

    # both should have fallen (platform moved down from y=0)
    assert platform.position.y < 0
    # ball should still be resting on top of the (now lower) platform,
    # not clipped through it
    assert ball.position.y > platform.position.y + 0.4


def test_is_solid_reports_correctly():
    p1 = Platform()
    assert not pydamics.is_solid(p1)
    pydamics.solidify(p1, position=(0, 0))
    assert not pydamics.is_solid(p1)  # solidify()-ed but no shape yet
    p1.seo.solid(width=1, height=1)
    assert pydamics.is_solid(p1)
