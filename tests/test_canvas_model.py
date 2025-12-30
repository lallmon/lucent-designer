"""Unit tests for canvas_model module."""

import pytest
from lucent.canvas_model import CanvasModel
from lucent.canvas_items import RectangleItem, EllipseItem, LayerItem
from lucent.commands import (
    Command,
    AddItemCommand,
    RemoveItemCommand,
    UpdateItemCommand,
    TransactionCommand,
)
from types import SimpleNamespace


class TestCanvasModelBasics:
    """Tests for basic CanvasModel operations."""

    def test_initial_state_empty(self, canvas_model):
        """Test that a new CanvasModel starts empty."""
        assert canvas_model.count() == 0
        assert canvas_model.getItems() == []

    def test_add_rectangle_item(self, canvas_model, qtbot):
        """Test adding a rectangle item to the model."""
        item_data = {
            "type": "rectangle",
            "x": 10,
            "y": 20,
            "width": 100,
            "height": 50,
            "strokeWidth": 2,
            "strokeColor": "#ff0000",
        }

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000) as blocker:
            canvas_model.addItem(item_data)

        assert canvas_model.count() == 1
        assert blocker.args == [0]  # Index of added item

        items = canvas_model.getItems()
        assert len(items) == 1
        assert isinstance(items[0], RectangleItem)
        assert items[0].x == 10
        assert items[0].y == 20

    def test_add_ellipse_item(self, canvas_model, qtbot):
        """Test adding an ellipse item to the model."""
        item_data = {
            "type": "ellipse",
            "centerX": 50,
            "centerY": 75,
            "radiusX": 30,
            "radiusY": 20,
            "fillColor": "#00ff00",
            "fillOpacity": 0.5,
        }

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000) as blocker:
            canvas_model.addItem(item_data)

        assert canvas_model.count() == 1
        assert blocker.args == [0]

        items = canvas_model.getItems()
        assert len(items) == 1
        assert isinstance(items[0], EllipseItem)
        assert items[0].center_x == 50
        assert items[0].center_y == 75

    def test_add_multiple_items(self, canvas_model, qtbot):
        """Test adding multiple items maintains correct order."""
        rect_data = {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        ellipse_data = {
            "type": "ellipse",
            "centerX": 20,
            "centerY": 20,
            "radiusX": 5,
            "radiusY": 5,
        }

        canvas_model.addItem(rect_data)
        canvas_model.addItem(ellipse_data)

        assert canvas_model.count() == 2
        items = canvas_model.getItems()
        assert isinstance(items[0], RectangleItem)
        assert isinstance(items[1], EllipseItem)

    def test_add_unknown_item_type_ignored(self, canvas_model, qtbot):
        """Test that adding an unknown item type is safely ignored."""
        item_data = {"type": "triangle", "x": 0, "y": 0}

        # Should not emit signal or add item
        canvas_model.addItem(item_data)
        assert canvas_model.count() == 0

    def test_data_invalid_index_and_role_returns_none(self, canvas_model):
        from PySide6.QtCore import QModelIndex, Qt

        assert canvas_model.data(QModelIndex(), Qt.DisplayRole) is None
        idx = canvas_model.index(0, 0)
        assert canvas_model.data(idx, 9999) is None

    def test_add_malformed_item_ignored(self, canvas_model):
        """Test that adding malformed data is safely handled."""
        # Missing type field
        item_data = {"x": 10, "y": 20}
        canvas_model.addItem(item_data)
        assert canvas_model.count() == 0


class TestCanvasModelRemoval:
    """Tests for removing items from CanvasModel."""

    def test_remove_item_by_index(self, canvas_model, qtbot):
        """Test removing an item by its index."""
        # Add two items
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 20,
                "centerY": 20,
                "radiusX": 5,
                "radiusY": 5,
            }
        )

        assert canvas_model.count() == 2

        # Remove first item
        with qtbot.waitSignal(canvas_model.itemRemoved, timeout=1000) as blocker:
            canvas_model.removeItem(0)

        assert blocker.args == [0]
        assert canvas_model.count() == 1

        # Remaining item should be the ellipse
        items = canvas_model.getItems()
        assert isinstance(items[0], EllipseItem)

    def test_remove_last_item(self, canvas_model, qtbot):
        """Test removing the last item in the list."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 20,
                "centerY": 20,
                "radiusX": 5,
                "radiusY": 5,
            }
        )

        with qtbot.waitSignal(canvas_model.itemRemoved, timeout=1000):
            canvas_model.removeItem(1)

        assert canvas_model.count() == 1
        items = canvas_model.getItems()
        assert isinstance(items[0], RectangleItem)

    def test_remove_invalid_index_negative(self, canvas_model):
        """Test that removing with negative index is safely handled."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        # Should not crash or emit signal
        canvas_model.removeItem(-1)
        assert canvas_model.count() == 1

    def test_remove_invalid_index_too_large(self, canvas_model):
        """Test that removing with out-of-bounds index is safely handled."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        # Should not crash or emit signal
        canvas_model.removeItem(5)
        assert canvas_model.count() == 1

    def test_remove_from_empty_model(self, canvas_model):
        """Test that removing from an empty model is safely handled."""
        canvas_model.removeItem(0)
        assert canvas_model.count() == 0

    def test_remove_layer_deletes_children(self, canvas_model, qtbot):
        """Removing a layer should delete its child shapes as well."""
        canvas_model.addLayer()
        layer_id = canvas_model.getItems()[0].id
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.setParent(1, layer_id)
        assert canvas_model.count() == 2

        with qtbot.waitSignal(canvas_model.itemRemoved, timeout=1000) as blocker:
            canvas_model.removeItem(0)

        assert blocker.args == [0]
        assert canvas_model.count() == 0

    def test_remove_layer_with_children_supports_undo_redo(self, canvas_model):
        """Removing a layer with children should be undoable/redoable."""
        canvas_model.addLayer()
        layer_id = canvas_model.getItems()[0].id
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.setParent(1, layer_id)
        assert canvas_model.count() == 2

        canvas_model.removeItem(0)
        assert canvas_model.count() == 0

        canvas_model.undo()
        assert canvas_model.count() == 2
        assert canvas_model.getItems()[0].id == layer_id
        assert canvas_model.getItems()[1].parent_id == layer_id

        canvas_model.redo()
        assert canvas_model.count() == 0


class TestCanvasModelClear:
    """Tests for clearing all items from CanvasModel."""

    def test_clear_empty_model(self, canvas_model, qtbot):
        """Test clearing an already empty model."""
        with qtbot.waitSignal(canvas_model.itemsCleared, timeout=1000):
            canvas_model.clear()

        assert canvas_model.count() == 0

    def test_clear_model_with_items(self, canvas_model, qtbot):
        """Test clearing a model with multiple items."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 20,
                "centerY": 20,
                "radiusX": 5,
                "radiusY": 5,
            }
        )
        canvas_model.addItem(
            {"type": "rectangle", "x": 30, "y": 30, "width": 15, "height": 15}
        )

        assert canvas_model.count() == 3

        with qtbot.waitSignal(canvas_model.itemsCleared, timeout=1000):
            canvas_model.clear()

        assert canvas_model.count() == 0
        assert canvas_model.getItems() == []


class TestCanvasModelUpdate:
    """Tests for updating item properties in CanvasModel."""

    def test_update_rectangle_position(self, canvas_model, qtbot):
        """Test updating a rectangle's position."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 10, "y": 20, "width": 100, "height": 50}
        )

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000) as blocker:
            canvas_model.updateItem(0, {"x": 50, "y": 75})

        assert blocker.args[0] == 0  # Index
        assert blocker.args[1]["x"] == 50  # Updated data
        assert blocker.args[1]["y"] == 75

        items = canvas_model.getItems()
        assert items[0].x == 50
        assert items[0].y == 75
        # Other properties unchanged
        assert items[0].width == 100
        assert items[0].height == 50

    def test_update_rectangle_dimensions(self, canvas_model, qtbot):
        """Test updating a rectangle's dimensions."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 50, "height": 50}
        )

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, {"width": 100, "height": 75})

        items = canvas_model.getItems()
        assert items[0].width == 100
        assert items[0].height == 75

    def test_update_ellipse_position(self, canvas_model, qtbot):
        """Test updating an ellipse's center position."""
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 50,
                "centerY": 50,
                "radiusX": 20,
                "radiusY": 20,
            }
        )

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, {"centerX": 100, "centerY": 150})

        items = canvas_model.getItems()
        assert items[0].center_x == 100
        assert items[0].center_y == 150

    def test_update_ellipse_radii(self, canvas_model, qtbot):
        """Test updating an ellipse's radii."""
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 0,
                "centerY": 0,
                "radiusX": 10,
                "radiusY": 10,
            }
        )

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, {"radiusX": 30, "radiusY": 25})

        items = canvas_model.getItems()
        assert items[0].radius_x == 30
        assert items[0].radius_y == 25

    def test_update_stroke_properties(self, canvas_model, qtbot):
        """Test updating stroke properties (width, color, opacity)."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(
                0, {"strokeWidth": 5, "strokeColor": "#ff0000", "strokeOpacity": 0.8}
            )

        items = canvas_model.getItems()
        assert items[0].stroke_width == 5
        assert items[0].stroke_color == "#ff0000"
        assert items[0].stroke_opacity == 0.8

    def test_update_fill_properties(self, canvas_model, qtbot):
        """Test updating fill properties (color, opacity)."""
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 0,
                "centerY": 0,
                "radiusX": 10,
                "radiusY": 10,
            }
        )

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, {"fillColor": "#00ff00", "fillOpacity": 0.6})

        items = canvas_model.getItems()
        assert items[0].fill_color == "#00ff00"
        assert items[0].fill_opacity == 0.6

    def test_update_partial_properties(self, canvas_model, qtbot):
        """Test updating only some properties leaves others unchanged."""
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 10,
                "y": 20,
                "width": 100,
                "height": 50,
                "strokeWidth": 2,
                "strokeColor": "#ffffff",
            }
        )

        # Update only x coordinate
        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, {"x": 30})

        items = canvas_model.getItems()
        assert items[0].x == 30
        # Everything else unchanged
        assert items[0].y == 20
        assert items[0].width == 100
        assert items[0].height == 50
        assert items[0].stroke_width == 2

    def test_update_validates_negative_dimensions(self, canvas_model, qtbot):
        """Test that update validates and clamps negative dimensions."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, {"width": -50, "height": -30})

        items = canvas_model.getItems()
        assert items[0].width == 0.0
        assert items[0].height == 0.0

    def test_update_validates_stroke_width_bounds(self, canvas_model, qtbot):
        """Test that update validates stroke width bounds."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, {"strokeWidth": 200})

        items = canvas_model.getItems()
        assert items[0].stroke_width == 100.0

    def test_update_validates_opacity_bounds(self, canvas_model, qtbot):
        """Test that update validates opacity bounds."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, {"strokeOpacity": 5.0, "fillOpacity": -2.0})

        items = canvas_model.getItems()
        assert items[0].stroke_opacity == 1.0
        assert items[0].fill_opacity == 0.0

    def test_update_invalid_index_ignored(self, canvas_model):
        """Test that updating with invalid index is safely handled."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        # Should not crash
        canvas_model.updateItem(5, {"x": 100})

        # Item unchanged
        items = canvas_model.getItems()
        assert items[0].x == 0

    def test_update_with_malformed_data_handled(self, canvas_model, qtbot):
        """Test that update with malformed data is handled gracefully."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 10, "y": 20, "width": 100, "height": 50}
        )

        # Try to update with invalid data type
        canvas_model.updateItem(0, {"width": "not a number"})

        # Item should remain unchanged
        items = canvas_model.getItems()
        assert items[0].width == 100


class TestCanvasModelRename:
    """Tests for renaming items in CanvasModel."""

    def test_rename_item_updates_name_and_emits(self, canvas_model, qtbot):
        """Renaming should update the item name and emit itemModified."""
        canvas_model.addLayer()

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000) as blocker:
            canvas_model.renameItem(0, "Renamed Layer")

        assert blocker.args[0] == 0
        assert blocker.args[1]["name"] == "Renamed Layer"
        assert canvas_model.getItems()[0].name == "Renamed Layer"

    def test_rename_item_supports_undo_redo(self, canvas_model):
        """Rename should be undoable and redoable."""
        canvas_model.addLayer()
        original_name = canvas_model.getItems()[0].name

        canvas_model.renameItem(0, "Renamed Layer")
        assert canvas_model.getItems()[0].name == "Renamed Layer"

        canvas_model.undo()
        assert canvas_model.getItems()[0].name == original_name

        canvas_model.redo()
        assert canvas_model.getItems()[0].name == "Renamed Layer"

    def test_rename_invalid_index_is_noop(self, canvas_model):
        """Renaming with an invalid index should do nothing."""
        canvas_model.addLayer()
        original_name = canvas_model.getItems()[0].name
        initial_can_undo = canvas_model.canUndo

        canvas_model.renameItem(-1, "Ignored")
        canvas_model.renameItem(5, "Ignored")

        assert canvas_model.getItems()[0].name == original_name
        assert canvas_model.canUndo == initial_can_undo

    def test_rename_same_name_is_noop(self, canvas_model):
        """Renaming to the same value should do nothing and not emit."""
        canvas_model.addLayer()
        original_name = canvas_model.getItems()[0].name
        initial_can_undo = canvas_model.canUndo

        emissions = []
        canvas_model.itemModified.connect(
            lambda idx, data: emissions.append((idx, data))
        )

        canvas_model.renameItem(0, original_name)

        assert canvas_model.getItems()[0].name == original_name
        assert emissions == []
        assert canvas_model.canUndo == initial_can_undo

    def test_rename_shape_updates_name_and_preserves_parent(self, canvas_model, qtbot):
        """Shapes can be renamed and keep their parent relationship."""
        canvas_model.addLayer()
        layer_id = canvas_model.getItems()[0].id
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.setParent(1, layer_id)

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000) as blocker:
            canvas_model.renameItem(1, "Renamed Rect")

        assert blocker.args[0] == 1
        assert blocker.args[1]["name"] == "Renamed Rect"
        rect = canvas_model.getItems()[1]
        assert rect.name == "Renamed Rect"
        assert rect.parent_id == layer_id


class TestCanvasModelQueries:
    """Tests for querying item data from CanvasModel."""

    def test_get_item_data_rectangle(self, canvas_model):
        """Test getting data for a rectangle item."""
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 10,
                "y": 20,
                "width": 100,
                "height": 50,
                "strokeWidth": 2,
                "strokeColor": "#ff0000",
            }
        )

        data = canvas_model.getItemData(0)
        assert data is not None
        assert data["type"] == "rectangle"
        assert data["x"] == 10
        assert data["y"] == 20
        assert data["width"] == 100
        assert data["height"] == 50
        assert data["strokeWidth"] == 2
        assert data["strokeColor"] == "#ff0000"

    def test_get_item_data_ellipse(self, canvas_model):
        """Test getting data for an ellipse item."""
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 50,
                "centerY": 75,
                "radiusX": 30,
                "radiusY": 20,
                "fillColor": "#00ff00",
                "fillOpacity": 0.5,
            }
        )

        data = canvas_model.getItemData(0)
        assert data is not None
        assert data["type"] == "ellipse"
        assert data["centerX"] == 50
        assert data["centerY"] == 75
        assert data["radiusX"] == 30
        assert data["radiusY"] == 20
        assert data["fillColor"] == "#00ff00"
        assert data["fillOpacity"] == 0.5

    def test_get_item_data_invalid_index(self, canvas_model):
        """Test getting data for invalid index returns None."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        assert canvas_model.getItemData(-1) is None
        assert canvas_model.getItemData(5) is None

    def test_get_items_for_hit_test(self, canvas_model):
        """Test getting all items as dictionaries for hit testing."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 20,
                "centerY": 20,
                "radiusX": 5,
                "radiusY": 5,
            }
        )

        items = canvas_model.getItemsForHitTest()
        assert len(items) == 2
        assert items[0]["type"] == "rectangle"
        assert items[1]["type"] == "ellipse"

    def test_get_items_for_hit_test_empty(self, canvas_model):
        """Test getting items for hit test from empty model."""
        items = canvas_model.getItemsForHitTest()
        assert items == []


class TestCanvasModelUndo:
    """Tests for undo functionality in CanvasModel."""

    def test_can_undo_empty_stack(self, canvas_model):
        """Test canUndo returns False when undo stack is empty."""
        assert canvas_model.canUndo is False

    def test_undo_empty_stack_returns_false(self, canvas_model):
        """Test undo returns False when nothing to undo."""
        assert canvas_model.undo() is False

    def test_undo_add_item(self, canvas_model, qtbot):
        """Test undoing addItem removes the item."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 10, "y": 20, "width": 100, "height": 50}
        )
        assert canvas_model.count() == 1
        assert canvas_model.canUndo is True

        with qtbot.waitSignal(canvas_model.itemRemoved, timeout=1000):
            result = canvas_model.undo()

        assert result is True
        assert canvas_model.count() == 0
        assert canvas_model.canUndo is False

    def test_undo_remove_item(self, canvas_model, qtbot):
        """Test undoing removeItem restores the item."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 10, "y": 20, "width": 100, "height": 50}
        )
        canvas_model.removeItem(0)
        assert canvas_model.count() == 0

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            result = canvas_model.undo()

        assert result is True
        assert canvas_model.count() == 1
        items = canvas_model.getItems()
        assert items[0].x == 10
        assert items[0].width == 100

    def test_undo_update_item(self, canvas_model, qtbot):
        """Test undoing updateItem restores previous properties."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 10, "y": 20, "width": 100, "height": 50}
        )
        canvas_model.updateItem(0, {"x": 50, "y": 75})

        items = canvas_model.getItems()
        assert items[0].x == 50
        assert items[0].y == 75

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            result = canvas_model.undo()

        assert result is True
        items = canvas_model.getItems()
        assert items[0].x == 10
        assert items[0].y == 20

    def test_undo_clear(self, canvas_model, qtbot):
        """Test undoing clear restores all items."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 20,
                "centerY": 20,
                "radiusX": 5,
                "radiusY": 5,
            }
        )
        canvas_model.clear()
        assert canvas_model.count() == 0

        result = canvas_model.undo()

        assert result is True
        assert canvas_model.count() == 2
        items = canvas_model.getItems()
        assert isinstance(items[0], RectangleItem)
        assert isinstance(items[1], EllipseItem)

    def test_multiple_undos(self, canvas_model):
        """Test multiple sequential undos work correctly."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 20,
                "centerY": 20,
                "radiusX": 5,
                "radiusY": 5,
            }
        )
        assert canvas_model.count() == 2

        canvas_model.undo()
        assert canvas_model.count() == 1
        assert isinstance(canvas_model.getItems()[0], RectangleItem)

        canvas_model.undo()
        assert canvas_model.count() == 0
        assert canvas_model.canUndo is False

    def test_undo_stack_changed_signal(self, canvas_model, qtbot):
        """Test undoStackChanged signal is emitted on undo stack changes."""
        with qtbot.waitSignal(canvas_model.undoStackChanged, timeout=1000):
            canvas_model.addItem(
                {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
            )

        with qtbot.waitSignal(canvas_model.undoStackChanged, timeout=1000):
            canvas_model.undo()

    def test_undo_stack_contains_command_objects(self, canvas_model):
        """Undo should be available after an action and clear after undo."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        assert canvas_model.canUndo is True
        canvas_model.undo()
        assert canvas_model.canUndo is False

    def test_add_item_pushes_add_command(self, canvas_model):
        """addItem should enable undo."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        assert canvas_model.canUndo is True

    def test_remove_item_pushes_remove_command(self, canvas_model):
        """removeItem should enable undo and allow restoration."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.removeItem(0)
        assert canvas_model.canUndo is True
        canvas_model.undo()
        assert canvas_model.count() == 1

    def test_update_item_pushes_update_command(self, canvas_model):
        """updateItem should enable undo and allow restoration."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.updateItem(0, {"x": 50})
        assert canvas_model.canUndo is True
        canvas_model.undo()
        assert canvas_model.getItems()[0].x == 0


class TestCanvasModelTransactions:
    """Tests for transaction coalescing in CanvasModel."""

    def test_transaction_coalesces_multiple_updates(self, canvas_model):
        """Test that updates within a transaction create a single undo entry."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )
        assert canvas_model.canUndo is True

        canvas_model.beginTransaction()
        canvas_model.updateItem(0, {"x": 10})
        canvas_model.updateItem(0, {"x": 20})
        canvas_model.updateItem(0, {"x": 30})
        canvas_model.endTransaction()

        assert canvas_model.getItems()[0].x == 30

    def test_undo_transaction_restores_original_state(self, canvas_model):
        """Test that undoing a transaction restores the pre-transaction state."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )

        canvas_model.beginTransaction()
        canvas_model.updateItem(0, {"x": 50, "y": 50})
        canvas_model.updateItem(0, {"x": 100, "y": 100})
        canvas_model.updateItem(0, {"x": 150, "y": 150})
        canvas_model.endTransaction()

        canvas_model.undo()

        items = canvas_model.getItems()
        assert items[0].x == 0
        assert items[0].y == 0

    def test_empty_transaction_creates_no_undo(self, canvas_model):
        """Test that a transaction with no changes creates no undo entry."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )
        initial_can_undo = canvas_model.canUndo

        canvas_model.beginTransaction()
        canvas_model.endTransaction()

        assert canvas_model.canUndo == initial_can_undo

    def test_transaction_tracks_multiple_items(self, canvas_model):
        """Test that transactions can track changes to multiple items."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 50,
                "centerY": 50,
                "radiusX": 25,
                "radiusY": 25,
            }
        )

        canvas_model.beginTransaction()
        canvas_model.updateItem(0, {"x": 100})
        canvas_model.updateItem(1, {"centerX": 200})
        canvas_model.endTransaction()

        canvas_model.undo()

        assert canvas_model.getItems()[0].x == 0
        assert canvas_model.getItems()[1].center_x == 50

    def test_nested_begin_transaction_ignored(self, canvas_model):
        """Test that calling beginTransaction while active is safely ignored."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )

        canvas_model.beginTransaction()
        canvas_model.updateItem(0, {"x": 50})
        canvas_model.beginTransaction()
        canvas_model.updateItem(0, {"x": 100})
        canvas_model.endTransaction()

        canvas_model.undo()
        assert canvas_model.getItems()[0].x == 0

    def test_end_transaction_without_begin_is_noop(self, canvas_model):
        """Calling endTransaction without beginTransaction should be a no-op."""
        initial_can_undo = canvas_model.canUndo
        canvas_model.endTransaction()
        assert canvas_model.canUndo == initial_can_undo

    def test_transaction_pushes_transaction_command(self, canvas_model):
        """Test that transactions push TransactionCommand to the stack."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )

        canvas_model.beginTransaction()
        canvas_model.updateItem(0, {"x": 50})
        canvas_model.endTransaction()

        assert canvas_model.canUndo is True


class TestCanvasModelRedo:
    """Tests for redo functionality in CanvasModel."""

    def test_can_redo_empty_stack(self, canvas_model):
        """Test canRedo returns False when redo stack is empty."""
        assert canvas_model.canRedo is False

    def test_redo_empty_stack_returns_false(self, canvas_model):
        """Test redo returns False when nothing to redo."""
        assert canvas_model.redo() is False

    def test_undo_enables_redo(self, canvas_model):
        """Test that performing undo enables redo."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )
        assert canvas_model.canRedo is False

        canvas_model.undo()

        assert canvas_model.canRedo is True

    def test_redo_add_item(self, canvas_model, qtbot):
        """Test redoing an undone addItem."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 10, "y": 20, "width": 100, "height": 50}
        )
        canvas_model.undo()
        assert canvas_model.count() == 0

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            result = canvas_model.redo()

        assert result is True
        assert canvas_model.count() == 1
        assert canvas_model.getItems()[0].x == 10

    def test_redo_remove_item(self, canvas_model, qtbot):
        """Test redoing an undone removeItem."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )
        canvas_model.removeItem(0)
        canvas_model.undo()
        assert canvas_model.count() == 1

        with qtbot.waitSignal(canvas_model.itemRemoved, timeout=1000):
            result = canvas_model.redo()

        assert result is True
        assert canvas_model.count() == 0

    def test_redo_update_item(self, canvas_model, qtbot):
        """Test redoing an undone updateItem."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )
        canvas_model.updateItem(0, {"x": 50, "y": 75})
        canvas_model.undo()
        assert canvas_model.getItems()[0].x == 0

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            result = canvas_model.redo()

        assert result is True
        assert canvas_model.getItems()[0].x == 50
        assert canvas_model.getItems()[0].y == 75

    def test_new_action_clears_redo_stack(self, canvas_model):
        """Test that performing a new action clears the redo stack."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )
        canvas_model.undo()
        assert canvas_model.canRedo is True

        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 50,
                "centerY": 50,
                "radiusX": 25,
                "radiusY": 25,
            }
        )

        assert canvas_model.canRedo is False

    def test_multiple_undo_redo_cycle(self, canvas_model):
        """Test multiple undo/redo operations work correctly."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 50,
                "centerY": 50,
                "radiusX": 25,
                "radiusY": 25,
            }
        )
        assert canvas_model.count() == 2

        canvas_model.undo()
        canvas_model.undo()
        assert canvas_model.count() == 0

        canvas_model.redo()
        assert canvas_model.count() == 1
        assert isinstance(canvas_model.getItems()[0], RectangleItem)

        canvas_model.redo()
        assert canvas_model.count() == 2

    def test_redo_stack_changed_signal(self, canvas_model, qtbot):
        """Test redoStackChanged signal is emitted appropriately."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )

        with qtbot.waitSignal(canvas_model.redoStackChanged, timeout=1000):
            canvas_model.undo()

        with qtbot.waitSignal(canvas_model.redoStackChanged, timeout=1000):
            canvas_model.redo()


class TestSelectionManagerLogic:
    """Unit-level tests mirroring SelectionManager delete handling."""

    def _attach_selection(self, canvas_model):
        state = SimpleNamespace(selectedItemIndex=-1, selectedItem=None)

        def on_modified(index, data):
            if index == state.selectedItemIndex:
                state.selectedItem = data

        def on_removed(index):
            if index == state.selectedItemIndex:
                state.selectedItemIndex = -1
                state.selectedItem = None
            elif index < state.selectedItemIndex:
                state.selectedItemIndex -= 1

        def on_cleared():
            state.selectedItemIndex = -1
            state.selectedItem = None

        canvas_model.itemModified.connect(on_modified)
        canvas_model.itemRemoved.connect(on_removed)
        canvas_model.itemsCleared.connect(on_cleared)
        return state

    def test_selection_clears_when_selected_item_removed(self, canvas_model):
        canvas_model.addLayer()
        sel = self._attach_selection(canvas_model)
        sel.selectedItemIndex = 0
        sel.selectedItem = canvas_model.getItemData(0)

        canvas_model.removeItem(0)

        assert sel.selectedItemIndex == -1
        assert sel.selectedItem is None

    def test_selection_clears_on_items_cleared(self, canvas_model):
        canvas_model.addLayer()
        sel = self._attach_selection(canvas_model)
        sel.selectedItemIndex = 0
        sel.selectedItem = canvas_model.getItemData(0)

        canvas_model.clear()

        assert sel.selectedItemIndex == -1
        assert sel.selectedItem is None


class TestCanvasModelAutoNames:
    """Tests for auto-generated item names."""

    def test_add_rectangle_generates_name(self, canvas_model):
        """First rectangle should be named 'Rectangle 1'."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        item = canvas_model.getItems()[0]
        assert item.name == "Rectangle 1"

    def test_add_ellipse_generates_name(self, canvas_model):
        """First ellipse should be named 'Ellipse 1'."""
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 0,
                "centerY": 0,
                "radiusX": 10,
                "radiusY": 10,
            }
        )
        item = canvas_model.getItems()[0]
        assert item.name == "Ellipse 1"

    def test_add_multiple_rectangles_increments_counter(self, canvas_model):
        """Multiple rectangles should get incrementing numbers."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {"type": "rectangle", "x": 40, "y": 0, "width": 10, "height": 10}
        )
        items = canvas_model.getItems()
        assert items[0].name == "Rectangle 1"
        assert items[1].name == "Rectangle 2"
        assert items[2].name == "Rectangle 3"

    def test_add_mixed_types_separate_counters(self, canvas_model):
        """Different types should have separate counters."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 0,
                "centerY": 0,
                "radiusX": 10,
                "radiusY": 10,
            }
        )
        canvas_model.addItem(
            {"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 20,
                "centerY": 0,
                "radiusX": 10,
                "radiusY": 10,
            }
        )
        items = canvas_model.getItems()
        assert items[0].name == "Rectangle 1"
        assert items[1].name == "Ellipse 1"
        assert items[2].name == "Rectangle 2"
        assert items[3].name == "Ellipse 2"

    def test_provided_name_not_overwritten(self, canvas_model):
        """If item data includes a name, it should be preserved."""
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 0,
                "y": 0,
                "width": 10,
                "height": 10,
                "name": "My Custom Rect",
            }
        )
        item = canvas_model.getItems()[0]
        assert item.name == "My Custom Rect"

    def test_name_preserved_in_getItemData(self, canvas_model):
        """getItemData should return the item name."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        data = canvas_model.getItemData(0)
        assert data["name"] == "Rectangle 1"

    def test_clear_resets_type_counters(self, canvas_model):
        """Clear should reset type counters so new items start from 1."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10}
        )
        assert canvas_model.getItems()[1].name == "Rectangle 2"

        canvas_model.clear()
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        assert canvas_model.getItems()[0].name == "Rectangle 1"


class TestCanvasModelLayers:
    """Tests for layer functionality in CanvasModel."""

    def test_add_layer_via_addItem(self, canvas_model, qtbot):
        """Test adding a layer using addItem with type 'layer'."""
        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000) as blocker:
            canvas_model.addItem({"type": "layer"})

        assert canvas_model.count() == 1
        assert blocker.args == [0]

        items = canvas_model.getItems()
        assert len(items) == 1
        assert isinstance(items[0], LayerItem)

    def test_add_layer_via_addLayer_slot(self, canvas_model, qtbot):
        """Test adding a layer using the addLayer convenience slot."""
        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            canvas_model.addLayer()

        assert canvas_model.count() == 1
        items = canvas_model.getItems()
        assert isinstance(items[0], LayerItem)

    def test_layer_gets_auto_generated_name(self, canvas_model):
        """Layers should get auto-generated names like 'Layer 1'."""
        canvas_model.addLayer()
        item = canvas_model.getItems()[0]
        assert item.name == "Layer 1"

    def test_multiple_layers_increment_counter(self, canvas_model):
        """Multiple layers should get incrementing numbers."""
        canvas_model.addLayer()
        canvas_model.addLayer()
        canvas_model.addLayer()
        items = canvas_model.getItems()
        assert items[0].name == "Layer 1"
        assert items[1].name == "Layer 2"
        assert items[2].name == "Layer 3"

    def test_layer_counter_separate_from_shapes(self, canvas_model):
        """Layer counter should be separate from rectangle/ellipse counters."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addLayer()
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 0,
                "centerY": 0,
                "radiusX": 10,
                "radiusY": 10,
            }
        )
        canvas_model.addLayer()

        items = canvas_model.getItems()
        assert items[0].name == "Rectangle 1"
        assert items[1].name == "Layer 1"
        assert items[2].name == "Ellipse 1"
        assert items[3].name == "Layer 2"

    def test_get_item_data_returns_layer_data(self, canvas_model):
        """getItemData should return layer type and name."""
        canvas_model.addLayer()
        data = canvas_model.getItemData(0)

        assert data is not None
        assert data["type"] == "layer"
        assert data["name"] == "Layer 1"

    def test_layer_type_role_returns_layer(self, canvas_model):
        """TypeRole should return 'layer' for LayerItem."""
        canvas_model.addLayer()
        index = canvas_model.index(0, 0)
        item_type = canvas_model.data(index, canvas_model.TypeRole)
        assert item_type == "layer"

    def test_layer_undo_redo(self, canvas_model):
        """Undo/redo should work for layer creation."""
        canvas_model.addLayer()
        assert canvas_model.count() == 1

        canvas_model.undo()
        assert canvas_model.count() == 0

        canvas_model.redo()
        assert canvas_model.count() == 1
        assert isinstance(canvas_model.getItems()[0], LayerItem)


class TestCanvasModelMoveItem:
    """Tests for moveItem reordering functionality."""

    def test_move_item_forward(self, canvas_model):
        """Move item from index 0 to index 2."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10}
        )

        canvas_model.moveItem(0, 2)

        items = canvas_model.getItems()
        assert items[0].name == "Rectangle 2"
        assert items[1].name == "Rectangle 3"
        assert items[2].name == "Rectangle 1"

    def test_move_item_backward(self, canvas_model):
        """Move item from index 2 to index 0."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10}
        )

        canvas_model.moveItem(2, 0)

        items = canvas_model.getItems()
        assert items[0].name == "Rectangle 3"
        assert items[1].name == "Rectangle 1"
        assert items[2].name == "Rectangle 2"

    def test_move_item_same_index_no_op(self, canvas_model, qtbot):
        """Moving item to same index should be a no-op."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10}
        )

        initial_can_undo = canvas_model.canUndo
        canvas_model.moveItem(1, 1)

        assert canvas_model.canUndo == initial_can_undo

    def test_move_item_invalid_from_index(self, canvas_model):
        """Invalid from index should do nothing."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        initial_can_undo = canvas_model.canUndo
        canvas_model.moveItem(-1, 0)
        canvas_model.moveItem(5, 0)

        assert canvas_model.canUndo == initial_can_undo

    def test_move_item_invalid_to_index(self, canvas_model):
        """Invalid to index should do nothing."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        initial_can_undo = canvas_model.canUndo
        canvas_model.moveItem(0, -1)
        canvas_model.moveItem(0, 5)

        assert canvas_model.canUndo == initial_can_undo

    def test_set_parent_invalid_index_is_noop(self, canvas_model):
        """setParent should no-op on invalid index."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]
        # Invalid indices should not raise or add undo entries
        initial_can_undo = canvas_model.canUndo
        canvas_model.setParent(-1, layer.id)
        canvas_model.setParent(99, layer.id)
        assert canvas_model.canUndo == initial_can_undo

    def test_move_item_emits_signal(self, canvas_model, qtbot):
        """moveItem should emit itemsReordered signal."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10}
        )

        with qtbot.waitSignal(canvas_model.itemsReordered, timeout=1000):
            canvas_model.moveItem(0, 1)

    def test_move_item_many_entries(self, canvas_model):
        """Reordering works with larger lists (UI scrolling should not affect model)."""
        for i in range(20):
            canvas_model.addItem(
                {"type": "rectangle", "x": i, "y": i, "width": 10, "height": 10}
            )

        from_index = 18
        to_index = 1
        canvas_model.moveItem(from_index, to_index)

        items = canvas_model.getItems()
        assert items[to_index].x == 18

    def test_move_item_many_entries_reverse(self, canvas_model):
        """Reordering near the top when list is long still works."""
        for i in range(25):
            canvas_model.addItem(
                {"type": "rectangle", "x": i, "y": i, "width": 10, "height": 10}
            )

        from_index = 2
        to_index = 20
        canvas_model.moveItem(from_index, to_index)

        items = canvas_model.getItems()
        assert items[to_index].x == 2

    def test_move_item_undo(self, canvas_model):
        """Undo should restore original order."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10}
        )

        canvas_model.moveItem(0, 2)
        canvas_model.undo()

        items = canvas_model.getItems()
        assert items[0].name == "Rectangle 1"
        assert items[1].name == "Rectangle 2"
        assert items[2].name == "Rectangle 3"

    def test_move_item_redo(self, canvas_model):
        """Redo should restore moved order."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10}
        )

        canvas_model.moveItem(0, 2)
        canvas_model.undo()
        canvas_model.redo()

        items = canvas_model.getItems()
        assert items[0].name == "Rectangle 2"
        assert items[1].name == "Rectangle 3"
        assert items[2].name == "Rectangle 1"


class TestCanvasModelListModel:
    """Tests for QAbstractListModel behavior."""

    def test_row_count_matches_item_count(self, canvas_model):
        """rowCount should match number of items."""
        from PySide6.QtCore import QModelIndex

        assert canvas_model.rowCount(QModelIndex()) == 0

        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        assert canvas_model.rowCount(QModelIndex()) == 1

        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 0,
                "centerY": 0,
                "radiusX": 10,
                "radiusY": 10,
            }
        )
        assert canvas_model.rowCount(QModelIndex()) == 2

    def test_data_returns_name_role(self, canvas_model):
        """data() should return item name for NameRole."""
        from PySide6.QtCore import Qt

        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        index = canvas_model.index(0, 0)
        name = canvas_model.data(index, canvas_model.NameRole)
        assert name == "Rectangle 1"

    def test_data_returns_type_role(self, canvas_model):
        """data() should return item type for TypeRole."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        index = canvas_model.index(0, 0)
        item_type = canvas_model.data(index, canvas_model.TypeRole)
        assert item_type == "rectangle"

    def test_role_names_exposed(self, canvas_model):
        """roleNames should map roles to QML property names."""
        role_names = canvas_model.roleNames()

        assert canvas_model.NameRole in role_names
        assert canvas_model.TypeRole in role_names
        assert role_names[canvas_model.NameRole] == b"name"
        assert role_names[canvas_model.TypeRole] == b"itemType"

    def test_add_item_emits_rows_inserted(self, canvas_model, qtbot):
        """addItem should emit rowsInserted signal."""
        with qtbot.waitSignal(canvas_model.rowsInserted, timeout=1000) as blocker:
            canvas_model.addItem(
                {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
            )

        parent, first, last = blocker.args
        assert first == 0
        assert last == 0

    def test_remove_item_emits_rows_removed(self, canvas_model, qtbot):
        """removeItem should emit rowsRemoved signal."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        with qtbot.waitSignal(canvas_model.rowsRemoved, timeout=1000) as blocker:
            canvas_model.removeItem(0)

        parent, first, last = blocker.args
        assert first == 0
        assert last == 0

    def test_move_item_emits_rows_moved(self, canvas_model, qtbot):
        """moveItem should emit rowsMoved signal."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10}
        )

        with qtbot.waitSignal(canvas_model.rowsMoved, timeout=1000):
            canvas_model.moveItem(0, 2)

    def test_clear_emits_model_reset(self, canvas_model, qtbot):
        """clear should emit modelReset signal."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 0,
                "centerY": 0,
                "radiusX": 10,
                "radiusY": 10,
            }
        )

        with qtbot.waitSignal(canvas_model.modelReset, timeout=1000):
            canvas_model.clear()

    def test_data_changed_on_update(self, canvas_model, qtbot):
        """updateItem should emit dataChanged signal."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        with qtbot.waitSignal(canvas_model.dataChanged, timeout=1000):
            canvas_model.updateItem(0, {"x": 50})


class TestCanvasModelParentChild:
    """Tests for parent-child relationships between layers and shapes."""

    def test_shape_has_no_parent_by_default(self, canvas_model):
        """Shapes should have no parent by default."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        item = canvas_model.getItems()[0]
        assert item.parent_id is None

    def test_layer_has_unique_id(self, canvas_model):
        """Layers should have a unique ID."""
        canvas_model.addLayer()
        item = canvas_model.getItems()[0]
        assert item.id is not None
        assert len(item.id) > 0

    def test_multiple_layers_have_different_ids(self, canvas_model):
        """Multiple layers should have different IDs."""
        canvas_model.addLayer()
        canvas_model.addLayer()
        items = canvas_model.getItems()
        assert items[0].id != items[1].id

    def test_set_parent_assigns_parent_id(self, canvas_model):
        """setParent should assign parent_id to shape."""
        canvas_model.addLayer()
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        layer = canvas_model.getItems()[0]
        canvas_model.setParent(1, layer.id)

        shape = canvas_model.getItems()[1]
        assert shape.parent_id == layer.id

    def test_set_parent_empty_string_clears_parent(self, canvas_model):
        """setParent with empty string should clear parent_id."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 0,
                "y": 0,
                "width": 10,
                "height": 10,
                "parentId": layer.id,
            }
        )

        shape = canvas_model.getItems()[1]
        assert shape.parent_id == layer.id

        canvas_model.setParent(1, "")

        shape = canvas_model.getItems()[1]
        assert shape.parent_id is None

    def test_set_parent_on_layer_does_nothing(self, canvas_model):
        """setParent on a layer should do nothing (layers can't have parents)."""
        canvas_model.addLayer()
        canvas_model.addLayer()

        layer1 = canvas_model.getItems()[0]
        layer2 = canvas_model.getItems()[1]

        canvas_model.setParent(1, layer1.id)

        # Layer 2 should still have no parent-like property
        assert (
            not hasattr(layer2, "parent_id")
            or getattr(layer2, "parent_id", None) is None
        )

    def test_item_data_includes_parent_id(self, canvas_model):
        """getItemData should include parentId for shapes."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.setParent(1, layer.id)

        data = canvas_model.getItemData(1)
        assert data["parentId"] == layer.id

    def test_layer_data_includes_id(self, canvas_model):
        """getItemData should include id for layers."""
        canvas_model.addLayer()
        data = canvas_model.getItemData(0)

        assert "id" in data
        assert data["id"] is not None

    def test_parent_id_role_returns_parent_id(self, canvas_model):
        """ParentIdRole should return the parent_id of a shape."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.setParent(1, layer.id)

        index = canvas_model.index(1, 0)
        parent_id = canvas_model.data(index, canvas_model.ParentIdRole)
        assert parent_id == layer.id

    def test_item_id_role_returns_layer_id(self, canvas_model):
        """ItemIdRole should return the id of a layer."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]

        index = canvas_model.index(0, 0)
        item_id = canvas_model.data(index, canvas_model.ItemIdRole)
        assert item_id == layer.id

    def test_parent_id_role_returns_none_for_layers(self, canvas_model):
        """ParentIdRole should return None for layers."""
        canvas_model.addLayer()

        index = canvas_model.index(0, 0)
        parent_id = canvas_model.data(index, canvas_model.ParentIdRole)
        assert parent_id is None

    def test_item_id_role_returns_none_for_shapes(self, canvas_model):
        """ItemIdRole should return None for shapes."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        index = canvas_model.index(0, 0)
        item_id = canvas_model.data(index, canvas_model.ItemIdRole)
        assert item_id is None

    def test_get_layer_index_finds_layer(self, canvas_model):
        """getLayerIndex should return the index of a layer by ID."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addLayer()
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 0,
                "centerY": 0,
                "radiusX": 10,
                "radiusY": 10,
            }
        )

        layer = canvas_model.getItems()[1]
        index = canvas_model.getLayerIndex(layer.id)
        assert index == 1

    def test_get_layer_index_returns_negative_for_invalid_id(self, canvas_model):
        """getLayerIndex should return -1 for non-existent ID."""
        canvas_model.addLayer()

        index = canvas_model.getLayerIndex("non-existent-id")
        assert index == -1

    def test_set_parent_undo_restores_original_parent(self, canvas_model):
        """Undo of setParent should restore the original parent_id."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        # Shape has no parent initially
        assert canvas_model.getItems()[1].parent_id is None

        canvas_model.setParent(1, layer.id)
        assert canvas_model.getItems()[1].parent_id == layer.id

        canvas_model.undo()
        assert canvas_model.getItems()[1].parent_id is None

    def test_set_parent_redo_restores_new_parent(self, canvas_model):
        """Redo of setParent should restore the new parent_id."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        canvas_model.setParent(1, layer.id)
        canvas_model.undo()
        canvas_model.redo()

        assert canvas_model.getItems()[1].parent_id == layer.id


class TestCanvasModelLayerDeletion:
    """Tests for layer deletion behavior (children removed with layer)."""

    def test_delete_layer_removes_children(self, canvas_model):
        """Deleting a layer should remove its children."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.setParent(1, layer.id)

        # Verify child is parented
        assert canvas_model.getItems()[1].parent_id == layer.id

        # Delete the layer
        canvas_model.removeItem(0)

        # Layer and child removed
        assert canvas_model.count() == 0

    def test_delete_layer_with_multiple_children_removes_them(self, canvas_model):
        """Deleting a layer should remove all its children, leaving other items intact."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]

        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 0,
                "centerY": 0,
                "radiusX": 10,
                "radiusY": 10,
            }
        )
        canvas_model.addItem(
            {"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10}
        )

        canvas_model.setParent(1, layer.id)
        canvas_model.setParent(2, layer.id)
        # Item 3 remains top-level

        canvas_model.removeItem(0)

        items = canvas_model.getItems()
        # Only the previously top-level item should remain
        assert len(items) == 1
        assert isinstance(items[0], RectangleItem)
        assert items[0].parent_id is None


class TestCanvasModelShapeDeletion:
    """Tests for deleting non-layer items."""

    def test_delete_shape_removes_only_that_shape(self, canvas_model, qtbot):
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {"type": "ellipse", "centerX": 0, "centerY": 0, "radiusX": 5, "radiusY": 5}
        )
        assert canvas_model.count() == 2

        with qtbot.waitSignal(canvas_model.itemRemoved, timeout=1000) as blocker:
            canvas_model.removeItem(0)

        assert blocker.args == [0]
        assert canvas_model.count() == 1
        remaining = canvas_model.getItems()[0]
        assert isinstance(remaining, EllipseItem)

    def test_delete_shape_updates_selection(self, canvas_model):
        selection = {"index": -1, "item": None}

        def on_modified(index, data):
            if index == selection["index"]:
                selection["item"] = data

        def on_removed(index):
            if index == selection["index"]:
                selection["index"] = -1
                selection["item"] = None
            elif index < selection["index"]:
                selection["index"] -= 1

        def on_cleared():
            selection["index"] = -1
            selection["item"] = None

        canvas_model.itemModified.connect(on_modified)
        canvas_model.itemRemoved.connect(on_removed)
        canvas_model.itemsCleared.connect(on_cleared)

        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {"type": "ellipse", "centerX": 0, "centerY": 0, "radiusX": 5, "radiusY": 5}
        )

        selection["index"] = 1
        selection["item"] = canvas_model.getItemData(1)

        canvas_model.removeItem(1)

        assert selection["index"] == -1
        assert selection["item"] is None


class TestCanvasModelVisibility:
    """Tests for visibility toggling and cascading."""

    def test_items_default_visible(self, canvas_model):
        canvas_model.addLayer()
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        assert canvas_model.getItems()[0].visible is True
        assert canvas_model.getItems()[1].visible is True

    def test_roles_include_visibility(self, canvas_model):
        role_names = canvas_model.roleNames()
        assert canvas_model.VisibleRole in role_names
        assert canvas_model.EffectiveVisibleRole in role_names
        assert role_names[canvas_model.VisibleRole] == b"modelVisible"
        assert role_names[canvas_model.EffectiveVisibleRole] == b"modelEffectiveVisible"

    def test_toggle_shape_visibility(self, canvas_model, qtbot):
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000) as blocker:
            canvas_model.toggleVisibility(0)

        assert blocker.args[0] == 0
        assert blocker.args[1]["visible"] is False
        assert canvas_model.getItems()[0].visible is False

        canvas_model.undo()
        assert canvas_model.getItems()[0].visible is True

        canvas_model.redo()
        assert canvas_model.getItems()[0].visible is False

    def test_toggle_layer_hides_children_effectively(self, canvas_model):
        canvas_model.addLayer()
        layer_id = canvas_model.getItems()[0].id
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.setParent(1, layer_id)

        # initial render includes child
        assert len(canvas_model.getRenderItems()) == 1

        canvas_model.toggleVisibility(0)
        # Layer visible flag false, child remains true but should not render
        assert canvas_model.getItems()[0].visible is False
        assert canvas_model.getItems()[1].visible is True
        assert len(canvas_model.getRenderItems()) == 0

        # Undo restores visibility and render
        canvas_model.undo()
        assert canvas_model.getItems()[0].visible is True
        assert len(canvas_model.getRenderItems()) == 1
        hit = canvas_model.getItemsForHitTest()
        assert len(hit) == 2

    def test_invalid_toggle_is_noop(self, canvas_model):
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        initial_can_undo = canvas_model.canUndo
        canvas_model.toggleVisibility(-1)
        canvas_model.toggleVisibility(5)
        assert canvas_model.canUndo == initial_can_undo

    def test_parent_hidden_effective_visibility_false_for_child(self, canvas_model):
        canvas_model.addLayer()
        layer_id = canvas_model.getItems()[0].id
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.setParent(1, layer_id)

        canvas_model.toggleVisibility(0)  # hide layer

        idx_child = canvas_model.index(1, 0)
        assert canvas_model.data(idx_child, canvas_model.VisibleRole) is True
        assert canvas_model.data(idx_child, canvas_model.EffectiveVisibleRole) is False
        assert canvas_model.getItemsForHitTest() == []  # hidden via parent

    def test_undo_delete_layer_restores_parent_relationships(self, canvas_model):
        """Undo of layer deletion should restore children's parent_id."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]
        layer_id = layer.id

        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.setParent(1, layer_id)

        canvas_model.removeItem(0)
        canvas_model.undo()

        # Layer should be back
        assert canvas_model.count() == 2
        restored_layer = canvas_model.getItems()[0]
        assert isinstance(restored_layer, LayerItem)

        # Child should have parent restored
        shape = canvas_model.getItems()[1]
        assert shape.parent_id == layer_id

    def test_delete_non_layer_does_not_affect_siblings(self, canvas_model):
        """Deleting a shape should not affect other shapes' parent_id."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]

        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 0,
                "centerY": 0,
                "radiusX": 10,
                "radiusY": 10,
            }
        )

        canvas_model.setParent(1, layer.id)
        canvas_model.setParent(2, layer.id)

        # Delete the rectangle (index 1)
        canvas_model.removeItem(1)

        # Ellipse should still be parented
        ellipse = canvas_model.getItems()[1]
        assert ellipse.parent_id == layer.id


class TestCanvasModelReparentItem:
    """Tests for reparentItem which combines setParent + moveItem."""

    def test_reparent_sets_parent_id(self, canvas_model):
        """reparentItem should set the parent_id on the shape."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        canvas_model.reparentItem(1, layer.id)

        shape = canvas_model.getItems()[1]
        assert shape.parent_id == layer.id

    def test_reparent_moves_item_after_layer(self, canvas_model):
        """reparentItem should move shape to be last child of layer."""
        # Setup: Layer at 0, shapes at 1, 2, 3
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )  # Rect 1
        canvas_model.addItem(
            {"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10}
        )  # Rect 2
        canvas_model.addItem(
            {"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10}
        )  # Rect 3

        # Reparent Rect 3 (index 3) to layer
        canvas_model.reparentItem(3, layer.id)

        # Rect 3 should now be at index 1 (right after layer)
        items = canvas_model.getItems()
        assert items[0].name == "Layer 1"
        assert items[1].name == "Rectangle 3"
        assert items[1].parent_id == layer.id
        assert items[2].name == "Rectangle 1"
        assert items[3].name == "Rectangle 2"

    def test_reparent_to_layer_with_existing_children(self, canvas_model):
        """reparentItem should place new child after existing children."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]

        # Add shapes and parent first two to layer
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )  # Rect 1
        canvas_model.addItem(
            {"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10}
        )  # Rect 2
        canvas_model.addItem(
            {"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10}
        )  # Rect 3

        # Parent Rect 1 to layer
        canvas_model.reparentItem(1, layer.id)

        # Now parent Rect 3 to layer (it should go after Rect 1)
        canvas_model.reparentItem(3, layer.id)

        items = canvas_model.getItems()
        assert items[0].name == "Layer 1"
        assert items[1].name == "Rectangle 1"
        assert items[1].parent_id == layer.id
        assert items[2].name == "Rectangle 3"
        assert items[2].parent_id == layer.id
        assert items[3].name == "Rectangle 2"
        assert items[3].parent_id is None

    def test_reparent_unparent_clears_parent_id(self, canvas_model):
        """reparentItem with empty string should clear parent_id."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        # Parent then unparent
        canvas_model.reparentItem(1, layer.id)
        assert canvas_model.getItems()[1].parent_id == layer.id

        canvas_model.reparentItem(1, "")
        assert canvas_model.getItems()[1].parent_id is None

    def test_reparent_on_layer_does_nothing(self, canvas_model):
        """reparentItem on a layer should do nothing."""
        canvas_model.addLayer()
        canvas_model.addLayer()

        layer1 = canvas_model.getItems()[0]
        layer2 = canvas_model.getItems()[1]

        initial_can_undo = canvas_model.canUndo
        canvas_model.reparentItem(1, layer1.id)

        # No command should be added
        assert canvas_model.canUndo == initial_can_undo

    def test_reparent_same_parent_does_nothing(self, canvas_model):
        """reparentItem to same parent should do nothing."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        canvas_model.reparentItem(1, layer.id)
        initial_can_undo = canvas_model.canUndo

        # Reparent to same layer
        canvas_model.reparentItem(1, layer.id)

        # No additional command should be added
        assert canvas_model.canUndo == initial_can_undo

    def test_reparent_undo_restores_parent_and_position(self, canvas_model):
        """Undo of reparentItem should restore both parent and position."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )  # Rect 1
        canvas_model.addItem(
            {"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10}
        )  # Rect 2

        # Rect 2 is at index 2, no parent
        assert canvas_model.getItems()[2].name == "Rectangle 2"
        assert canvas_model.getItems()[2].parent_id is None

        # Reparent Rect 2 to layer
        canvas_model.reparentItem(2, layer.id)

        # Rect 2 should be at index 1 with parent
        assert canvas_model.getItems()[1].name == "Rectangle 2"
        assert canvas_model.getItems()[1].parent_id == layer.id

        # Undo
        canvas_model.undo()

        # Rect 2 should be back at index 2 with no parent
        assert canvas_model.getItems()[2].name == "Rectangle 2"
        assert canvas_model.getItems()[2].parent_id is None

    def test_reparent_redo_restores_parent_and_position(self, canvas_model):
        """Redo of reparentItem should restore both parent and position."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )  # Rect 1
        canvas_model.addItem(
            {"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10}
        )  # Rect 2

        canvas_model.reparentItem(2, layer.id)
        canvas_model.undo()
        canvas_model.redo()

        # Rect 2 should be at index 1 with parent
        assert canvas_model.getItems()[1].name == "Rectangle 2"
        assert canvas_model.getItems()[1].parent_id == layer.id

    def test_reparent_invalid_index_does_nothing(self, canvas_model):
        """reparentItem with invalid index should do nothing."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]

        initial_can_undo = canvas_model.canUndo
        canvas_model.reparentItem(-1, layer.id)
        canvas_model.reparentItem(10, layer.id)

        assert canvas_model.canUndo == initial_can_undo

    def test_find_last_child_position_no_children(self, canvas_model):
        """_findLastChildPosition should return position after layer when no children."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )  # Top-level

        # Layer at 0, Rect at 1 (top-level)
        pos = canvas_model._findLastChildPosition(layer.id)
        assert pos == 1  # Should insert before the top-level rect

    def test_find_last_child_position_with_children(self, canvas_model):
        """_findLastChildPosition should return position after last child."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]

        # Add child to layer
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.setParent(1, layer.id)

        # Add top-level shape
        canvas_model.addItem(
            {"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10}
        )

        # Layer at 0, child at 1, top-level at 2
        pos = canvas_model._findLastChildPosition(layer.id)
        assert pos == 2  # Should insert before the top-level rect

    def test_find_last_child_position_at_end(self, canvas_model):
        """_findLastChildPosition should return end of list if no top-level after layer."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )  # Top-level
        canvas_model.addLayer()
        layer = canvas_model.getItems()[1]

        # Top-level at 0, Layer at 1
        pos = canvas_model._findLastChildPosition(layer.id)
        assert pos == 2  # Should insert at end


class TestLayerMoveWithChildren:
    """Tests for moving layers with their children as a group."""

    def test_move_layer_with_one_child_up(self, canvas_model):
        """Moving a layer up should move its child with it."""
        # Create: Layer1, Rect1 (child of Layer1), Layer2, Rect2 (child of Layer2)
        canvas_model.addLayer()
        layer1 = canvas_model.getItems()[0]
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 0,
                "y": 0,
                "width": 10,
                "height": 10,
                "name": "Rect1",
            }
        )
        canvas_model.setParent(1, layer1.id)

        canvas_model.addLayer()
        layer2 = canvas_model.getItems()[2]
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 20,
                "y": 0,
                "width": 10,
                "height": 10,
                "name": "Rect2",
            }
        )
        canvas_model.setParent(3, layer2.id)

        # Order: [Layer1, Rect1, Layer2, Rect2]
        assert canvas_model.getItems()[0].name == "Layer 1"
        assert canvas_model.getItems()[1].name == "Rect1"
        assert canvas_model.getItems()[2].name == "Layer 2"
        assert canvas_model.getItems()[3].name == "Rect2"

        # Move Layer2 up (from index 2 to index 0)
        canvas_model.moveItem(2, 0)

        # Order should now be: [Layer2, Rect2, Layer1, Rect1]
        items = canvas_model.getItems()
        assert items[0].name == "Layer 2"
        assert items[1].name == "Rect2"
        assert items[1].parent_id == layer2.id
        assert items[2].name == "Layer 1"
        assert items[3].name == "Rect1"
        assert items[3].parent_id == layer1.id

    def test_move_layer_with_multiple_children(self, canvas_model):
        """Moving a layer should move all its children with it."""
        # Create: Layer1 with 2 children, then Layer2
        canvas_model.addLayer()
        layer1 = canvas_model.getItems()[0]
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 0,
                "y": 0,
                "width": 10,
                "height": 10,
                "name": "Rect1",
            }
        )
        canvas_model.setParent(1, layer1.id)
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 5,
                "centerY": 5,
                "radiusX": 5,
                "radiusY": 5,
                "name": "Ellipse1",
            }
        )
        canvas_model.setParent(2, layer1.id)

        canvas_model.addLayer()
        layer2 = canvas_model.getItems()[3]

        # Order: [Layer1, Rect1, Ellipse1, Layer2]
        assert canvas_model.count() == 4

        # Move Layer1 down (to index 3, after Layer2)
        canvas_model.moveItem(0, 3)

        # Order should now be: [Layer2, Layer1, Rect1, Ellipse1]
        items = canvas_model.getItems()
        assert items[0].name == "Layer 2"
        assert items[1].name == "Layer 1"
        assert items[2].name == "Rect1"
        assert items[2].parent_id == layer1.id
        assert items[3].name == "Ellipse1"
        assert items[3].parent_id == layer1.id

    def test_move_layer_without_children_uses_regular_move(self, canvas_model):
        """Moving a layer without children should just move the layer."""
        canvas_model.addLayer()
        canvas_model.addLayer()
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 0,
                "y": 0,
                "width": 10,
                "height": 10,
                "name": "Rect1",
            }
        )

        # Order: [Layer1, Layer2, Rect1]
        # Move Layer2 to position 0
        canvas_model.moveItem(1, 0)

        items = canvas_model.getItems()
        assert items[0].name == "Layer 2"
        assert items[1].name == "Layer 1"
        assert items[2].name == "Rect1"

    def test_get_layer_children_indices(self, canvas_model):
        """_getLayerChildrenIndices should find all children of a layer."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]

        # Add children
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.setParent(1, layer.id)
        canvas_model.addItem(
            {"type": "ellipse", "centerX": 5, "centerY": 5, "radiusX": 5, "radiusY": 5}
        )
        canvas_model.setParent(2, layer.id)

        # Add unrelated item
        canvas_model.addItem(
            {"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10}
        )

        children = canvas_model._getLayerChildrenIndices(layer.id)
        assert children == [1, 2]

    def test_move_child_within_layer_does_not_trigger_group_move(self, canvas_model):
        """Moving a non-layer item should not trigger _moveLayerWithChildren."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]

        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 0,
                "y": 0,
                "width": 10,
                "height": 10,
                "name": "Rect1",
            }
        )
        canvas_model.setParent(1, layer.id)
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 10,
                "y": 0,
                "width": 10,
                "height": 10,
                "name": "Rect2",
            }
        )
        canvas_model.setParent(2, layer.id)

        # Order: [Layer, Rect1, Rect2]
        # Move Rect2 before Rect1 (index 2 to 1)
        canvas_model.moveItem(2, 1)

        items = canvas_model.getItems()
        assert items[0].name == "Layer 1"
        assert items[1].name == "Rect2"
        assert items[2].name == "Rect1"


class TestZOrderRendering:
    """Tests for z-order (render order) behavior."""

    def test_get_render_items_matches_reverse_shapes(self, canvas_model):
        """Model should expose a unified render order helper."""
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 0,
                "y": 0,
                "width": 10,
                "height": 10,
                "name": "Bottom",
            }
        )
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 5,
                "y": 5,
                "width": 10,
                "height": 10,
                "name": "Top",
            }
        )

        ordered = canvas_model.getRenderItems()
        # Render order is bottom-to-top, reversed model order for shapes
        assert [item.name for item in ordered] == ["Top", "Bottom"]

    def test_render_order_reversed_from_model(self, canvas_model):
        """Items at lower model indices should render last (on top)."""
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 0,
                "y": 0,
                "width": 10,
                "height": 10,
                "name": "Bottom",
            }
        )
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 5,
                "y": 5,
                "width": 10,
                "height": 10,
                "name": "Top",
            }
        )

        items = canvas_model.getItems()
        # Model order: [Bottom (idx 0), Top (idx 1)]
        assert items[0].name == "Bottom"
        assert items[1].name == "Top"

        # Render order should be reversed: Top renders last (on top)
        # This is verified by canvas_renderer which reverses the order

    def test_move_item_up_changes_z_order(self, canvas_model):
        """Moving an item to a lower index should move it above other items."""
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 0,
                "y": 0,
                "width": 10,
                "height": 10,
                "name": "A",
            }
        )
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 5,
                "y": 5,
                "width": 10,
                "height": 10,
                "name": "B",
            }
        )
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 10,
                "y": 10,
                "width": 10,
                "height": 10,
                "name": "C",
            }
        )

        # Initial order: [A, B, C] (A is on top)
        # Move C to top (index 2 -> 0)
        canvas_model.moveItem(2, 0)

        items = canvas_model.getItems()
        assert items[0].name == "C"  # C is now at top (lowest index = on top visually)
        assert items[1].name == "A"
        assert items[2].name == "B"

    def test_layer_children_grouped_in_z_order(self, canvas_model):
        """Children of a layer should remain grouped with their parent in z-order."""
        canvas_model.addLayer()
        layer1 = canvas_model.getItems()[0]
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 0,
                "y": 0,
                "width": 10,
                "height": 10,
                "name": "Child1",
            }
        )
        canvas_model.setParent(1, layer1.id)

        canvas_model.addLayer()
        layer2 = canvas_model.getItems()[2]
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 20,
                "y": 0,
                "width": 10,
                "height": 10,
                "name": "Child2",
            }
        )
        canvas_model.setParent(3, layer2.id)

        # Order: [Layer1, Child1, Layer2, Child2]
        # Layer1 and its children should be "above" Layer2 and its children

        # Move Layer2 to top (index 2 -> 0)
        canvas_model.moveItem(2, 0)

        items = canvas_model.getItems()
        # New order: [Layer2, Child2, Layer1, Child1]
        assert items[0].name == "Layer 2"
        assert items[1].name == "Child2"
        assert items[1].parent_id == layer2.id
        assert items[2].name == "Layer 1"
        assert items[3].name == "Child1"
        assert items[3].parent_id == layer1.id


class TestLockedFunctionality:
    """Tests for object lock feature."""

    def test_locked_role_exists(self, canvas_model):
        """LockedRole should be defined in role names."""
        role_names = canvas_model.roleNames()
        assert canvas_model.LockedRole in role_names
        assert role_names[canvas_model.LockedRole] == b"modelLocked"

    def test_locked_role_returns_false_by_default(self, canvas_model):
        """LockedRole should return False for new items."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        idx = canvas_model.index(0, 0)
        assert canvas_model.data(idx, canvas_model.LockedRole) is False

    def test_toggle_locked_sets_locked_true(self, canvas_model, qtbot):
        """toggleLocked should toggle item's locked state."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000) as blocker:
            canvas_model.toggleLocked(0)

        assert blocker.args[0] == 0
        assert blocker.args[1]["locked"] is True
        assert canvas_model.getItems()[0].locked is True

    def test_toggle_locked_toggles_back_to_false(self, canvas_model):
        """toggleLocked should toggle locked from True back to False."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.toggleLocked(0)
        assert canvas_model.getItems()[0].locked is True

        canvas_model.toggleLocked(0)
        assert canvas_model.getItems()[0].locked is False

    def test_toggle_locked_supports_undo_redo(self, canvas_model):
        """toggleLocked should support undo/redo."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.toggleLocked(0)
        assert canvas_model.getItems()[0].locked is True

        canvas_model.undo()
        assert canvas_model.getItems()[0].locked is False

        canvas_model.redo()
        assert canvas_model.getItems()[0].locked is True

    def test_toggle_locked_invalid_index_is_noop(self, canvas_model):
        """toggleLocked with invalid index should do nothing."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        initial_can_undo = canvas_model.canUndo
        canvas_model.toggleLocked(-1)
        canvas_model.toggleLocked(5)
        assert canvas_model.canUndo == initial_can_undo

    def test_toggle_locked_on_layer(self, canvas_model):
        """toggleLocked should work on layers."""
        canvas_model.addLayer()
        canvas_model.toggleLocked(0)
        assert canvas_model.getItems()[0].locked is True

    def test_toggle_locked_on_ellipse(self, canvas_model):
        """toggleLocked should work on ellipses."""
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 0,
                "centerY": 0,
                "radiusX": 10,
                "radiusY": 10,
            }
        )
        canvas_model.toggleLocked(0)
        assert canvas_model.getItems()[0].locked is True

    def test_locked_role_returns_true_after_toggle(self, canvas_model):
        """LockedRole should return True after toggleLocked."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.toggleLocked(0)
        idx = canvas_model.index(0, 0)
        assert canvas_model.data(idx, canvas_model.LockedRole) is True

    def test_get_item_data_includes_locked(self, canvas_model):
        """getItemData should include locked property."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.toggleLocked(0)
        data = canvas_model.getItemData(0)
        assert data["locked"] is True

    def test_locked_items_still_in_hit_test(self, canvas_model):
        """Locked items should still appear in getItemsForHitTest (unlike hidden)."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.toggleLocked(0)
        hit_items = canvas_model.getItemsForHitTest()
        assert len(hit_items) == 1


class TestEffectiveLockedFunctionality:
    """Tests for effective locked behavior (children inherit parent layer's locked state)."""

    def test_effective_locked_role_exists(self, canvas_model):
        """EffectiveLockedRole should be defined in role names."""
        role_names = canvas_model.roleNames()
        assert canvas_model.EffectiveLockedRole in role_names
        assert role_names[canvas_model.EffectiveLockedRole] == b"modelEffectiveLocked"

    def test_effective_locked_false_by_default(self, canvas_model):
        """EffectiveLockedRole should return False for unlocked items."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        idx = canvas_model.index(0, 0)
        assert canvas_model.data(idx, canvas_model.EffectiveLockedRole) is False

    def test_effective_locked_true_when_item_locked(self, canvas_model):
        """EffectiveLockedRole should return True when item itself is locked."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.toggleLocked(0)
        idx = canvas_model.index(0, 0)
        assert canvas_model.data(idx, canvas_model.EffectiveLockedRole) is True

    def test_child_effective_locked_when_parent_layer_locked(self, canvas_model):
        """Child should be effectively locked when parent layer is locked."""
        canvas_model.addLayer()
        layer_id = canvas_model.getItems()[0].id
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.setParent(1, layer_id)

        # Lock the parent layer
        canvas_model.toggleLocked(0)

        # Child's own locked is False, but effective locked should be True
        idx_child = canvas_model.index(1, 0)
        assert canvas_model.data(idx_child, canvas_model.LockedRole) is False
        assert canvas_model.data(idx_child, canvas_model.EffectiveLockedRole) is True

    def test_child_not_effective_locked_when_parent_unlocked(self, canvas_model):
        """Child should not be effectively locked when parent layer is unlocked."""
        canvas_model.addLayer()
        layer_id = canvas_model.getItems()[0].id
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.setParent(1, layer_id)

        # Parent layer is not locked
        idx_child = canvas_model.index(1, 0)
        assert canvas_model.data(idx_child, canvas_model.EffectiveLockedRole) is False

    def test_unlocking_parent_restores_child_effective_state(self, canvas_model):
        """Unlocking parent layer should restore child's effective locked state."""
        canvas_model.addLayer()
        layer_id = canvas_model.getItems()[0].id
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.setParent(1, layer_id)

        # Lock parent, then unlock
        canvas_model.toggleLocked(0)
        idx_child = canvas_model.index(1, 0)
        assert canvas_model.data(idx_child, canvas_model.EffectiveLockedRole) is True

        canvas_model.toggleLocked(0)  # Unlock parent
        assert canvas_model.data(idx_child, canvas_model.EffectiveLockedRole) is False

    def test_child_locked_independently_of_parent(self, canvas_model):
        """Child can be locked independently even when parent is unlocked."""
        canvas_model.addLayer()
        layer_id = canvas_model.getItems()[0].id
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.setParent(1, layer_id)

        # Lock only the child
        canvas_model.toggleLocked(1)

        idx_child = canvas_model.index(1, 0)
        assert canvas_model.data(idx_child, canvas_model.LockedRole) is True
        assert canvas_model.data(idx_child, canvas_model.EffectiveLockedRole) is True

    def test_layer_effective_locked_equals_own_locked(self, canvas_model):
        """Layer's effective locked should equal its own locked (no parent)."""
        canvas_model.addLayer()
        idx = canvas_model.index(0, 0)
        assert canvas_model.data(idx, canvas_model.EffectiveLockedRole) is False

        canvas_model.toggleLocked(0)
        assert canvas_model.data(idx, canvas_model.EffectiveLockedRole) is True


class TestCoverageEdgeCases:
    """Tests for edge cases and guard clauses to improve coverage."""

    def test_row_count_with_valid_parent_returns_zero(self, canvas_model):
        """rowCount returns 0 for hierarchical parent (flat model)."""
        from PySide6.QtCore import QModelIndex

        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        parent_idx = canvas_model.index(0, 0)
        assert canvas_model.rowCount(parent_idx) == 0

    def test_type_role_returns_ellipse(self, canvas_model):
        """TypeRole returns 'ellipse' for EllipseItem."""
        canvas_model.addItem(
            {"type": "ellipse", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        idx = canvas_model.index(0, 0)
        assert canvas_model.data(idx, canvas_model.TypeRole) == "ellipse"

    def test_index_role_returns_row(self, canvas_model):
        """IndexRole returns the item's row index."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        idx = canvas_model.index(1, 0)
        assert canvas_model.data(idx, canvas_model.IndexRole) == 1

    def test_unhandled_role_returns_none(self, canvas_model):
        """Unhandled role returns None."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        idx = canvas_model.index(0, 0)
        # Use a role that doesn't exist
        fake_role = 9999
        assert canvas_model.data(idx, fake_role) is None

    def test_is_effectively_locked_slot(self, canvas_model):
        """isEffectivelyLocked slot returns correct value."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        assert canvas_model.isEffectivelyLocked(0) is False
        canvas_model.toggleLocked(0)
        assert canvas_model.isEffectivelyLocked(0) is True

    def test_is_effectively_locked_invalid_index(self, canvas_model):
        """isEffectivelyLocked returns False for invalid index."""
        assert canvas_model.isEffectivelyLocked(-1) is False
        assert canvas_model.isEffectivelyLocked(999) is False

    def test_is_layer_locked_nonexistent_layer(self, canvas_model):
        """_is_layer_locked returns False for nonexistent layer ID."""
        canvas_model.addLayer()
        # Access private method to test edge case
        assert canvas_model._is_layer_locked("nonexistent-id") is False

    def test_is_layer_visible_nonexistent_layer(self, canvas_model):
        """_is_layer_visible returns True for nonexistent layer ID."""
        canvas_model.addLayer()
        # Access private method to test edge case
        assert canvas_model._is_layer_visible("nonexistent-id") is True

    def test_find_last_child_position_nonexistent_layer(self, canvas_model):
        """_findLastChildPosition returns end of list for nonexistent layer."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        result = canvas_model._findLastChildPosition("nonexistent-id")
        assert result == canvas_model.rowCount()

    def test_find_last_child_position_next_item_is_layer(self, canvas_model):
        """_findLastChildPosition returns correct index when next item is a layer."""
        canvas_model.addLayer()  # Layer at index 0
        layer_id = canvas_model.data(canvas_model.index(0, 0), canvas_model.ItemIdRole)
        canvas_model.addLayer()  # Layer at index 1
        # Position for first layer's children should be before second layer
        result = canvas_model._findLastChildPosition(layer_id)
        assert result == 1

    def test_reparent_item_when_source_before_target(self, canvas_model):
        """reparentItem adjusts target when source item is before target position."""
        # Create: rect0, layer, rect1
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )
        canvas_model.addLayer()
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        )

        layer_id = canvas_model.data(canvas_model.index(1, 0), canvas_model.ItemIdRole)

        # Reparent rect0 (index 0) to layer (index 1)
        # This should trigger the adjustment since item_index < target_index
        canvas_model.reparentItem(0, layer_id)

        # Verify rect0 is now a child of the layer
        rect_parent = canvas_model.data(
            canvas_model.index(1, 0), canvas_model.ParentIdRole
        )
        assert rect_parent == layer_id

    def test_is_effectively_visible_invalid_index(self, canvas_model):
        """_is_effectively_visible returns False for invalid index."""
        assert canvas_model._is_effectively_visible(-1) is False
        assert canvas_model._is_effectively_visible(999) is False

    def test_add_item_with_invalid_schema(self, canvas_model):
        """addItem handles schema validation errors gracefully."""
        # Invalid numeric field should trigger schema error
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": "not-a-number",
                "y": 0,
                "width": 10,
                "height": 10,
            }
        )
        # Should not crash, and no item should be added
        assert canvas_model.rowCount() == 0

    def test_execute_command_without_recording(self, canvas_model):
        """_execute_command with record=False executes without history."""
        from lucent.commands import AddItemCommand
        from lucent.item_schema import parse_item_data

        parsed = parse_item_data(
            {
                "type": "rectangle",
                "x": 0,
                "y": 0,
                "width": 10,
                "height": 10,
                "name": "Test",
            }
        )
        command = AddItemCommand(canvas_model, parsed.data)

        # Execute without recording
        canvas_model._execute_command(command, record=False)

        assert canvas_model.rowCount() == 1
        # Undo should not be available since we didn't record
        assert canvas_model.canUndo is False
