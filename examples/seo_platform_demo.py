"""
Example: the exact patterns from the pydamics 0.3.0 design discussion --
ball.physics2d.gravity(...) and platform.seo.solid(...).

Run with: python examples/seo_platform_demo.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pydamics
from pydamics import Entity, World


# --- a ball, the usual way ---
class Ball(Entity):
    pass


ball = Ball(mass=1.0, position=(0, 10))
ball.physics2d.gravity(force=9.8)
ball.physics2d.collider(radius=0.4, restitution=0.5)


# --- a platform: your own class, made solid via SEO, no physics required ---
class Platform:
    pass


platform = Platform()
pydamics.solidify(platform, position=(0, 0))
platform.seo.solid(width=8, height=1, restitution=0.5)


world = World()
world.add(ball)
world.add_solid(platform)

for frame in range(240):
    world.step(1 / 60)
    if frame % 30 == 0:
        print(f"t={world.time_elapsed:.2f}s  ball={ball.position}")

print(f"\nball rested at y={ball.position.y:.3f} "
      f"(platform top surface is at y=0.5, ball radius 0.4)")


# --- a "physicsified" platform: has physics AND is solid ---
class FallingPlatform:
    pass


falling_platform = pydamics.attach(FallingPlatform(), mass=100.0, position=(0, -20))
falling_platform.physics2d.gravity(force=0.5)  # drifts down very slowly
pydamics.solidify(falling_platform)  # reuses the position attach() already set
falling_platform.seo.solid(width=8, height=1, restitution=0.3)

ball2 = Entity(mass=1.0, position=(0, -17))
ball2.physics2d.gravity(force=9.8)
ball2.physics2d.collider(radius=0.4, restitution=0.3)

world2 = World()
world2.add(falling_platform)  # physics-capable -> also auto-detected as a solid
world2.add(ball2)

for frame in range(240):
    world2.step(1 / 60)
    if frame % 30 == 0:
        print(f"t={world2.time_elapsed:.2f}s  platform={falling_platform.position}  ball={ball2.position}")
