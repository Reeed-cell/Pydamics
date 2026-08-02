"""
2D vector math used throughout the engine.
"""
from __future__ import annotations
import math


class Vec2:
    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = float(x)
        self.y = float(y)

    # --- operators ---
    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vec2":
        if isinstance(scalar, Vec2):
            raise TypeError(
                "Vec2 * Vec2 isn't supported (there's no single sensible "
                "meaning -- did you want .dot(other) instead?). Multiply "
                "by a scalar (int/float)."
            )
        return Vec2(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def __truediv__(self, scalar: float) -> "Vec2":
        return Vec2(self.x / scalar, self.y / scalar)

    def __neg__(self) -> "Vec2":
        return Vec2(-self.x, -self.y)

    # Deliberately NOT defining __iadd__/__isub__/etc: without them,
    # `position += x` falls back to `position = position.__add__(x)`,
    # which creates a new Vec2 and rebinds the attribute rather than
    # mutating the old object in place. That matters because attach()/
    # solidify()/fluidify() copy incoming Vec2s defensively, but if any
    # of them were ever aliased (two objects sharing one Vec2 instance),
    # in-place += would silently entangle their motion forever. Keeping
    # Vec2 value-semantic (like a tuple) everywhere avoids that whole
    # class of bug, at the cost of one extra allocation per += -- cheap
    # relative to everything else a physics step already allocates.

    def __repr__(self) -> str:
        return f"Vec2({self.x:.4f}, {self.y:.4f})"

    def __iter__(self):
        yield self.x
        yield self.y

    # --- vector ops ---
    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)

    def length_sq(self) -> float:
        return self.x * self.x + self.y * self.y

    def normalized(self) -> "Vec2":
        l = self.length()
        if l == 0:
            return Vec2(0.0, 0.0)
        return Vec2(self.x / l, self.y / l)

    def dot(self, other: "Vec2") -> float:
        return self.x * other.x + self.y * other.y

    def cross(self, other: "Vec2") -> float:
        """2D cross product -- returns a scalar (the z-component of the
        3D cross product with both vectors' z=0). Used for torque =
        lever_arm x force."""
        return self.x * other.y - self.y * other.x

    def copy(self) -> "Vec2":
        return Vec2(self.x, self.y)

    @staticmethod
    def zero() -> "Vec2":
        return Vec2(0.0, 0.0)
