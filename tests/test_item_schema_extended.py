# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest

from lucent.canvas_items import LayerItem
from lucent.item_schema import (
    ItemSchemaError,
    _should_serialize_transform,
    validate_path,
    validate_rectangle,
)


def test_validate_rectangle_clamps_corner_radii_and_ignores_zero():
    data = {
        "geometry": {
            "x": 0,
            "y": 0,
            "width": 10,
            "height": 20,
            "cornerRadiusTL": 10,
            "cornerRadiusTR": 100,
            "cornerRadiusBR": 25,
            "cornerRadiusBL": 30,
        },
        "appearances": [],
    }
    result = validate_rectangle(data)
    assert result["geometry"]["cornerRadiusTL"] == 10.0
    assert result["geometry"]["cornerRadiusTR"] == 50.0
    assert result["geometry"]["cornerRadiusBR"] == 25.0
    assert result["geometry"]["cornerRadiusBL"] == 30.0


def test_validate_rectangle_ignores_zero_corner_radius():
    data = {
        "geometry": {"x": 0, "y": 0, "width": 10, "height": 10, "cornerRadiusTL": 0},
        "appearances": [],
    }
    result = validate_rectangle(data)
    assert "cornerRadiusTL" not in result["geometry"]


def test_validate_rectangle_rejects_invalid_numbers():
    data = {
        "geometry": {"x": 0, "y": 0, "width": "bad", "height": 10},
        "appearances": [],
    }
    with pytest.raises(ItemSchemaError, match="Invalid rectangle numeric field"):
        validate_rectangle(data)


def test_validate_rectangle_fixes_invalid_stroke_values():
    data = {
        "geometry": {"x": 0, "y": 0, "width": 10, "height": 10},
        "appearances": [
            {"type": "stroke", "cap": "invalid", "align": "oops", "order": "nope"},
        ],
    }
    result = validate_rectangle(data)
    stroke = result["appearances"][0]
    assert stroke["cap"] == "butt"
    assert stroke["align"] == "center"
    assert stroke["order"] == "top"


def test_validate_path_ignores_invalid_handles():
    data = {
        "geometry": {
            "points": [
                {"x": 0, "y": 0, "handleIn": "bad"},
                {"x": 10, "y": 0},
            ],
            "closed": False,
        },
        "appearances": [],
    }
    result = validate_path(data)
    assert "handleIn" not in result["geometry"]["points"][0]


def test_validate_path_rejects_points_not_list():
    data = {"geometry": {"points": "bad"}, "appearances": []}
    with pytest.raises(ItemSchemaError, match="Path points must be a list"):
        validate_path(data)


def test_should_serialize_transform_false_without_transform():
    layer = LayerItem(name="Layer")
    assert _should_serialize_transform(layer) is False
