"""
Visual demo #1: matplotlib animation.

Simulates a few balls falling under gravity + air drag, bouncing off a
floor, and renders it as an animated GIF. No display/window needed --
this works headlessly (great for servers, CI, sharing online).

Run with:  python examples/visual_matplotlib.py
Output:    examples/falling_balls.gif
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import matplotlib
matplotlib.use("Agg")  # headless backend, no display server needed
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from pydamics import Entity, World

# --- set up a few balls with different properties ---
FLOOR_Y = 0.0
RADIUS = 0.4
BOUNCE_DAMPING = 0.65  # energy lost per bounce

balls_config = [
    dict(mass=1.0, position=(1.0, 12.0), color="#e63946", drag=0.15),
    dict(mass=2.0, position=(3.0, 9.0), color="#457b9d", drag=0.05),
    dict(mass=0.5, position=(5.0, 14.0), color="#2a9d8f", drag=0.35),
]

balls = []
world = World()
for cfg in balls_config:
    e = Entity(mass=cfg["mass"], position=cfg["position"])
    e.physics2d.gravity(force=9.8)
    e.physics2d.fluid(density=1.0, drag=cfg["drag"])
    e.color = cfg["color"]  # just tagging it for rendering, not used by the engine
    world.add(e)
    balls.append(e)


def bounce_check(world, dt):
    """Simple floor bounce -- not part of the core engine (no collision
    system yet), just demo-level logic so the sim looks lively."""
    for e in world.entities:
        if e.position.y - RADIUS < FLOOR_Y:
            e.position.y = FLOOR_Y + RADIUS
            e.velocity.y = -e.velocity.y * BOUNCE_DAMPING
            # resync verlet's cached acceleration so next step isn't skewed
            e._prev_accel = e.compute_total_acceleration()


world.on_step = bounce_check

# --- render ---
fig, ax = plt.subplots(figsize=(6, 6))
ax.set_xlim(-1, 8)
ax.set_ylim(0, 16)
ax.axhline(FLOOR_Y, color="black", linewidth=2)
ax.set_title("pydamics: bouncing balls (gravity + drag)")
ax.set_aspect("equal")

circles = [plt.Circle((e.position.x, e.position.y), RADIUS, color=e.color) for e in balls]
for c in circles:
    ax.add_patch(c)

DT = 1 / 60
STEPS_PER_FRAME = 2  # simulate a bit faster than 60fps real-time for a snappier gif


def update(frame):
    for _ in range(STEPS_PER_FRAME):
        world.step(DT)
    for c, e in zip(circles, balls):
        c.center = (e.position.x, e.position.y)
    return circles


anim = animation.FuncAnimation(fig, update, frames=180, interval=33, blit=True)

out_path = os.path.join(os.path.dirname(__file__), "falling_balls.gif")
anim.save(out_path, writer="pillow", fps=30)
print(f"Saved animation to {out_path}")
