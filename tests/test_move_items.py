# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for CanvasModel.moveItems() method - bulk position updates."""

from test_helpers import (
    make_rectangle,
    make_ellipse,
    make_path,
    make_text,
    make_group,
    make_artboard,
)


# Uses canvas_model fixture from conftest.py


def _assert_transform_translation(data, tx, ty):
    transform = data.get("transform", {})
    assert transform.get("translateX", 0) == tx
    assert transform.get("translateY", 0) == ty


class TestMoveItemsRectangle:
    """Test moving rectangle items."""

    def test_move_single_rectangle(self, canvas_model):
        """Moving a rectangle updates its translation."""
        canvas_model.addItem(make_rectangle(x=10, y=20, width=100, height=50))

        canvas_model.moveItems([0], 15, 25)

        data = canvas_model.getItemData(0)
        assert data["geometry"]["x"] == 10  # unchanged
        assert data["geometry"]["y"] == 20  # unchanged
        assert data["geometry"]["width"] == 100  # unchanged
        assert data["geometry"]["height"] == 50  # unchanged
        _assert_transform_translation(data, 15, 25)

    def test_move_multiple_rectangles(self, canvas_model):
        """Moving multiple rectangles updates translation for all of them."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=50, height=50))
        canvas_model.addItem(make_rectangle(x=100, y=100, width=50, height=50))

        canvas_model.moveItems([0, 1], 10, 20)

        data0 = canvas_model.getItemData(0)
        assert data0["geometry"]["x"] == 0
        assert data0["geometry"]["y"] == 0
        _assert_transform_translation(data0, 10, 20)

        data1 = canvas_model.getItemData(1)
        assert data1["geometry"]["x"] == 100
        assert data1["geometry"]["y"] == 100
        _assert_transform_translation(data1, 10, 20)

    def test_move_rectangle_negative_delta(self, canvas_model):
        """Moving with negative deltas updates translation."""
        canvas_model.addItem(make_rectangle(x=100, y=100, width=50, height=50))

        canvas_model.moveItems([0], -30, -40)

        data = canvas_model.getItemData(0)
        assert data["geometry"]["x"] == 100
        assert data["geometry"]["y"] == 100
        _assert_transform_translation(data, -30, -40)


class TestMoveItemsEllipse:
    """Test moving ellipse items."""

    def test_move_single_ellipse(self, canvas_model):
        """Moving an ellipse updates its translation."""
        canvas_model.addItem(
            make_ellipse(center_x=50, center_y=50, radius_x=30, radius_y=20)
        )

        canvas_model.moveItems([0], 10, 15)

        data = canvas_model.getItemData(0)
        assert data["geometry"]["centerX"] == 50  # unchanged
        assert data["geometry"]["centerY"] == 50  # unchanged
        assert data["geometry"]["radiusX"] == 30  # unchanged
        assert data["geometry"]["radiusY"] == 20  # unchanged
        _assert_transform_translation(data, 10, 15)


class TestMoveItemsText:
    """Test moving text items."""

    def test_move_single_text(self, canvas_model):
        """Moving a text item updates its translation."""
        canvas_model.addItem(make_text(x=20, y=30, text="Hello"))

        canvas_model.moveItems([0], 5, 10)

        data = canvas_model.getItemData(0)
        assert data["geometry"]["x"] == 20  # unchanged
        assert data["geometry"]["y"] == 30  # unchanged
        assert data["text"] == "Hello"  # unchanged
        _assert_transform_translation(data, 5, 10)


class TestMoveItemsPath:
    """Test moving path items."""

    def test_move_single_path(self, canvas_model):
        """Moving a path updates its translation."""
        points = [{"x": 0, "y": 0}, {"x": 50, "y": 0}, {"x": 25, "y": 40}]
        canvas_model.addItem(make_path(points=points, closed=True))

        canvas_model.moveItems([0], 10, 20)

        data = canvas_model.getItemData(0)
        assert data["geometry"]["points"][0] == {"x": 0, "y": 0}
        assert data["geometry"]["points"][1] == {"x": 50, "y": 0}
        assert data["geometry"]["points"][2] == {"x": 25, "y": 40}
        assert data["geometry"]["closed"] is True  # unchanged
        _assert_transform_translation(data, 10, 20)


class TestMoveItemsGroup:
    """Test moving group/artboard containers."""

    def test_move_group_moves_children(self, canvas_model):
        """Moving a group updates translation for all its child items."""
        canvas_model.addItem(make_group(name="Group", group_id="grp1"))
        canvas_model.addItem(
            make_rectangle(x=0, y=0, width=50, height=50, parent_id="grp1")
        )
        canvas_model.addItem(make_ellipse(center_x=100, center_y=100, parent_id="grp1"))

        canvas_model.moveItems([0], 20, 30)

        rect_data = canvas_model.getItemData(1)
        assert rect_data["geometry"]["x"] == 0
        assert rect_data["geometry"]["y"] == 0
        _assert_transform_translation(rect_data, 20, 30)

        ellipse_data = canvas_model.getItemData(2)
        assert ellipse_data["geometry"]["centerX"] == 100
        assert ellipse_data["geometry"]["centerY"] == 100
        _assert_transform_translation(ellipse_data, 20, 30)

    def test_move_artboard_moves_children(self, canvas_model):
        """Moving an artboard updates translation for all its child items."""
        canvas_model.addItem(make_artboard(name="Artboard", artboard_id="artboard1"))
        canvas_model.addItem(make_rectangle(x=10, y=10, parent_id="artboard1"))

        canvas_model.moveItems([0], 5, 5)

        data = canvas_model.getItemData(1)
        assert data["geometry"]["x"] == 10
        assert data["geometry"]["y"] == 10
        _assert_transform_translation(data, 5, 5)


class TestMoveItemsAvoidDoubleMoves:
    """Test that items inside selected containers are not moved twice."""

    def test_selecting_group_and_child_moves_once(self, canvas_model):
        """When both group and child are selected, child translates only once."""
        canvas_model.addItem(make_group(name="Group", group_id="grp1"))
        canvas_model.addItem(
            make_rectangle(x=0, y=0, width=50, height=50, parent_id="grp1")
        )

        # Select both group (0) and rectangle (1)
        canvas_model.moveItems([0, 1], 10, 10)

        # Rectangle should move only 10,10 - not 20,20
        data = canvas_model.getItemData(1)
        assert data["geometry"]["x"] == 0
        assert data["geometry"]["y"] == 0
        _assert_transform_translation(data, 10, 10)


class TestMoveItemsLocked:
    """Test that locked items are not moved."""

    def test_locked_item_not_moved(self, canvas_model):
        """Locked items should not be moved."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=50, height=50, locked=True))

        canvas_model.moveItems([0], 10, 10)

        data = canvas_model.getItemData(0)
        assert data["geometry"]["x"] == 0
        assert data["geometry"]["y"] == 0
        _assert_transform_translation(data, 0, 0)

    def test_effectively_locked_item_not_moved(self, canvas_model):
        """Items in locked artboards should still be moved."""
        canvas_model.addItem(
            make_artboard(name="Layer", artboard_id="layer1", locked=True)
        )
        canvas_model.addItem(make_rectangle(x=0, y=0, parent_id="layer1"))

        canvas_model.moveItems([1], 10, 10)

        data = canvas_model.getItemData(1)
        assert data["geometry"]["x"] == 0
        assert data["geometry"]["y"] == 0
        _assert_transform_translation(data, 10, 10)


class TestMoveItemsMixedTypes:
    """Test moving multiple items of different types together."""

    def test_move_mixed_selection(self, canvas_model):
        """Moving a mixed selection updates translation for all item types."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=50, height=50))
        canvas_model.addItem(make_ellipse(center_x=100, center_y=100))
        canvas_model.addItem(make_text(x=200, y=200, text="Test"))
        points = [{"x": 300, "y": 300}, {"x": 350, "y": 350}]
        canvas_model.addItem(make_path(points=points))

        canvas_model.moveItems([0, 1, 2, 3], 10, 20)

        rect = canvas_model.getItemData(0)
        assert rect["geometry"]["x"] == 0
        assert rect["geometry"]["y"] == 0
        _assert_transform_translation(rect, 10, 20)

        ellipse = canvas_model.getItemData(1)
        assert ellipse["geometry"]["centerX"] == 100
        assert ellipse["geometry"]["centerY"] == 100
        _assert_transform_translation(ellipse, 10, 20)

        text = canvas_model.getItemData(2)
        assert text["geometry"]["x"] == 200
        assert text["geometry"]["y"] == 200
        _assert_transform_translation(text, 10, 20)

        path = canvas_model.getItemData(3)
        assert path["geometry"]["points"][0] == {"x": 300, "y": 300}
        assert path["geometry"]["points"][1] == {"x": 350, "y": 350}
        _assert_transform_translation(path, 10, 20)


class TestMoveItemsUndoRedo:
    """Test undo/redo for moveItems."""

    def test_move_items_undoable(self, canvas_model):
        """moveItems should be undoable."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=50, height=50))

        canvas_model.moveItems([0], 10, 20)
        _assert_transform_translation(canvas_model.getItemData(0), 10, 20)

        canvas_model.undo()
        _assert_transform_translation(canvas_model.getItemData(0), 0, 0)

    def test_move_items_redoable(self, canvas_model):
        """moveItems should be redoable after undo."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=50, height=50))

        canvas_model.moveItems([0], 10, 20)
        canvas_model.undo()
        canvas_model.redo()

        _assert_transform_translation(canvas_model.getItemData(0), 10, 20)

    def test_move_multiple_items_single_undo(self, canvas_model):
        """Moving multiple items should undo as a single operation."""
        canvas_model.addItem(make_rectangle(x=0, y=0))
        canvas_model.addItem(make_rectangle(x=100, y=100))

        canvas_model.moveItems([0, 1], 10, 10)

        # Single undo should restore both
        canvas_model.undo()

        _assert_transform_translation(canvas_model.getItemData(0), 0, 0)
        _assert_transform_translation(canvas_model.getItemData(1), 0, 0)


class TestMoveItemsEdgeCases:
    """Test edge cases for moveItems."""

    def test_empty_indices_list(self, canvas_model):
        """Empty indices list should be a no-op."""
        canvas_model.addItem(make_rectangle(x=0, y=0))

        canvas_model.moveItems([], 10, 10)

        data = canvas_model.getItemData(0)
        assert data["geometry"]["x"] == 0
        _assert_transform_translation(data, 0, 0)

    def test_invalid_indices_ignored(self, canvas_model):
        """Invalid indices should be silently ignored."""
        canvas_model.addItem(make_rectangle(x=0, y=0))

        # Index 99 doesn't exist
        canvas_model.moveItems([0, 99], 10, 10)

        data = canvas_model.getItemData(0)
        assert data["geometry"]["x"] == 0
        _assert_transform_translation(data, 10, 10)

    def test_zero_delta_no_op(self, canvas_model):
        """Zero delta should not create unnecessary undo entries."""
        canvas_model.addItem(make_rectangle(x=0, y=0))

        initial_can_undo = canvas_model.canUndo

        canvas_model.moveItems([0], 0, 0)

        # Should not add undo entry for no-op
        assert canvas_model.canUndo == initial_can_undo
