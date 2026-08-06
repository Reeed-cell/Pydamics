import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import math
import pydamics
from pydamics import Entity, World, Vec2
from pydamics.sat import sat_box_vs_box, closest_point_on_box, box_axes


# --- pure geometry sanity checks (sat.py directly) ---

def test_sat_two_axis_aligned_overlapping_boxes():
    result = sat_box_vs_box(Vec2(0, 0), 0.0, 1.0, 1.0, Vec2(1.5, 0), 0.0, 1.0, 1.0)
    assert result is not None
    normal, overlap = result
    assert normal.x > 0  # points from a to b, roughly +x
    assert math.isclose(overlap, 0.5, abs_tol=1e-6)


def test_sat_two_axis_aligned_separated_boxes():
    result = sat_box_vs_box(Vec2(0, 0), 0.0, 1.0, 1.0, Vec2(10, 0), 0.0, 1.0, 1.0)
    assert result is None


def test_sat_rotated_45_degree_boxes_corner_overlap():
    # a diamond-oriented box (45 degrees) just touching another
    result = sat_box_vs_box(Vec2(0, 0), math.pi / 4, 1.0, 1.0, Vec2(2.0, 0), math.pi / 4, 1.0, 1.0)
    # half-diagonal of a 1x1 box is sqrt(2) ~ 1.414, so two of them
    # touching corner-to-corner span ~2.83 -- at distance 2.0 they overlap
    assert result is not None


def test_closest_point_on_axis_aligned_box_outside():
    closest, inside, lx, ly = closest_point_on_box(Vec2(5, 0), Vec2(0, 0), 0.0, 1.0, 1.0)
    assert not inside
    assert closest.x == 1.0 and closest.y == 0.0


def test_closest_point_on_rotated_box():
    # box rotated 90 degrees -- its "width" axis now points along world y
    closest, inside, lx, ly = closest_point_on_box(Vec2(0, 5), Vec2(0, 0), math.pi / 2, 1.0, 2.0)
    assert not inside
    # after a 90-degree rotation, the box's half-height (2.0) axis now
    # points along world -x, and half-width (1.0) along world y
    assert math.isclose(closest.y, 1.0, abs_tol=1e-6)


# --- box vs box collision (entity-entity), axis-aligned vs axis-aligned ---

def test_box_vs_box_axis_aligned_separates_and_bounces():
    a = Entity(mass=1.0, position=(0, 0), velocity=(2, 0))
    a.physics2d.collider(shape="box", width=1.0, height=1.0, restitution=0.8)
    b = Entity(mass=1.0, position=(0.9, 0))
    b.physics2d.collider(shape="box", width=1.0, height=1.0, restitution=0.8)

    world = World()
    world.add(a)
    world.add(b)
    for _ in range(30):
        world.step(1 / 60)

    # boxes should have separated (not still overlapping) and b should
    # have picked up rightward velocity from the hit
    assert (b.position.x - a.position.x) >= 1.0 - 1e-6
    assert b.velocity.x > 0


# --- box vs box, axis-aligned vs rotated ---

def test_box_vs_box_axis_aligned_vs_rotated():
    a = Entity(mass=1.0, position=(0, 0), velocity=(2, 0), angle=0.0)
    a.physics2d.collider(shape="box", width=1.0, height=1.0, restitution=0.5)
    b = Entity(mass=1.0, position=(1.3, 0), angle=math.pi / 4)  # 45-degree rotated
    b.physics2d.collider(shape="box", width=1.0, height=1.0, restitution=0.5)

    world = World()
    world.add(a)
    world.add(b)
    for _ in range(30):
        world.step(1 / 60)

    # collision happened -- b should have moved from the impact
    assert b.velocity.x > 0 or b.position.x > 1.3


# --- box vs box, rotated vs rotated ---

def test_box_vs_box_rotated_vs_rotated():
    a = Entity(mass=1.0, position=(0, 0), velocity=(2, 0), angle=math.pi / 6)
    a.physics2d.collider(shape="box", width=1.0, height=1.0, restitution=0.5)
    b = Entity(mass=1.0, position=(1.3, 0), angle=-math.pi / 6)
    b.physics2d.collider(shape="box", width=1.0, height=1.0, restitution=0.5)

    world = World()
    world.add(a)
    world.add(b)
    for _ in range(30):
        world.step(1 / 60)

    assert b.velocity.x > 0 or b.position.x > 1.3


# --- box vs box, corner-only contact ---

def test_box_vs_box_corner_contact_still_detected():
    # two 45-degree-rotated boxes (diamonds) approaching so their
    # corners meet -- SAT must still catch this
    a = Entity(mass=1.0, position=(0, 0), velocity=(1.5, 0), angle=math.pi / 4)
    a.physics2d.collider(shape="box", width=1.0, height=1.0, restitution=0.5)
    b = Entity(mass=1.0, position=(2.0, 0), angle=math.pi / 4)
    b.physics2d.collider(shape="box", width=1.0, height=1.0, restitution=0.5)

    world = World()
    world.add(a)
    world.add(b)
    hit = [False]
    world.on_collision(lambda x, y, p, n, imp: hit.__setitem__(0, True))
    for _ in range(60):
        world.step(1 / 60)

    assert hit[0] is True


# --- circle vs box (entity-entity) ---

def test_circle_vs_box_entity_entity():
    circle = Entity(mass=1.0, position=(0, 0), velocity=(2, 0))
    circle.physics2d.collider(radius=0.4, restitution=0.6)
    box = Entity(mass=1.0, position=(1.0, 0))
    box.physics2d.collider(shape="box", width=1.0, height=1.0, restitution=0.6)

    world = World()
    world.add(circle)
    world.add(box)
    for _ in range(30):
        world.step(1 / 60)

    assert box.velocity.x > 0  # box got pushed by the circle


def test_circle_vs_rotated_box_entity_entity():
    circle = Entity(mass=1.0, position=(0, 0), velocity=(2, 0))
    circle.physics2d.collider(radius=0.4, restitution=0.6)
    box = Entity(mass=1.0, position=(1.0, 0), angle=math.pi / 4)
    box.physics2d.collider(shape="box", width=1.0, height=1.0, restitution=0.6)

    world = World()
    world.add(circle)
    world.add(box)
    for _ in range(30):
        world.step(1 / 60)

    assert box.velocity.x > 0


# --- box vs SEO solid ---

def test_box_entity_lands_on_static_seo_box_platform():
    class Platform:
        pass

    platform = pydamics.solidify(Platform(), position=(0, 0))
    platform.seo.solid(width=8, height=1, restitution=0.1)

    crate = Entity(mass=1.0, position=(0, 5))
    crate.physics2d.gravity(force=9.8)
    crate.physics2d.collider(shape="box", width=1.0, height=1.0, restitution=0.1)

    world = World()
    world.add(crate)
    world.add_solid(platform)
    for _ in range(200):
        world.step(1 / 60)

    # crate should rest on top of the platform (top at y=0.5, crate half-height 0.5)
    assert 0.9 < crate.position.y < 1.5


def test_rotated_box_entity_vs_seo_box():
    class Platform:
        pass

    platform = pydamics.solidify(Platform(), position=(0, 0))
    platform.seo.solid(width=8, height=1, restitution=0.1)

    crate = Entity(mass=1.0, position=(0, 5), angle=math.pi / 6, moment_of_inertia=1.0)
    crate.physics2d.gravity(force=9.8)
    crate.physics2d.collider(shape="box", width=1.0, height=1.0, restitution=0.1)

    world = World()
    world.add(crate)
    world.add_solid(platform)
    for _ in range(200):
        world.step(1 / 60)

    # doesn't fall through the platform
    assert crate.position.y > 0.0


def test_box_entity_vs_seo_circle_solid():
    class Boulder:
        pass

    boulder = pydamics.solidify(Boulder(), position=(0, 0))
    boulder.seo.solid(radius=1.0, restitution=0.1)

    crate = Entity(mass=1.0, position=(0, 5))
    crate.physics2d.gravity(force=9.8)
    crate.physics2d.collider(shape="box", width=1.0, height=1.0, restitution=0.1)

    world = World()
    world.add(crate)
    world.add_solid(boulder)
    for _ in range(200):
        world.step(1 / 60)

    # crate should rest on top of the boulder, not fall through/past it
    assert crate.position.y > 0.5


def test_box_vs_seo_layer_filtering_respected():
    class Platform:
        pass

    platform = pydamics.solidify(Platform(), position=(0, 0))
    platform.seo.solid(width=8, height=1, layer="ghost")

    crate = Entity(mass=1.0, position=(0, 3))
    crate.physics2d.gravity(force=9.8)
    crate.physics2d.collider(shape="box", width=1.0, height=1.0, collides_with={"solid_wall"})

    world = World()
    world.add(crate)
    world.add_solid(platform)
    for _ in range(120):
        world.step(1 / 60)

    assert crate.position.y < -0.5  # fell straight through, layers didn't match
