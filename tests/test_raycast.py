import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import math
import pydamics
from pydamics import Entity, World, Vec2


def test_ray_toward_single_static_circle_hits_correctly():
    target = Entity(mass=1.0, position=(10, 0))
    target.physics2d.collider(radius=1.0, static=True)

    world = World()
    world.add(target)

    hit = world.raycast(origin=(0, 0), direction=Vec2(1, 0), max_distance=50)
    assert hit is not None
    assert hit.entity is target
    # ray hits the near edge of the circle: distance 9 (10 - radius 1)
    assert math.isclose(hit.distance, 9.0, abs_tol=1e-6)
    assert math.isclose(hit.point.x, 9.0, abs_tol=1e-6)
    # normal should point away from the circle's center, roughly -x
    assert hit.normal.x < 0


def test_ray_that_misses_returns_no_hit():
    target = Entity(mass=1.0, position=(10, 5))  # well off the ray's path
    target.physics2d.collider(radius=1.0)

    world = World()
    world.add(target)

    hit = world.raycast(origin=(0, 0), direction=Vec2(1, 0), max_distance=50)
    assert hit is None


def test_raycast_all_returns_multiple_hits_in_distance_order():
    near = Entity(mass=1.0, position=(5, 0))
    near.physics2d.collider(radius=0.5)
    far = Entity(mass=1.0, position=(10, 0))
    far.physics2d.collider(radius=0.5)

    world = World()
    world.add(near)
    world.add(far)

    hits = world.raycast_all(origin=(0, 0), direction=Vec2(1, 0), max_distance=50)
    assert len(hits) == 2
    assert hits[0].entity is near
    assert hits[1].entity is far
    assert hits[0].distance < hits[1].distance


def test_raycast_respects_layer_filtering():
    ghost = Entity(mass=1.0, position=(5, 0))
    ghost.physics2d.collider(radius=0.5, layer="ghost")
    wall = Entity(mass=1.0, position=(10, 0))
    wall.physics2d.collider(radius=0.5, layer="wall")

    world = World()
    world.add(ghost)
    world.add(wall)

    hit = world.raycast(origin=(0, 0), direction=Vec2(1, 0), max_distance=50, collides_with={"wall"})
    assert hit is not None
    assert hit.entity is wall  # ghost was filtered out


def test_raycast_against_seo_box_solid():
    class Wall:
        pass

    wall = pydamics.solidify(Wall(), position=(10, 0))
    wall.seo.solid(width=1, height=4)

    world = World()
    world.add_solid(wall)

    hit = world.raycast(origin=(0, 0), direction=Vec2(1, 0), max_distance=50)
    assert hit is not None
    assert hit.entity is wall
    assert math.isclose(hit.distance, 9.5, abs_tol=1e-6)  # box half-width 0.5


def test_raycast_against_rotated_seo_box():
    class Wall:
        pass

    # a physicsified box rotated 45 degrees
    wall = pydamics.attach(Wall(), mass=1.0, position=(10, 0), angle=math.pi / 4)
    pydamics.solidify(wall)
    wall.seo.solid(width=2, height=2)

    world = World()
    world.add(wall)

    hit = world.raycast(origin=(0, 0), direction=Vec2(1, 0), max_distance=50)
    assert hit is not None
    assert hit.entity is wall


def test_raycast_max_distance_respected():
    target = Entity(mass=1.0, position=(100, 0))
    target.physics2d.collider(radius=1.0)

    world = World()
    world.add(target)

    hit = world.raycast(origin=(0, 0), direction=Vec2(1, 0), max_distance=10)
    assert hit is None  # target is beyond max_distance


def test_raycast_direction_does_not_need_to_be_normalized():
    target = Entity(mass=1.0, position=(10, 0))
    target.physics2d.collider(radius=1.0)

    world = World()
    world.add(target)

    hit = world.raycast(origin=(0, 0), direction=Vec2(5, 0), max_distance=50)  # not unit length
    assert hit is not None
    assert math.isclose(hit.distance, 9.0, abs_tol=1e-6)
