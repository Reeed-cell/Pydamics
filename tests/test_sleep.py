import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pydamics import Entity, World


def test_sleep_disabled_by_default():
    ball = Entity(mass=1.0, position=(0, 0))
    assert ball.physics2d.sleep_threshold is None
    assert ball.physics2d.is_sleeping is False


def test_entity_falls_asleep_after_settling():
    ball = Entity(mass=1.0, position=(0, 0), velocity=(0, 0))
    ball.physics2d.sleep_threshold = 0.1
    # no forces -- velocity stays 0, well under threshold immediately

    world = World()
    world.add(ball)
    for _ in range(60):  # 1 second, > SLEEP_DELAY (0.5s)
        world.step(1 / 60)

    assert ball.physics2d.is_sleeping is True


def test_sleeping_entity_stops_integrating():
    ball = Entity(mass=1.0, position=(0, 5), velocity=(0, 0))
    ball.physics2d.sleep_threshold = 0.1

    world = World()
    world.add(ball)
    for _ in range(60):
        world.step(1 / 60)
    assert ball.physics2d.is_sleeping is True

    frozen_position = ball.position
    ball.physics2d.gravity(force=9.8)  # attach gravity AFTER it's asleep
    for _ in range(60):
        world.step(1 / 60)

    # still sleeping -> gravity never gets computed/integrated
    assert ball.position.y == frozen_position.y


def test_wake_resets_sleep_state():
    ball = Entity(mass=1.0, position=(0, 0), velocity=(0, 0))
    ball.physics2d.sleep_threshold = 0.1
    world = World()
    world.add(ball)
    for _ in range(60):
        world.step(1 / 60)
    assert ball.physics2d.is_sleeping is True

    ball.physics2d.wake()
    assert ball.physics2d.is_sleeping is False


def test_moving_object_wakes_sleeping_object_on_collision():
    sleeper = Entity(mass=1.0, position=(2, 0), velocity=(0, 0))
    sleeper.physics2d.collider(radius=0.5, restitution=0.8)
    sleeper.physics2d.sleep_threshold = 0.1

    world = World()
    world.add(sleeper)
    for _ in range(60):
        world.step(1 / 60)
    assert sleeper.physics2d.is_sleeping is True

    mover = Entity(mass=1.0, position=(0, 0), velocity=(5, 0))
    mover.physics2d.collider(radius=0.5, restitution=0.8)
    world.add(mover)

    for _ in range(60):
        world.step(1 / 60)
        if not sleeper.physics2d.is_sleeping:
            break

    assert sleeper.physics2d.is_sleeping is False


def test_setting_threshold_to_none_disables_sleep_and_wakes():
    ball = Entity(mass=1.0, position=(0, 0), velocity=(0, 0))
    ball.physics2d.sleep_threshold = 0.1
    world = World()
    world.add(ball)
    for _ in range(60):
        world.step(1 / 60)
    assert ball.physics2d.is_sleeping is True

    ball.physics2d.sleep_threshold = None
    assert ball.physics2d.is_sleeping is False
