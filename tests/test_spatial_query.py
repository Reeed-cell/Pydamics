import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pydamics import Entity, World, Vec2


def test_query_radius_finds_nearby_entities():
    near = Entity(mass=1.0, position=(1, 0))
    far = Entity(mass=1.0, position=(100, 0))

    world = World()
    world.add(near)
    world.add(far)

    results = world.query_radius(center=(0, 0), radius=5)
    assert near in results
    assert far not in results


def test_query_radius_boundary_inclusive():
    on_edge = Entity(mass=1.0, position=(5, 0))
    world = World()
    world.add(on_edge)

    results = world.query_radius(center=(0, 0), radius=5)
    assert on_edge in results


def test_query_radius_empty_world():
    world = World()
    assert world.query_radius(center=(0, 0), radius=10) == []


def test_query_rect_finds_entities_inside():
    inside = Entity(mass=1.0, position=(5, 5))
    outside = Entity(mass=1.0, position=(50, 50))

    world = World()
    world.add(inside)
    world.add(outside)

    results = world.query_rect(min_point=(0, 0), max_point=(10, 10))
    assert inside in results
    assert outside not in results


def test_query_rect_boundary_inclusive():
    on_corner = Entity(mass=1.0, position=(10, 10))
    world = World()
    world.add(on_corner)

    results = world.query_rect(min_point=(0, 0), max_point=(10, 10))
    assert on_corner in results


def test_query_rect_elongated_rectangle():
    # a wide, short rectangle -- exercises the cell-size-covers-half-
    # diagonal correctness property with an asymmetric shape
    inside = Entity(mass=1.0, position=(90, 0.5))
    outside = Entity(mass=1.0, position=(90, 5))

    world = World()
    world.add(inside)
    world.add(outside)

    results = world.query_rect(min_point=(0, 0), max_point=(100, 1))
    assert inside in results
    assert outside not in results


def test_query_radius_with_many_scattered_entities():
    world = World()
    center_entities = []
    for i in range(5):
        e = Entity(mass=1.0, position=(i * 0.5, 0))  # clustered near origin
        world.add(e)
        center_entities.append(e)
    for i in range(20):
        e = Entity(mass=1.0, position=(1000 + i * 10, 1000))  # far away cluster
        world.add(e)

    results = world.query_radius(center=(0, 0), radius=3)
    assert len(results) == 5
    for e in center_entities:
        assert e in results
