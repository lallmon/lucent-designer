# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for unit conversion helpers."""

import math

import pytest

from lucent.units import (
    canvas_to_unit,
    unit_to_canvas,
    convert,
    format_value,
    DISPLAY_PRECISION,
)


@pytest.mark.parametrize("dpi", [96, 300])
@pytest.mark.parametrize(
    "unit,expected_per_inch",
    [
        ("in", 1.0),
        ("mm", 25.4),
        ("pt", 72.0),
        ("px", None),  # handled separately
    ],
)
def test_convert_inch_basis(unit, expected_per_inch, dpi):
    if unit == "px":
        assert math.isclose(convert(dpi, "px", "in", dpi), 1.0)
        assert math.isclose(convert(1, "in", "px", dpi), dpi)
        return
    assert math.isclose(convert(1, "in", unit, dpi), expected_per_inch)
    assert math.isclose(convert(expected_per_inch, unit, "in", dpi), 1.0)


@pytest.mark.parametrize("dpi", [96, 300])
@pytest.mark.parametrize("unit", ["px", "mm", "in", "pt"])
def test_round_trip_canvas(unit, dpi):
    original = 123.456
    converted = canvas_to_unit(original, unit, dpi)
    back = unit_to_canvas(converted, unit, dpi)
    assert math.isclose(back, original, rel_tol=1e-9, abs_tol=1e-9)


def test_invalid_dpi_raises():
    with pytest.raises(ValueError):
        canvas_to_unit(10, "in", 0)
    with pytest.raises(ValueError):
        unit_to_canvas(10, "in", -1)


@pytest.mark.parametrize(
    "unit,places,raw,expected",
    [
        ("px", 1, 12.345, "12.3"),
        ("mm", 2, 12.345, "12.35"),
        ("in", 3, 1.23456, "1.235"),
        ("pt", 2, 12.345, "12.35"),
    ],
)
def test_format_value_precision(unit, places, raw, expected):
    assert DISPLAY_PRECISION[unit] == places
    assert format_value(raw, unit) == expected
