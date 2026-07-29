"""
World -- holds all entities and advances the simulation.

Two ways to run it:
  1. Manual:   world.step(dt)            <- call this yourself in your own loop
  2. Auto-run: world.run(dt=1/60)        <- spins up an internal background
               world.stop()                 thread that calls step() for you
"""
from __future__ import annotations
import threading
import time
from .integrators import velocity_verlet_step


class World:
    def __init__(self):
        self._entities = []
        self._running = False
        self._thread: threading.Thread | None = None
        self.time_elapsed = 0.0

        # optional hook called after every step, e.g. for logging/rendering
        self.on_step = None

    # --- entity management ---
    def add(self, entity) -> None:
        self._entities.append(entity)

    def remove(self, entity) -> None:
        if entity in self._entities:
            self._entities.remove(entity)

    @property
    def entities(self):
        return list(self._entities)

    # --- manual stepping ---
    def step(self, dt: float = 1 / 60) -> None:
        for entity in self._entities:
            velocity_verlet_step(entity, dt)
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
