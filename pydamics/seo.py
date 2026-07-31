"""
SEO -- Solid Environment Object.

`.seo` is a namespace you attach to ANY object (like `.physics2d`) to make
it solid -- something physics objects collide with and rest/bounce against.

It does NOT require the object to be physics-capable (attach()-ed):

    class Platform:
        pass

    platform = Platform()
    pydamics.solidify(platform, position=(0, 0))
    platform.seo.solid(width=8, height=1)

That's a purely static, immovable solid -- fine for ground/walls/platforms
that never move.

If the object IS also physics-capable (you called pydamics.attach() on it
first, so it has velocity/mass/forces), it becomes a "physicsified" solid:
movable, affected by forces, AND still solid -- e.g. a platform that falls
under gravity but still carries/blocks whatever's resting on it.

    platform = pydamics.attach(Platform(), mass=50.0, position=(0, 10))
    platform.physics2d.gravity(force=2.0)   # falls slowly
    platform.seo.solid(width=8, height=1)   # still solid while it falls
"""
from __future__ import annotations
from .vector import Vec2


class SEOShapeBox:
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height


class SEOShapeCircle:
    def __init__(self, radius: float):
        self.radius = radius


class SEO:
    """Attached to `obj.seo` by solidify(). Call `.solid(...)` to actually
    give it a shape -- until then it's registered but not yet collidable."""

    def __init__(self, obj):
        self._obj = obj
        self.shape = None
        self.restitution = 0.3

    def solid(self, width: float = None, height: float = None,
              radius: float = None, restitution: float = 0.3) -> "SEO":
        """Give this object a solid shape. Pass width+height for a
        rectangular platform/wall, or radius for a circular solid."""
        if radius is not None:
            self.shape = SEOShapeCircle(radius)
        else:
            self.shape = SEOShapeBox(width if width is not None else 1.0,
                                      height if height is not None else 1.0)
        self.restitution = restitution
        return self


def solidify(obj, position=(0.0, 0.0)):
    """Make `obj` a Solid Environment Object. Adds `.seo` (call
    `.seo.solid(...)` next to give it a shape) and `.position` if it
    doesn't already have one (physics-capable objects already do).

    Returns obj, so this can be chained.
    """
    if not hasattr(obj, "position"):
        obj.position = position.copy() if isinstance(position, Vec2) else Vec2(*position)
    obj.seo = SEO(obj)
    return obj


def is_solid(obj) -> bool:
    """Whether `obj` has been solidify()-ed AND given a shape via `.seo.solid(...)`."""
    return hasattr(obj, "seo") and obj.seo.shape is not None


class SolidObject:
    """Optional mixin/base class, mirroring PhysicsObject -- inherit from
    this to get solidify() auto-applied through normal Python inheritance
    instead of calling solidify() yourself. You still need to call
    `.seo.solid(...)` to give it a shape.

        class Platform(pydamics.SolidObject):
            def __init__(self, **seo_kwargs):
                super().__init__(**seo_kwargs)

        platform = Platform(position=(0, 0))
        platform.seo.solid(width=8, height=1)
    """

    def __init__(self, position=(0.0, 0.0)):
        solidify(self, position=position)


def solid_class(position=(0.0, 0.0)):
    """Class decorator, mirroring physics_class -- every instance gets
    solidify()-ed with these defaults before your own __init__ runs.
    You still need to call `.seo.solid(...)` on the instance afterward.

        @pydamics.solid_class(position=(0, 0))
        class Platform:
            pass
    """

    def decorator(cls):
        original_init = cls.__init__

        def new_init(self, *args, **kwargs):
            solidify(self, position=position)
            original_init(self, *args, **kwargs)

        cls.__init__ = new_init
        return cls

    return decorator
