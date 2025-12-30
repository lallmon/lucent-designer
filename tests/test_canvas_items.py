"""Unit tests for canvas_items module."""

import pytest
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import QRectF
from lucent.canvas_items import (
    CanvasItem,
    RectangleItem,
    EllipseItem,
    LayerItem,
    CANVAS_OFFSET_X,
    CANVAS_OFFSET_Y,
)
from PySide6.QtGui import QImage, QPainter
from PySide6.QtCore import QSize


class TestRectangleItem:
    """Tests for RectangleItem class."""

    def test_basic_creation(self):
        """Test creating a basic rectangle with default parameters."""
        rect = RectangleItem(x=10, y=20, width=100, height=50)
        assert rect.x == 10
        assert rect.y == 20
        assert rect.width == 100
        assert rect.height == 50
        assert rect.stroke_width == 1
        assert rect.stroke_color == "#ffffff"
        assert rect.fill_color == "#ffffff"
        assert rect.fill_opacity == 0.0
        assert rect.stroke_opacity == 1.0

    def test_creation_with_styling(self):
        """Test creating a rectangle with custom styling."""
        rect = RectangleItem(
            x=0,
            y=0,
            width=50,
            height=50,
            stroke_width=3,
            stroke_color="#ff0000",
            fill_color="#00ff00",
            fill_opacity=0.5,
            stroke_opacity=0.8,
        )
        assert rect.stroke_width == 3
        assert rect.stroke_color == "#ff0000"
        assert rect.fill_color == "#00ff00"
        assert rect.fill_opacity == 0.5
        assert rect.stroke_opacity == 0.8

    def test_negative_width_clamped_to_zero(self):
        """Test that negative width is clamped to 0."""
        rect = RectangleItem(x=0, y=0, width=-10, height=20)
        assert rect.width == 0.0

    def test_negative_height_clamped_to_zero(self):
        """Test that negative height is clamped to 0."""
        rect = RectangleItem(x=0, y=0, width=20, height=-15)
        assert rect.height == 0.0

    def test_stroke_width_minimum_clamped(self):
        """Test that stroke width below 0.1 is clamped to 0.1."""
        rect = RectangleItem(x=0, y=0, width=10, height=10, stroke_width=0.01)
        assert rect.stroke_width == 0.1

    def test_stroke_width_maximum_clamped(self):
        """Test that stroke width above 100 is clamped to 100."""
        rect = RectangleItem(x=0, y=0, width=10, height=10, stroke_width=150)
        assert rect.stroke_width == 100.0

    def test_stroke_opacity_minimum_clamped(self):
        """Test that stroke opacity below 0 is clamped to 0."""
        rect = RectangleItem(x=0, y=0, width=10, height=10, stroke_opacity=-0.5)
        assert rect.stroke_opacity == 0.0

    def test_stroke_opacity_maximum_clamped(self):
        """Test that stroke opacity above 1 is clamped to 1."""
        rect = RectangleItem(x=0, y=0, width=10, height=10, stroke_opacity=1.5)
        assert rect.stroke_opacity == 1.0

    def test_fill_opacity_minimum_clamped(self):
        """Test that fill opacity below 0 is clamped to 0."""
        rect = RectangleItem(x=0, y=0, width=10, height=10, fill_opacity=-0.5)
        assert rect.fill_opacity == 0.0

    def test_fill_opacity_maximum_clamped(self):
        """Test that fill opacity above 1 is clamped to 1."""
        rect = RectangleItem(x=0, y=0, width=10, height=10, fill_opacity=2.0)
        assert rect.fill_opacity == 1.0

    def test_from_dict_basic(self):
        """Test creating rectangle from dictionary with basic data."""
        data = {"type": "rectangle", "x": 15, "y": 25, "width": 80, "height": 60}
        rect = RectangleItem.from_dict(data)
        assert rect.x == 15
        assert rect.y == 25
        assert rect.width == 80
        assert rect.height == 60

    def test_from_dict_with_styling(self):
        """Test creating rectangle from dictionary with styling data."""
        data = {
            "type": "rectangle",
            "x": 0,
            "y": 0,
            "width": 50,
            "height": 50,
            "strokeWidth": 2.5,
            "strokeColor": "#0000ff",
            "strokeOpacity": 0.7,
            "fillColor": "#ffff00",
            "fillOpacity": 0.3,
        }
        rect = RectangleItem.from_dict(data)
        assert rect.stroke_width == 2.5
        assert rect.stroke_color == "#0000ff"
        assert rect.stroke_opacity == 0.7
        assert rect.fill_color == "#ffff00"
        assert rect.fill_opacity == 0.3

    def test_from_dict_missing_fields_use_defaults(self):
        """Test that missing fields in dictionary use default values."""
        data = {"type": "rectangle"}
        rect = RectangleItem.from_dict(data)
        assert rect.x == 0
        assert rect.y == 0
        assert rect.width == 0
        assert rect.height == 0

    def test_from_dict_validates_negative_dimensions(self):
        """Test that from_dict clamps negative dimensions."""
        data = {"type": "rectangle", "x": 0, "y": 0, "width": -20, "height": -30}
        rect = RectangleItem.from_dict(data)
        assert rect.width == 0.0
        assert rect.height == 0.0

    def test_from_dict_validates_stroke_width_bounds(self):
        """Test that from_dict clamps stroke width to valid range."""
        data = {
            "type": "rectangle",
            "x": 0,
            "y": 0,
            "width": 10,
            "height": 10,
            "strokeWidth": 200,
        }
        rect = RectangleItem.from_dict(data)
        assert rect.stroke_width == 100.0

    def test_from_dict_validates_opacity_bounds(self):
        """Test that from_dict clamps opacity values."""
        data = {
            "type": "rectangle",
            "x": 0,
            "y": 0,
            "width": 10,
            "height": 10,
            "strokeOpacity": 5.0,
            "fillOpacity": -2.0,
        }
        rect = RectangleItem.from_dict(data)
        assert rect.stroke_opacity == 1.0
        assert rect.fill_opacity == 0.0


class TestEllipseItem:
    """Tests for EllipseItem class."""

    def test_basic_creation(self):
        """Test creating a basic ellipse with default parameters."""
        ellipse = EllipseItem(center_x=50, center_y=75, radius_x=30, radius_y=20)
        assert ellipse.center_x == 50
        assert ellipse.center_y == 75
        assert ellipse.radius_x == 30
        assert ellipse.radius_y == 20
        assert ellipse.stroke_width == 1
        assert ellipse.stroke_color == "#ffffff"
        assert ellipse.fill_color == "#ffffff"
        assert ellipse.fill_opacity == 0.0
        assert ellipse.stroke_opacity == 1.0

    def test_creation_with_styling(self):
        """Test creating an ellipse with custom styling."""
        ellipse = EllipseItem(
            center_x=0,
            center_y=0,
            radius_x=10,
            radius_y=10,
            stroke_width=2,
            stroke_color="#ff00ff",
            fill_color="#00ffff",
            fill_opacity=0.6,
            stroke_opacity=0.9,
        )
        assert ellipse.stroke_width == 2
        assert ellipse.stroke_color == "#ff00ff"
        assert ellipse.fill_color == "#00ffff"
        assert ellipse.fill_opacity == 0.6
        assert ellipse.stroke_opacity == 0.9

    def test_negative_radius_x_clamped_to_zero(self):
        """Test that negative radiusX is clamped to 0."""
        ellipse = EllipseItem(center_x=0, center_y=0, radius_x=-15, radius_y=20)
        assert ellipse.radius_x == 0.0

    def test_negative_radius_y_clamped_to_zero(self):
        """Test that negative radiusY is clamped to 0."""
        ellipse = EllipseItem(center_x=0, center_y=0, radius_x=20, radius_y=-10)
        assert ellipse.radius_y == 0.0

    def test_stroke_width_minimum_clamped(self):
        """Test that stroke width below 0.1 is clamped to 0.1."""
        ellipse = EllipseItem(
            center_x=0, center_y=0, radius_x=10, radius_y=10, stroke_width=0.05
        )
        assert ellipse.stroke_width == 0.1

    def test_stroke_width_maximum_clamped(self):
        """Test that stroke width above 100 is clamped to 100."""
        ellipse = EllipseItem(
            center_x=0, center_y=0, radius_x=10, radius_y=10, stroke_width=250
        )
        assert ellipse.stroke_width == 100.0

    def test_stroke_opacity_clamped_to_range(self):
        """Test that stroke opacity is clamped to 0-1 range."""
        ellipse1 = EllipseItem(
            center_x=0, center_y=0, radius_x=10, radius_y=10, stroke_opacity=-0.3
        )
        assert ellipse1.stroke_opacity == 0.0

        ellipse2 = EllipseItem(
            center_x=0, center_y=0, radius_x=10, radius_y=10, stroke_opacity=1.8
        )
        assert ellipse2.stroke_opacity == 1.0

    def test_fill_opacity_clamped_to_range(self):
        """Test that fill opacity is clamped to 0-1 range."""
        ellipse1 = EllipseItem(
            center_x=0, center_y=0, radius_x=10, radius_y=10, fill_opacity=-1.0
        )
        assert ellipse1.fill_opacity == 0.0

        ellipse2 = EllipseItem(
            center_x=0, center_y=0, radius_x=10, radius_y=10, fill_opacity=3.0
        )
        assert ellipse2.fill_opacity == 1.0

    def test_from_dict_basic(self):
        """Test creating ellipse from dictionary with basic data."""
        data = {
            "type": "ellipse",
            "centerX": 100,
            "centerY": 150,
            "radiusX": 40,
            "radiusY": 30,
        }
        ellipse = EllipseItem.from_dict(data)
        assert ellipse.center_x == 100
        assert ellipse.center_y == 150
        assert ellipse.radius_x == 40
        assert ellipse.radius_y == 30

    def test_from_dict_with_styling(self):
        """Test creating ellipse from dictionary with styling data."""
        data = {
            "type": "ellipse",
            "centerX": 0,
            "centerY": 0,
            "radiusX": 25,
            "radiusY": 25,
            "strokeWidth": 3.5,
            "strokeColor": "#123456",
            "strokeOpacity": 0.4,
            "fillColor": "#abcdef",
            "fillOpacity": 0.8,
        }
        ellipse = EllipseItem.from_dict(data)
        assert ellipse.stroke_width == 3.5
        assert ellipse.stroke_color == "#123456"
        assert ellipse.stroke_opacity == 0.4
        assert ellipse.fill_color == "#abcdef"
        assert ellipse.fill_opacity == 0.8

    def test_from_dict_missing_fields_use_defaults(self):
        """Test that missing fields in dictionary use default values."""
        data = {"type": "ellipse"}
        ellipse = EllipseItem.from_dict(data)
        assert ellipse.center_x == 0
        assert ellipse.center_y == 0
        assert ellipse.radius_x == 0
        assert ellipse.radius_y == 0

    def test_from_dict_validates_negative_radii(self):
        """Test that from_dict clamps negative radii."""
        data = {
            "type": "ellipse",
            "centerX": 0,
            "centerY": 0,
            "radiusX": -50,
            "radiusY": -40,
        }
        ellipse = EllipseItem.from_dict(data)
        assert ellipse.radius_x == 0.0
        assert ellipse.radius_y == 0.0

    def test_from_dict_validates_stroke_width_bounds(self):
        """Test that from_dict clamps stroke width to valid range."""
        data = {
            "type": "ellipse",
            "centerX": 0,
            "centerY": 0,
            "radiusX": 10,
            "radiusY": 10,
            "strokeWidth": 0.001,
        }
        ellipse = EllipseItem.from_dict(data)
        assert ellipse.stroke_width == 0.1

    def test_from_dict_validates_opacity_bounds(self):
        """Test that from_dict clamps opacity values."""
        data = {
            "type": "ellipse",
            "centerX": 0,
            "centerY": 0,
            "radiusX": 10,
            "radiusY": 10,
            "strokeOpacity": -0.5,
            "fillOpacity": 10.0,
        }
        ellipse = EllipseItem.from_dict(data)
        assert ellipse.stroke_opacity == 0.0
        assert ellipse.fill_opacity == 1.0


class TestCanvasCoordinates:
    """Tests for canvas coordinate system constants."""

    def test_canvas_offset_constants_exist(self):
        """Test that canvas offset constants are defined."""
        assert CANVAS_OFFSET_X == 5000
        assert CANVAS_OFFSET_Y == 5000


class TestCanvasPainting:
    """Smoke tests for paint paths to ensure coverage."""

    def test_rectangle_paint_runs(self, qtbot):
        img = QImage(QSize(10, 10), QImage.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        rect = RectangleItem(x=0, y=0, width=5, height=5)
        rect.paint(painter, zoom_level=1.0)
        painter.end()

    def test_ellipse_paint_runs(self, qtbot):
        img = QImage(QSize(10, 10), QImage.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        ellipse = EllipseItem(center_x=5, center_y=5, radius_x=4, radius_y=3)
        ellipse.paint(painter, zoom_level=2.0)
        painter.end()


class TestCanvasItemName:
    """Tests for name property on canvas items."""

    def test_rectangle_has_name_property(self):
        """Rectangle should have a name property."""
        rect = RectangleItem(x=0, y=0, width=10, height=10, name="Rectangle 1")
        assert rect.name == "Rectangle 1"

    def test_rectangle_name_defaults_to_empty(self):
        """Rectangle name should default to empty string."""
        rect = RectangleItem(x=0, y=0, width=10, height=10)
        assert rect.name == ""

    def test_ellipse_has_name_property(self):
        """Ellipse should have a name property."""
        ellipse = EllipseItem(
            center_x=0, center_y=0, radius_x=10, radius_y=10, name="Ellipse 1"
        )
        assert ellipse.name == "Ellipse 1"

    def test_ellipse_name_defaults_to_empty(self):
        """Ellipse name should default to empty string."""
        ellipse = EllipseItem(center_x=0, center_y=0, radius_x=10, radius_y=10)
        assert ellipse.name == ""

    def test_rectangle_from_dict_includes_name(self):
        """RectangleItem.from_dict should parse name field."""
        data = {
            "type": "rectangle",
            "x": 0,
            "y": 0,
            "width": 10,
            "height": 10,
            "name": "My Rect",
        }
        rect = RectangleItem.from_dict(data)
        assert rect.name == "My Rect"

    def test_rectangle_from_dict_name_defaults_to_empty(self):
        """RectangleItem.from_dict should default name to empty."""
        data = {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        rect = RectangleItem.from_dict(data)
        assert rect.name == ""

    def test_ellipse_from_dict_includes_name(self):
        """EllipseItem.from_dict should parse name field."""
        data = {
            "type": "ellipse",
            "centerX": 0,
            "centerY": 0,
            "radiusX": 10,
            "radiusY": 10,
            "name": "My Ellipse",
        }
        ellipse = EllipseItem.from_dict(data)
        assert ellipse.name == "My Ellipse"

    def test_ellipse_from_dict_name_defaults_to_empty(self):
        """EllipseItem.from_dict should default name to empty."""
        data = {
            "type": "ellipse",
            "centerX": 0,
            "centerY": 0,
            "radiusX": 10,
            "radiusY": 10,
        }
        ellipse = EllipseItem.from_dict(data)
        assert ellipse.name == ""


class TestLayerItem:
    """Tests for LayerItem class."""

    def test_basic_creation(self):
        """Test creating a basic layer with a name."""
        layer = LayerItem(name="Layer 1")
        assert layer.name == "Layer 1"

    def test_creation_empty_name(self):
        """Test creating a layer with empty name."""
        layer = LayerItem()
        assert layer.name == ""

    def test_layer_has_unique_id(self):
        """LayerItem should have an auto-generated unique ID."""
        layer = LayerItem(name="Test")
        assert layer.id is not None
        assert len(layer.id) > 0

    def test_multiple_layers_have_different_ids(self):
        """Multiple LayerItems should have different IDs."""
        layer1 = LayerItem(name="Layer 1")
        layer2 = LayerItem(name="Layer 2")
        assert layer1.id != layer2.id

    def test_layer_id_preserved_when_provided(self):
        """LayerItem should use provided ID if given."""
        layer = LayerItem(name="Test", layer_id="custom-id-123")
        assert layer.id == "custom-id-123"

    def test_from_dict_with_name(self):
        """Test creating layer from dictionary with name."""
        data = {"type": "layer", "name": "Background"}
        layer = LayerItem.from_dict(data)
        assert layer.name == "Background"

    def test_from_dict_with_id(self):
        """Test creating layer from dictionary with id."""
        data = {"type": "layer", "name": "Background", "id": "layer-abc-123"}
        layer = LayerItem.from_dict(data)
        assert layer.id == "layer-abc-123"

    def test_from_dict_generates_id_if_missing(self):
        """Test creating layer from dictionary without id generates one."""
        data = {"type": "layer", "name": "Background"}
        layer = LayerItem.from_dict(data)
        assert layer.id is not None
        assert len(layer.id) > 0

    def test_from_dict_missing_name_defaults_to_empty(self):
        """Test creating layer from dictionary without name defaults to empty."""
        data = {"type": "layer"}
        layer = LayerItem.from_dict(data)
        assert layer.name == ""

    def test_layer_is_canvas_item(self):
        """LayerItem should be a CanvasItem subclass."""
        layer = LayerItem(name="Test Layer")
        assert isinstance(layer, CanvasItem)

    def test_paint_does_nothing(self):
        """Layer paint method should be a no-op (doesn't raise)."""
        layer = LayerItem(name="Test Layer")
        # Should not raise any exception when called with None
        # (paint is a no-op, so it doesn't use the painter)
        layer.paint(None, 1.0, 0, 0)


class TestShapeParentId:
    """Tests for parent_id property on shape items."""

    def test_rectangle_no_parent_by_default(self):
        """RectangleItem should have no parent by default."""
        rect = RectangleItem(x=0, y=0, width=10, height=10)
        assert rect.parent_id is None

    def test_rectangle_with_parent_id(self):
        """RectangleItem can be created with a parent_id."""
        rect = RectangleItem(x=0, y=0, width=10, height=10, parent_id="layer-123")
        assert rect.parent_id == "layer-123"

    def test_rectangle_from_dict_with_parent_id(self):
        """RectangleItem.from_dict should parse parentId."""
        data = {
            "type": "rectangle",
            "x": 0,
            "y": 0,
            "width": 10,
            "height": 10,
            "parentId": "layer-abc",
        }
        rect = RectangleItem.from_dict(data)
        assert rect.parent_id == "layer-abc"

    def test_rectangle_from_dict_parent_id_defaults_to_none(self):
        """RectangleItem.from_dict should default parentId to None."""
        data = {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        rect = RectangleItem.from_dict(data)
        assert rect.parent_id is None

    def test_ellipse_no_parent_by_default(self):
        """EllipseItem should have no parent by default."""
        ellipse = EllipseItem(center_x=0, center_y=0, radius_x=10, radius_y=10)
        assert ellipse.parent_id is None

    def test_ellipse_with_parent_id(self):
        """EllipseItem can be created with a parent_id."""
        ellipse = EllipseItem(
            center_x=0, center_y=0, radius_x=10, radius_y=10, parent_id="layer-456"
        )
        assert ellipse.parent_id == "layer-456"

    def test_ellipse_from_dict_with_parent_id(self):
        """EllipseItem.from_dict should parse parentId."""
        data = {
            "type": "ellipse",
            "centerX": 0,
            "centerY": 0,
            "radiusX": 10,
            "radiusY": 10,
            "parentId": "layer-xyz",
        }
        ellipse = EllipseItem.from_dict(data)
        assert ellipse.parent_id == "layer-xyz"

    def test_ellipse_from_dict_parent_id_defaults_to_none(self):
        """EllipseItem.from_dict should default parentId to None."""
        data = {
            "type": "ellipse",
            "centerX": 0,
            "centerY": 0,
            "radiusX": 10,
            "radiusY": 10,
        }
        ellipse = EllipseItem.from_dict(data)
        assert ellipse.parent_id is None


class TestLockedProperty:
    """Tests for locked property on canvas items."""

    def test_rectangle_unlocked_by_default(self):
        """RectangleItem should be unlocked by default."""
        rect = RectangleItem(x=0, y=0, width=10, height=10)
        assert rect.locked is False

    def test_rectangle_with_locked_true(self):
        """RectangleItem can be created with locked=True."""
        rect = RectangleItem(x=0, y=0, width=10, height=10, locked=True)
        assert rect.locked is True

    def test_rectangle_from_dict_with_locked(self):
        """RectangleItem.from_dict should parse locked."""
        data = {
            "type": "rectangle",
            "x": 0,
            "y": 0,
            "width": 10,
            "height": 10,
            "locked": True,
        }
        rect = RectangleItem.from_dict(data)
        assert rect.locked is True

    def test_rectangle_from_dict_locked_defaults_false(self):
        """RectangleItem.from_dict should default locked to False."""
        data = {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        rect = RectangleItem.from_dict(data)
        assert rect.locked is False

    def test_ellipse_unlocked_by_default(self):
        """EllipseItem should be unlocked by default."""
        ellipse = EllipseItem(center_x=0, center_y=0, radius_x=10, radius_y=10)
        assert ellipse.locked is False

    def test_ellipse_with_locked_true(self):
        """EllipseItem can be created with locked=True."""
        ellipse = EllipseItem(
            center_x=0, center_y=0, radius_x=10, radius_y=10, locked=True
        )
        assert ellipse.locked is True

    def test_ellipse_from_dict_with_locked(self):
        """EllipseItem.from_dict should parse locked."""
        data = {
            "type": "ellipse",
            "centerX": 0,
            "centerY": 0,
            "radiusX": 10,
            "radiusY": 10,
            "locked": True,
        }
        ellipse = EllipseItem.from_dict(data)
        assert ellipse.locked is True

    def test_ellipse_from_dict_locked_defaults_false(self):
        """EllipseItem.from_dict should default locked to False."""
        data = {
            "type": "ellipse",
            "centerX": 0,
            "centerY": 0,
            "radiusX": 10,
            "radiusY": 10,
        }
        ellipse = EllipseItem.from_dict(data)
        assert ellipse.locked is False

    def test_layer_unlocked_by_default(self):
        """LayerItem should be unlocked by default."""
        layer = LayerItem(name="Test")
        assert layer.locked is False

    def test_layer_with_locked_true(self):
        """LayerItem can be created with locked=True."""
        layer = LayerItem(name="Test", locked=True)
        assert layer.locked is True

    def test_layer_from_dict_with_locked(self):
        """LayerItem.from_dict should parse locked."""
        data = {"type": "layer", "name": "Test", "locked": True}
        layer = LayerItem.from_dict(data)
        assert layer.locked is True

    def test_layer_from_dict_locked_defaults_false(self):
        """LayerItem.from_dict should default locked to False."""
        data = {"type": "layer", "name": "Test"}
        layer = LayerItem.from_dict(data)
        assert layer.locked is False
