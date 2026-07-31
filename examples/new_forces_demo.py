"""
Example: the new force types -- Spring, Wind, Attractor.

Run with: python examples/new_forces_demo.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pydamics import Entity, World, Vec2

# --- Spring: oscillates around an anchor point ---
print("=== Spring ===")
ball = Entity(mass=1.0, position=(5, 0))
ball.physics2d.spring(anchor=Vec2(0, 0), stiffness=8.0, rest_length=1.0, damping=0.3)
world = World()
world.add(ball)
for frame in range(90):
    world.step(1 / 60)
    if frame % 15 == 0:
        print(f"  t={world.time_elapsed:.2f}s  pos={ball.position}")

# --- Wind: constant horizontal push, with gusting ---
print("\n=== Wind (gusting) ===")
leaf = Entity(mass=0.1, position=(0, 10))
leaf.physics2d.gravity(force=2.0)  # light gravity, it's a leaf
leaf.physics2d.wind(force=3.0, direction=Vec2(1, 0), gust=1.5)
world2 = World()
world2.add(leaf)
for frame in range(90):
    world2.step(1 / 60)
    if frame % 15 == 0:
        print(f"  t={world2.time_elapsed:.2f}s  pos={leaf.position}")

# --- Attractor: orbital-style pull toward a point ---
print("\n=== Attractor (orbit-ish) ===")
planet = Vec2(0, 0)
satellite = Entity(mass=1.0, position=(8, 0), velocity=(0, 4.0))  # sideways kick for orbit
satellite.physics2d.attractor(target=planet, strength=100.0)
world3 = World()
world3.add(satellite)
for frame in range(180):
    world3.step(1 / 60)
    if frame % 30 == 0:
        print(f"  t={world3.time_elapsed:.2f}s  pos={satellite.position}")
