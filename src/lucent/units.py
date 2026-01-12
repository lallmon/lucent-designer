# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Unit conversion helpers for canvas measurements."""

from __future__ import annotations

from typing import Literal

Unit = Literal["px", "mm", "in", "pt"]

_MM_PER_INCH = 25.4
_PT_PER_INCH = 72.0


def _to_inches(value: float, unit: Unit, dpi: float) -> float:
    if dpi <= 0:
        raise ValueError("dpi must be > 0")
    if unit == "in":
        return value
    if unit == "mm":
        return value / _MM_PER_INCH
    if unit == "pt":
        return value / _PT_PER_INCH
    if unit == "px":
        return value / dpi
    raise ValueError(f"Unknown unit '{unit}'")


def _from_inches(value_in_inches: float, unit: Unit, dpi: float) -> float:
    if dpi <= 0:
        raise ValueError("dpi must be > 0")
    if unit == "in":
        return value_in_inches
    if unit == "mm":
        return value_in_inches * _MM_PER_INCH
    if unit == "pt":
        return value_in_inches * _PT_PER_INCH
    if unit == "px":
        return value_in_inches * dpi
    raise ValueError(f"Unknown unit '{unit}'")


def convert(value: float, from_unit: Unit, to_unit: Unit, dpi: float) -> float:
    """Convert a value between units using the provided DPI."""
    inches = _to_inches(value, from_unit, dpi)
    return _from_inches(inches, to_unit, dpi)


def canvas_to_unit(value: float, unit: Unit, dpi: float) -> float:
    """Convert a canvas value (logical px) to the requested unit."""
    return convert(value, "px", unit, dpi)


def unit_to_canvas(value: float, unit: Unit, dpi: float) -> float:
    """Convert a unit value to canvas units (logical px)."""
    return convert(value, unit, "px", dpi)


# Preferred display precision per unit
DISPLAY_PRECISION = {
    "px": 1,
    "mm": 2,
    "in": 3,
    "pt": 2,
}


def format_value(value: float, unit: Unit) -> str:
    """Format a value for display based on unit-specific precision."""
    places = DISPLAY_PRECISION.get(unit, 2)
    return f"{value:.{places}f}"
