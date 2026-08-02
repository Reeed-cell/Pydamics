import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pydamics
from pydamics import Entity, World


def test_same_layer_no_mask_collides_by_default():
    a = Entity(mass=1.0, position=(0, 0), velocity=(1, 0))
    a.physics2d.collider(radius=0.5, restitution=1.0)
    b = Entity(mass=1.0, position=(0.9, 0))
    b.physics2d.collider(radius=0.5, restitution=1.0)

    world = World()
    world.add(a)
    world.add(b)
    world.step(1 / 60)

    assert b.velocity.x > 0  # collided normally, no filtering applied


def test_collides_with_filters_out_non_matching_layer():
    bullet = Entity(mass=1.0, position=(0, 0), velocity=(5, 0))
    bullet.physics2d.collider(radius=0.3, restitution=1.0, layer="player_bullet",
                               collides_with={"enemy"})
    wall = Entity(mass=1.0, position=(0.5, 0))
    wall.physics2d.collider(radius=0.3, restitution=1.0, layer="wall")

    world = World()
    world.add(bullet)
    world.add(wall)
    for _ in range(10):
        world.step(1 / 60)

    # bullet only collides_with "enemy", wall is layer "wall" -> no collision,
    # bullet should have passed straight through
    assert bullet.position.x > 0.5


def test_collides_with_allows_matching_layer():
    bullet = Entity(mass=1.0, position=(0, 0), velocity=(5, 0))
    bullet.physics2d.collider(radius=0.3, restitution=1.0, layer="player_bullet",
                               collides_with={"enemy"})
    enemy = Entity(mass=1.0, position=(0.5, 0))
    enemy.physics2d.collider(radius=0.3, restitution=1.0, layer="enemy")

    world = World()
    world.add(bullet)
    world.add(enemy)
    world.step(1 / 60)

    assert enemy.velocity.x > 0  # collision happened, enemy got pushed


def test_symmetric_and_filter_both_sides_must_agree():
    # a only collides_with "b_layer", but b has no restriction (collides
    # with everything) -- should still NOT collide, since a's restriction
    # excludes b's layer
    a = Entity(mass=1.0, position=(0, 0), velocity=(5, 0))
    a.physics2d.collider(radius=0.3, restitution=1.0, layer="a_layer",
                          collides_with={"something_else"})
    b = Entity(mass=1.0, position=(0.5, 0))
    b.physics2d.collider(radius=0.3, restitution=1.0, layer="b_layer")

    world = World()
    world.add(a)
    world.add(b)
    for _ in range(10):
        world.step(1 / 60)

    assert a.position.x > 0.5  # passed through, no collision


def test_seo_solid_respects_layer_filtering():
    import pydamics as pd

    class Platform:
        pass

    platform = pd.solidify(Platform(), position=(0, 0))
    platform.seo.solid(width=4, height=1, layer="ghost_wall")

    ball = Entity(mass=1.0, position=(0, 3))
    ball.physics2d.gravity(force=9.8)
    ball.physics2d.collider(radius=0.3, collides_with={"normal_wall"})

    world = World()
    world.add(ball)
    world.add_solid(platform)
    for _ in range(120):
        world.step(1 / 60)

    assert ball.position.y < -0.5  # fell straight through, layers didn't match
