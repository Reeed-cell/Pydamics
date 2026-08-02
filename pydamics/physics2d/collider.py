"""
CircleCollider -- attach via `obj.physics2d.collider(...)`.

This is just a data holder (radius, restitution, static flag, layer,
collides_with). The actual pairwise detection/resolution logic lives in
`pydamics.collision`, kept separate because collision needs to compare
PAIRS of entities across the whole World, unlike Force (which only
needs its own entity).
"""
from __future__ import annotations


class CircleCollider:
    """
    radius:        collision radius
    restitution:   bounciness, 0 = perfectly inelastic (no bounce), 1 = perfectly elastic
    static:        if True, this object never moves in response to a collision
                   (use for walls/floors/anchors), but still pushes movable
                   things away from it
    layer:         what this collider IS (a string label, e.g. "player_bullet")
    collides_with: what layers this collider interacts with -- a list/set
                   of layer names, or None (default) to collide with
                   everything regardless of layer. Filtering is
                   symmetric-AND: a pair only collides if EACH side's
                   collides_with (when set) includes the other's layer.
    """

    def __init__(self, radius: float = 0.5, restitution: float = 0.6, static: bool = False,
                 layer: str = "default", collides_with=None):
        self.radius = radius
        self.restitution = restitution
        self.static = static
        self.layer = layer
        self.collides_with = set(collides_with) if collides_with is not None else None
