import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
from pydamics import Entity, World, Vec2
from pydamics.spatial_hash import SpatialHash


def test_spatial_hash_finds_nearby_objects():
    grid = SpatialHash(cell_size=1.0)

    class Dummy:
        def __init__(self, position):
            self.position = position

    near_a = Dummy(Vec2(0.1, 0.1))
    near_b = Dummy(Vec2(0.9, 0.9))
    far_away = Dummy(Vec2(50.0, 50.0))

    grid.rebuild([near_a, near_b, far_away])

    neighbors = list(grid.query_neighbors(Vec2(0.0, 0.0)))
    assert near_a in neighbors
    assert near_b in neighbors
    assert far_away not in neighbors


def test_spatial_hash_empty_query_returns_nothing():
    grid = SpatialHash(cell_size=1.0)
    grid.rebuild([])
    assert list(grid.query_neighbors(Vec2(0, 0))) == []


def test_collision_correctness_with_many_scattered_entities():
    # entities spread far apart shouldn't spuriously collide, and ones
    # placed touching should -- sanity check that the spatial-hash
    # broad-phase doesn't miss or fabricate collisions
    world = World()
    scattered = []
    for i in range(20):
        e = Entity(mass=1.0, position=(i * 10.0, 0))  # far apart, radius 0.4 each
        e.physics2d.collider(radius=0.4, restitution=0.5)
        world.add(e)
        scattered.append(e)

    # one touching pair placed among the scattered ones
    a = Entity(mass=1.0, position=(500.0, 0), velocity=(1.0, 0))
    a.physics2d.collider(radius=0.5, restitution=0.5)
    b = Entity(mass=1.0, position=(500.9, 0), velocity=(0.0, 0))
    b.physics2d.collider(radius=0.5, restitution=0.5)
    world.add(a)
    world.add(b)

    positions_before = [e.position.x for e in scattered]
    world.step(1 / 60)

    # scattered (far apart) entities should be completely unaffected
    for e, before in zip(scattered, positions_before):
        assert e.position.x == before

    # the touching pair should have actually resolved (b picked up velocity)
    assert b.velocity.x > 0


def test_spatial_hash_scales_better_than_naive_for_scattered_objects():
    # not a strict timing assertion (flaky on shared CI runners), but a
    # sanity check that a large scattered scene doesn't blow up in cost
    world = World()
    for i in range(150):
        e = Entity(mass=1.0, position=(i * 5.0, 0))  # spread far apart
        e.physics2d.collider(radius=0.3)
        world.add(e)

    start = time.perf_counter()
    for _ in range(10):
        world.step(1 / 60)
    elapsed = time.perf_counter() - start

    # 150 scattered (non-colliding) entities over 10 steps should be fast;
    # a naive O(n^2) scan would do 150*149/2 = ~11k checks per step just
    # for broad-phase, spatial hash should do a small fraction of that
    assert elapsed < 2.0
