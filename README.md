# pydamics

A small, chainable-syntax 2D physics engine for Python. 3D support planned.

## Install

```bash
pip install pydamics          # once published to PyPI
# or, from source:
pip install -e .
```

## Usage

pydamics works two ways. Use whichever fits your project.

### 1. With the built-in `Entity` class

```python
from pydamics import Entity, World

ball = Entity(mass=2.0, position=(0, 10))
ball.physics2d.gravity(force=9.8)
ball.physics2d.fluid(density=1.2, drag=0.3)

world = World()
world.add(ball)

# Option 1: step it yourself
for _ in range(120):
    world.step(dt=1/60)
    print(ball.position)

# Option 2: let the engine run itself on a background thread
world.run(dt=1/60)
...
world.stop()
```

### 2. As an extension on YOUR OWN class

pydamics doesn't force an Entity/World object model on you. If you
already have your own classes, three equivalent ways to make an object
physics-capable -- pick whichever fits how you write your classes:

```python
import pydamics
from pydamics import World

class Spaceship:
    def __init__(self, name):
        self.name = name          # your own attributes, untouched

# (a) function call -- no inheritance required
ship = pydamics.attach(Spaceship("Falcon"), mass=1500.0, position=(0, 20))

# (b) mixin -- inherit and call super().__init__()
class Spaceship(pydamics.PhysicsObject):
    def __init__(self, name, **physics_kwargs):
        super().__init__(**physics_kwargs)
        self.name = name
ship = Spaceship("Falcon", mass=1500.0, position=(0, 20))

# (c) decorator -- no inheritance, no manual call
@pydamics.physics_class(mass=1500.0, position=(0, 20))
class Spaceship:
    def __init__(self, name):
        self.name = name
ship = Spaceship("Falcon")

ship.physics2d.gravity(force=9.8)

world = World()
world.add(ship)   # World.add() checks pydamics.has_physics(ship) and
                   # raises a clear TypeError if you forgot to attach()
world.step(dt=1/60)
```

`Entity` is just a thin convenience wrapper around `attach()` -- use
whichever suits how you're structuring your project.

### 3. One unified entry point: classify() + kind_of()

`attach()`/`solidify()`/`fluidify()` are three different verbs to
remember. `classify()` is a thin dispatcher over all three -- pick a
`kind` (or a list of them) instead:

```python
import pydamics
from pydamics import World

pydamics.classify(ship, kind="rigid", mass=1500.0, position=(0, 20))
pydamics.classify(platform, kind=["rigid", "solid"], mass=50.0, position=(0, 0))  # both at once
pydamics.classify(droplet, kind="fluid", mass=1.0, position=(0, 5))

pydamics.kind_of(ship)  # -> frozenset({"rigid"})
```

It works as a plain call (classification already happened by the time
you get the return value) or as a `with`-block for grouping setup
visually -- `__enter__` just hands back the object itself:

```python
with pydamics.classify(platform, kind=["rigid", "solid"], mass=50.0, position=(0, 0)) as cfg:
    cfg.physics2d.mass(9).velocity(0, 0)
    cfg.seo.solid(width=8, height=1)
```

Passing a property that doesn't apply to the requested kind raises a
clear error instead of silently doing nothing -- e.g. `mass=` with
`kind="solid"` alone (no `"rigid"`) raises `TypeError`, since a pure
solid never gets a `.physics2d` namespace or gets integrated by
`world.step()`.

`classify()`/`kind_of()` don't replace `attach()`/`solidify()`/
`fluidify()` -- those work exactly as before; `classify()` is additive
sugar on top.

## Attachable forces (`obj.physics2d`)

| Method | Description |
|---|---|
| `.gravity(force=9.8, direction=None)` | Constant acceleration in a direction (default: down) |
| `.fluid(density=1.0, drag=0.1)` | Velocity-proportional drag (air/water resistance) |
| `.friction(coefficient=0.3, normal_force=9.8)` | Kinetic friction opposing motion |
| `.spring(anchor, stiffness=10.0, rest_length=1.0, damping=0.1)` | Hooke's-law spring toward a point or another physics object (anchor can be moving) |
| `.wind(force=2.0, direction=None, gust=0.0)` | Constant directional acceleration, optionally gusting |
| `.attractor(target, strength=50.0, min_distance=0.1)` | Inverse-square pull toward a point/object (orbital-style gravity) |
| `.vortex(center, strength=20.0, min_distance=0.1)` | Tangential swirling force around a point |
| `.buoyancy(zone, radius=0.4, gravity=9.8)` | Archimedes-style float/sink force inside a `FluidZone` |
| `.gas(zone)` | Constant x-only push inside a `GasZone` -- deliberately minimal (no drag/gust/y) |
| `.custom(force)` | Attach your own `Force` subclass |
| `.remove(force)` | Detach a previously attached force |
| `.clear()` | Detach all forces |

Every attach method returns the `Force` object, so you can hold onto it and
remove/tweak it later:

```python
g = ball.physics2d.gravity(force=9.8)
ball.physics2d.remove(g)
```

### Chainable setters

Update state after construction -- each returns `self` so they stack:

```python
ball.physics2d.mass(9).velocity(0, 0).position(3, 4)
```

| Method | Description |
|---|---|
| `.mass(value)` | Update mass |
| `.position(x, y)` | Update position |
| `.velocity(x, y)` | Update velocity |
| `.restitution(value)` | Update collider bounciness -- **requires `.collider()` already called**, raises `RuntimeError` otherwise |
| `.radius(value)` | Update collider size -- same requirement |
| `.static(bool)` | Toggle whether a collider is static -- same requirement |

## Collision

```python
ball.physics2d.collider(radius=0.4, restitution=0.7)   # bouncy
wall.physics2d.collider(radius=0.5, restitution=0.5, static=True)  # never moves
```

`World.step()` automatically detects and resolves overlaps between any
entities that have a `.physics2d.collider(...)` -- impulse-based, with a
`restitution` (bounciness) you set per object; the lower of the two
objects' restitution values is used per collision.

### Layers and masks

Filter what collides with what:

```python
bullet.physics2d.collider(radius=0.1, layer="player_bullet", collides_with={"enemy"})
enemy.physics2d.collider(radius=0.5, layer="enemy")
wall.physics2d.collider(radius=1.0, layer="wall")
```

`collides_with=None` (the default) collides with everything regardless
of layer. When set, filtering is symmetric-AND: a pair only collides if
**each** side's `collides_with` (when set) includes the other's layer —
so the bullet above hits the enemy but passes straight through the
wall. `.seo.solid()` takes the same `layer`/`collides_with` kwargs.

### Collision events

```python
world.on_collision(lambda a, b, point, normal, impulse: print(f"{a} hit {b}"))
ball.physics2d.on_collision(lambda other, point, normal, impulse: print("I got hit"))
```

Fires once per step for every collision actually resolved (entity-entity
or entity-vs-solid). `world.on_collision`'s `normal` points from `a` to
`b`; the per-object `.physics2d.on_collision` gets a normal pointing
*away from* the other object (i.e. "the direction I got pushed").

## Trigger / sensor zones

Overlap detection with `on_enter`/`on_exit` callbacks, but no collision
response — nothing bounces off a trigger. Good for checkpoints, pickups,
aggro radii, damage zones:

```python
zone = pydamics.TriggerZone(position=(10, 0), radius=2.0,
                             on_enter=lambda e: print("entered!"),
                             on_exit=lambda e: print("left!"))
world.add_trigger(zone)
```

Pass `radius` for a circular zone or `width`+`height` for a rectangular
one. Entities are checked against their `.position` (treated as a
point, ignoring any collider radius) — matches the simple "is this
point inside this zone" check most games actually want. Callbacks fire
once per transition, not every frame while inside/outside; if an entity
is already inside on the first check (e.g. it spawned there), `on_enter`
fires then.

## Sleep / deactivation

Skip integrating objects that have settled, for performance:

```python
ball.physics2d.sleep_threshold = 0.05   # velocity below this -> eligible to sleep
ball.physics2d.is_sleeping              # read-only
ball.physics2d.wake()                   # force it awake immediately
```

`sleep_threshold` defaults to `None` (sleeping disabled) — opt-in only,
so nothing changes unless you set it. Once velocity stays below the
threshold for half a second, the object stops getting force-computed
and integrated entirely, but still participates in collision detection
— a moving object hitting a sleeping one wakes it automatically. Set
`sleep_threshold = None` again to disable sleep and wake it.

## Orientation — angle, angular velocity, torque

Every `Entity`/`attach()`-ed object has rotational state alongside its
linear position/velocity, integrated with the same velocity-Verlet
scheme:

```python
ball = Entity(mass=1.0, position=(0, 10), angle=0.0, angular_velocity=0.0,
              moment_of_inertia=None)   # defaults to mass * 0.5
ball.physics2d.torque(magnitude=5.0)    # steady torque, returns a Torque you can remove
ball.physics2d.remove_torque(t)
```

Defaults are a complete no-op — `angle`/`angular_velocity` never change
unless you apply torque or an off-center collision imparts spin. That
second part only actually happens for **box** solids, not circles: since
the collision normal is always computed from the contact point toward a
circle's own center, a circular mover's lever arm is always exactly
parallel to its own impulse (cross product is provably always zero) —
matching real frictionless sphere physics (no tangential/friction impulse
is modeled here). A physicsified box hit away from its center, though,
picks up genuine torque, since a box's geometry isn't radially symmetric.

## SEO — Solid Environment Objects

For solid geometry (platforms, walls, floors) that things collide with,
`.seo` works whether or not the object is also physics-capable:

```python
import pydamics

# a plain object, made purely static/solid -- doesn't need attach()
class Platform:
    pass

platform = Platform()
pydamics.solidify(platform, position=(0, 0))
platform.seo.solid(width=8, height=1, restitution=0.4)

world.add_solid(platform)   # register it for collision (not world.add() --
                             # it isn't physics-capable, so world.add()
                             # would reject it)
```

If the object is ALSO physics-capable (`attach()`-ed or an `Entity`), it
becomes a "physicsified" solid: movable/affected by forces, but still
solid -- e.g. a platform that falls under gravity but still carries a
ball resting on top of it. Physicsified solids just go through the
normal `world.add()` -- they're auto-detected as solids too, no need to
also call `add_solid()`.

```python
platform = pydamics.attach(Platform(), mass=50.0, position=(0, 10))
platform.physics2d.gravity(force=2.0)
pydamics.solidify(platform)          # reuses the position attach() set
platform.seo.solid(width=8, height=1)
world.add(platform)                  # physics-capable -> world.add(), not add_solid()
```

`.seo.solid()` accepts either `width`+`height` (rectangle) or `radius`
(circle). Like physics attachment, `solidify()` has mixin/decorator
equivalents too -- `pydamics.SolidObject` (inherit + `super().__init__()`)
and `@pydamics.solid_class(position=...)`.

## Fluid dynamics

Two different scopes, depending on what you need:

**FluidZone (buoyancy)** — lightweight: a rectangular region entities
float or sink in, via `.physics2d.buoyancy(zone)` (see the forces table
above). `density` is *relative* to your entities' own effective density
(`mass / (pi * radius^2)`) — not a literal real-world kg/m³ value; pick
values relative to what your entities' mass/radius actually imply, or
you'll get correctly-extreme (but probably undesired) results, the same
way a helium balloon dropped in water would rocket upward in real life.

```python
pool = pydamics.FluidZone(min_point=(-5, 0), max_point=(5, 5), density=1.8, drag=1.5)
cork.physics2d.buoyancy(zone=pool, radius=0.3)
```

**GasZone (minimal air push)** — deliberately much simpler than
`FluidZone`: no buoyancy, no drag, no gust, no y-component or direction
vector. Just a constant push along x for anything inside, via
`.physics2d.gas(zone)`. Requesting `kind="gas"` through `classify()`
also gives the object `.physics2d` (a `"rigid"` classification comes
along with it), since the push is a `Force` like any other:

```python
wind_tunnel = pydamics.GasZone(min_point=(-10, -10), max_point=(10, 10), force=5.0)
puff = pydamics.classify(MyParticle(), kind="gas", mass=0.2, position=(0, 0)).obj
puff.physics2d.gas(wind_tunnel)
```

**FluidSystem (full SPH)** — real smoothed-particle-hydrodynamics: particles
with density/pressure/viscosity computed from their neighbors, genuinely
fluid-like behavior. Its own particle system (not the `Entity`/`physics2d`
model, since SPH forces are inherently pairwise), and uses a spatial hash
internally so it scales past a few hundred particles:

```python
from pydamics import FluidSystem, Vec2

fluid = FluidSystem(smoothing_radius=1.0, rest_density=1000.0, stiffness=150.0)
fluid.add_particle(position=(0, 5))          # built-in particle
# ... add more particles ...

world.add_fluid_system(fluid, gravity=9.8)   # steps alongside world.step()
# or drive it yourself:
fluid.step(dt=1/120, gravity=9.8)
fluid.apply_bounds(Vec2(-5, 0), Vec2(5, 10))  # optional container walls
```

**Using your own class as a fluid particle** — mirrors `attach()`/`solidify()`:

```python
class WaterDroplet:
    def __init__(self, name):
        self.name = name

droplet = pydamics.fluidify(WaterDroplet("drop1"), mass=1.0, position=(0, 5))
pydamics.is_fluid(droplet)   # True -- check whether something's fluid-capable
fluid.add(droplet)            # register it directly (fluid.add_particle() only
                               # makes built-in FluidParticle instances)
```

Also has mixin (`pydamics.FluidObject`) and decorator (`@pydamics.fluid_class(...)`)
equivalents, same pattern as physics/SEO.

## Performance

Both collision (entity-entity) and SPH neighbor search use a uniform
grid spatial hash internally instead of a naive O(n²) scan — roughly
O(n) for reasonably spread-out scenes instead of quadratic. This is an
implementation detail, not an API change; `pydamics.SpatialHash` is
exposed if you want it for your own pairwise-interaction code.

## Integration

Uses **Velocity Verlet** integration (not simple Euler, not full RK4) —
it's the standard for force-based particle sims: stable, and integrates
naturally with drag and collision impulses.

## Tests

```bash
pip install -e ".[dev]"
pytest tests/
```

## Visualization

Rendering (matplotlib GIFs, interactive pygame windows) lives in a separate
companion package so this core library stays dependency-free:

```bash
pip install pydamicsvisual
```

See [pydamicsvisual](https://pypi.org/project/pydamicsvisual/) for details.

## Roadmap

**Staged for v0.5.1:**
- [ ] Raycasting (`world.raycast(...)`, `world.raycast_all(...)`)
- [ ] Dynamic box/capsule colliders for moving entities (currently circles only for movers; boxes exist for SEO solids)
- [ ] Spatial query API (`world.query_radius(...)`, `world.query_box(...)`)

**Further out:**
- [ ] 3D physics namespace (`entity.physics3d`)
- [ ] Polygon collision shapes
- [ ] Joints/constraints (pin, distance, fixed, rope) -- likely its own v0.6.0, this is a bigger undertaking than anything above (iterative constraint solver)
- [ ] Tangential/friction impulses (would let circular movers pick up spin from off-center contact, not just boxes)

## Publishing (for maintainers)

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: pydamics 2D physics engine"
git branch -M main
git remote add origin https://github.com/<your-username>/pydamics.git
git push -u origin main
```

The `.github/workflows/tests.yml` workflow will auto-run the test suite on
every push.

### 2. One-time PyPI setup (Trusted Publishing — no API tokens needed)

1. Create a [PyPI account](https://pypi.org/account/register/) if you don't have one.
2. Go to **pypi.org → Your account → Publishing** and add a new "trusted publisher":
   - PyPI project name: `pydamics`
   - Owner: `<your-github-username>`
   - Repository name: `pydamics`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
3. In your GitHub repo, go to **Settings → Environments** and create an environment named `pypi` (this matches the workflow file — no secrets needed, trusted publishing handles auth).

### 3. Ship a release

Bump the version in `pyproject.toml`, commit, then on GitHub:
**Releases → Draft a new release → tag `v0.1.0` → Publish release.**

That triggers `.github/workflows/publish.yml`, which builds the package and
uploads it to PyPI automatically. From then on, anyone can:

```bash
pip install pydamics
```
