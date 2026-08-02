"""
TriggerZone -- overlap detection with on_enter/on_exit callbacks, but no
collision response (nothing bounces off a trigger). Register with
`world.add_trigger(zone)`.

The zone and its overlap detection are the engine's job; what "entering"
a zone MEANS (advance a checkpoint, open a door, deal damage) is game
code, passed in as a plain callback -- the engine doesn't know or care
what the callback does.

Entities are treated as points for trigger purposes (checked against
their `.position`, not any collider radius they might have) -- matches
the simple "is this point inside this zone" check most games actually
want for checkpoints/pickups/aggro radii.

If an entity is already inside a zone the first time it's checked (e.g.
it spawned there), on_enter fires on that first check -- there's no
special-cased "was already inside" state.
"""
from __future__ import annotations
from .vector import Vec2


class TriggerZone:
    def __init__(self, position, radius: float = None, width: float = None,
                 height: float = None, on_enter=None, on_exit=None):
        """
        Pass `radius` for a circular zone, or `width`+`height` for a
        rectangular one (centered on `position`).
        on_enter(entity) / on_exit(entity) -- called once per entity per
        transition, not every frame while inside/outside.
        """
        self.position = position.copy() if isinstance(position, Vec2) else Vec2(*position)
        self.radius = radius
        self.width = width
        self.height = height
        self.on_enter = on_enter
        self.on_exit = on_exit
        self._inside = set()  # ids of entities currently considered "inside"

    def _contains(self, point: Vec2) -> bool:
        if self.radius is not None:
            return (point - self.position).length() <= self.radius
        half_w = (self.width or 1.0) / 2.0
        half_h = (self.height or 1.0) / 2.0
        return (abs(point.x - self.position.x) <= half_w and
                abs(point.y - self.position.y) <= half_h)

    def check(self, entities) -> None:
        """Called once per World.step() -- checks every entity against
        this zone and fires on_enter/on_exit on state transitions."""
        currently_inside = set()
        for entity in entities:
            if self._contains(entity.position):
                currently_inside.add(id(entity))
                if id(entity) not in self._inside and self.on_enter:
                    self.on_enter(entity)

        just_left = self._inside - currently_inside
        if just_left and self.on_exit:
            # `entities` is the full world entity list (not just the ones
            # inside), so it still contains whatever just left the zone
            for entity in entities:
                if id(entity) in just_left:
                    self.on_exit(entity)

        self._inside = currently_inside
