"""
Example: FluidZone buoyancy, SPH FluidSystem, and the Vortex force.

Run with: python examples/fluid_and_vortex_demo.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pydamics import Entity, World, Vec2, FluidZone, FluidSystem

# --- buoyancy zone: a cork floating in a pool ---
print("=== FluidZone buoyancy ===")
# cork: mass=0.2, radius=0.3 -> effective density ~0.71; zone density=1.8
# is ~2.5x denser -> floats
pool = FluidZone(min_point=(-5, 0), max_point=(5, 5), density=1.8, drag=1.5)
cork = Entity(mass=0.2, position=(0, 6))
cork.physics2d.gravity(force=9.8)
cork.physics2d.buoyancy(zone=pool, radius=0.3)

world = World()
world.add(cork)
for frame in range(180):
    world.step(1 / 60)
    if frame % 30 == 0:
        print(f"  t={world.time_elapsed:.2f}s  cork y={cork.position.y:.3f}")

# --- SPH: a small drop of fluid falling into a container ---
print("\n=== SPH FluidSystem ===")
fluid = FluidSystem(smoothing_radius=1.0, rest_density=1000.0, stiffness=150.0, viscosity=0.3)
for i in range(16):
    x = (i % 4) * 0.4 - 0.6
    y = 6.0 + (i // 4) * 0.4
    fluid.add_particle(position=(x, y))

for frame in range(120):
    fluid.step(dt=1 / 120, gravity=9.8)
    fluid.apply_bounds(Vec2(-3, 0), Vec2(3, 10), damping=0.4)
    if frame % 20 == 0:
        avg_y = sum(p.position.y for p in fluid.particles) / len(fluid.particles)
        print(f"  frame={frame}  avg particle height={avg_y:.3f}")

# --- vortex: swirling motion around a center point ---
print("\n=== Vortex ===")
debris = Entity(mass=1.0, position=(4, 0))
debris.physics2d.vortex(center=Vec2(0, 0), strength=15.0)

world2 = World()
world2.add(debris)
for frame in range(180):
    world2.step(1 / 60)
    if frame % 30 == 0:
        print(f"  t={world2.time_elapsed:.2f}s  debris={debris.position}")
