"""
World -- holds all entities and advances the simulation.

Two ways to run it:
  1. Manual:   world.step(dt)            <- call this yourself in your own loop
  2. Auto-run: world.run(dt=1/60)        <- spins up an internal background
               world.stop()                 thread that calls step() for you

Each step() does, in order: integrate every entity's motion, resolve
entity-entity collisions, resolve entity-vs-SEO-solid collisions, step
any attached fluid systems, then fire the on_step hook.
"""
from __future__ import annotations
import threading
import time
from .integrators import velocity_verlet_step
from .physics_core import has_physics
from .collision import resolve_all_collisions


class World:
    def __init__(self):
        self._entities = []
        self._solids = []          # pure SEO objects (not necessarily physics-capable)
        self._fluid_systems = []   # list of (FluidSystem, gravity) pairs
        self._running = False
        self._thread: threading.Thread | None = None
        self.time_elapsed = 0.0

        # optional hook called after every step, e.g. for logging/rendering
        self.on_step = None

    # --- entity management ---
    def add(self, entity) -> None:
        """Add a physics-capable object (attach()-ed or an Entity). It'll
        be integrated every step. If it also has an SEO shape
        (`.seo.solid(...)`), it automatically participates in collision
        as a "physicsified" solid too -- no need to also call add_solid()."""
        if not has_physics(entity):
            raise TypeError(
                f"{type(entity).__name__} isn't physics-capable yet. "
                f"Call pydamics.attach(obj, mass=..., position=...) on it "
                f"first, or use pydamics.Entity which does this "
                f"automatically."
            )
        self._entities.append(entity)

    def remove(self, entity) -> None:
        if entity in self._entities:
            self._entities.remove(entity)

    def add_solid(self, obj) -> None:
        """Register a purely static SEO object (solidify()-ed, not
        physics-capable) so entities collide with it. Physics-capable
        "physicsified" solids don't need this -- just use world.add()."""
        self._solids.append(obj)

    def remove_solid(self, obj) -> None:
        if obj in self._solids:
            self._solids.remove(obj)

    def add_fluid_system(self, fluid_system, gravity: float = 9.8) -> None:
        """Register an SPH FluidSystem so it steps alongside the rest of
        the world. Not required -- you can call fluid_system.step(dt)
        yourself instead if you want more control."""
        self._fluid_systems.append((fluid_system, gravity))

    @property
    def entities(self):
        return list(self._entities)

    @property
    def solids(self):
        return list(self._solids)

    # --- manual stepping ---
    def step(self, dt: float = 1 / 60) -> None:
        for entity in self._entities:
            velocity_verlet_step(entity, dt)

        # physicsified solids (physics-capable AND have .seo) live in
        # self._entities already, so combine them with the pure-SEO list
        # for collision purposes
        all_solids = self._solids + [e for e in self._entities if hasattr(e, "seo")]
        resolve_all_collisions(self._entities, all_solids)

        for fluid_system, gravity in self._fluid_systems:
            fluid_system.step(dt, gravity=gravity)

        self.time_elapsed += dt
        if self.on_step:
            self.on_step(self, dt)

    # --- auto-run (internal loop in a background thread) ---
    def run(self, dt: float = 1 / 60, real_time: bool = True) -> None:
        """Start an internal loop that calls step(dt) repeatedly on its own
        thread. Use world.stop() to end it. If real_time=True, it sleeps
        between steps to match wall-clock dt; set False to run as fast as
        possible (e.g. for headless batch simulation)."""
        if self._running:
            return
        self._running = True

        def _loop():
            while self._running:
                start = time.perf_counter()
                self.step(dt)
                if real_time:
                    elapsed = time.perf_counter() - start
                    remaining = dt - elapsed
                    if remaining > 0:
                        time.sleep(remaining)

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    @property
    def running(self) -> bool:
        return self._running
