import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pydamics import Entity, World, TriggerZone


def test_on_enter_fires_once_when_entering():
    enters = []
    zone = TriggerZone(position=(5, 0), radius=1.0, on_enter=lambda e: enters.append(e))

    ball = Entity(mass=1.0, position=(0, 0), velocity=(2, 0))
    world = World()
    world.add(ball)
    world.add_trigger(zone)

    for _ in range(300):  # ball travels well past x=5
        world.step(1 / 60)

    assert len(enters) == 1
    assert enters[0] is ball


def test_on_exit_fires_once_when_leaving():
    exits = []
    zone = TriggerZone(position=(5, 0), radius=1.0, on_exit=lambda e: exits.append(e))

    ball = Entity(mass=1.0, position=(0, 0), velocity=(2, 0))
    world = World()
    world.add(ball)
    world.add_trigger(zone)

    for _ in range(300):
        world.step(1 / 60)

    assert len(exits) == 1
    assert exits[0] is ball


def test_no_collision_response_from_trigger():
    zone = TriggerZone(position=(0, 0), radius=5.0)  # ball spawns inside
    ball = Entity(mass=1.0, position=(0, 0), velocity=(1, 0))
    world = World()
    world.add(ball)
    world.add_trigger(zone)

    for _ in range(10):
        world.step(1 / 60)

    # ball should move freely through the trigger zone -- no bounce, no push
    assert ball.position.x > 0
    assert ball.velocity.x == 1.0  # unchanged, no impulse ever applied


def test_box_trigger_zone():
    entered = []
    zone = TriggerZone(position=(0, 0), width=4, height=4,
                        on_enter=lambda e: entered.append(e))
    ball = Entity(mass=1.0, position=(-5, 0), velocity=(2, 0))
    world = World()
    world.add(ball)
    world.add_trigger(zone)

    for _ in range(300):
        world.step(1 / 60)

    assert len(entered) == 1


def test_entity_already_inside_fires_enter_on_first_check():
    entered = []
    zone = TriggerZone(position=(0, 0), radius=2.0, on_enter=lambda e: entered.append(e))
    ball = Entity(mass=1.0, position=(0, 0))  # spawns inside
    world = World()
    world.add(ball)
    world.add_trigger(zone)

    world.step(1 / 60)

    assert len(entered) == 1


def test_multiple_entities_tracked_independently():
    enters = []
    zone = TriggerZone(position=(0, 0), radius=1.0, on_enter=lambda e: enters.append(e))

    a = Entity(mass=1.0, position=(0, 0))  # already inside
    b = Entity(mass=1.0, position=(10, 0))  # far outside

    world = World()
    world.add(a)
    world.add(b)
    world.add_trigger(zone)
    world.step(1 / 60)

    assert enters == [a]
