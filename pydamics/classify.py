"""
classify() -- one unified entry point over attach()/solidify()/fluidify(),
plus kind_of() to ask what an object has been classified as.

    pydamics.classify(ball, kind="rigid", mass=9, position=(0, 10))

    with pydamics.classify(ball, kind=["rigid", "solid"]) as cfg:
        cfg.physics2d.mass(9)
        cfg.seo.solid(width=2, height=2)

`classify()` doesn't replace attach()/solidify()/fluidify() -- it's a
thin dispatcher over them, so those stay exactly as they were. The
`with` form is optional sugar: `__enter__` just returns the object
itself (already fully classified by the time you get it), so the
indentation is real Python grouping, not magic.
"""
from __future__ import annotations
from .physics_core import attach
from .seo import solidify
from .sph import fluidify

_VALID_KINDS = frozenset({"rigid", "solid", "fluid", "gas"})

# which kinds actually consume mass= / velocity= -- used to catch
# "you set a property that doesn't apply to this kind" mistakes early
_MASS_KINDS = frozenset({"rigid", "gas", "fluid"})
_VELOCITY_KINDS = frozenset({"rigid", "gas", "fluid"})

_UNSET = object()


def classify(obj, kind, mass=_UNSET, position=(0.0, 0.0), velocity=_UNSET):
    """
    Classify `obj` as one or more kinds -- "rigid" (attach()), "solid"
    (solidify()), "fluid" (fluidify()), and/or "gas" (rigid + gives
    access to `.physics2d.gas(zone)`). `kind` can be a single string or
    a list of them for objects that are multiple kinds at once (e.g. a
    physicsified solid: kind=["rigid", "solid"]).

    Raises ValueError for an unknown kind, or TypeError if you pass
    mass=/velocity= for a kind that doesn't use them (e.g. mass= with
    kind="solid" alone) -- these are "incorrect properties for this
    kind" errors, not silently ignored.

    Returns an object that works two ways:
        pydamics.classify(ball, kind="rigid")           # plain call
        with pydamics.classify(ball, kind="rigid") as cfg:  # with-block
            cfg.physics2d.mass(9)
    """
    kinds = frozenset([kind]) if isinstance(kind, str) else frozenset(kind)
    if not kinds:
        raise ValueError("kind cannot be empty -- pass a kind or a list of kinds.")
    unknown = kinds - _VALID_KINDS
    if unknown:
        raise ValueError(
            f"Unknown kind(s) {sorted(unknown)} -- must be one or more of "
            f"{sorted(_VALID_KINDS)}."
        )

    if mass is not _UNSET and not (kinds & _MASS_KINDS):
        raise TypeError(
            f"mass= doesn't apply to kind {sorted(kinds)} -- only "
            f"{sorted(_MASS_KINDS)} use mass. (Incorrect property for this kind.)"
        )
    if velocity is not _UNSET and not (kinds & _VELOCITY_KINDS):
        raise TypeError(
            f"velocity= doesn't apply to kind {sorted(kinds)} -- only "
            f"{sorted(_VELOCITY_KINDS)} use velocity. (Incorrect property for this kind.)"
        )

    mass_val = 1.0 if mass is _UNSET else mass
    velocity_val = (0.0, 0.0) if velocity is _UNSET else velocity

    # "gas" needs .physics2d (GasPush is a Force, same mechanism as
    # buoyancy) -- so it always brings "rigid" along with it
    effective_kinds = set(kinds)
    if "gas" in effective_kinds:
        effective_kinds.add("rigid")

    if "rigid" in effective_kinds:
        attach(obj, mass=mass_val, position=position, velocity=velocity_val)
    if "solid" in effective_kinds:
        solidify(obj, position=position)
    if "fluid" in effective_kinds:
        fluidify(obj, mass=mass_val, position=position, velocity=velocity_val)

    # accumulate across repeated classify() calls rather than overwrite --
    # classifying an already-rigid object as also "solid" shouldn't erase
    # the fact that it's rigid
    obj._pydamics_kind = kind_of(obj) | frozenset(effective_kinds)

    return _ClassifyContext(obj)


def kind_of(obj) -> frozenset:
    """What has `obj` been classified as? Returns a frozenset, e.g.
    frozenset({"rigid"}), frozenset({"rigid", "solid"}), or an empty
    frozenset if never classified via classify() (attach()/solidify()/
    fluidify() called directly don't set this -- use has_physics()/
    is_solid()/is_fluid() to check those regardless of how they were set)."""
    return getattr(obj, "_pydamics_kind", frozenset())


class _ClassifyContext:
    """Returned by classify(). Usable as a plain value (classification
    already happened by the time you get this) or as a context manager
    for the indented with-block configuration style."""

    def __init__(self, obj):
        self.obj = obj

    def __enter__(self):
        return self.obj

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
