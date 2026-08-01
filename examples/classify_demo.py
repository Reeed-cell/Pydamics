"""
Example: pydamics v0.4.0 -- classify(), kind_of(), the with-block style,
chainable setters, and GasZone.

Run with: python examples/classify_demo.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pydamics
from pydamics import World, GasZone


class Ball:
    pass


class Platform:
    pass


# --- plain call ---
print("=== plain classify() call ===")
ball = pydamics.classify(Ball(), kind="rigid", mass=1.0, position=(0, 10)).obj
ball.physics2d.gravity(force=9.8)
ball.physics2d.collider(radius=0.4, restitution=0.6)
print(f"kind_of(ball) = {pydamics.kind_of(ball)}")


# --- with-block style, multiple kinds at once ---
print("\n=== with-block, rigid + solid ===")
with pydamics.classify(Platform(), kind=["rigid", "solid"], mass=50.0, position=(0, 0)) as cfg:
    cfg.physics2d.mass(9)            # chainable setter, overrides the mass= above
    cfg.physics2d.gravity(force=1.0)  # falls slowly
    cfg.seo.solid(width=8, height=1, restitution=0.4)

platform = cfg
print(f"kind_of(platform) = {pydamics.kind_of(platform)}")
print(f"platform.mass = {platform.mass}")  # 9, set inside the block


# --- run a quick sim to prove it actually works end to end ---
world = World()
world.add(ball)
world.add(platform)
for _ in range(180):
    world.step(1 / 60)
print(f"\nball settled at y={ball.position.y:.3f}, platform at y={platform.position.y:.3f}")


# --- chainable setters, error validation ---
print("\n=== setter validation ===")
lone_ball = pydamics.classify(Ball(), kind="rigid", mass=1.0, position=(0, 0)).obj
try:
    lone_ball.physics2d.restitution(0.9)  # no collider yet
except RuntimeError as e:
    print(f"Expected error (no collider yet): {e}")

lone_ball.physics2d.collider(radius=0.3)
lone_ball.physics2d.restitution(0.9)  # works now
print("restitution set fine once a collider exists")

try:
    pydamics.classify(Platform(), kind="solid", mass=5.0)  # mass doesn't apply to solid-only
except TypeError as e:
    print(f"Expected error (mass doesn't apply to solid-only): {e}")


# --- gas zone ---
print("\n=== gas zone ===")
wind_tunnel = GasZone(min_point=(-10, -10), max_point=(10, 10), force=5.0)
puff = pydamics.classify(Ball(), kind="gas", mass=0.2, position=(0, 0)).obj
puff.physics2d.gas(wind_tunnel)
print(f"kind_of(puff) = {pydamics.kind_of(puff)}")  # includes "rigid" too

world2 = World()
world2.add(puff)
for _ in range(60):
    world2.step(1 / 60)
print(f"puff pushed to x={puff.position.x:.3f} (y stays {puff.position.y:.3f}, gas is x-only)")
