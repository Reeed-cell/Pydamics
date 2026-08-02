"""
Velocity Verlet integration -- linear and rotational.

Chosen over simple Euler for stability, and over full RK4 because
force-based particle sims (with drag/collision impulses down the line)
integrate more naturally and cheaply with velocity verlet.

Works on anything `attach()` has touched -- Entity or your own class --
since it only relies on the attributes attach() adds, not a bound method.
"""
from __future__ import annotations
from .physics_core import compute_total_acceleration, compute_total_torque

# how long velocity has to stay below sleep_threshold before an entity
# actually goes to sleep -- avoids flickering asleep/awake right at the
# threshold boundary. Only relevant if sleep_threshold is set (not None).
SLEEP_DELAY = 0.5


def velocity_verlet_step(entity, dt: float) -> None:
    # --- linear motion ---
    a_t = entity._prev_accel
    entity.position += entity.velocity * dt + a_t * (0.5 * dt * dt)

    a_t_dt = compute_total_acceleration(entity)
    entity.velocity += (a_t + a_t_dt) * (0.5 * dt)
    entity._prev_accel = a_t_dt

    # --- rotational motion (mirrors the linear half above) ---
    alpha_t = entity._prev_angular_accel
    entity.angle += entity.angular_velocity * dt + 0.5 * alpha_t * dt * dt

    total_torque = compute_total_torque(entity)
    alpha_t_dt = total_torque / entity.moment_of_inertia if entity.moment_of_inertia else 0.0
    entity.angular_velocity += (alpha_t + alpha_t_dt) * (0.5 * dt)
    entity._prev_angular_accel = alpha_t_dt

    # --- sleep bookkeeping (no-op unless sleep_threshold has been set) ---
    if entity._sleep_threshold is not None:
        if entity.velocity.length() < entity._sleep_threshold:
            entity._sleep_still_time += dt
            if entity._sleep_still_time >= SLEEP_DELAY:
                entity._is_sleeping = True
        else:
            entity._sleep_still_time = 0.0
