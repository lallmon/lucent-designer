"""Unit tests for canvas_items module."""

import pytest
from PySide6.QtGui import QPainter
from lucent.canvas_items import (
    CanvasItem,
    RectangleItem,
    EllipseItem,
    LayerItem,
    GroupItem,
    PathItem,
    TextItem,
    CANVAS_OFFSET_X,
    CANVAS_OFFSET_Y,
)
from PySide6.QtGui import QImage
from PySide6.QtCore import QSize, QRectF


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

    def test_stroke_width_allows_zero(self):
        """Test that stroke width of 0 is allowed (no stroke)."""
        rect = RectangleItem(x=0, y=0, width=10, height=10, stroke_width=0)
        assert rect.stroke_width == 0.0

    def test_stroke_width_clamps_negative(self):
        """Test that negative stroke width is clamped to 0."""
        rect = RectangleItem(x=0, y=0, width=10, height=10, stroke_width=-5)
        assert rect.stroke_width == 0.0

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

    def test_stroke_width_allows_zero(self):
        """Test that stroke width of 0 is allowed (no stroke)."""
        ellipse = EllipseItem(
            center_x=0, center_y=0, radius_x=10, radius_y=10, stroke_width=0
        )
        assert ellipse.stroke_width == 0.0

    def test_stroke_width_clamps_negative(self):
        """Test that negative stroke width is clamped to 0."""
        ellipse = EllipseItem(
            center_x=0, center_y=0, radius_x=10, radius_y=10, stroke_width=-1
        )
        assert ellipse.stroke_width == 0.0

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
        """Test that from_dict clamps negative stroke width to 0."""
        data = {
            "type": "ellipse",
            "centerX": 0,
            "centerY": 0,
            "radiusX": 10,
            "radiusY": 10,
            "strokeWidth": -5,
        }
        ellipse = EllipseItem.from_dict(data)
        assert ellipse.stroke_width == 0.0

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


class TestPathItem:
    """Tests for PathItem class."""

    def test_basic_creation_defaults(self):
        """PathItem defaults to stroke-only and open path."""
        path = PathItem(points=[{"x": 0, "y": 0}, {"x": 5, "y": 5}])
        assert path.stroke_width == 1
        assert path.stroke_color == "#ffffff"
        assert path.stroke_opacity == 1.0
        assert path.fill_opacity == 0.0
        assert path.closed is False
        assert path.points == [{"x": 0.0, "y": 0.0}, {"x": 5.0, "y": 5.0}]

    def test_creation_with_closed_and_clamping(self):
        """Closed path clamps stroke and opacity values."""
        path = PathItem(
            points=[{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}],
            stroke_width=-5,
            stroke_opacity=2.0,
            fill_opacity=1.5,
            closed=True,
            stroke_color="#00ff00",
            fill_color="#112233",
        )
        assert path.stroke_width == 0.0
        assert path.stroke_opacity == 1.0
        assert path.closed is True
        assert path.stroke_color == "#00ff00"
        assert path.fill_opacity == 1.0
        assert path.fill_color == "#112233"

    def test_from_dict_preserves_points_and_closed(self):
        """from_dict creates PathItem with provided points and closed flag."""
        data = {
            "type": "path",
            "points": [{"x": 1, "y": 2}, {"x": 3, "y": 4}, {"x": 5, "y": 2}],
            "strokeWidth": 2,
            "strokeColor": "#ff00ff",
            "strokeOpacity": 0.75,
            "closed": True,
            "name": "Polyline",
            "fillColor": "#101010",
            "fillOpacity": 0.4,
        }
        path = PathItem.from_dict(data)
        assert path.points == [
            {"x": 1.0, "y": 2.0},
            {"x": 3.0, "y": 4.0},
            {"x": 5.0, "y": 2.0},
        ]
        assert path.stroke_width == 2
        assert path.stroke_color == "#ff00ff"
        assert path.stroke_opacity == 0.75
        assert path.closed is True
        assert path.name == "Polyline"
        assert path.fill_color == "#101010"
        assert path.fill_opacity == 0.4

    def test_paint_runs_with_fill(self, qtbot):
        """Smoke test: paint path with fill does not crash."""
        img = QImage(QSize(20, 20), QImage.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        path = PathItem(
            points=[{"x": -5, "y": -5}, {"x": 5, "y": -5}, {"x": 0, "y": 5}],
            stroke_width=1,
            stroke_color="#ffffff",
            stroke_opacity=1.0,
            fill_color="#ff0000",
            fill_opacity=0.5,
            closed=True,
        )
        path.paint(painter, zoom_level=1.0)
        painter.end()

    def test_path_requires_two_points(self):
        """Constructor should reject fewer than two points."""
        with pytest.raises(ValueError):
            PathItem(points=[{"x": 0, "y": 0}])

    def test_path_from_dict_invalid_points_raises(self):
        """from_dict should reject non-list points."""
        with pytest.raises(ValueError):
            PathItem.from_dict({"type": "path", "points": "bad"})

    def test_paint_no_points_returns_early(self):
        """Paint should no-op gracefully when no points exist."""
        img = QImage(QSize(10, 10), QImage.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        path = PathItem(points=[{"x": 0, "y": 0}, {"x": 1, "y": 1}])
        # empty points to trigger early return
        path.points = []
        path.paint(painter, zoom_level=1.0)
        painter.end()

    def test_paint_closed_without_fill(self, qtbot):
        """Closed path with no fill still renders stroke."""
        img = QImage(QSize(20, 20), QImage.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        path = PathItem(
            points=[{"x": -2, "y": -2}, {"x": 2, "y": -2}, {"x": 0, "y": 2}],
            stroke_width=2,
            stroke_color="#00ffff",
            stroke_opacity=1.0,
            closed=True,
        )
        path.paint(painter, zoom_level=1.0)
        painter.end()


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


class TestTextItem:
    """Tests for TextItem class."""

    def test_basic_creation(self):
        """Test creating a basic text item with default parameters."""
        text = TextItem(x=10, y=20, text="Hello")
        assert text.x == 10
        assert text.y == 20
        assert text.text == "Hello"
        assert text.font_family == "Sans Serif"
        assert text.font_size == 16
        assert text.text_color == "#ffffff"
        assert text.text_opacity == 1.0

    def test_creation_with_styling(self):
        """Test creating a text item with custom styling."""
        text = TextItem(
            x=0,
            y=0,
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

    def test_font_size_minimum_clamped(self):
        """Test that font size below 8 is clamped to 8."""
        text = TextItem(x=0, y=0, text="Small", font_size=2)
        assert text.font_size == 8

    def test_font_size_maximum_clamped(self):
        """Test that font size above 200 is clamped to 200."""
        text = TextItem(x=0, y=0, text="Large", font_size=500)
        assert text.font_size == 200

    def test_text_opacity_minimum_clamped(self):
        """Test that text opacity below 0 is clamped to 0."""
        text = TextItem(x=0, y=0, text="Faded", text_opacity=-0.5)
        assert text.text_opacity == 0.0

    def test_text_opacity_maximum_clamped(self):
        """Test that text opacity above 1 is clamped to 1."""
        text = TextItem(x=0, y=0, text="Solid", text_opacity=1.5)
        assert text.text_opacity == 1.0

    def test_empty_text_allowed(self):
        """Test that empty text string is allowed."""
        text = TextItem(x=0, y=0, text="")
        assert text.text == ""

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

    def test_from_dict_missing_fields_use_defaults(self):
        """Test that missing fields in dictionary use default values."""
        data = {"type": "text", "text": "Minimal"}
        text = TextItem.from_dict(data)
        assert text.x == 0
        assert text.y == 0
        assert text.font_family == "Sans Serif"
        assert text.font_size == 16
        assert text.text_color == "#ffffff"
        assert text.text_opacity == 1.0

    def test_from_dict_validates_font_size_bounds(self):
        """Test that from_dict clamps font size to valid range."""
        data = {"type": "text", "x": 0, "y": 0, "text": "Big", "fontSize": 999}
        text = TextItem.from_dict(data)
        assert text.font_size == 200

    def test_from_dict_validates_opacity_bounds(self):
        """Test that from_dict clamps opacity values."""
        data = {"type": "text", "x": 0, "y": 0, "text": "Test", "textOpacity": 5.0}
        text = TextItem.from_dict(data)
        assert text.text_opacity == 1.0

    def test_text_has_name_property(self):
        """TextItem should have a name property."""
        text = TextItem(x=0, y=0, text="Hello", name="Text 1")
        assert text.name == "Text 1"

    def test_text_name_defaults_to_empty(self):
        """TextItem name should default to empty string."""
        text = TextItem(x=0, y=0, text="Hello")
        assert text.name == ""

    def test_text_no_parent_by_default(self):
        """TextItem should have no parent by default."""
        text = TextItem(x=0, y=0, text="Hello")
        assert text.parent_id is None

    def test_text_with_parent_id(self):
        """TextItem can be created with a parent_id."""
        text = TextItem(x=0, y=0, text="Hello", parent_id="layer-123")
        assert text.parent_id == "layer-123"

    def test_text_unlocked_by_default(self):
        """TextItem should be unlocked by default."""
        text = TextItem(x=0, y=0, text="Hello")
        assert text.locked is False

    def test_text_with_locked_true(self):
        """TextItem can be created with locked=True."""
        text = TextItem(x=0, y=0, text="Hello", locked=True)
        assert text.locked is True

    def test_text_visible_by_default(self):
        """TextItem should be visible by default."""
        text = TextItem(x=0, y=0, text="Hello")
        assert text.visible is True

    def test_text_with_visible_false(self):
        """TextItem can be created with visible=False."""
        text = TextItem(x=0, y=0, text="Hello", visible=False)
        assert text.visible is False

    def test_text_is_canvas_item(self):
        """TextItem should be a CanvasItem subclass."""
        text = TextItem(x=0, y=0, text="Hello")
        assert isinstance(text, CanvasItem)

    def test_paint_runs(self, qtbot):
        """Smoke test: paint text does not crash."""
        img = QImage(QSize(100, 50), QImage.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        text = TextItem(x=0, y=0, text="Hello World", font_size=16)
        text.paint(painter, zoom_level=1.0)
        painter.end()

    def test_paint_with_zoom(self, qtbot):
        """Text paint should handle zoom levels."""
        img = QImage(QSize(200, 100), QImage.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        text = TextItem(x=10, y=10, text="Zoomed", font_size=20)
        text.paint(painter, zoom_level=2.0)
        painter.end()

    def test_from_dict_with_parent_id(self):
        """TextItem.from_dict should parse parentId."""
        data = {
            "type": "text",
            "x": 0,
            "y": 0,
            "text": "Hello",
            "parentId": "layer-abc",
        }
        text = TextItem.from_dict(data)
        assert text.parent_id == "layer-abc"

    def test_from_dict_with_locked(self):
        """TextItem.from_dict should parse locked."""
        data = {
            "type": "text",
            "x": 0,
            "y": 0,
            "text": "Hello",
            "locked": True,
        }
        text = TextItem.from_dict(data)
        assert text.locked is True

    def test_from_dict_with_visible(self):
        """TextItem.from_dict should parse visible."""
        data = {
            "type": "text",
            "x": 0,
            "y": 0,
            "text": "Hello",
            "visible": False,
        }
        text = TextItem.from_dict(data)
        assert text.visible is False

    def test_text_has_width_height_properties(self):
        """TextItem should have width and height properties for text box."""
        text = TextItem(x=0, y=0, text="Hello", width=200, height=50)
        assert text.width == 200
        assert text.height == 50

    def test_text_width_height_default_values(self):
        """TextItem width/height should have sensible defaults."""
        text = TextItem(x=0, y=0, text="Hello")
        # Default width should be reasonable for a text box
        assert text.width == 100
        # Default height of 0 means auto-height (not constrained)
        assert text.height == 0

    def test_text_width_minimum_clamped(self):
        """TextItem width should be clamped to minimum of 1."""
        text = TextItem(x=0, y=0, text="Hello", width=-10)
        assert text.width == 1

    def test_text_height_minimum_clamped(self):
        """TextItem height should be clamped to minimum of 0 (auto)."""
        text = TextItem(x=0, y=0, text="Hello", height=-10)
        assert text.height == 0

    def test_from_dict_with_width_height(self):
        """TextItem.from_dict should parse width and height."""
        data = {
            "type": "text",
            "x": 10,
            "y": 20,
            "text": "Box Text",
            "width": 300,
            "height": 100,
        }
        text = TextItem.from_dict(data)
        assert text.width == 300
        assert text.height == 100

    def test_from_dict_width_height_defaults(self):
        """TextItem.from_dict should use defaults for missing width/height."""
        data = {"type": "text", "x": 0, "y": 0, "text": "Hello"}
        text = TextItem.from_dict(data)
        assert text.width == 100
        assert text.height == 0

    def test_paint_empty_text_returns_early(self, qtbot):
        """TextItem.paint() should return early when text is empty."""
        img = QImage(QSize(100, 50), QImage.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        text = TextItem(x=0, y=0, text="")
        # Should not crash and should return early
        text.paint(painter, zoom_level=1.0)
        painter.end()

    def test_paint_multiline_text(self, qtbot):
        """TextItem.paint() should handle multiline text with newlines."""
        img = QImage(QSize(200, 100), QImage.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        text = TextItem(x=0, y=0, text="Line 1\nLine 2\nLine 3", width=200)
        text.paint(painter, zoom_level=1.0)
        painter.end()


class TestGetBounds:
    """Tests for get_bounds() method on canvas items."""

    def test_rectangle_bounds(self):
        """RectangleItem.get_bounds() returns correct bounding rect."""
        rect = RectangleItem(x=10, y=20, width=100, height=50)
        bounds = rect.get_bounds()
        assert bounds == QRectF(10, 20, 100, 50)

    def test_rectangle_bounds_at_origin(self):
        """RectangleItem at origin returns correct bounds."""
        rect = RectangleItem(x=0, y=0, width=50, height=30)
        bounds = rect.get_bounds()
        assert bounds == QRectF(0, 0, 50, 30)

    def test_rectangle_bounds_negative_position(self):
        """RectangleItem with negative position returns correct bounds."""
        rect = RectangleItem(x=-50, y=-25, width=100, height=50)
        bounds = rect.get_bounds()
        assert bounds == QRectF(-50, -25, 100, 50)

    def test_ellipse_bounds(self):
        """EllipseItem.get_bounds() returns correct bounding rect."""
        ellipse = EllipseItem(center_x=100, center_y=100, radius_x=50, radius_y=30)
        bounds = ellipse.get_bounds()
        assert bounds == QRectF(50, 70, 100, 60)

    def test_ellipse_bounds_at_origin(self):
        """EllipseItem centered at origin returns correct bounds."""
        ellipse = EllipseItem(center_x=0, center_y=0, radius_x=25, radius_y=25)
        bounds = ellipse.get_bounds()
        assert bounds == QRectF(-25, -25, 50, 50)

    def test_path_bounds(self):
        """PathItem.get_bounds() returns bounding rect of all points."""
        path = PathItem(
            points=[
                {"x": 10, "y": 20},
                {"x": 50, "y": 10},
                {"x": 30, "y": 60},
            ]
        )
        bounds = path.get_bounds()
        assert bounds == QRectF(10, 10, 40, 50)

    def test_path_bounds_single_line(self):
        """PathItem with two points returns correct bounds."""
        path = PathItem(points=[{"x": 0, "y": 0}, {"x": 100, "y": 100}])
        bounds = path.get_bounds()
        assert bounds == QRectF(0, 0, 100, 100)

    def test_path_bounds_negative_coords(self):
        """PathItem with negative coordinates returns correct bounds."""
        path = PathItem(
            points=[
                {"x": -50, "y": -30},
                {"x": 50, "y": 30},
            ]
        )
        bounds = path.get_bounds()
        assert bounds == QRectF(-50, -30, 100, 60)

    def test_text_bounds(self):
        """TextItem.get_bounds() returns bounding rect based on position and width."""
        text = TextItem(x=10, y=20, text="Hello", width=100, height=30)
        bounds = text.get_bounds()
        assert bounds.x() == 10
        assert bounds.y() == 20
        assert bounds.width() == 100
        assert bounds.height() == 30

    def test_text_bounds_auto_height(self, qtbot):
        """TextItem with height=0 (auto) returns positive height based on font."""
        text = TextItem(x=0, y=0, text="Hello", width=100, height=0, font_size=16)
        bounds = text.get_bounds()
        assert bounds.x() == 0
        assert bounds.y() == 0
        assert bounds.width() == 100
        assert bounds.height() > 0

    def test_layer_bounds_empty(self):
        """LayerItem.get_bounds() returns empty rect (non-rendering)."""
        layer = LayerItem(name="Test Layer")
        bounds = layer.get_bounds()
        assert bounds.isEmpty() or bounds == QRectF()

    def test_group_bounds_empty(self):
        """GroupItem.get_bounds() returns empty rect (non-rendering)."""
        group = GroupItem(name="Test Group")
        bounds = group.get_bounds()
        assert bounds.isEmpty() or bounds == QRectF()


class TestRectangleItemNewArchitecture:
    """Tests for RectangleItem with new geometry+appearances architecture."""

    def test_has_geometry_property(self):
        """RectangleItem should have a geometry property."""
        rect = RectangleItem(x=10, y=20, width=100, height=50)
        assert hasattr(rect, "geometry")
        assert rect.geometry is not None

    def test_geometry_matches_dimensions(self):
        """RectangleItem geometry should match constructor dimensions."""
        rect = RectangleItem(x=10, y=20, width=100, height=50)
        assert rect.geometry.x == 10
        assert rect.geometry.y == 20
        assert rect.geometry.width == 100
        assert rect.geometry.height == 50

    def test_has_appearances_property(self):
        """RectangleItem should have an appearances list."""
        rect = RectangleItem(x=0, y=0, width=10, height=10)
        assert hasattr(rect, "appearances")
        assert isinstance(rect.appearances, list)
        assert len(rect.appearances) >= 2  # At least fill and stroke

    def test_fill_property_accessor(self):
        """RectangleItem should have fill property accessor."""
        rect = RectangleItem(
            x=0, y=0, width=10, height=10, fill_color="#ff0000", fill_opacity=0.5
        )
        assert rect.fill is not None
        assert rect.fill.color == "#ff0000"
        assert rect.fill.opacity == 0.5

    def test_stroke_property_accessor(self):
        """RectangleItem should have stroke property accessor."""
        rect = RectangleItem(
            x=0,
            y=0,
            width=10,
            height=10,
            stroke_color="#00ff00",
            stroke_width=3.0,
            stroke_opacity=0.8,
        )
        assert rect.stroke is not None
        assert rect.stroke.color == "#00ff00"
        assert rect.stroke.width == 3.0
        assert rect.stroke.opacity == 0.8

    def test_has_transform_property(self):
        """RectangleItem should have a transform property."""
        rect = RectangleItem(x=0, y=0, width=10, height=10)
        assert hasattr(rect, "transform")
        assert rect.transform is not None
        assert rect.transform.is_identity()

    def test_get_bounds_uses_geometry(self):
        """RectangleItem.get_bounds() should use geometry bounds."""
        rect = RectangleItem(x=10, y=20, width=100, height=50)
        bounds = rect.get_bounds()
        assert bounds == QRectF(10, 20, 100, 50)

    def test_paint_smoke_test(self, qtbot):
        """Smoke test: paint with new architecture does not crash."""
        img = QImage(QSize(100, 100), QImage.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        rect = RectangleItem(
            x=10,
            y=10,
            width=50,
            height=30,
            fill_color="#ff0000",
            fill_opacity=0.5,
            stroke_color="#00ff00",
            stroke_width=2.0,
        )
        rect.paint(painter, zoom_level=1.0)
        painter.end()

    def test_backwards_compatible_properties(self):
        """RectangleItem should maintain backwards-compatible properties."""
        rect = RectangleItem(
            x=10,
            y=20,
            width=100,
            height=50,
            stroke_width=3,
            stroke_color="#ff0000",
            fill_color="#00ff00",
            fill_opacity=0.5,
            stroke_opacity=0.8,
        )
        # Old-style property access should still work
        assert rect.x == 10
        assert rect.y == 20
        assert rect.width == 100
        assert rect.height == 50
        assert rect.stroke_width == 3
        assert rect.stroke_color == "#ff0000"
        assert rect.fill_color == "#00ff00"
        assert rect.fill_opacity == 0.5
        assert rect.stroke_opacity == 0.8

    def test_from_dict_legacy_format(self):
        """RectangleItem.from_dict should handle legacy flat format."""
        data = {
            "type": "rectangle",
            "x": 10,
            "y": 20,
            "width": 100,
            "height": 50,
            "strokeWidth": 3,
            "strokeColor": "#ff0000",
            "strokeOpacity": 0.8,
            "fillColor": "#00ff00",
            "fillOpacity": 0.5,
        }
        rect = RectangleItem.from_dict(data)
        assert rect.x == 10
        assert rect.y == 20
        assert rect.width == 100
        assert rect.height == 50
        assert rect.fill.color == "#00ff00"
        assert rect.fill.opacity == 0.5
        assert rect.stroke.color == "#ff0000"
        assert rect.stroke.width == 3
        assert rect.stroke.opacity == 0.8
