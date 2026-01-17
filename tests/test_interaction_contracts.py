# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Interaction contract tests for core transformations."""

from test_helpers import make_path, make_rectangle


def test_translate_items_updates_transform_only(canvas_model):
    canvas_model.addItem(make_rectangle(x=10, y=20, width=50, height=40))

    canvas_model.translateItems([0], 12, -5)

    data = canvas_model.getItemData(0)
    assert data["geometry"]["x"] == 10
    assert data["geometry"]["y"] == 20
    transform = data.get("transform", {})
    assert transform.get("translateX", 0) == 12
    assert transform.get("translateY", 0) == -5


def test_rotate_item_preserves_geometry(canvas_model):
    canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

    canvas_model.rotateItem(0, 45)

    data = canvas_model.getItemData(0)
    assert data["geometry"]["width"] == 100
    assert data["geometry"]["height"] == 50
    transform = data.get("transform", {})
    assert transform.get("rotate", 0) == 45


def test_scale_item_preserves_geometry_and_pivot(canvas_model):
    canvas_model.addItem(make_rectangle(x=0, y=0, width=80, height=40))

    canvas_model.scaleItem(0, 2.0, 1.5, 0.5, 0.5)

    after = canvas_model.getItemData(0)
    assert after["geometry"]["width"] == 80
    assert after["geometry"]["height"] == 40
    after_transform = after.get("transform", {})
    assert after_transform.get("scaleX", 1) == 2.0
    assert after_transform.get("scaleY", 1) == 1.5
    assert after_transform.get("pivotX") == 40.0
    assert after_transform.get("pivotY") == 20.0


def test_update_geometry_locked_does_not_change_transform(canvas_model):
    points = [{"x": 0, "y": 0}, {"x": 20, "y": 0}, {"x": 20, "y": 10}]
    canvas_model.addItem(make_path(points=points, closed=False))
    before = canvas_model.getItemData(0)
    before_transform = dict(before.get("transform", {}))

    canvas_model.updateGeometryLocked(
        0,
        {
            "points": [{"x": 5, "y": 5}, {"x": 25, "y": 5}, {"x": 25, "y": 15}],
            "closed": False,
        },
    )

    after = canvas_model.getItemData(0)
    assert after["geometry"]["points"][0] == {"x": 5, "y": 5}
    assert after["geometry"]["points"][1] == {"x": 25, "y": 5}
    assert after["geometry"]["points"][2] == {"x": 25, "y": 15}
    assert after.get("transform", {}) == before_transform
