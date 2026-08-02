import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pydamics import Entity, World


def test_world_on_collision_fires_for_entity_entity():
    events = []
    a = Entity(mass=1.0, position=(0, 0), velocity=(2, 0))
    a.physics2d.collider(radius=0.5, restitution=0.8)
    b = Entity(mass=1.0, position=(0.9, 0))
    b.physics2d.collider(radius=0.5, restitution=0.8)

    world = World()
    world.add(a)
    world.add(b)
    world.on_collision(lambda a_, b_, point, normal, impulse: events.append((a_, b_, point, normal, impulse)))
    world.step(1 / 60)

    assert len(events) == 1
    ev_a, ev_b, point, normal, impulse = events[0]
    assert {ev_a, ev_b} == {a, b}


def test_world_on_collision_fires_for_entity_vs_solid():
    import pydamics as pd

    class Platform:
        pass

    platform = pd.solidify(Platform(), position=(0, 0))
    platform.seo.solid(width=4, height=1, restitution=0.5)

    ball = Entity(mass=1.0, position=(0, 3))
    ball.physics2d.gravity(force=9.8)
    ball.physics2d.collider(radius=0.3, restitution=0.5)

    events = []
    world = World()
    world.add(ball)
    world.add_solid(platform)
    world.on_collision(lambda a, b, point, normal, impulse: events.append((a, b)))

    for _ in range(120):
        world.step(1 / 60)

    assert len(events) >= 1
    assert any(ball in pair for pair in events)


def test_per_entity_on_collision_fires_with_other_and_impulse():
    hits_a = []
    hits_b = []

    a = Entity(mass=1.0, position=(0, 0), velocity=(3, 0))
    a.physics2d.collider(radius=0.5, restitution=1.0)
    a.physics2d.on_collision(lambda other, point, normal, impulse: hits_a.append((other, impulse)))

    b = Entity(mass=1.0, position=(0.9, 0))
    b.physics2d.collider(radius=0.5, restitution=1.0)
    b.physics2d.on_collision(lambda other, point, normal, impulse: hits_b.append((other, impulse)))

    world = World()
    world.add(a)
    world.add(b)
    world.step(1 / 60)

    assert len(hits_a) == 1 and hits_a[0][0] is b
    assert len(hits_b) == 1 and hits_b[0][0] is a


def test_impulse_scales_with_incoming_speed():
    def make_pair(speed):
        a = Entity(mass=1.0, position=(0, 0), velocity=(speed, 0))
        a.physics2d.collider(radius=0.5, restitution=1.0)
        b = Entity(mass=1.0, position=(0.9, 0))
        b.physics2d.collider(radius=0.5, restitution=1.0)
        events = []
        world = World()
        world.add(a)
        world.add(b)
        world.on_collision(lambda x, y, p, n, imp: events.append(imp))
        world.step(1 / 60)
        return events[0].length() if events else 0.0

    slow_impulse = make_pair(1.0)
    fast_impulse = make_pair(5.0)
    assert fast_impulse > slow_impulse


def test_no_collision_no_events():
    a = Entity(mass=1.0, position=(0, 0))
    a.physics2d.collider(radius=0.3)
    b = Entity(mass=1.0, position=(100, 0))
    b.physics2d.collider(radius=0.3)

    events = []
    world = World()
    world.add(a)
    world.add(b)
    world.on_collision(lambda *args: events.append(args))
    world.step(1 / 60)

    assert events == []
