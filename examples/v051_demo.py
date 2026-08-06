"""
Example: pydamics v0.5.1 -- oriented box colliders, raycasting, and
spatial queries.

Run with: python examples/v051_demo.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import math
import pydamics
from pydamics import Entity, World, Vec2

# --- oriented box colliders: a tilted crate falling onto a platform ---
print("=== Box colliders ===")


class Platform:
    pass


platform = pydamics.solidify(Platform(), position=(0, 0))
platform.seo.solid(width=10, height=1, restitution=0.2)

crate = Entity(mass=1.0, position=(0, 5), angle=math.pi / 8, moment_of_inertia=1.0)
crate.physics2d.gravity(force=9.8)
crate.physics2d.collider(shape="box", width=1.5, height=1.5, restitution=0.2)

world = World()
world.add(crate)
world.add_solid(platform)
for frame in range(180):
    world.step(1 / 60)
    if frame % 30 == 0:
        print(f"  t={world.time_elapsed:.2f}s  crate y={crate.position.y:.3f}  angle={crate.angle:.3f}")


# --- raycasting: a wall detector ---
print("\n=== Raycasting ===")


class Wall:
    pass


wall = pydamics.solidify(Wall(), position=(10, 3))
wall.seo.solid(width=1, height=6)

world2 = World()
world2.add_solid(wall)

hit = world2.raycast(origin=(0, 3), direction=Vec2(1, 0), max_distance=50)
if hit:
    print(f"  ray hit {type(hit.entity).__name__} at distance {hit.distance:.2f}, point={hit.point}")

miss = world2.raycast(origin=(0, 3), direction=Vec2(0, 1), max_distance=50)
print(f"  straight up: {'hit' if miss else 'no hit (correctly missed the wall)'}")


# --- spatial queries: find nearby entities for an AOE-style check ---
print("\n=== Spatial queries ===")
world3 = World()
for i in range(8):
    e = Entity(mass=1.0, position=(i * 2.0, 0))
    world3.add(e)

nearby = world3.query_radius(center=(5, 0), radius=3)
print(f"  {len(nearby)} entities within radius 3 of (5,0)")

in_box = world3.query_rect(min_point=(0, -1), max_point=(6, 1))
print(f"  {len(in_box)} entities inside the rect (0,-1)-(6,1)")
