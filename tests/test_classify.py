import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pydamics
from pydamics import World, GasZone


class Ball:
    pass


class Platform:
    pass


# --- basic classify() dispatch ---

def test_classify_rigid_matches_attach():
    ball = pydamics.classify(Ball(), kind="rigid", mass=9.0, position=(0, 10)).obj
    assert pydamics.has_physics(ball)
    assert ball.mass == 9.0
    assert ball.position.y == 10


def test_classify_solid_matches_solidify():
    platform = pydamics.classify(Platform(), kind="solid", position=(0, 0)).obj
    assert not pydamics.has_physics(platform)  # solid-only doesn't get physics2d
    assert hasattr(platform, "seo")
    platform.seo.solid(width=4, height=1)
    assert pydamics.is_solid(platform)


def test_classify_multiple_kinds_at_once():
    platform = pydamics.classify(Platform(), kind=["rigid", "solid"], mass=50.0, position=(0, 10)).obj
    assert pydamics.has_physics(platform)
    assert hasattr(platform, "seo")
    platform.physics2d.gravity(force=2.0)
    platform.seo.solid(width=8, height=1)
    assert pydamics.is_solid(platform)


def test_classify_fluid_matches_fluidify():
    droplet = pydamics.classify(Ball(), kind="fluid", mass=1.0, position=(0, 5)).obj
    assert pydamics.is_fluid(droplet)


def test_classify_unknown_kind_raises():
    with pytest.raises(ValueError):
        pydamics.classify(Ball(), kind="liquid_metal")


def test_classify_empty_kind_list_raises():
    with pytest.raises(ValueError):
        pydamics.classify(Ball(), kind=[])


# --- with-block usage ---

def test_classify_as_context_manager_yields_the_object():
    with pydamics.classify(Ball(), kind="rigid", mass=1.0, position=(0, 10)) as cfg:
        cfg.physics2d.mass(9)
        cfg.physics2d.velocity(1, 2)

    assert cfg.mass == 9
    assert cfg.velocity.x == 1 and cfg.velocity.y == 2


def test_classify_plain_call_already_fully_classified():
    # not using `with` at all -- classification already happened
    result = pydamics.classify(Ball(), kind="rigid", mass=3.0, position=(0, 0))
    assert pydamics.has_physics(result.obj)
    assert result.obj.mass == 3.0


# --- kind_of() ---

def test_kind_of_reports_classification():
    ball = pydamics.classify(Ball(), kind="rigid", mass=1.0, position=(0, 0)).obj
    assert pydamics.kind_of(ball) == frozenset({"rigid"})


def test_kind_of_unclassified_object_is_empty():
    assert pydamics.kind_of(Ball()) == frozenset()


def test_kind_of_gas_also_reports_rigid():
    zone = GasZone(min_point=(-5, -5), max_point=(5, 5), force=2.0)
    puff = pydamics.classify(Ball(), kind="gas", mass=1.0, position=(0, 0)).obj
    assert pydamics.kind_of(puff) == frozenset({"gas", "rigid"})
    assert pydamics.has_physics(puff)  # gas implies physics2d exists
    puff.physics2d.gas(zone)


def test_kind_of_accumulates_across_repeated_classify_calls():
    obj = pydamics.classify(Platform(), kind="rigid", mass=1.0, position=(0, 0)).obj
    assert pydamics.kind_of(obj) == frozenset({"rigid"})
    pydamics.classify(obj, kind="solid", position=(0, 0))
    assert pydamics.kind_of(obj) == frozenset({"rigid", "solid"})


# --- "wrong property for this kind" validation ---

def test_classify_mass_on_solid_only_raises():
    with pytest.raises(TypeError):
        pydamics.classify(Platform(), kind="solid", mass=5.0)


def test_classify_velocity_on_solid_only_raises():
    with pytest.raises(TypeError):
        pydamics.classify(Platform(), kind="solid", velocity=(1, 0))


def test_classify_mass_on_rigid_plus_solid_is_fine():
    # mass applies because "rigid" is one of the requested kinds
    platform = pydamics.classify(Platform(), kind=["rigid", "solid"], mass=10.0, position=(0, 0)).obj
    assert platform.mass == 10.0
