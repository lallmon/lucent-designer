# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Unit tests for canvas_items module."""

import pytest
from PySide6.QtGui import QPainter
from lucent.canvas_items import (
    CanvasItem,
    RectangleItem,
    ArtboardItem,
    EllipseItem,
    GroupItem,
    PathItem,
    TextItem,
    CANVAS_OFFSET_X,
    CANVAS_OFFSET_Y,
)
from lucent.geometry import (
    RectGeometry,
    EllipseGeometry,
    PolylineGeometry,
    TextGeometry,
)
from lucent.appearances import Fill, Stroke
from lucent.transforms import Transform
from PySide6.QtGui import QImage
from PySide6.QtCore import QSize, QRectF


# Helper to create default appearances
def default_appearances(
    fill_color="#ffffff",
    fill_opacity=0.0,
    stroke_color="#ffffff",
    stroke_width=1.0,
    stroke_opacity=1.0,
):
    return [
        Fill(color=fill_color, opacity=fill_opacity),
        Stroke(color=stroke_color, width=stroke_width, opacity=stroke_opacity),
    ]


class TestRectangleItem:
    """Tests for RectangleItem class."""

    def test_basic_creation(self):
        """Test creating a basic rectangle."""
        geometry = RectGeometry(x=10, y=20, width=100, height=50)
        appearances = default_appearances()
        rect = RectangleItem(geometry=geometry, appearances=appearances)
        assert rect.geometry.x == 10
        assert rect.geometry.y == 20
        assert rect.geometry.width == 100
        assert rect.geometry.height == 50

    def test_creation_with_styling(self):
        """Test creating a rectangle with custom styling."""
        geometry = RectGeometry(x=0, y=0, width=50, height=50)
        appearances = [
            Fill(color="#00ff00", opacity=0.5),
            Stroke(color="#ff0000", width=3.0, opacity=0.8),
        ]
        rect = RectangleItem(geometry=geometry, appearances=appearances)
        assert rect.fill.color == "#00ff00"
        assert rect.fill.opacity == 0.5
        assert rect.stroke.color == "#ff0000"
        assert rect.stroke.width == 3.0
        assert rect.stroke.opacity == 0.8

    def test_fill_property_accessor(self):
        """Test fill property returns first Fill appearance."""
        geometry = RectGeometry(x=0, y=0, width=10, height=10)
        appearances = [
            Fill(color="#ff0000", opacity=0.5),
            Stroke(color="#00ff00", width=2.0),
        ]
        rect = RectangleItem(geometry=geometry, appearances=appearances)
        assert rect.fill is not None
        assert rect.fill.color == "#ff0000"
        assert rect.fill.opacity == 0.5

    def test_stroke_property_accessor(self):
        """Test stroke property returns first Stroke appearance."""
        geometry = RectGeometry(x=0, y=0, width=10, height=10)
        appearances = [
            Fill(color="#ff0000", opacity=0.5),
            Stroke(color="#00ff00", width=2.0, opacity=0.8),
        ]
        rect = RectangleItem(geometry=geometry, appearances=appearances)
        assert rect.stroke is not None
        assert rect.stroke.color == "#00ff00"
        assert rect.stroke.width == 2.0
        assert rect.stroke.opacity == 0.8

    def test_has_transform_property(self):
        """RectangleItem should have a transform property."""
        geometry = RectGeometry(x=0, y=0, width=10, height=10)
        rect = RectangleItem(geometry=geometry, appearances=default_appearances())
        assert rect.transform is not None
        assert rect.transform.is_identity()

    def test_from_dict_new_format(self):
        """Test creating rectangle from dictionary with new format."""
        data = {
            "type": "rectangle",
            "geometry": {"x": 15, "y": 25, "width": 80, "height": 60},
            "appearances": [
                {"type": "fill", "color": "#ff0000", "opacity": 0.5, "visible": True},
                {
                    "type": "stroke",
                    "color": "#00ff00",
                    "width": 2.0,
                    "opacity": 0.8,
                    "visible": True,
                },
            ],
        }
        rect = RectangleItem.from_dict(data)
        assert rect.geometry.x == 15
        assert rect.geometry.y == 25
        assert rect.geometry.width == 80
        assert rect.geometry.height == 60
        assert rect.fill.color == "#ff0000"
        assert rect.stroke.color == "#00ff00"

    def test_from_dict_missing_appearances_uses_defaults(self):
        """Test that missing appearances in dictionary creates empty list."""
        data = {
            "type": "rectangle",
            "geometry": {"x": 0, "y": 0, "width": 10, "height": 10},
        }
        rect = RectangleItem.from_dict(data)
        assert rect.appearances == []

    def test_get_bounds(self):
        """Test get_bounds returns correct bounding rect."""
        geometry = RectGeometry(x=10, y=20, width=100, height=50)
        rect = RectangleItem(geometry=geometry, appearances=default_appearances())
        bounds = rect.get_bounds()
        assert bounds == QRectF(10, 20, 100, 50)

    def test_name_property(self):
        """Test name property."""
        geometry = RectGeometry(x=0, y=0, width=10, height=10)
        rect = RectangleItem(
            geometry=geometry, appearances=default_appearances(), name="My Rectangle"
        )
        assert rect.name == "My Rectangle"

    @pytest.mark.parametrize(
        "kwargs, attr, expected",
        [
            ({"name": "My Rectangle"}, "name", "My Rectangle"),
            ({"parent_id": "layer-123"}, "parent_id", "layer-123"),
            ({"locked": True}, "locked", True),
            ({"visible": False}, "visible", False),
        ],
    )
    def test_common_properties(self, kwargs, attr, expected):
        geometry = RectGeometry(x=0, y=0, width=10, height=10)
        rect = RectangleItem(
            geometry=geometry, appearances=default_appearances(), **kwargs
        )
        assert getattr(rect, attr) == expected


class TestEllipseItem:
    """Tests for EllipseItem class."""

    def test_basic_creation(self):
        """Test creating a basic ellipse."""
        geometry = EllipseGeometry(center_x=50, center_y=75, radius_x=30, radius_y=20)
        appearances = default_appearances()
        ellipse = EllipseItem(geometry=geometry, appearances=appearances)
        assert ellipse.geometry.center_x == 50
        assert ellipse.geometry.center_y == 75
        assert ellipse.geometry.radius_x == 30
        assert ellipse.geometry.radius_y == 20

    def test_creation_with_styling(self):
        """Test creating an ellipse with custom styling."""
        geometry = EllipseGeometry(center_x=0, center_y=0, radius_x=10, radius_y=10)
        appearances = [
            Fill(color="#00ffff", opacity=0.6),
            Stroke(color="#ff00ff", width=2.0, opacity=0.9),
        ]
        ellipse = EllipseItem(geometry=geometry, appearances=appearances)
        assert ellipse.fill.color == "#00ffff"
        assert ellipse.fill.opacity == 0.6
        assert ellipse.stroke.color == "#ff00ff"
        assert ellipse.stroke.width == 2.0
        assert ellipse.stroke.opacity == 0.9

    def test_from_dict_new_format(self):
        """Test creating ellipse from dictionary with new format."""
        data = {
            "type": "ellipse",
            "geometry": {
                "centerX": 100,
                "centerY": 150,
                "radiusX": 40,
                "radiusY": 30,
            },
            "appearances": [
                {"type": "fill", "color": "#123456", "opacity": 0.8, "visible": True},
                {
                    "type": "stroke",
                    "color": "#abcdef",
                    "width": 3.5,
                    "opacity": 0.4,
                    "visible": True,
                },
            ],
        }
        ellipse = EllipseItem.from_dict(data)
        assert ellipse.geometry.center_x == 100
        assert ellipse.geometry.center_y == 150
        assert ellipse.geometry.radius_x == 40
        assert ellipse.geometry.radius_y == 30
        assert ellipse.fill.color == "#123456"
        assert ellipse.stroke.color == "#abcdef"

    def test_get_bounds(self):
        """Test get_bounds returns correct bounding rect."""
        geometry = EllipseGeometry(center_x=100, center_y=100, radius_x=50, radius_y=30)
        ellipse = EllipseItem(geometry=geometry, appearances=default_appearances())
        bounds = ellipse.get_bounds()
        assert bounds == QRectF(50, 70, 100, 60)


class TestPathItem:
    """Tests for PathItem class."""

    def test_basic_creation(self):
        """Test creating a basic path."""
        geometry = PolylineGeometry(
            points=[{"x": 0, "y": 0}, {"x": 5, "y": 5}], closed=False
        )
        appearances = default_appearances(stroke_width=1.0, stroke_opacity=1.0)
        path = PathItem(geometry=geometry, appearances=appearances)
        assert len(path.geometry.points) == 2
        assert path.geometry.closed is False

    def test_creation_closed_path(self):
        """Test creating a closed path."""
        geometry = PolylineGeometry(
            points=[{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}],
            closed=True,
        )
        appearances = [
            Fill(color="#112233", opacity=0.5),
            Stroke(color="#00ff00", width=2.0, opacity=1.0),
        ]
        path = PathItem(geometry=geometry, appearances=appearances)
        assert path.geometry.closed is True
        assert path.fill.color == "#112233"
        assert path.stroke.color == "#00ff00"

    def test_from_dict_new_format(self):
        """Test creating path from dictionary with new format."""
        data = {
            "type": "path",
            "geometry": {
                "points": [{"x": 1, "y": 2}, {"x": 3, "y": 4}, {"x": 5, "y": 2}],
                "closed": True,
            },
            "appearances": [
                {"type": "fill", "color": "#101010", "opacity": 0.4, "visible": True},
                {
                    "type": "stroke",
                    "color": "#ff00ff",
                    "width": 2.0,
                    "opacity": 0.75,
                    "visible": True,
                },
            ],
            "name": "Polyline",
        }
        path = PathItem.from_dict(data)
        assert len(path.geometry.points) == 3
        assert path.geometry.closed is True
        assert path.name == "Polyline"
        assert path.fill.color == "#101010"
        assert path.stroke.color == "#ff00ff"

    def test_paint_runs_with_fill(self, qtbot):
        """Smoke test: paint path with fill does not crash."""
        img = QImage(QSize(20, 20), QImage.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        geometry = PolylineGeometry(
            points=[{"x": -5, "y": -5}, {"x": 5, "y": -5}, {"x": 0, "y": 5}],
            closed=True,
        )
        appearances = [
            Fill(color="#ff0000", opacity=0.5),
            Stroke(color="#ffffff", width=1.0, opacity=1.0),
        ]
        path = PathItem(geometry=geometry, appearances=appearances)
        path.paint(painter, zoom_level=1.0)
        painter.end()

    def test_get_bounds(self):
        """Test get_bounds returns bounding rect of all points."""
        geometry = PolylineGeometry(
            points=[{"x": 10, "y": 20}, {"x": 50, "y": 10}, {"x": 30, "y": 60}],
            closed=False,
        )
        path = PathItem(geometry=geometry, appearances=default_appearances())
        bounds = path.get_bounds()
        assert bounds == QRectF(10, 10, 40, 50)


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
        geometry = RectGeometry(x=0, y=0, width=5, height=5)
        rect = RectangleItem(geometry=geometry, appearances=default_appearances())
        rect.paint(painter, zoom_level=1.0)
        painter.end()

    def test_ellipse_paint_runs(self, qtbot):
        img = QImage(QSize(10, 10), QImage.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        geometry = EllipseGeometry(center_x=5, center_y=5, radius_x=4, radius_y=3)
        ellipse = EllipseItem(geometry=geometry, appearances=default_appearances())
        ellipse.paint(painter, zoom_level=2.0)
        painter.end()

    def test_invisible_item_not_painted(self, qtbot):
        """Invisible items should return early from paint."""
        img = QImage(QSize(10, 10), QImage.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        geometry = RectGeometry(x=0, y=0, width=5, height=5)
        rect = RectangleItem(
            geometry=geometry, appearances=default_appearances(), visible=False
        )
        rect.paint(painter, zoom_level=1.0)
        painter.end()


class TestArtboardItem:
    """Tests for ArtboardItem class."""

    def test_basic_creation(self):
        """Test creating a basic artboard with a name."""
        artboard = ArtboardItem(name="Artboard 1")
        assert artboard.name == "Artboard 1"

    def test_creation_with_geometry(self):
        """Test creating an artboard with geometry."""
        artboard = ArtboardItem(x=100, y=50, width=800, height=600)
        assert artboard.x == 100
        assert artboard.y == 50
        assert artboard.width == 800
        assert artboard.height == 600

    def test_background_color_defaults_and_custom(self):
        """Artboards should default to white background and accept custom colors."""
        artboard = ArtboardItem()
        assert artboard.background_color == "#ffffff"
        custom = ArtboardItem(background_color="#112233")
        assert custom.background_color == "#112233"

    def test_creation_empty_name(self):
        """Test creating an artboard with empty name."""
        artboard = ArtboardItem()
        assert artboard.name == ""

    def test_artboard_has_unique_id(self):
        """ArtboardItem should have an auto-generated unique ID."""
        artboard = ArtboardItem(name="Test")
        assert artboard.id is not None
        assert len(artboard.id) > 0

    def test_multiple_artboards_have_different_ids(self):
        """Multiple ArtboardItems should have different IDs."""
        artboard1 = ArtboardItem(name="Artboard 1")
        artboard2 = ArtboardItem(name="Artboard 2")
        assert artboard1.id != artboard2.id

    def test_artboard_id_preserved_when_provided(self):
        """ArtboardItem should use provided ID if given."""
        artboard = ArtboardItem(name="Test", artboard_id="custom-id-123")
        assert artboard.id == "custom-id-123"

    def test_from_dict_with_name(self):
        """Test creating artboard from dictionary with name."""
        data = {
            "type": "artboard",
            "name": "Background",
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 100,
        }
        artboard = ArtboardItem.from_dict(data)
        assert artboard.name == "Background"

    def test_from_dict_with_id(self):
        """Test creating artboard from dictionary with id."""
        data = {
            "type": "artboard",
            "name": "Background",
            "id": "artboard-abc-123",
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 100,
        }
        artboard = ArtboardItem.from_dict(data)
        assert artboard.id == "artboard-abc-123"

    def test_artboard_is_canvas_item(self):
        """ArtboardItem should be a CanvasItem subclass."""
        artboard = ArtboardItem(name="Test Artboard")
        assert isinstance(artboard, CanvasItem)

    def test_get_bounds(self):
        """Artboard get_bounds should return its geometry."""
        artboard = ArtboardItem(x=10, y=20, width=200, height=150)
        bounds = artboard.get_bounds()
        assert bounds.x() == 10
        assert bounds.y() == 20
        assert bounds.width() == 200
        assert bounds.height() == 150

    def test_locked_property(self):
        """Test locked property."""
        artboard = ArtboardItem(name="Test", locked=True)
        assert artboard.locked is True

    def test_visible_property(self):
        """Test visible property."""
        artboard = ArtboardItem(name="Test", visible=False)
        assert artboard.visible is False


class TestGroupItem:
    """Tests for GroupItem class."""

    def test_basic_creation(self):
        """Test creating a basic group."""
        group = GroupItem(name="Group 1")
        assert group.name == "Group 1"

    def test_group_has_unique_id(self):
        """GroupItem should have an auto-generated unique ID."""
        group = GroupItem(name="Test")
        assert group.id is not None
        assert len(group.id) > 0

    def test_from_dict(self):
        """Test creating group from dictionary."""
        data = {"type": "group", "name": "My Group", "id": "group-123"}
        group = GroupItem.from_dict(data)
        assert group.name == "My Group"
        assert group.id == "group-123"

    def test_parent_id_property(self):
        """Test parent_id property."""
        group = GroupItem(name="Test", parent_id="layer-456")
        assert group.parent_id == "layer-456"

    def test_paint_does_nothing(self):
        """Group paint method should be a no-op."""
        group = GroupItem(name="Test Group")
        group.paint(None, 1.0, 0, 0)


class TestTextItem:
    """Tests for TextItem class."""

    def test_basic_creation(self):
        """Test creating a basic text item with default parameters."""
        geometry = TextGeometry(x=10, y=20, width=100, height=0)
        text = TextItem(geometry=geometry, text="Hello")
        assert text.x == 10
        assert text.y == 20
        assert text.text == "Hello"
        assert text.font_family == "Sans Serif"
        assert text.font_size == 16
        assert text.text_color == "#ffffff"
        assert text.text_opacity == 1.0

    def test_creation_with_styling(self):
        """Test creating a text item with custom styling."""
        geometry = TextGeometry(x=0, y=0, width=100, height=0)
        text = TextItem(
            geometry=geometry,
            text="Styled",
            font_family="Monospace",
            font_size=24,
            text_color="#ff0000",
            text_opacity=0.8,
        )
        assert text.font_family == "Monospace"
        assert text.font_size == 24
        assert text.text_color == "#ff0000"
        assert text.text_opacity == 0.8

    @pytest.mark.parametrize(
        "font_size, expected",
        [(2, 8), (500, 200)],
    )
    def test_font_size_clamped(self, font_size, expected):
        """Font size is clamped to valid range."""
        geometry = TextGeometry(x=0, y=0, width=100, height=0)
        text = TextItem(geometry=geometry, text="Size", font_size=font_size)
        assert text.font_size == expected

    @pytest.mark.parametrize(
        "opacity, expected",
        [(-0.5, 0.0), (1.5, 1.0)],
    )
    def test_text_opacity_clamped(self, opacity, expected):
        """Text opacity is clamped to valid range."""
        geometry = TextGeometry(x=0, y=0, width=100, height=0)
        text = TextItem(geometry=geometry, text="Opacity", text_opacity=opacity)
        assert text.text_opacity == expected

    def test_from_dict_basic(self):
        """Test creating text item from dictionary with basic data."""
        data = {"type": "text", "x": 15, "y": 25, "text": "Test Text"}
        text = TextItem.from_dict(data)
        assert text.x == 15
        assert text.y == 25
        assert text.text == "Test Text"

    def test_from_dict_with_styling(self):
        """Test creating text item from dictionary with styling data."""
        data = {
            "type": "text",
            "x": 0,
            "y": 0,
            "text": "Styled Text",
            "fontFamily": "Serif",
            "fontSize": 32,
            "textColor": "#00ff00",
            "textOpacity": 0.6,
        }
        text = TextItem.from_dict(data)
        assert text.font_family == "Serif"
        assert text.font_size == 32
        assert text.text_color == "#00ff00"
        assert text.text_opacity == 0.6

    def test_text_is_canvas_item(self):
        """TextItem should be a CanvasItem subclass."""
        geometry = TextGeometry(x=0, y=0, width=100, height=0)
        text = TextItem(geometry=geometry, text="Hello")
        assert isinstance(text, CanvasItem)

    def test_paint_runs(self, qtbot):
        """Smoke test: paint text does not crash."""
        img = QImage(QSize(100, 50), QImage.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        geometry = TextGeometry(x=0, y=0, width=100, height=0)
        text = TextItem(geometry=geometry, text="Hello World", font_size=16)
        text.paint(painter, zoom_level=1.0)
        painter.end()

    def test_paint_empty_text_returns_early(self, qtbot):
        """TextItem.paint() should return early when text is empty."""
        img = QImage(QSize(100, 50), QImage.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        geometry = TextGeometry(x=0, y=0, width=100, height=0)
        text = TextItem(geometry=geometry, text="")
        text.paint(painter, zoom_level=1.0)
        painter.end()

    def test_get_bounds(self):
        """TextItem.get_bounds() returns bounding rect based on position and width."""
        geometry = TextGeometry(x=10, y=20, width=100, height=30)
        text = TextItem(geometry=geometry, text="Hello")
        bounds = text.get_bounds()
        assert bounds.x() == 10
        assert bounds.y() == 20
        assert bounds.width() == 100
        assert bounds.height() == 30

    def test_width_height_properties(self):
        """TextItem should have width and height properties."""
        geometry = TextGeometry(x=0, y=0, width=200, height=50)
        text = TextItem(geometry=geometry, text="Hello")
        assert text.width == 200
        assert text.height == 50

    def test_name_property(self):
        """TextItem should have a name property."""
        geometry = TextGeometry(x=0, y=0, width=100, height=0)
        text = TextItem(geometry=geometry, text="Hello", name="Text 1")
        assert text.name == "Text 1"

    def test_parent_id_property(self):
        """TextItem should have parent_id property."""
        geometry = TextGeometry(x=0, y=0, width=100, height=0)
        text = TextItem(geometry=geometry, text="Hello", parent_id="layer-123")
        assert text.parent_id == "layer-123"

    def test_locked_property(self):
        """TextItem should have locked property."""
        geometry = TextGeometry(x=0, y=0, width=100, height=0)
        text = TextItem(geometry=geometry, text="Hello", locked=True)
        assert text.locked is True

    def test_visible_property(self):
        """TextItem should have visible property."""
        geometry = TextGeometry(x=0, y=0, width=100, height=0)
        text = TextItem(geometry=geometry, text="Hello", visible=False)
        assert text.visible is False


class TestShapeItemWithTransform:
    """Tests for ShapeItem transform handling."""

    def test_default_pivot_is_center(self):
        """Shapes without explicit transform default pivot to bounds center."""
        geometry = RectGeometry(x=10, y=20, width=100, height=50)
        rect = RectangleItem(geometry=geometry, appearances=default_appearances())
        bounds = geometry.get_bounds()
        assert rect.transform.pivot_x == bounds.x() + bounds.width() * 0.5
        assert rect.transform.pivot_y == bounds.y() + bounds.height() * 0.5

    def test_transform_applied_to_bounds(self):
        """Transform should affect get_bounds result."""
        geometry = RectGeometry(x=0, y=0, width=100, height=50)
        transform = Transform(translate_x=50, translate_y=25)
        rect = RectangleItem(
            geometry=geometry, appearances=default_appearances(), transform=transform
        )
        bounds = rect.get_bounds()
        assert bounds.x() == 50
        assert bounds.y() == 25
        assert bounds.width() == 100
        assert bounds.height() == 50

    def test_identity_transform_no_effect(self):
        """Identity transform should not affect bounds."""
        geometry = RectGeometry(x=10, y=20, width=100, height=50)
        transform = Transform()  # Identity
        rect = RectangleItem(
            geometry=geometry, appearances=default_appearances(), transform=transform
        )
        assert rect.transform.is_identity()
        bounds = rect.get_bounds()
        assert bounds == QRectF(10, 20, 100, 50)

    def test_paint_with_transform(self, qtbot):
        """Paint should apply transform without crashing."""
        img = QImage(QSize(200, 200), QImage.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        geometry = RectGeometry(x=0, y=0, width=50, height=30)
        transform = Transform(translate_x=50, translate_y=50, rotate=45)
        rect = RectangleItem(
            geometry=geometry, appearances=default_appearances(), transform=transform
        )
        rect.paint(painter, zoom_level=1.0)
        painter.end()

    def test_rotation_expands_bounds(self):
        """Rotated shape should have expanded axis-aligned bounding box."""
        import math

        # 100x50 rectangle at origin
        geometry = RectGeometry(x=0, y=0, width=100, height=50)
        # Rotate 45 degrees around center
        transform = Transform(rotate=45, pivot_x=50, pivot_y=25)
        rect = RectangleItem(
            geometry=geometry, appearances=default_appearances(), transform=transform
        )
        bounds = rect.get_bounds()

        # 45 degree rotation of 100x50 rect should produce larger bounding box
        # Diagonal of rectangle determines the new width/height
        diagonal = math.sqrt(100**2 + 50**2)
        # The bounds should be approximately the diagonal in both dimensions
        # (actually slightly less because it's not a square)
        assert bounds.width() > 100  # Wider than original
        assert bounds.height() > 50  # Taller than original
        assert bounds.width() < diagonal + 1  # But not larger than diagonal

    def test_rotation_with_topleft_origin(self):
        """Rotation around top-left origin produces different bounds than center."""
        # Rectangle at (50, 50) with size 100x50
        geometry = RectGeometry(x=50, y=50, width=100, height=50)

        # Rotate around top-left
        transform_tl = Transform(rotate=90, pivot_x=50, pivot_y=50)
        rect_tl = RectangleItem(
            geometry=geometry, appearances=default_appearances(), transform=transform_tl
        )
        bounds_tl = rect_tl.get_bounds()

        # Rotate around center
        transform_center = Transform(rotate=90, pivot_x=100, pivot_y=75)
        rect_center = RectangleItem(
            geometry=geometry,
            appearances=default_appearances(),
            transform=transform_center,
        )
        bounds_center = rect_center.get_bounds()

        # Bounds should be different positions
        assert bounds_tl.x() != bounds_center.x() or bounds_tl.y() != bounds_center.y()

    def test_combined_translate_and_rotate_bounds(self):
        """Combined translation and rotation produces correct bounds."""
        geometry = RectGeometry(x=0, y=0, width=100, height=50)
        # Translate then rotate around center
        transform = Transform(
            translate_x=100, translate_y=100, rotate=90, pivot_x=50, pivot_y=25
        )
        rect = RectangleItem(
            geometry=geometry, appearances=default_appearances(), transform=transform
        )
        bounds = rect.get_bounds()

        # After 90 degree rotation around center, width and height swap
        # Translation shifts the whole thing
        assert abs(bounds.width() - 50) < 0.01  # Width becomes height
        assert abs(bounds.height() - 100) < 0.01  # Height becomes width
        # Center should be at (50 + 100, 25 + 100) = (150, 125)
        center_x = bounds.x() + bounds.width() / 2
        center_y = bounds.y() + bounds.height() / 2
        assert abs(center_x - 150) < 0.01
        assert abs(center_y - 125) < 0.01

    def test_origin_affects_rotation_pivot(self):
        """Different origin points produce different rotation results."""
        geometry = RectGeometry(x=0, y=0, width=100, height=100)

        # Rotate 180 degrees around top-left - shape moves to negative quadrant
        transform_tl = Transform(rotate=180, pivot_x=0, pivot_y=0)
        rect_tl = RectangleItem(
            geometry=geometry, appearances=default_appearances(), transform=transform_tl
        )
        bounds_tl = rect_tl.get_bounds()
        assert bounds_tl.x() == -100  # Rotated to left
        assert bounds_tl.y() == -100  # Rotated up

        # Rotate 180 degrees around center - shape stays in same position
        transform_center = Transform(rotate=180, pivot_x=50, pivot_y=50)
        rect_center = RectangleItem(
            geometry=geometry,
            appearances=default_appearances(),
            transform=transform_center,
        )
        bounds_center = rect_center.get_bounds()
        assert abs(bounds_center.x()) < 0.01  # Stays at origin
        assert abs(bounds_center.y()) < 0.01
