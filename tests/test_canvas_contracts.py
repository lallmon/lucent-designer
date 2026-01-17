# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Contract tests for Canvas.qml refactoring.

These tests document the exact interface contract between Canvas.qml and
CanvasModel. They capture how QML currently calls the Python API and what
results it expects.

When refactoring Canvas.qml or moving logic to Python, these tests ensure
the interface behavior remains unchanged.
"""

import pytest
from test_helpers import (
    make_rectangle,
    make_ellipse,
    make_path,
    make_text,
    make_group,
)


@pytest.mark.contract
class TestRectanglePositionContract:
    """Contract: Canvas.qml updates rectangle position via geometry.x/y."""

    def test_rectangle_position_update_modifies_geometry(self, canvas_model):
        """Rectangle position is updated by modifying geometry.x and geometry.y."""
        canvas_model.addItem(
            make_rectangle(x=100, y=100, width=50, height=50, name="Test Rect")
        )

        # Simulate Canvas.qml's updateSelectedItemPosition
        data = canvas_model.getItemData(0)
        new_geom = dict(data["geometry"])
        new_geom["x"] = new_geom["x"] + 10
        new_geom["y"] = new_geom["y"] + 20

        canvas_model.updateItem(
            0,
            {
                "type": data["type"],
                "geometry": new_geom,
                "appearances": data["appearances"],
                "name": data["name"],
                "parentId": data.get("parentId"),
                "visible": data["visible"],
                "locked": data["locked"],
            },
        )

        result = canvas_model.getItemData(0)
        assert result["geometry"]["x"] == 110
        assert result["geometry"]["y"] == 120

    def test_rectangle_position_update_preserves_properties(self, canvas_model):
        """All non-position properties are preserved after position update."""
        canvas_model.addItem(
            make_rectangle(
                x=100,
                y=100,
                width=50,
                height=50,
                fill_color="#ff0000",
                fill_opacity=0.8,
                stroke_color="#00ff00",
                stroke_width=2.0,
                name="Preserved Rect",
            )
        )

        data = canvas_model.getItemData(0)
        original_appearances = data["appearances"]
        original_name = data["name"]
        original_width = data["geometry"]["width"]
        original_height = data["geometry"]["height"]

        # Move the rectangle
        new_geom = dict(data["geometry"])
        new_geom["x"] = 200
        new_geom["y"] = 200

        canvas_model.updateItem(
            0,
            {
                "type": data["type"],
                "geometry": new_geom,
                "appearances": data["appearances"],
                "name": data["name"],
                "parentId": data.get("parentId"),
                "visible": data["visible"],
                "locked": data["locked"],
            },
        )

        result = canvas_model.getItemData(0)

        # Position changed
        assert result["geometry"]["x"] == 200
        assert result["geometry"]["y"] == 200

        # Everything else preserved
        assert result["geometry"]["width"] == original_width
        assert result["geometry"]["height"] == original_height
        assert result["appearances"] == original_appearances
        assert result["name"] == original_name


@pytest.mark.contract
class TestEllipsePositionContract:
    """Contract: Canvas.qml updates ellipse position via centerX/centerY."""

    def test_ellipse_position_update_uses_center(self, canvas_model):
        """Ellipse position is updated by modifying centerX and centerY."""
        canvas_model.addItem(
            make_ellipse(center_x=100, center_y=100, radius_x=30, radius_y=20)
        )

        data = canvas_model.getItemData(0)
        new_geom = dict(data["geometry"])
        new_geom["centerX"] = new_geom["centerX"] + 10
        new_geom["centerY"] = new_geom["centerY"] + 20

        canvas_model.updateItem(
            0,
            {
                "type": data["type"],
                "geometry": new_geom,
                "appearances": data["appearances"],
                "name": data["name"],
                "parentId": data.get("parentId"),
                "visible": data["visible"],
                "locked": data["locked"],
            },
        )

        result = canvas_model.getItemData(0)
        assert result["geometry"]["centerX"] == 110
        assert result["geometry"]["centerY"] == 120

    def test_ellipse_position_update_preserves_radii(self, canvas_model):
        """Ellipse radii are preserved after position update."""
        canvas_model.addItem(
            make_ellipse(center_x=100, center_y=100, radius_x=30, radius_y=20)
        )

        data = canvas_model.getItemData(0)
        original_rx = data["geometry"]["radiusX"]
        original_ry = data["geometry"]["radiusY"]

        new_geom = dict(data["geometry"])
        new_geom["centerX"] = 200
        new_geom["centerY"] = 200

        canvas_model.updateItem(
            0,
            {
                "type": data["type"],
                "geometry": new_geom,
                "appearances": data["appearances"],
                "name": data["name"],
                "parentId": data.get("parentId"),
                "visible": data["visible"],
                "locked": data["locked"],
            },
        )

        result = canvas_model.getItemData(0)
        assert result["geometry"]["radiusX"] == original_rx
        assert result["geometry"]["radiusY"] == original_ry


@pytest.mark.contract
class TestPathPositionContract:
    """Contract: Canvas.qml updates path position by translating all points."""

    def test_path_position_update_translates_all_points(self, canvas_model):
        """Path position is updated by adding delta to all point coordinates."""
        original_points = [
            {"x": 0, "y": 0},
            {"x": 100, "y": 0},
            {"x": 100, "y": 100},
            {"x": 0, "y": 100},
        ]
        canvas_model.addItem(make_path(points=original_points, closed=True))

        data = canvas_model.getItemData(0)
        dx, dy = 10, 20

        # Canvas.qml translates all points
        new_points = [
            {"x": p["x"] + dx, "y": p["y"] + dy} for p in data["geometry"]["points"]
        ]

        canvas_model.updateItem(
            0,
            {
                "type": data["type"],
                "geometry": {
                    "points": new_points,
                    "closed": data["geometry"]["closed"],
                },
                "appearances": data["appearances"],
                "name": data["name"],
                "parentId": data.get("parentId"),
                "visible": data["visible"],
                "locked": data["locked"],
            },
        )

        result = canvas_model.getItemData(0)
        result_points = result["geometry"]["points"]

        assert result_points[0]["x"] == 10
        assert result_points[0]["y"] == 20
        assert result_points[1]["x"] == 110
        assert result_points[1]["y"] == 20
        assert result_points[2]["x"] == 110
        assert result_points[2]["y"] == 120

    def test_path_position_update_preserves_closed_state(self, canvas_model):
        """Path closed state is preserved after position update."""
        canvas_model.addItem(
            make_path(points=[{"x": 0, "y": 0}, {"x": 100, "y": 100}], closed=False)
        )

        data = canvas_model.getItemData(0)
        new_points = [
            {"x": p["x"] + 10, "y": p["y"] + 10} for p in data["geometry"]["points"]
        ]

        canvas_model.updateItem(
            0,
            {
                "type": data["type"],
                "geometry": {
                    "points": new_points,
                    "closed": data["geometry"]["closed"],
                },
                "appearances": data["appearances"],
                "name": data["name"],
                "parentId": data.get("parentId"),
                "visible": data["visible"],
                "locked": data["locked"],
            },
        )

        result = canvas_model.getItemData(0)
        assert result["geometry"]["closed"] is False


@pytest.mark.contract
class TestTextPositionContract:
    """Contract: Canvas.qml updates text position via x/y fields."""

    def test_text_position_update(self, canvas_model):
        """Text position is updated by modifying x and y fields."""
        canvas_model.addItem(
            make_text(x=100, y=100, text="Hello", font_size=16, name="Test Text")
        )

        data = canvas_model.getItemData(0)

        canvas_model.updateItem(
            0,
            {
                "type": data["type"],
                "geometry": {
                    "x": data["geometry"]["x"] + 10,
                    "y": data["geometry"]["y"] + 20,
                    "width": data["geometry"]["width"],
                    "height": data["geometry"]["height"],
                },
                "text": data["text"],
                "fontFamily": data["fontFamily"],
                "fontSize": data["fontSize"],
                "textColor": data["textColor"],
                "textOpacity": data["textOpacity"],
                "name": data["name"],
                "parentId": data.get("parentId"),
                "visible": data["visible"],
                "locked": data["locked"],
            },
        )

        result = canvas_model.getItemData(0)
        assert result["geometry"]["x"] == 110
        assert result["geometry"]["y"] == 120

    def test_text_position_update_preserves_text_properties(self, canvas_model):
        """Text content and styling are preserved after position update."""
        canvas_model.addItem(
            make_text(
                x=100,
                y=100,
                text="Hello World",
                font_family="Arial",
                font_size=24,
                text_color="#ff0000",
            )
        )

        data = canvas_model.getItemData(0)

        canvas_model.updateItem(
            0,
            {
                "type": data["type"],
                "geometry": {
                    "x": 200,
                    "y": 200,
                    "width": data["geometry"]["width"],
                    "height": data["geometry"]["height"],
                },
                "text": data["text"],
                "fontFamily": data["fontFamily"],
                "fontSize": data["fontSize"],
                "textColor": data["textColor"],
                "textOpacity": data["textOpacity"],
                "name": data["name"],
                "parentId": data.get("parentId"),
                "visible": data["visible"],
                "locked": data["locked"],
            },
        )

        result = canvas_model.getItemData(0)
        assert result["text"] == "Hello World"
        assert result["fontFamily"] == "Arial"
        assert result["fontSize"] == 24
        assert result["textColor"] == "#ff0000"


@pytest.mark.contract
class TestGroupMoveContract:
    """Contract: Canvas.qml moves groups via canvasModel.moveGroup()."""

    def test_group_move_translates_children(self, canvas_model):
        """moveGroup translates all descendant shapes."""
        # Create group with children
        canvas_model.addItem(make_group(name="Test Group", group_id="grp1"))
        canvas_model.addItem(
            make_rectangle(x=0, y=0, width=50, height=50, parent_id="grp1")
        )
        canvas_model.addItem(make_ellipse(center_x=100, center_y=100, parent_id="grp1"))

        # Move group (Canvas.qml calls this for groups/layers)
        canvas_model.moveGroup(0, 10, 20)

        # Verify children moved
        rect_data = canvas_model.getItemData(1)
        ellipse_data = canvas_model.getItemData(2)

        assert rect_data["geometry"]["x"] == 0
        assert rect_data["geometry"]["y"] == 0
        assert rect_data["transform"]["translateX"] == 10
        assert rect_data["transform"]["translateY"] == 20
        assert ellipse_data["geometry"]["centerX"] == 100
        assert ellipse_data["geometry"]["centerY"] == 100
        assert ellipse_data["transform"]["translateX"] == 10
        assert ellipse_data["transform"]["translateY"] == 20


@pytest.mark.contract
class TestBoundingBoxContract:
    """Contract: getBoundingBox returns consistent format for all types."""

    def test_bounding_box_format_rectangle(self, canvas_model):
        """Rectangle bounding box has x, y, width, height."""
        canvas_model.addItem(make_rectangle(x=10, y=20, width=100, height=50))

        bounds = canvas_model.getBoundingBox(0)

        assert "x" in bounds
        assert "y" in bounds
        assert "width" in bounds
        assert "height" in bounds
        assert bounds["x"] == 10
        assert bounds["y"] == 20
        assert bounds["width"] == 100
        assert bounds["height"] == 50

    def test_bounding_box_format_ellipse(self, canvas_model):
        """Ellipse bounding box derived from center and radii."""
        canvas_model.addItem(
            make_ellipse(center_x=100, center_y=100, radius_x=30, radius_y=20)
        )

        bounds = canvas_model.getBoundingBox(0)

        assert bounds["x"] == 70  # center - radius
        assert bounds["y"] == 80
        assert bounds["width"] == 60  # 2 * radius
        assert bounds["height"] == 40

    def test_bounding_box_format_path(self, canvas_model):
        """Path bounding box encompasses all points."""
        canvas_model.addItem(
            make_path(
                points=[
                    {"x": 10, "y": 20},
                    {"x": 110, "y": 20},
                    {"x": 110, "y": 120},
                ]
            )
        )

        bounds = canvas_model.getBoundingBox(0)

        assert bounds["x"] == 10
        assert bounds["y"] == 20
        assert bounds["width"] == 100
        assert bounds["height"] == 100
