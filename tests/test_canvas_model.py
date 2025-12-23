"""Unit tests for canvas_model module."""
import pytest
from canvas_model import CanvasModel
from canvas_items import RectangleItem, EllipseItem


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
        
        assert blocker.args == [0]
        
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

