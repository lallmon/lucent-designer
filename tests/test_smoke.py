# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Smoke tests for Lucent canvas operations.

These tests provide quick sanity checks for critical canvas functionality.
Run these after any QML changes to verify basic operations still work.

Usage:
    pytest -m smoke -v
"""

import pytest
from test_helpers import (
    make_rectangle,
    make_ellipse,
    make_path,
    make_text,
    make_artboard,
    make_group,
)


@pytest.mark.smoke
class TestSmokeCreateShapes:
    """Quick checks that all shape types can be created."""

    def test_create_all_shape_types(self, canvas_model):
        """All shape types can be added to the model."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=100))
        canvas_model.addItem(make_ellipse(center_x=200, center_y=200))
        canvas_model.addItem(make_path(points=[{"x": 0, "y": 0}, {"x": 100, "y": 100}]))
        canvas_model.addItem(make_text(x=300, y=300, text="Hello"))
        canvas_model.addItem(make_artboard(name="Layer 1"))
        canvas_model.addItem(make_group(name="Group 1"))

        assert canvas_model.count() == 6

    def test_create_shape_returns_valid_data(self, canvas_model):
        """Created shapes can be retrieved with valid data."""
        canvas_model.addItem(make_rectangle(x=50, y=50, width=100, height=100))

        data = canvas_model.getItemData(0)

        assert data is not None
        assert data["type"] == "rectangle"
        assert data["geometry"]["x"] == 50
        assert data["geometry"]["width"] == 100


@pytest.mark.smoke
class TestSmokeUpdateShapes:
    """Quick checks that shapes can be updated."""

    def test_update_and_verify_bounds(self, canvas_model):
        """Updating a shape changes its bounding box."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=100))

        bounds_before = canvas_model.getBoundingBox(0)
        assert bounds_before["x"] == 0

        data = canvas_model.getItemData(0)
        data["geometry"]["x"] = 50
        canvas_model.updateItem(0, data)

        bounds_after = canvas_model.getBoundingBox(0)
        assert bounds_after["x"] == 50

    def test_update_multiple_shapes(self, canvas_model):
        """Multiple shapes can be updated sequentially."""
        canvas_model.addItem(make_rectangle(x=0, y=0))
        canvas_model.addItem(make_ellipse(center_x=100, center_y=100))

        for i in range(2):
            data = canvas_model.getItemData(i)
            if data["type"] == "rectangle":
                data["geometry"]["x"] = 999
            else:
                data["geometry"]["centerX"] = 999
            canvas_model.updateItem(i, data)

        rect_data = canvas_model.getItemData(0)
        ellipse_data = canvas_model.getItemData(1)

        assert rect_data["geometry"]["x"] == 999
        assert ellipse_data["geometry"]["centerX"] == 999


@pytest.mark.smoke
class TestSmokeDeleteShapes:
    """Quick checks that shapes can be deleted."""

    def test_delete_single_shape(self, canvas_model):
        """Single shape can be deleted."""
        canvas_model.addItem(make_rectangle())

        assert canvas_model.count() == 1

        canvas_model.removeItem(0)

        assert canvas_model.count() == 0

    def test_delete_shifts_indices(self, canvas_model):
        """Deleting a shape shifts subsequent indices."""
        canvas_model.addItem(make_rectangle(name="First"))
        canvas_model.addItem(make_rectangle(name="Second"))
        canvas_model.addItem(make_rectangle(name="Third"))

        canvas_model.removeItem(0)  # Remove "First"

        assert canvas_model.count() == 2
        assert canvas_model.getItemData(0)["name"] == "Second"
        assert canvas_model.getItemData(1)["name"] == "Third"

    def test_clear_removes_all(self, canvas_model):
        """Clear removes all shapes."""
        for i in range(5):
            canvas_model.addItem(make_rectangle(x=i * 10))

        assert canvas_model.count() == 5

        canvas_model.clear()

        assert canvas_model.count() == 0


@pytest.mark.smoke
class TestSmokeUndoRedo:
    """Quick checks that undo/redo works."""

    def test_undo_add(self, canvas_model):
        """Undo reverses an add operation."""
        canvas_model.addItem(make_rectangle())

        assert canvas_model.count() == 1

        canvas_model.undo()

        assert canvas_model.count() == 0

    def test_redo_after_undo(self, canvas_model):
        """Redo restores after undo."""
        canvas_model.addItem(make_rectangle())
        canvas_model.undo()

        assert canvas_model.count() == 0

        canvas_model.redo()

        assert canvas_model.count() == 1

    def test_undo_update(self, canvas_model):
        """Undo reverses an update operation."""
        canvas_model.addItem(make_rectangle(x=0))

        data = canvas_model.getItemData(0)
        data["geometry"]["x"] = 100
        canvas_model.updateItem(0, data)

        assert canvas_model.getItemData(0)["geometry"]["x"] == 100

        canvas_model.undo()

        assert canvas_model.getItemData(0)["geometry"]["x"] == 0


@pytest.mark.smoke
class TestSmokeBoundingBox:
    """Quick checks that bounding boxes work."""

    def test_bounding_box_exists_for_all_types(self, canvas_model):
        """All renderable shape types have bounding boxes."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=100))
        canvas_model.addItem(
            make_ellipse(center_x=200, center_y=200, radius_x=50, radius_y=50)
        )
        canvas_model.addItem(
            make_path(points=[{"x": 300, "y": 300}, {"x": 400, "y": 400}])
        )

        for i in range(3):
            bounds = canvas_model.getBoundingBox(i)
            assert bounds is not None
            assert "x" in bounds
            assert "y" in bounds
            assert "width" in bounds
            assert "height" in bounds


@pytest.mark.smoke
class TestSmokeStress:
    """Quick stress tests to verify stability."""

    def test_rapid_operations_no_crash(self, canvas_model):
        """Model survives rapid create/update/delete cycles."""
        # Create many items
        for i in range(20):
            canvas_model.addItem(make_rectangle(x=i * 10, y=i * 10))

        assert canvas_model.count() == 20

        # Update all items
        for i in range(20):
            data = canvas_model.getItemData(i)
            data["geometry"]["x"] = i * 20
            canvas_model.updateItem(i, data)

        # Delete half
        for _ in range(10):
            canvas_model.removeItem(0)

        assert canvas_model.count() == 10

        # Clear the rest
        canvas_model.clear()

        assert canvas_model.count() == 0

    def test_mixed_shape_types_no_crash(self, canvas_model):
        """Model handles mixed shape types without issues."""
        shapes = [
            make_rectangle(x=0, y=0),
            make_ellipse(center_x=100, center_y=100),
            make_path(points=[{"x": 0, "y": 0}, {"x": 50, "y": 50}]),
            make_text(x=200, y=200, text="Test"),
            make_artboard(name="Layer"),
            make_rectangle(x=300, y=300),
        ]

        for shape in shapes:
            canvas_model.addItem(shape)

        assert canvas_model.count() == 6

        # Access all items
        for i in range(6):
            data = canvas_model.getItemData(i)
            assert data is not None
            assert "type" in data
