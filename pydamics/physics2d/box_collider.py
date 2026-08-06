"""
BoxCollider -- attach via `obj.physics2d.collider(shape="box", width=..., height=...)`.

Mirrors CircleCollider's fields (restitution, static, layer,
collides_with) but for a rectangular shape. Respects the entity's
`.angle` if it has one (from v0.5.0's orientation system) -- an
attach()-ed entity always has `.angle` (defaults to 0.0), so box
colliders are oriented by default, not just axis-aligned.
"""
from __future__ import annotations


class BoxCollider:
    """
    width/height:  box dimensions (centered on the entity's position)
    restitution:   bounciness, 0 = perfectly inelastic, 1 = perfectly elastic
    static:        if True, this object never moves in response to a collision
    layer:         what this collider IS (a string label)
    collides_with: what layers this collider interacts with -- None (default)
                   collides with everything, same symmetric-AND filtering
                   as CircleCollider
    """

    def __init__(self, width: float = 1.0, height: float = 1.0, restitution: float = 0.6,
                 static: bool = False, layer: str = "default", collides_with=None):
        self.width = width
        self.height = height
        self.restitution = restitution
        self.static = static
        self.layer = layer
        self.collides_with = set(collides_with) if collides_with is not None else None
