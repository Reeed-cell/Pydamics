"""
Basic 2D smoothed-particle-hydrodynamics (SPH) fluid simulation.

This is a real (if small-scale) SPH implementation, in the classic
Muller et al. style: each particle's density comes from a smoothing
kernel over nearby particles, pressure comes from an equation of state
tied to that density, and pressure + viscosity forces push particles
apart/together based on their neighbors.

It's a separate system from the physics2d Force API on purpose: SPH
forces are inherently pairwise (a particle's force depends on ITS
NEIGHBORS' state), unlike Force (which only needs its own entity), so it
doesn't fit the per-object Force model. FluidSystem runs its own step().

Naive O(n^2) neighbor search -- fine for tens to a few hundred particles
at real-time. A spatial hash would be the next optimization for thousands.
"""
from __future__ import annotations
import math
from .vector import Vec2


class FluidParticle:
    __slots__ = ("position", "velocity", "mass", "density", "pressure")

    def __init__(self, position, velocity=(0.0, 0.0), mass: float = 1.0):
        self.position = position if isinstance(position, Vec2) else Vec2(*position)
        self.velocity = velocity if isinstance(velocity, Vec2) else Vec2(*velocity)
        self.mass = mass
        self.density = 0.0
        self.pressure = 0.0


class FluidSystem:
    """
    A group of SPH fluid particles simulated together.

        fluid = FluidSystem(smoothing_radius=1.2, rest_density=1000.0,
                             stiffness=200.0, viscosity=0.1)
        fluid.add_particle(position=(0, 5))
        ...
        fluid.step(dt=1/120, gravity=9.8)
        fluid.apply_bounds(Vec2(-5, 0), Vec2(5, 10))  # optional container walls
    """

    def __init__(self, smoothing_radius: float = 1.2, rest_density: float = 1000.0,
                 stiffness: float = 200.0, viscosity: float = 0.1):
        self.h = smoothing_radius
        self.rest_density = rest_density
        self.stiffness = stiffness
        self.viscosity = viscosity
        self.particles: list[FluidParticle] = []

        # standard 2D SPH kernel normalization constants
        self._poly6_const = 4.0 / (math.pi * self.h ** 8)
        self._spiky_grad_const = -30.0 / (math.pi * self.h ** 5)
        self._visc_lap_const = 40.0 / (math.pi * self.h ** 5)

    def add_particle(self, position, velocity=(0.0, 0.0), mass: float = 1.0) -> FluidParticle:
        p = FluidParticle(position=position, velocity=velocity, mass=mass)
        self.particles.append(p)
        return p

    def _poly6(self, r2: float) -> float:
        h2 = self.h * self.h
        if r2 >= h2:
            return 0.0
        diff = h2 - r2
        return self._poly6_const * diff ** 3

    def _spiky_grad(self, r: float) -> float:
        if r >= self.h or r == 0:
            return 0.0
        diff = self.h - r
        return self._spiky_grad_const * diff * diff

    def _visc_laplacian(self, r: float) -> float:
        if r >= self.h:
            return 0.0
        return self._visc_lap_const * (self.h - r)

    def _compute_density_pressure(self) -> None:
        for pi in self.particles:
            density = 0.0
            for pj in self.particles:
                delta = pi.position - pj.position
                density += pj.mass * self._poly6(delta.length_sq())
            pi.density = max(density, 1e-6)
            # simplified equation of state: pressure grows with density above rest
            pi.pressure = max(0.0, self.stiffness * (pi.density - self.rest_density))

    def _compute_forces_and_integrate(self, dt: float, gravity: float) -> None:
        for pi in self.particles:
            pressure_force = Vec2.zero()
            viscosity_force = Vec2.zero()

            for pj in self.particles:
                if pi is pj:
                    continue
                delta = pi.position - pj.position
                r = delta.length()
                if r == 0 or r >= self.h:
                    continue
                direction = delta / r

                # symmetrized pressure force (Muller et al.) to avoid clumping
                pressure_term = (pi.pressure + pj.pressure) / (2.0 * pj.density)
                pressure_force -= direction * (pj.mass * pressure_term * self._spiky_grad(r))

                # viscosity smooths relative velocities between neighbors
                vel_diff = pj.velocity - pi.velocity
                viscosity_force += vel_diff * (
                    self.viscosity * pj.mass / pj.density * self._visc_laplacian(r)
                )

            gravity_force = Vec2(0, -gravity) * pi.density
            total_force = pressure_force + viscosity_force + gravity_force
            accel = total_force / max(pi.density, 1e-6)

            # semi-implicit Euler -- standard for SPH since forces are
            # recomputed fresh from neighbor state every step anyway
            pi.velocity += accel * dt
            pi.position += pi.velocity * dt

    def step(self, dt: float = 1 / 120, gravity: float = 9.8) -> None:
        self._compute_density_pressure()
        self._compute_forces_and_integrate(dt, gravity)

    def apply_bounds(self, min_point, max_point, damping: float = 0.5) -> None:
        """Optional helper: keep particles inside a box, bouncing off walls
        with some energy loss (`damping`). Call after step()."""
        min_point = min_point if isinstance(min_point, Vec2) else Vec2(*min_point)
        max_point = max_point if isinstance(max_point, Vec2) else Vec2(*max_point)
        for p in self.particles:
            if p.position.x < min_point.x:
                p.position.x = min_point.x
                p.velocity.x *= -damping
            elif p.position.x > max_point.x:
                p.position.x = max_point.x
                p.velocity.x *= -damping
            if p.position.y < min_point.y:
                p.position.y = min_point.y
                p.velocity.y *= -damping
            elif p.position.y > max_point.y:
                p.position.y = max_point.y
                p.velocity.y *= -damping
