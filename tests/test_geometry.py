"""Unit tests for geometry module."""

import pytest
from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainterPath

from lucent.geometry import (
    Geometry,
    RectGeometry,
    EllipseGeometry,
    PolylineGeometry,
    TextGeometry,
)


class TestRectGeometry:
    """Tests for RectGeometry class."""

    def test_basic_creation(self):
        """Test creating a basic rectangle geometry."""
        rect = RectGeometry(x=10, y=20, width=100, height=50)
        assert rect.x == 10
        assert rect.y == 20
        assert rect.width == 100
        assert rect.height == 50

    def test_negative_width_clamped_to_zero(self):
        """Test that negative width is clamped to 0."""
        rect = RectGeometry(x=0, y=0, width=-10, height=20)
        assert rect.width == 0.0

    def test_negative_height_clamped_to_zero(self):
        """Test that negative height is clamped to 0."""
        rect = RectGeometry(x=0, y=0, width=20, height=-15)
        assert rect.height == 0.0

    def test_get_bounds(self):
        """Test get_bounds returns correct bounding rectangle."""
        rect = RectGeometry(x=10, y=20, width=100, height=50)
        bounds = rect.get_bounds()
        assert bounds == QRectF(10, 20, 100, 50)

    def test_get_bounds_at_origin(self):
        """Test get_bounds at origin."""
        rect = RectGeometry(x=0, y=0, width=50, height=30)
        bounds = rect.get_bounds()
        assert bounds == QRectF(0, 0, 50, 30)

    def test_get_bounds_negative_position(self):
        """Test get_bounds with negative position."""
        rect = RectGeometry(x=-50, y=-25, width=100, height=50)
        bounds = rect.get_bounds()
        assert bounds == QRectF(-50, -25, 100, 50)

    def test_to_painter_path(self):
        """Test to_painter_path creates correct path."""
        rect = RectGeometry(x=10, y=20, width=100, height=50)
        path = rect.to_painter_path()
        assert isinstance(path, QPainterPath)
        # Path bounding rect should match geometry bounds
        assert path.boundingRect() == QRectF(10, 20, 100, 50)

    def test_to_painter_path_zero_size(self):
        """Test to_painter_path with zero dimensions."""
        rect = RectGeometry(x=10, y=20, width=0, height=0)
        path = rect.to_painter_path()
        assert isinstance(path, QPainterPath)

    def test_to_dict(self):
        """Test serialization to dictionary."""
        rect = RectGeometry(x=10, y=20, width=100, height=50)
        data = rect.to_dict()
        assert data == {"x": 10, "y": 20, "width": 100, "height": 50}

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {"x": 15, "y": 25, "width": 80, "height": 60}
        rect = RectGeometry.from_dict(data)
        assert rect.x == 15
        assert rect.y == 25
        assert rect.width == 80
        assert rect.height == 60

    def test_from_dict_missing_fields_use_defaults(self):
        """Test from_dict uses defaults for missing fields."""
        data = {}
        rect = RectGeometry.from_dict(data)
        assert rect.x == 0
        assert rect.y == 0
        assert rect.width == 0
        assert rect.height == 0

    def test_from_dict_clamps_negative_dimensions(self):
        """Test from_dict clamps negative dimensions."""
        data = {"x": 0, "y": 0, "width": -20, "height": -30}
        rect = RectGeometry.from_dict(data)
        assert rect.width == 0.0
        assert rect.height == 0.0

    def test_round_trip(self):
        """Test serialization round-trip."""
        original = RectGeometry(x=10, y=20, width=100, height=50)
        data = original.to_dict()
        restored = RectGeometry.from_dict(data)
        assert restored.x == original.x
        assert restored.y == original.y
        assert restored.width == original.width
        assert restored.height == original.height


class TestEllipseGeometry:
    """Tests for EllipseGeometry class."""

    def test_basic_creation(self):
        """Test creating a basic ellipse geometry."""
        ellipse = EllipseGeometry(center_x=50, center_y=75, radius_x=30, radius_y=20)
        assert ellipse.center_x == 50
        assert ellipse.center_y == 75
        assert ellipse.radius_x == 30
        assert ellipse.radius_y == 20

    def test_negative_radius_x_clamped_to_zero(self):
        """Test that negative radius_x is clamped to 0."""
        ellipse = EllipseGeometry(center_x=0, center_y=0, radius_x=-15, radius_y=20)
        assert ellipse.radius_x == 0.0

    def test_negative_radius_y_clamped_to_zero(self):
        """Test that negative radius_y is clamped to 0."""
        ellipse = EllipseGeometry(center_x=0, center_y=0, radius_x=20, radius_y=-10)
        assert ellipse.radius_y == 0.0

    def test_get_bounds(self):
        """Test get_bounds returns correct bounding rectangle."""
        ellipse = EllipseGeometry(center_x=100, center_y=100, radius_x=50, radius_y=30)
        bounds = ellipse.get_bounds()
        assert bounds == QRectF(50, 70, 100, 60)

    def test_get_bounds_at_origin(self):
        """Test get_bounds for ellipse centered at origin."""
        ellipse = EllipseGeometry(center_x=0, center_y=0, radius_x=25, radius_y=25)
        bounds = ellipse.get_bounds()
        assert bounds == QRectF(-25, -25, 50, 50)

    def test_to_painter_path(self):
        """Test to_painter_path creates correct path."""
        ellipse = EllipseGeometry(center_x=50, center_y=50, radius_x=30, radius_y=20)
        path = ellipse.to_painter_path()
        assert isinstance(path, QPainterPath)
        # Path bounding rect should match geometry bounds
        bounds = path.boundingRect()
        assert abs(bounds.x() - 20) < 0.01
        assert abs(bounds.y() - 30) < 0.01
        assert abs(bounds.width() - 60) < 0.01
        assert abs(bounds.height() - 40) < 0.01

    def test_to_dict(self):
        """Test serialization to dictionary."""
        ellipse = EllipseGeometry(center_x=50, center_y=75, radius_x=30, radius_y=20)
        data = ellipse.to_dict()
        assert data == {
            "centerX": 50,
            "centerY": 75,
            "radiusX": 30,
            "radiusY": 20,
        }

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {"centerX": 100, "centerY": 150, "radiusX": 40, "radiusY": 30}
        ellipse = EllipseGeometry.from_dict(data)
        assert ellipse.center_x == 100
        assert ellipse.center_y == 150
        assert ellipse.radius_x == 40
        assert ellipse.radius_y == 30

    def test_from_dict_missing_fields_use_defaults(self):
        """Test from_dict uses defaults for missing fields."""
        data = {}
        ellipse = EllipseGeometry.from_dict(data)
        assert ellipse.center_x == 0
        assert ellipse.center_y == 0
        assert ellipse.radius_x == 0
        assert ellipse.radius_y == 0

    def test_from_dict_clamps_negative_radii(self):
        """Test from_dict clamps negative radii."""
        data = {"centerX": 0, "centerY": 0, "radiusX": -50, "radiusY": -40}
        ellipse = EllipseGeometry.from_dict(data)
        assert ellipse.radius_x == 0.0
        assert ellipse.radius_y == 0.0

    def test_round_trip(self):
        """Test serialization round-trip."""
        original = EllipseGeometry(center_x=50, center_y=75, radius_x=30, radius_y=20)
        data = original.to_dict()
        restored = EllipseGeometry.from_dict(data)
        assert restored.center_x == original.center_x
        assert restored.center_y == original.center_y
        assert restored.radius_x == original.radius_x
        assert restored.radius_y == original.radius_y


class TestPolylineGeometry:
    """Tests for PolylineGeometry class."""

    def test_basic_creation(self):
        """Test creating a basic polyline geometry."""
        points = [{"x": 0, "y": 0}, {"x": 10, "y": 10}]
        polyline = PolylineGeometry(points=points)
        assert polyline.points == [{"x": 0.0, "y": 0.0}, {"x": 10.0, "y": 10.0}]
        assert polyline.closed is False

    def test_creation_with_closed_flag(self):
        """Test creating a closed polyline."""
        points = [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}]
        polyline = PolylineGeometry(points=points, closed=True)
        assert polyline.closed is True

    def test_points_normalized_to_float(self):
        """Test that points are normalized to float values."""
        points = [{"x": 1, "y": 2}, {"x": 3, "y": 4}]
        polyline = PolylineGeometry(points=points)
        assert polyline.points == [{"x": 1.0, "y": 2.0}, {"x": 3.0, "y": 4.0}]

    def test_requires_at_least_two_points(self):
        """Test that constructor requires at least two points."""
        with pytest.raises(ValueError, match="at least two points"):
            PolylineGeometry(points=[{"x": 0, "y": 0}])

    def test_requires_at_least_two_points_empty(self):
        """Test that constructor rejects empty points list."""
        with pytest.raises(ValueError, match="at least two points"):
            PolylineGeometry(points=[])

    def test_get_bounds(self):
        """Test get_bounds returns correct bounding rectangle."""
        points = [{"x": 10, "y": 20}, {"x": 50, "y": 10}, {"x": 30, "y": 60}]
        polyline = PolylineGeometry(points=points)
        bounds = polyline.get_bounds()
        assert bounds == QRectF(10, 10, 40, 50)

    def test_get_bounds_negative_coords(self):
        """Test get_bounds with negative coordinates."""
        points = [{"x": -50, "y": -30}, {"x": 50, "y": 30}]
        polyline = PolylineGeometry(points=points)
        bounds = polyline.get_bounds()
        assert bounds == QRectF(-50, -30, 100, 60)

    def test_to_painter_path_open(self):
        """Test to_painter_path for open polyline."""
        points = [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}]
        polyline = PolylineGeometry(points=points, closed=False)
        path = polyline.to_painter_path()
        assert isinstance(path, QPainterPath)
        # Open path should not be closed
        assert path.elementCount() == 3  # moveTo + 2 lineTo

    def test_to_painter_path_closed(self):
        """Test to_painter_path for closed polyline."""
        points = [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}]
        polyline = PolylineGeometry(points=points, closed=True)
        path = polyline.to_painter_path()
        assert isinstance(path, QPainterPath)
        # Closed path should have closeSubpath element
        assert path.elementCount() == 4  # moveTo + 2 lineTo + close

    def test_to_dict(self):
        """Test serialization to dictionary."""
        points = [{"x": 0, "y": 0}, {"x": 10, "y": 10}]
        polyline = PolylineGeometry(points=points, closed=True)
        data = polyline.to_dict()
        assert data == {
            "points": [{"x": 0.0, "y": 0.0}, {"x": 10.0, "y": 10.0}],
            "closed": True,
        }

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "points": [{"x": 1, "y": 2}, {"x": 3, "y": 4}, {"x": 5, "y": 6}],
            "closed": True,
        }
        polyline = PolylineGeometry.from_dict(data)
        assert polyline.points == [
            {"x": 1.0, "y": 2.0},
            {"x": 3.0, "y": 4.0},
            {"x": 5.0, "y": 6.0},
        ]
        assert polyline.closed is True

    def test_from_dict_defaults(self):
        """Test from_dict uses defaults for missing fields."""
        data = {"points": [{"x": 0, "y": 0}, {"x": 1, "y": 1}]}
        polyline = PolylineGeometry.from_dict(data)
        assert polyline.closed is False

    def test_from_dict_invalid_points_raises(self):
        """Test from_dict raises for invalid points."""
        with pytest.raises(ValueError):
            PolylineGeometry.from_dict({"points": "not a list"})

    def test_from_dict_too_few_points_raises(self):
        """Test from_dict raises for too few points."""
        with pytest.raises(ValueError):
            PolylineGeometry.from_dict({"points": [{"x": 0, "y": 0}]})

    def test_round_trip(self):
        """Test serialization round-trip."""
        points = [{"x": 0, "y": 0}, {"x": 10, "y": 10}, {"x": 20, "y": 0}]
        original = PolylineGeometry(points=points, closed=True)
        data = original.to_dict()
        restored = PolylineGeometry.from_dict(data)
        assert restored.points == original.points
        assert restored.closed == original.closed


class TestTextGeometry:
    """Tests for TextGeometry class."""

    def test_basic_creation(self):
        """Test creating a basic text geometry."""
        text_geom = TextGeometry(x=10, y=20, width=200, height=50)
        assert text_geom.x == 10
        assert text_geom.y == 20
        assert text_geom.width == 200
        assert text_geom.height == 50

    def test_width_clamped_to_minimum(self):
        """Test that width below minimum is clamped to 1."""
        text_geom = TextGeometry(x=0, y=0, width=0, height=20)
        assert text_geom.width == 1.0

    def test_height_clamped_to_zero(self):
        """Test that negative height is clamped to 0."""
        text_geom = TextGeometry(x=0, y=0, width=100, height=-15)
        assert text_geom.height == 0.0

    def test_get_bounds(self):
        """Test get_bounds returns correct bounding rectangle."""
        text_geom = TextGeometry(x=10, y=20, width=200, height=50)
        bounds = text_geom.get_bounds()
        assert bounds == QRectF(10, 20, 200, 50)

    def test_to_painter_path(self):
        """Test to_painter_path creates correct path."""
        text_geom = TextGeometry(x=10, y=20, width=200, height=50)
        path = text_geom.to_painter_path()
        assert isinstance(path, QPainterPath)
        # Path bounding rect should match geometry bounds
        assert path.boundingRect() == QRectF(10, 20, 200, 50)

    def test_to_dict(self):
        """Test serialization to dictionary."""
        text_geom = TextGeometry(x=10, y=20, width=200, height=50)
        data = text_geom.to_dict()
        assert data == {"x": 10, "y": 20, "width": 200, "height": 50}

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {"x": 15, "y": 25, "width": 180, "height": 60}
        text_geom = TextGeometry.from_dict(data)
        assert text_geom.x == 15
        assert text_geom.y == 25
        assert text_geom.width == 180
        assert text_geom.height == 60

    def test_from_dict_missing_fields_use_defaults(self):
        """Test from_dict uses defaults for missing fields."""
        data = {}
        text_geom = TextGeometry.from_dict(data)
        assert text_geom.x == 0
        assert text_geom.y == 0
        assert text_geom.width == 1  # Minimum width
        assert text_geom.height == 0

    def test_round_trip(self):
        """Test serialization round-trip."""
        original = TextGeometry(x=10, y=20, width=200, height=50)
        data = original.to_dict()
        restored = TextGeometry.from_dict(data)
        assert restored.x == original.x
        assert restored.y == original.y
        assert restored.width == original.width
        assert restored.height == original.height


class TestGeometryIsAbstract:
    """Tests to verify Geometry is properly abstract."""

    def test_cannot_instantiate_geometry_directly(self):
        """Test that Geometry cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Geometry()  # type: ignore
