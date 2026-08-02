"""
Example: pydamics v0.5.0 -- collision layers, collision events, trigger
zones, sleep, and orientation/torque.

Run with: python examples/v050_demo.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pydamics
from pydamics import Entity, World, TriggerZone

# --- collision layers: a bullet that only hits "enemy", not "wall" ---
print("=== Layers ===")
bullet = Entity(mass=0.1, position=(0, 0), velocity=(10, 0))
bullet.physics2d.collider(radius=0.1, restitution=1.0, layer="player_bullet",
                           collides_with={"enemy"})
wall = Entity(mass=1000.0, position=(2, 0))
wall.physics2d.collider(radius=0.5, restitution=1.0, layer="wall", static=True)

world = World()
world.add(bullet)
world.add(wall)
for _ in range(30):
    world.step(1 / 60)
print(f"bullet passed through wall at layer mismatch: x={bullet.position.x:.2f}")

# --- collision events ---
print("\n=== Collision events ===")
a = Entity(mass=1.0, position=(0, 0), velocity=(3, 0))
a.physics2d.collider(radius=0.5, restitution=0.8)
b = Entity(mass=1.0, position=(0.9, 0))
b.physics2d.collider(radius=0.5, restitution=0.8)

world2 = World()
world2.add(a)
world2.add(b)
world2.on_collision(lambda x, y, point, normal, impulse:
                     print(f"  world saw a collision, impulse magnitude={impulse.length():.2f}"))
b.physics2d.on_collision(lambda other, point, normal, impulse: print("  b got hit!"))
world2.step(1 / 60)

# --- trigger zone ---
print("\n=== Trigger zone ===")
checkpoint = TriggerZone(position=(5, 0), radius=1.0,
                          on_enter=lambda e: print("  checkpoint reached!"))
runner = Entity(mass=1.0, position=(0, 0), velocity=(2, 0))
world3 = World()
world3.add(runner)
world3.add_trigger(checkpoint)
for _ in range(200):
    world3.step(1 / 60)

# --- sleep ---
print("\n=== Sleep ===")
settled = Entity(mass=1.0, position=(0, 0), velocity=(0, 0))
settled.physics2d.sleep_threshold = 0.05
world4 = World()
world4.add(settled)
for _ in range(60):
    world4.step(1 / 60)
print(f"is_sleeping after settling: {settled.physics2d.is_sleeping}")

# --- orientation / torque ---
print("\n=== Orientation ===")
spinner = Entity(mass=1.0, position=(0, 0), moment_of_inertia=1.0)
spinner.physics2d.torque(magnitude=3.0)
world5 = World()
world5.add(spinner)
for _ in range(60):
    world5.step(1 / 60)
print(f"spinner angle={spinner.angle:.3f} rad, angular_velocity={spinner.angular_velocity:.3f} rad/s")
