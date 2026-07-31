"""
CircleCollider -- attach via `obj.physics2d.collider(...)`.

This is just a data holder (radius, restitution, static flag). The actual
pairwise detection/resolution logic lives in `pydamics.collision`, kept
separate because collision needs to compare PAIRS of entities across the
whole World, unlike Force (which only needs its own entity).
"""
from __future__ import annotations


class CircleCollider:
    """
    radius:      collision radius
    restitution: bounciness, 0 = perfectly inelastic (no bounce), 1 = perfectly elastic
    static:      if True, this object never moves in response to a collision
                 (use for walls/floors/anchors), but still pushes movable
                 things away from it
    """

    def __init__(self, radius: float = 0.5, restitution: float = 0.6, static: bool = False):
        self.radius = radius
        self.restitution = restitution
        self.static = static
