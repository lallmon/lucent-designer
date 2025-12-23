"""Unit tests for canvas_items module."""
import pytest
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import QRectF
from canvas_items import (
    CanvasItem, RectangleItem, EllipseItem,
    CANVAS_OFFSET_X, CANVAS_OFFSET_Y
)


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
            x=0, y=0, width=50, height=50,
            stroke_width=3, stroke_color="#ff0000",
            fill_color="#00ff00", fill_opacity=0.5,
            stroke_opacity=0.8
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
        data = {
            "type": "rectangle",
            "x": 15,
            "y": 25,
            "width": 80,
            "height": 60
        }
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
            "fillOpacity": 0.3
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
        data = {
            "type": "rectangle",
            "x": 0,
            "y": 0,
            "width": -20,
            "height": -30
        }
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
            "strokeWidth": 200
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
            "fillOpacity": -2.0
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
            center_x=0, center_y=0, radius_x=10, radius_y=10,
            stroke_width=2, stroke_color="#ff00ff",
            fill_color="#00ffff", fill_opacity=0.6,
            stroke_opacity=0.9
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
            center_x=0, center_y=0, radius_x=10, radius_y=10,
            stroke_width=0.05
        )
        assert ellipse.stroke_width == 0.1
    
    def test_stroke_width_maximum_clamped(self):
        """Test that stroke width above 100 is clamped to 100."""
        ellipse = EllipseItem(
            center_x=0, center_y=0, radius_x=10, radius_y=10,
            stroke_width=250
        )
        assert ellipse.stroke_width == 100.0
    
    def test_stroke_opacity_clamped_to_range(self):
        """Test that stroke opacity is clamped to 0-1 range."""
        ellipse1 = EllipseItem(
            center_x=0, center_y=0, radius_x=10, radius_y=10,
            stroke_opacity=-0.3
        )
        assert ellipse1.stroke_opacity == 0.0
        
        ellipse2 = EllipseItem(
            center_x=0, center_y=0, radius_x=10, radius_y=10,
            stroke_opacity=1.8
        )
        assert ellipse2.stroke_opacity == 1.0
    
    def test_fill_opacity_clamped_to_range(self):
        """Test that fill opacity is clamped to 0-1 range."""
        ellipse1 = EllipseItem(
            center_x=0, center_y=0, radius_x=10, radius_y=10,
            fill_opacity=-1.0
        )
        assert ellipse1.fill_opacity == 0.0
        
        ellipse2 = EllipseItem(
            center_x=0, center_y=0, radius_x=10, radius_y=10,
            fill_opacity=3.0
        )
        assert ellipse2.fill_opacity == 1.0
    
    def test_from_dict_basic(self):
        """Test creating ellipse from dictionary with basic data."""
        data = {
            "type": "ellipse",
            "centerX": 100,
            "centerY": 150,
            "radiusX": 40,
            "radiusY": 30
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
            "fillOpacity": 0.8
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
            "radiusY": -40
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
            "strokeWidth": 0.001
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
            "fillOpacity": 10.0
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

