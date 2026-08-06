"""
SAT (separating axis theorem) geometry helpers for oriented (rotated)
box collision. Pure geometry -- no physics/impulse logic here, that
stays in collision.py.

Correct 2D OBB-OBB SAT only needs to test 4 candidate axes (the two
unique perpendicular axes of each box) -- unlike 3D SAT, no cross
products of edges are needed.
"""
from __future__ import annotations
import math
from .vector import Vec2


def box_axes(angle: float):
    """Unit vectors along the box's own (possibly rotated) width/height axes."""
    c, s = math.cos(angle), math.sin(angle)
    return Vec2(c, s), Vec2(-s, c)


def box_corners(position: Vec2, angle: float, half_width: float, half_height: float):
    ax, ay = box_axes(angle)
    ex = ax * half_width
    ey = ay * half_height
    return [
        position + ex + ey,
        position + ex - ey,
        position - ex + ey,
        position - ex - ey,
    ]


def _project(corners, axis: Vec2):
    dots = [c.dot(axis) for c in corners]
    return min(dots), max(dots)


def sat_box_vs_box(pos_a: Vec2, angle_a: float, hw_a: float, hh_a: float,
                    pos_b: Vec2, angle_b: float, hw_b: float, hh_b: float):
    """Returns (normal, overlap) with normal pointing from A to B if the
    boxes overlap, else None."""
    corners_a = box_corners(pos_a, angle_a, hw_a, hh_a)
    corners_b = box_corners(pos_b, angle_b, hw_b, hh_b)
    ax_a1, ax_a2 = box_axes(angle_a)
    ax_b1, ax_b2 = box_axes(angle_b)

    min_overlap = None
    min_axis = None
    for axis in (ax_a1, ax_a2, ax_b1, ax_b2):
        min_a, max_a = _project(corners_a, axis)
        min_b, max_b = _project(corners_b, axis)
        overlap = min(max_a, max_b) - max(min_a, min_b)
        if overlap <= 0:
            return None  # a separating axis exists -- no collision
        if min_overlap is None or overlap < min_overlap:
            min_overlap = overlap
            min_axis = axis

    center_delta = pos_b - pos_a
    if center_delta.dot(min_axis) < 0:
        min_axis = min_axis * -1.0

    return min_axis, min_overlap


def closest_point_on_box(point: Vec2, box_position: Vec2, angle: float,
                          half_width: float, half_height: float):
    """Closest point on an oriented box's boundary/interior to `point`,
    in world coordinates. Returns (closest_point, is_inside, local_x, local_y)."""
    ax, ay = box_axes(angle)
    local = point - box_position
    local_x = local.dot(ax)
    local_y = local.dot(ay)

    inside = abs(local_x) <= half_width and abs(local_y) <= half_height

    clamped_x = max(-half_width, min(local_x, half_width))
    clamped_y = max(-half_height, min(local_y, half_height))

    closest = box_position + ax * clamped_x + ay * clamped_y
    return closest, inside, local_x, local_y
