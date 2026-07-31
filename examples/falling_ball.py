"""
Simple demo: a ball falling under gravity with air drag, manually stepped.

Run with:  python examples/falling_ball.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pydamics import Entity, World

ball = Entity(mass=2.0, position=(0.0, 10.0))
ball.physics2d.gravity(force=9.8)
ball.physics2d.fluid(density=1.2, drag=0.3)

world = World()
world.add(ball)

dt = 1 / 60
for frame in range(120):
    world.step(dt)
    if frame % 10 == 0:
        print(f"t={world.time_elapsed:5.2f}s  pos={ball.position}  vel={ball.velocity}")
