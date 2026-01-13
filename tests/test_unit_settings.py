# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
from PySide6.QtTest import QSignalSpy

from lucent.unit_settings import UnitSettings
from lucent.units import DISPLAY_PRECISION, unit_to_canvas


def test_defaults_and_meta_roundtrip():
    us = UnitSettings()
    assert us.displayUnit == "px"
    assert us.previewDPI == 96.0
    assert us.gridSpacingValue == 10.0
    assert us.gridSpacingUnit == "mm"

    meta = us.to_meta()
    assert meta["displayUnit"] == "px"
    assert meta["previewDPI"] == 96.0
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


def test_display_unit_no_change_is_noop(qtbot):
    us = UnitSettings(display_unit="mm")
    display_spy = QSignalSpy(us.displayUnitChanged)
    canvas_spy = QSignalSpy(us.gridSpacingCanvasChanged)

    us.displayUnit = "mm"

    assert us.displayUnit == "mm"
    assert display_spy.count() == 0
    assert canvas_spy.count() == 0


def test_preview_dpi_tiny_delta_skips_update(qtbot):
    us = UnitSettings(preview_dpi=200.0)
    dpi_spy = QSignalSpy(us.previewDPIChanged)
    canvas_spy = QSignalSpy(us.gridSpacingCanvasChanged)

    us.previewDPI = 200.0 + 5e-10

    assert us.previewDPI == 200.0
    assert dpi_spy.count() == 0
    assert canvas_spy.count() == 0


def test_grid_spacing_value_guards(qtbot):
    us = UnitSettings(grid_spacing_value=8.0)
    value_spy = QSignalSpy(us.gridSpacingValueChanged)
    canvas_spy = QSignalSpy(us.gridSpacingCanvasChanged)

    us.gridSpacingValue = 0  # non-positive rejected
    us.gridSpacingValue = 8.0 + 1e-10  # delta below epsilon rejected

    assert us.gridSpacingValue == 8.0
    assert value_spy.count() == 0
    assert canvas_spy.count() == 0


def test_grid_spacing_unit_no_change_is_noop(qtbot):
    us = UnitSettings(grid_spacing_unit="in")
    unit_spy = QSignalSpy(us.gridSpacingUnitChanged)
    canvas_spy = QSignalSpy(us.gridSpacingCanvasChanged)

    us.gridSpacingUnit = "in"

    assert us.gridSpacingUnit == "in"
    assert unit_spy.count() == 0
    assert canvas_spy.count() == 0


@pytest.mark.parametrize(
    "unit,dpi,expected_minor,expected_major_mult,expected_label,expected_target,expected_allowed",
    [
        (
            "in",
            96.0,
            unit_to_canvas(0.5, "in", 96.0),
            4,
            "fraction",
            100.0,
            [2.0, 4.0, 8.0],
        ),
        (
            "mm",
            150.0,
            unit_to_canvas(20.0, "mm", 150.0),
            5,
            "decimal",
            120.0,
            [100.0, 200.0, 500.0],
        ),
        (
            "px",
            110.0,
            10.0,
            10,
            "decimal",
            100.0,
            [100.0, 200.0, 400.0],
        ),
    ],
)
def test_grid_config_per_unit(
    unit,
    dpi,
    expected_minor,
    expected_major_mult,
    expected_label,
    expected_target,
    expected_allowed,
):
    us = UnitSettings(display_unit=unit, preview_dpi=dpi)

    config = us.gridConfig()

    assert config["minorCanvas"] == pytest.approx(expected_minor)
    assert config["majorMultiplier"] == expected_major_mult
    assert config["labelStyle"] == expected_label
    assert config["targetMajorPx"] == expected_target
    assert config["allowedMajorUnits"] == expected_allowed
