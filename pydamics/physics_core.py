"""
Generic physics extension system.

This is what lets pydamics work with YOUR classes instead of forcing you
into an Entity/World object model. Call `attach()` on any object you own
to make it physics-capable in place -- it gets `.position`, `.velocity`,
`.mass`, and a `.physics2d` namespace, exactly like an Entity has.

    class Spaceship:
        def __init__(self, name):
            self.name = name

    ship = Spaceship("Falcon")
    pydamics.attach(ship, mass=1500.0, position=(0, 20))
    ship.physics2d.gravity(force=9.8)

`Entity` (in entity.py) is just a small convenience class built on top of
this -- use it if you don't have your own class and don't want to think
about it, or use `attach()` directly if you do.
"""
from __future__ import annotations
from .vector import Vec2
from .physics2d import Physics2D

# the attributes attach() adds -- used by has_physics() to check whether
# a given object has already been made physics-capable
_REQUIRED_ATTRS = ("position", "velocity", "mass", "_forces", "_prev_accel", "physics2d")


def attach(obj, mass: float = 1.0, position=(0.0, 0.0), velocity=(0.0, 0.0)):
    """
    Make `obj` physics-capable, in place. Adds `.position`, `.velocity`,
    `.mass`, and a `.physics2d` namespace so `obj.physics2d.gravity(...)`
    etc. work exactly like they would on an Entity.

    Returns `obj`, so this can be chained:
        ship = pydamics.attach(Spaceship("Falcon"), mass=1500.0, position=(0, 20))

    Raises TypeError if `obj` can't hold new attributes (e.g. it uses
    `__slots__` without room for them).
    """
    try:
        obj.mass = float(mass)
    except AttributeError:
        raise TypeError(
            f"{type(obj).__name__} doesn't support attribute assignment "
            "(e.g. it uses __slots__ without room for new attributes), "
            "so pydamics can't attach physics to it. Add the missing "
            "slots ('position', 'velocity', 'mass', '_forces', "
            "'_prev_accel', 'physics2d') or use pydamics.Entity instead."
        )

    obj.position = position if isinstance(position, Vec2) else Vec2(*position)
    obj.velocity = velocity if isinstance(velocity, Vec2) else Vec2(*velocity)
    obj._prev_accel = Vec2.zero()
    obj._forces = []
    obj._collider = None

    def _add_force(force):
        obj._forces.append(force)

    def _remove_force(force):
        if force in obj._forces:
            obj._forces.remove(force)

    def _clear_forces():
        obj._forces.clear()

    obj._add_force = _add_force
    obj._remove_force = _remove_force
    obj._clear_forces = _clear_forces
    obj.physics2d = Physics2D(obj)

    return obj


def has_physics(obj) -> bool:
    """Check whether `attach()` has already been called on this object.
    World.add() uses this to give a clear error instead of failing deep
    inside the integrator when you forget to attach() something."""
    return all(hasattr(obj, attr) for attr in _REQUIRED_ATTRS)


def compute_total_acceleration(obj) -> Vec2:
    """Sum every attached force's contribution. Used by the integrator --
    works on anything attach() has touched, no bound method required."""
    total = Vec2.zero()
    for force in obj._forces:
        total += force.compute_acceleration(obj)
    return total


class PhysicsObject:
    """
    Optional mixin/base class -- an alternative to calling attach()
    yourself. Inherit from this (alongside your own base classes, if any)
    and call super().__init__(...) to get physics auto-attached through
    normal Python inheritance:

        class Spaceship(pydamics.PhysicsObject):
            def __init__(self, name, **physics_kwargs):
                super().__init__(**physics_kwargs)
                self.name = name

        ship = Spaceship("Falcon", mass=1500.0, position=(0, 20))
        ship.physics2d.gravity(force=9.8)

    Functionally identical to `pydamics.attach(self, ...)` -- use
    whichever fits how you structure your classes.
    """

    def __init__(self, mass: float = 1.0, position=(0.0, 0.0), velocity=(0.0, 0.0)):
        attach(self, mass=mass, position=position, velocity=velocity)


def physics_class(mass: float = 1.0, position=(0.0, 0.0), velocity=(0.0, 0.0)):
    """
    Class decorator -- a third way to make your own class physics-capable,
    for when you don't want to touch inheritance or call attach() by hand:

        @pydamics.physics_class(mass=1500.0, position=(0, 20))
        class Spaceship:
            def __init__(self, name):
                self.name = name

        ship = Spaceship("Falcon")   # already physics-capable
        ship.physics2d.gravity(force=9.8)

    Every instance gets attach()-ed with these defaults before your own
    __init__ runs, so your __init__ can freely set its own attributes
    afterward without worrying about physics setup.
    """

    def decorator(cls):
        original_init = cls.__init__

        def new_init(self, *args, **kwargs):
            attach(self, mass=mass, position=position, velocity=velocity)
            original_init(self, *args, **kwargs)

        cls.__init__ = new_init
        return cls

    return decorator
