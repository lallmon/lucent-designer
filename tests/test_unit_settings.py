# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest

from lucent.unit_settings import UnitSettings
from lucent.units import DISPLAY_PRECISION


def test_defaults_and_meta_roundtrip():
    us = UnitSettings()
    assert us.displayUnit == "px"
    assert us.previewDPI == 150.0
    assert us.gridSpacingValue == 10.0
    assert us.gridSpacingUnit == "mm"

    meta = us.to_meta()
    assert meta["displayUnit"] == "px"
    assert meta["previewDPI"] == 150.0
    assert meta["gridSpacingValue"] == 10.0
    assert meta["gridSpacingUnit"] == "mm"

    # Change values and load back from meta
    us.load_from_meta(
        {
            "displayUnit": "in",
            "previewDPI": 96,
            "gridSpacingValue": 5,
            "gridSpacingUnit": "pt",
        }
    )
    assert us.displayUnit == "in"
    assert us.previewDPI == 96
    assert us.gridSpacingValue == 5
    assert us.gridSpacingUnit == "pt"
    # 5 pt = 5/72 inches; at 96 dpi -> 6.666...
    assert us.gridSpacingCanvas == pytest.approx((5 / 72) * 96, rel=1e-6)


@pytest.mark.parametrize(
    "unit,value,dpi,expected",
    [
        ("px", 100, 150, 100),
        ("mm", 25.4, 254, 254),  # 25.4mm = 1in -> 254 px at 254 dpi
        ("in", 2, 96, 192),
        ("pt", 72, 96, 96),  # 72pt = 1in
    ],
)
def test_canvas_display_conversion(unit, value, dpi, expected):
    us = UnitSettings(display_unit=unit, preview_dpi=dpi)
    canvas_val = us.displayToCanvas(value)
    assert canvas_val == pytest.approx(expected, rel=1e-6)
    display_val = us.canvasToDisplay(expected)
    assert display_val == pytest.approx(value, rel=1e-6)


def test_preview_dpi_rejects_non_positive():
    us = UnitSettings()
    original = us.previewDPI
    us.previewDPI = -10
    assert us.previewDPI == original
    us.previewDPI = 0
    assert us.previewDPI == original


def test_display_precision_mapping():
    assert DISPLAY_PRECISION["px"] == 1
    assert DISPLAY_PRECISION["mm"] == 2
    assert DISPLAY_PRECISION["in"] == 3
    assert DISPLAY_PRECISION["pt"] == 2
