import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pydamics import Entity, World

ball = Entity(mass=1.0, position=(0.0, 5.0))
ball.physics2d.gravity(force=9.8)

world = World()
world.add(ball)

world.run(dt=1 / 60, real_time=False)  # run as fast as possible
time.sleep(0.2)
world.stop()

print(f"steps simulated: {world.time_elapsed:.3f}s of sim time")
print(f"final: {ball}")
