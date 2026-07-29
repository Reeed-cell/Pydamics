# pydamics

A small, chainable-syntax 2D physics engine for Python. 3D support planned.

## Install

```bash
pip install pydamics          # once published to PyPI
# or, from source:
pip install -e .
```

## Usage

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

## Attachable forces (`entity.physics2d`)

| Method | Description |
|---|---|
| `.gravity(force=9.8, direction=None)` | Constant acceleration in a direction (default: down) |
| `.fluid(density=1.0, drag=0.1)` | Velocity-proportional drag (air/water resistance) |
| `.friction(coefficient=0.3, normal_force=9.8)` | Kinetic friction opposing motion |
| `.custom(force)` | Attach your own `Force` subclass |
| `.remove(force)` | Detach a previously attached force |
| `.clear()` | Detach all forces |

Every attach method returns the `Force` object, so you can hold onto it and
remove/tweak it later:

```python
g = ball.physics2d.gravity(force=9.8)
ball.physics2d.remove(g)
```

## Integration

Uses **Velocity Verlet** integration (not simple Euler, not full RK4) —
it's the standard for force-based particle sims: stable, and integrates
naturally with drag and future collision impulses.

## Tests

```bash
pip install -e ".[dev]"
pytest tests/
```

## Roadmap

- [ ] Collision detection/response
- [ ] More force types (springs, wind, etc.)
- [ ] 3D physics namespace (`entity.physics3d`)

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
