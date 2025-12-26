"""Unit tests for canvas_model module."""
import pytest
from canvas_model import CanvasModel
from canvas_items import RectangleItem, EllipseItem, LayerItem
from commands import (
    Command, AddItemCommand, RemoveItemCommand, UpdateItemCommand, TransactionCommand
)


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
            "strokeColor": "#ff0000"
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
            "fillOpacity": 0.5
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
        ellipse_data = {"type": "ellipse", "centerX": 20, "centerY": 20, "radiusX": 5, "radiusY": 5}
        
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
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "ellipse", "centerX": 20, "centerY": 20, "radiusX": 5, "radiusY": 5})
        
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
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "ellipse", "centerX": 20, "centerY": 20, "radiusX": 5, "radiusY": 5})
        
        with qtbot.waitSignal(canvas_model.itemRemoved, timeout=1000):
            canvas_model.removeItem(1)
        
        assert canvas_model.count() == 1
        items = canvas_model.getItems()
        assert isinstance(items[0], RectangleItem)
    
    def test_remove_invalid_index_negative(self, canvas_model):
        """Test that removing with negative index is safely handled."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        
        # Should not crash or emit signal
        canvas_model.removeItem(-1)
        assert canvas_model.count() == 1
    
    def test_remove_invalid_index_too_large(self, canvas_model):
        """Test that removing with out-of-bounds index is safely handled."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        
        # Should not crash or emit signal
        canvas_model.removeItem(5)
        assert canvas_model.count() == 1
    
    def test_remove_from_empty_model(self, canvas_model):
        """Test that removing from an empty model is safely handled."""
        canvas_model.removeItem(0)
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
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "ellipse", "centerX": 20, "centerY": 20, "radiusX": 5, "radiusY": 5})
        canvas_model.addItem({"type": "rectangle", "x": 30, "y": 30, "width": 15, "height": 15})
        
        assert canvas_model.count() == 3
        
        with qtbot.waitSignal(canvas_model.itemsCleared, timeout=1000):
            canvas_model.clear()
        
        assert canvas_model.count() == 0
        assert canvas_model.getItems() == []


class TestCanvasModelUpdate:
    """Tests for updating item properties in CanvasModel."""
    
    def test_update_rectangle_position(self, canvas_model, qtbot):
        """Test updating a rectangle's position."""
        canvas_model.addItem({"type": "rectangle", "x": 10, "y": 20, "width": 100, "height": 50})
        
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
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 50, "height": 50})
        
        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, {"width": 100, "height": 75})
        
        items = canvas_model.getItems()
        assert items[0].width == 100
        assert items[0].height == 75
    
    def test_update_ellipse_position(self, canvas_model, qtbot):
        """Test updating an ellipse's center position."""
        canvas_model.addItem({"type": "ellipse", "centerX": 50, "centerY": 50, "radiusX": 20, "radiusY": 20})
        
        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, {"centerX": 100, "centerY": 150})
        
        items = canvas_model.getItems()
        assert items[0].center_x == 100
        assert items[0].center_y == 150
    
    def test_update_ellipse_radii(self, canvas_model, qtbot):
        """Test updating an ellipse's radii."""
        canvas_model.addItem({"type": "ellipse", "centerX": 0, "centerY": 0, "radiusX": 10, "radiusY": 10})
        
        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, {"radiusX": 30, "radiusY": 25})
        
        items = canvas_model.getItems()
        assert items[0].radius_x == 30
        assert items[0].radius_y == 25
    
    def test_update_stroke_properties(self, canvas_model, qtbot):
        """Test updating stroke properties (width, color, opacity)."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        
        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, {
                "strokeWidth": 5,
                "strokeColor": "#ff0000",
                "strokeOpacity": 0.8
            })
        
        items = canvas_model.getItems()
        assert items[0].stroke_width == 5
        assert items[0].stroke_color == "#ff0000"
        assert items[0].stroke_opacity == 0.8
    
    def test_update_fill_properties(self, canvas_model, qtbot):
        """Test updating fill properties (color, opacity)."""
        canvas_model.addItem({"type": "ellipse", "centerX": 0, "centerY": 0, "radiusX": 10, "radiusY": 10})
        
        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, {
                "fillColor": "#00ff00",
                "fillOpacity": 0.6
            })
        
        items = canvas_model.getItems()
        assert items[0].fill_color == "#00ff00"
        assert items[0].fill_opacity == 0.6
    
    def test_update_partial_properties(self, canvas_model, qtbot):
        """Test updating only some properties leaves others unchanged."""
        canvas_model.addItem({
            "type": "rectangle",
            "x": 10,
            "y": 20,
            "width": 100,
            "height": 50,
            "strokeWidth": 2,
            "strokeColor": "#ffffff"
        })
        
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
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100})
        
        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, {"width": -50, "height": -30})
        
        items = canvas_model.getItems()
        assert items[0].width == 0.0
        assert items[0].height == 0.0
    
    def test_update_validates_stroke_width_bounds(self, canvas_model, qtbot):
        """Test that update validates stroke width bounds."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        
        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, {"strokeWidth": 200})
        
        items = canvas_model.getItems()
        assert items[0].stroke_width == 100.0
    
    def test_update_validates_opacity_bounds(self, canvas_model, qtbot):
        """Test that update validates opacity bounds."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        
        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, {"strokeOpacity": 5.0, "fillOpacity": -2.0})
        
        items = canvas_model.getItems()
        assert items[0].stroke_opacity == 1.0
        assert items[0].fill_opacity == 0.0
    
    def test_update_invalid_index_ignored(self, canvas_model):
        """Test that updating with invalid index is safely handled."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        
        # Should not crash
        canvas_model.updateItem(5, {"x": 100})
        
        # Item unchanged
        items = canvas_model.getItems()
        assert items[0].x == 0
    
    def test_update_with_malformed_data_handled(self, canvas_model, qtbot):
        """Test that update with malformed data is handled gracefully."""
        canvas_model.addItem({"type": "rectangle", "x": 10, "y": 20, "width": 100, "height": 50})
        
        # Try to update with invalid data type
        canvas_model.updateItem(0, {"width": "not a number"})
        
        # Item should remain unchanged
        items = canvas_model.getItems()
        assert items[0].width == 100


class TestCanvasModelQueries:
    """Tests for querying item data from CanvasModel."""
    
    def test_get_item_data_rectangle(self, canvas_model):
        """Test getting data for a rectangle item."""
        canvas_model.addItem({
            "type": "rectangle",
            "x": 10,
            "y": 20,
            "width": 100,
            "height": 50,
            "strokeWidth": 2,
            "strokeColor": "#ff0000"
        })
        
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
        canvas_model.addItem({
            "type": "ellipse",
            "centerX": 50,
            "centerY": 75,
            "radiusX": 30,
            "radiusY": 20,
            "fillColor": "#00ff00",
            "fillOpacity": 0.5
        })
        
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
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        
        assert canvas_model.getItemData(-1) is None
        assert canvas_model.getItemData(5) is None
    
    def test_get_items_for_hit_test(self, canvas_model):
        """Test getting all items as dictionaries for hit testing."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "ellipse", "centerX": 20, "centerY": 20, "radiusX": 5, "radiusY": 5})
        
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
        canvas_model.addItem({"type": "rectangle", "x": 10, "y": 20, "width": 100, "height": 50})
        assert canvas_model.count() == 1
        assert canvas_model.canUndo is True

        with qtbot.waitSignal(canvas_model.itemRemoved, timeout=1000):
            result = canvas_model.undo()

        assert result is True
        assert canvas_model.count() == 0
        assert canvas_model.canUndo is False

    def test_undo_remove_item(self, canvas_model, qtbot):
        """Test undoing removeItem restores the item."""
        canvas_model.addItem({"type": "rectangle", "x": 10, "y": 20, "width": 100, "height": 50})
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
        canvas_model.addItem({"type": "rectangle", "x": 10, "y": 20, "width": 100, "height": 50})
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
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "ellipse", "centerX": 20, "centerY": 20, "radiusX": 5, "radiusY": 5})
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
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "ellipse", "centerX": 20, "centerY": 20, "radiusX": 5, "radiusY": 5})
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
            canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})

        with qtbot.waitSignal(canvas_model.undoStackChanged, timeout=1000):
            canvas_model.undo()

    def test_undo_stack_contains_command_objects(self, canvas_model):
        """Test that undo stack contains Command objects."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        assert len(canvas_model._undo_stack) == 1
        assert isinstance(canvas_model._undo_stack[0], Command)

    def test_add_item_pushes_add_command(self, canvas_model):
        """Test addItem pushes an AddItemCommand to the stack."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        assert isinstance(canvas_model._undo_stack[-1], AddItemCommand)

    def test_remove_item_pushes_remove_command(self, canvas_model):
        """Test removeItem pushes a RemoveItemCommand to the stack."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.removeItem(0)
        assert isinstance(canvas_model._undo_stack[-1], RemoveItemCommand)

    def test_update_item_pushes_update_command(self, canvas_model):
        """Test updateItem pushes an UpdateItemCommand to the stack."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.updateItem(0, {"x": 50})
        assert isinstance(canvas_model._undo_stack[-1], UpdateItemCommand)


class TestCanvasModelTransactions:
    """Tests for transaction coalescing in CanvasModel."""

    def test_transaction_coalesces_multiple_updates(self, canvas_model):
        """Test that updates within a transaction create a single undo entry."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100})
        initial_undo_count = len(canvas_model._undo_stack)

        canvas_model.beginTransaction()
        canvas_model.updateItem(0, {"x": 10})
        canvas_model.updateItem(0, {"x": 20})
        canvas_model.updateItem(0, {"x": 30})
        canvas_model.endTransaction()

        assert len(canvas_model._undo_stack) == initial_undo_count + 1
        assert canvas_model.getItems()[0].x == 30

    def test_undo_transaction_restores_original_state(self, canvas_model):
        """Test that undoing a transaction restores the pre-transaction state."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100})

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
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100})
        initial_undo_count = len(canvas_model._undo_stack)

        canvas_model.beginTransaction()
        canvas_model.endTransaction()

        assert len(canvas_model._undo_stack) == initial_undo_count

    def test_transaction_tracks_multiple_items(self, canvas_model):
        """Test that transactions can track changes to multiple items."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100})
        canvas_model.addItem({"type": "ellipse", "centerX": 50, "centerY": 50, "radiusX": 25, "radiusY": 25})

        canvas_model.beginTransaction()
        canvas_model.updateItem(0, {"x": 100})
        canvas_model.updateItem(1, {"centerX": 200})
        canvas_model.endTransaction()

        canvas_model.undo()

        assert canvas_model.getItems()[0].x == 0
        assert canvas_model.getItems()[1].center_x == 50

    def test_nested_begin_transaction_ignored(self, canvas_model):
        """Test that calling beginTransaction while active is safely ignored."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100})

        canvas_model.beginTransaction()
        canvas_model.updateItem(0, {"x": 50})
        canvas_model.beginTransaction()
        canvas_model.updateItem(0, {"x": 100})
        canvas_model.endTransaction()

        canvas_model.undo()
        assert canvas_model.getItems()[0].x == 0

    def test_transaction_pushes_transaction_command(self, canvas_model):
        """Test that transactions push TransactionCommand to the stack."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100})

        canvas_model.beginTransaction()
        canvas_model.updateItem(0, {"x": 50})
        canvas_model.endTransaction()

        assert isinstance(canvas_model._undo_stack[-1], TransactionCommand)


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
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100})
        assert canvas_model.canRedo is False

        canvas_model.undo()

        assert canvas_model.canRedo is True

    def test_redo_add_item(self, canvas_model, qtbot):
        """Test redoing an undone addItem."""
        canvas_model.addItem({"type": "rectangle", "x": 10, "y": 20, "width": 100, "height": 50})
        canvas_model.undo()
        assert canvas_model.count() == 0

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            result = canvas_model.redo()

        assert result is True
        assert canvas_model.count() == 1
        assert canvas_model.getItems()[0].x == 10

    def test_redo_remove_item(self, canvas_model, qtbot):
        """Test redoing an undone removeItem."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100})
        canvas_model.removeItem(0)
        canvas_model.undo()
        assert canvas_model.count() == 1

        with qtbot.waitSignal(canvas_model.itemRemoved, timeout=1000):
            result = canvas_model.redo()

        assert result is True
        assert canvas_model.count() == 0

    def test_redo_update_item(self, canvas_model, qtbot):
        """Test redoing an undone updateItem."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100})
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
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100})
        canvas_model.undo()
        assert canvas_model.canRedo is True

        canvas_model.addItem({"type": "ellipse", "centerX": 50, "centerY": 50, "radiusX": 25, "radiusY": 25})

        assert canvas_model.canRedo is False

    def test_multiple_undo_redo_cycle(self, canvas_model):
        """Test multiple undo/redo operations work correctly."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100})
        canvas_model.addItem({"type": "ellipse", "centerX": 50, "centerY": 50, "radiusX": 25, "radiusY": 25})
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
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100})

        with qtbot.waitSignal(canvas_model.redoStackChanged, timeout=1000):
            canvas_model.undo()

        with qtbot.waitSignal(canvas_model.redoStackChanged, timeout=1000):
            canvas_model.redo()


class TestCanvasModelAutoNames:
    """Tests for auto-generated item names."""

    def test_add_rectangle_generates_name(self, canvas_model):
        """First rectangle should be named 'Rectangle 1'."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        item = canvas_model.getItems()[0]
        assert item.name == "Rectangle 1"

    def test_add_ellipse_generates_name(self, canvas_model):
        """First ellipse should be named 'Ellipse 1'."""
        canvas_model.addItem({"type": "ellipse", "centerX": 0, "centerY": 0, "radiusX": 10, "radiusY": 10})
        item = canvas_model.getItems()[0]
        assert item.name == "Ellipse 1"

    def test_add_multiple_rectangles_increments_counter(self, canvas_model):
        """Multiple rectangles should get incrementing numbers."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "rectangle", "x": 40, "y": 0, "width": 10, "height": 10})
        items = canvas_model.getItems()
        assert items[0].name == "Rectangle 1"
        assert items[1].name == "Rectangle 2"
        assert items[2].name == "Rectangle 3"

    def test_add_mixed_types_separate_counters(self, canvas_model):
        """Different types should have separate counters."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "ellipse", "centerX": 0, "centerY": 0, "radiusX": 10, "radiusY": 10})
        canvas_model.addItem({"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "ellipse", "centerX": 20, "centerY": 0, "radiusX": 10, "radiusY": 10})
        items = canvas_model.getItems()
        assert items[0].name == "Rectangle 1"
        assert items[1].name == "Ellipse 1"
        assert items[2].name == "Rectangle 2"
        assert items[3].name == "Ellipse 2"

    def test_provided_name_not_overwritten(self, canvas_model):
        """If item data includes a name, it should be preserved."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10, "name": "My Custom Rect"})
        item = canvas_model.getItems()[0]
        assert item.name == "My Custom Rect"

    def test_name_preserved_in_getItemData(self, canvas_model):
        """getItemData should return the item name."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        data = canvas_model.getItemData(0)
        assert data["name"] == "Rectangle 1"

    def test_clear_resets_type_counters(self, canvas_model):
        """Clear should reset type counters so new items start from 1."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10})
        assert canvas_model.getItems()[1].name == "Rectangle 2"

        canvas_model.clear()
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})

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
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.addLayer()
        canvas_model.addItem({"type": "ellipse", "centerX": 0, "centerY": 0, "radiusX": 10, "radiusY": 10})
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
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10})
        
        canvas_model.moveItem(0, 2)
        
        items = canvas_model.getItems()
        assert items[0].name == "Rectangle 2"
        assert items[1].name == "Rectangle 3"
        assert items[2].name == "Rectangle 1"

    def test_move_item_backward(self, canvas_model):
        """Move item from index 2 to index 0."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10})
        
        canvas_model.moveItem(2, 0)
        
        items = canvas_model.getItems()
        assert items[0].name == "Rectangle 3"
        assert items[1].name == "Rectangle 1"
        assert items[2].name == "Rectangle 2"

    def test_move_item_same_index_no_op(self, canvas_model, qtbot):
        """Moving item to same index should be a no-op."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10})
        
        initial_undo_count = len(canvas_model._undo_stack)
        canvas_model.moveItem(1, 1)
        
        assert len(canvas_model._undo_stack) == initial_undo_count

    def test_move_item_invalid_from_index(self, canvas_model):
        """Invalid from index should do nothing."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        
        initial_undo_count = len(canvas_model._undo_stack)
        canvas_model.moveItem(-1, 0)
        canvas_model.moveItem(5, 0)
        
        assert len(canvas_model._undo_stack) == initial_undo_count

    def test_move_item_invalid_to_index(self, canvas_model):
        """Invalid to index should do nothing."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        
        initial_undo_count = len(canvas_model._undo_stack)
        canvas_model.moveItem(0, -1)
        canvas_model.moveItem(0, 5)
        
        assert len(canvas_model._undo_stack) == initial_undo_count

    def test_move_item_emits_signal(self, canvas_model, qtbot):
        """moveItem should emit itemsReordered signal."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10})
        
        with qtbot.waitSignal(canvas_model.itemsReordered, timeout=1000):
            canvas_model.moveItem(0, 1)

    def test_move_item_undo(self, canvas_model):
        """Undo should restore original order."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10})
        
        canvas_model.moveItem(0, 2)
        canvas_model.undo()
        
        items = canvas_model.getItems()
        assert items[0].name == "Rectangle 1"
        assert items[1].name == "Rectangle 2"
        assert items[2].name == "Rectangle 3"

    def test_move_item_redo(self, canvas_model):
        """Redo should restore moved order."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10})
        
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

        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        assert canvas_model.rowCount(QModelIndex()) == 1

        canvas_model.addItem({"type": "ellipse", "centerX": 0, "centerY": 0, "radiusX": 10, "radiusY": 10})
        assert canvas_model.rowCount(QModelIndex()) == 2

    def test_data_returns_name_role(self, canvas_model):
        """data() should return item name for NameRole."""
        from PySide6.QtCore import Qt
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        
        index = canvas_model.index(0, 0)
        name = canvas_model.data(index, canvas_model.NameRole)
        assert name == "Rectangle 1"

    def test_data_returns_type_role(self, canvas_model):
        """data() should return item type for TypeRole."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        
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
            canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        
        parent, first, last = blocker.args
        assert first == 0
        assert last == 0

    def test_remove_item_emits_rows_removed(self, canvas_model, qtbot):
        """removeItem should emit rowsRemoved signal."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        
        with qtbot.waitSignal(canvas_model.rowsRemoved, timeout=1000) as blocker:
            canvas_model.removeItem(0)
        
        parent, first, last = blocker.args
        assert first == 0
        assert last == 0

    def test_move_item_emits_rows_moved(self, canvas_model, qtbot):
        """moveItem should emit rowsMoved signal."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "rectangle", "x": 20, "y": 0, "width": 10, "height": 10})
        
        with qtbot.waitSignal(canvas_model.rowsMoved, timeout=1000):
            canvas_model.moveItem(0, 2)

    def test_clear_emits_model_reset(self, canvas_model, qtbot):
        """clear should emit modelReset signal."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        canvas_model.addItem({"type": "ellipse", "centerX": 0, "centerY": 0, "radiusX": 10, "radiusY": 10})
        
        with qtbot.waitSignal(canvas_model.modelReset, timeout=1000):
            canvas_model.clear()

    def test_data_changed_on_update(self, canvas_model, qtbot):
        """updateItem should emit dataChanged signal."""
        canvas_model.addItem({"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10})
        
        with qtbot.waitSignal(canvas_model.dataChanged, timeout=1000):
            canvas_model.updateItem(0, {"x": 50})

