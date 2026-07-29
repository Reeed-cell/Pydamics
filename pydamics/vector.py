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
        return Vec2(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def __truediv__(self, scalar: float) -> "Vec2":
        return Vec2(self.x / scalar, self.y / scalar)

    def __neg__(self) -> "Vec2":
        return Vec2(-self.x, -self.y)

    def __iadd__(self, other: "Vec2") -> "Vec2":
        self.x += other.x
        self.y += other.y
        return self

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

    def copy(self) -> "Vec2":
        return Vec2(self.x, self.y)

    @staticmethod
    def zero() -> "Vec2":
        return Vec2(0.0, 0.0)
