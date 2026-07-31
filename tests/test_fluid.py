import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pydamics import Entity, World, Vec2, FluidZone, FluidSystem


def test_buoyancy_slows_a_sinking_ball():
    # entity mass=1.0, radius=0.4 -> effective density ~1.99; zone density=3.0
    # is denser -> buoyancy partially offsets gravity, doesn't reverse it
    pool = FluidZone(min_point=(-5, 0), max_point=(5, 10), density=3.0, drag=1.0)

    sinking = Entity(mass=1.0, position=(0, 8))
    sinking.physics2d.gravity(force=9.8)
    sinking.physics2d.buoyancy(zone=pool, radius=0.4)

    falling_freely = Entity(mass=1.0, position=(10, 8))  # outside the pool's x range
    falling_freely.physics2d.gravity(force=9.8)
    falling_freely.physics2d.buoyancy(zone=pool, radius=0.4)  # zone won't apply (outside x bounds)

    world = World()
    world.add(sinking)
    world.add(falling_freely)
    for _ in range(120):
        world.step(1 / 60)

    # the one actually inside the pool's water should be falling slower
    # (or have fallen less) than the one that never touched the fluid
    assert sinking.position.y > falling_freely.position.y


def test_dense_fluid_floats_a_light_object():
    # mass=0.1, radius=0.3 -> effective density ~0.35; zone density=2.0 is
    # ~5.6x denser -> buoyancy dominates gravity, net upward acceleration
    pool = FluidZone(min_point=(-5, -5), max_point=(5, 5), density=2.0, drag=0.5)

    cork = Entity(mass=0.1, position=(0, 0))  # starts already submerged
    cork.physics2d.gravity(force=9.8)
    cork.physics2d.buoyancy(zone=pool, radius=0.3)

    world = World()
    world.add(cork)
    for _ in range(30):
        world.step(1 / 60)

    assert cork.position.y > 0  # floated upward


def test_sph_fluid_system_settles_under_gravity():
    fluid = FluidSystem(smoothing_radius=1.0, rest_density=1000.0, stiffness=100.0, viscosity=0.2)
    for i in range(9):
        x = (i % 3) * 0.5
        y = 5.0 + (i // 3) * 0.5
        fluid.add_particle(position=(x, y))

    for _ in range(60):
        fluid.step(dt=1 / 120, gravity=9.8)
        fluid.apply_bounds(Vec2(-5, 0), Vec2(5, 10), damping=0.3)

    # sanity: nothing exploded to infinity, and particles fell down some
    for p in fluid.particles:
        assert abs(p.position.x) < 20
        assert 0 <= p.position.y < 20
    avg_y = sum(p.position.y for p in fluid.particles) / len(fluid.particles)
    assert avg_y < 5.0  # settled downward from the starting height


def test_sph_particles_stay_within_bounds():
    fluid = FluidSystem()
    fluid.add_particle(position=(0, 5))
    fluid.add_particle(position=(0.3, 5.2))

    for _ in range(120):
        fluid.step(dt=1 / 120, gravity=9.8)
        fluid.apply_bounds(Vec2(-2, 0), Vec2(2, 10))

    for p in fluid.particles:
        assert -2 <= p.position.x <= 2
        assert 0 <= p.position.y <= 10
