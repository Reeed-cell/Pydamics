"""
Velocity Verlet integration.

Chosen over simple Euler for stability, and over full RK4 because
force-based particle sims (with drag/collision impulses down the line)
integrate more naturally and cheaply with velocity verlet.
"""
from __future__ import annotations


def velocity_verlet_step(entity, dt: float) -> None:
    # 1. update position using current velocity + current (previous) acceleration
    a_t = entity._prev_accel
    entity.position += entity.velocity * dt + a_t * (0.5 * dt * dt)

    # 2. compute new acceleration at the new position/velocity
    a_t_dt = entity.compute_total_acceleration()

    # 3. update velocity using the average of old and new acceleration
    entity.velocity += (a_t + a_t_dt) * (0.5 * dt)

    # 4. store for next step
    entity._prev_accel = a_t_dt
