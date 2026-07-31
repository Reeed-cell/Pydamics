"""
Example: attaching physics to YOUR OWN class instead of using pydamics.Entity.

pydamics doesn't force you into an Entity/World object model -- attach()
makes any object of yours physics-capable in place.

Run with: python examples/extend_own_class.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pydamics
from pydamics import World


class Spaceship:
    """A totally ordinary class of your own -- no pydamics involved yet."""

    def __init__(self, name):
        self.name = name
        self.fuel = 100.0  # your own unrelated game state

    def status(self):
        return (f"{self.name}: pos={self.position}, "
                f"falling at {self.velocity.y:.2f} m/s, fuel={self.fuel}")


# --- make it physics-capable ---
ship = Spaceship("Falcon")
pydamics.attach(ship, mass=1500.0, position=(0, 20))
ship.physics2d.gravity(force=9.8)
ship.physics2d.fluid(density=1.0, drag=0.05)

world = World()
world.add(ship)

for _ in range(120):
    world.step(1 / 60)

print(ship.status())

# --- world.add() checks physics-capability and errors clearly if you forget attach() ---
try:
    world.add(Spaceship("Forgotten"))
except TypeError as e:
    print(f"\nExpected error when forgetting attach(): {e}")
