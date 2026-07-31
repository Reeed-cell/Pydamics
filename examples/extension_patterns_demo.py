"""
Example: the three ways to make your own class physics/solid/fluid
capable -- function call, mixin, or decorator -- plus fluid identification.

Run with: python examples/extension_patterns_demo.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pydamics
from pydamics import World, FluidSystem


# --- 1. function call (the original style) ---
class Spaceship:
    def __init__(self, name):
        self.name = name


ship = pydamics.attach(Spaceship("Falcon"), mass=1500.0, position=(0, 20))
ship.physics2d.gravity(force=9.8)


# --- 2. mixin (inherit, call super().__init__) ---
class Drone(pydamics.PhysicsObject):
    def __init__(self, callsign, **physics_kwargs):
        super().__init__(**physics_kwargs)
        self.callsign = callsign


drone = Drone("Recon-1", mass=5.0, position=(2, 15))
drone.physics2d.gravity(force=3.0)  # has thrusters, falls slower


# --- 3. decorator (no inheritance needed) ---
@pydamics.physics_class(mass=0.5, position=(4, 25))
class Debris:
    def __init__(self, label):
        self.label = label


chunk = Debris("panel-A")
chunk.physics2d.gravity(force=9.8)


world = World()
world.add(ship)
world.add(drone)
world.add(chunk)

for _ in range(60):
    world.step(1 / 60)

print(f"{ship.name}: {ship.position}")
print(f"{drone.callsign}: {drone.position}")
print(f"{chunk.label}: {chunk.position}")


# --- fluid identification: is this thing a fluid particle? ---
print("\n=== fluid identification ===")


class WaterDroplet:
    def __init__(self, name):
        self.name = name


plain_object = WaterDroplet("unregistered")
print(f"is_fluid(plain_object) = {pydamics.is_fluid(plain_object)}")  # False

droplet = pydamics.fluidify(WaterDroplet("drop1"), mass=1.0, position=(0, 5))
print(f"is_fluid(droplet)      = {pydamics.is_fluid(droplet)}")  # True

fluid = FluidSystem()
fluid.add(droplet)  # register the custom object directly, no FluidParticle needed
fluid.add_particle(position=(0.3, 5.1))  # or use the built-in convenience

for _ in range(30):
    fluid.step(dt=1 / 120, gravity=9.8)

print(f"droplet fell to y={droplet.position.y:.3f}")
