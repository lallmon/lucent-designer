"""Unit tests for item_schema validation and serialization."""

import pytest

from lucent.canvas_items import (
    RectangleItem,
    EllipseItem,
    LayerItem,
    CanvasItem,
    PathItem,
    TextItem,
)
from lucent.item_schema import (
    ItemSchemaError,
    ItemType,
    parse_item,
    parse_item_data,
    validate_rectangle,
    validate_ellipse,
    validate_layer,
    validate_path,
    validate_text,
    item_to_dict,
)


def test_parse_item_data_rejects_missing_type():
    with pytest.raises(ItemSchemaError):
        parse_item_data({})


def test_parse_item_data_rejects_unknown_type():
    with pytest.raises(ItemSchemaError):
        parse_item_data({"type": "triangle"})


def test_validate_path_clamps_and_defaults():
    data = {
        "type": "path",
        "points": [{"x": 1, "y": 2}, {"x": -3, "y": 4}],
        "strokeWidth": -1,
        "strokeOpacity": 2,
        "closed": True,
        "strokeColor": "#123456",
        "fillColor": "#abcdef",
        "fillOpacity": 0.8,
    }
    out = validate_path(data)
    assert out["points"] == [{"x": 1.0, "y": 2.0}, {"x": -3.0, "y": 4.0}]
    assert out["strokeWidth"] == 0.0  # Minimum is 0 (no stroke)
    assert out["strokeOpacity"] == 1.0
    assert out["fillOpacity"] == 0.8
    assert out["closed"] is True
    assert out["strokeColor"] == "#123456"
    assert out["fillColor"] == "#abcdef"


def test_validate_path_requires_two_points():
    with pytest.raises(ItemSchemaError):
        validate_path({"type": "path", "points": [{"x": 0, "y": 0}]})


def test_validate_rectangle_clamps_and_defaults():
    data = {
        "type": "rectangle",
        "x": 1,
        "y": 2,
        "width": -5,
        "height": 10,
        "strokeWidth": 0.01,
        "strokeOpacity": 5.0,
        "fillOpacity": -2.0,
        "strokeColor": "#abc",
        "fillColor": "#def",
        "name": "Rect",
        "parentId": "layer-1",
    }
    out = validate_rectangle(data)
    assert out["width"] == 0.0
    assert out["height"] == 10
    assert out["strokeWidth"] == 0.01  # Values >= 0 pass through (0 = no stroke)
    assert out["strokeOpacity"] == 1.0
    assert out["fillOpacity"] == 0.0
    assert out["strokeColor"] == "#abc"
    assert out["fillColor"] == "#def"
    assert out["name"] == "Rect"
    assert out["parentId"] == "layer-1"


def test_validate_ellipse_clamps_and_defaults():
    data = {
        "type": "ellipse",
        "centerX": 3,
        "centerY": 4,
        "radiusX": -1,
        "radiusY": 5,
        "strokeWidth": 999,
        "strokeOpacity": -1,
        "fillOpacity": 2,
        "strokeColor": "#111",
        "fillColor": "#222",
        "name": "Ell",
        "parentId": "",
    }
    out = validate_ellipse(data)
    assert out["radiusX"] == 0.0
    assert out["radiusY"] == 5
    assert out["strokeWidth"] == 100.0
    assert out["strokeOpacity"] == 0.0
    assert out["fillOpacity"] == 1.0
    assert out["parentId"] is None
    assert out["name"] == "Ell"


def test_validate_layer_defaults_and_preserves_id():
    out = validate_layer({"type": "layer", "name": "Layer", "id": "custom"})
    assert out["name"] == "Layer"
    assert out["id"] == "custom"

    out2 = validate_layer({"type": "layer"})
    assert out2["name"] == ""
    assert out2["id"] is None


def test_validate_text_clamps_and_defaults():
    """validate_text should clamp font size and opacity values."""
    data = {
        "type": "text",
        "x": 10,
        "y": 20,
        "text": "Hello",
        "fontFamily": "Monospace",
        "fontSize": 5,  # Below minimum
        "textColor": "#ff0000",
        "textOpacity": 2.0,  # Above maximum
        "name": "MyText",
        "parentId": "layer-1",
    }
    out = validate_text(data)
    assert out["x"] == 10
    assert out["y"] == 20
    assert out["text"] == "Hello"
    assert out["fontFamily"] == "Monospace"
    assert out["fontSize"] == 8  # Clamped to minimum
    assert out["textColor"] == "#ff0000"
    assert out["textOpacity"] == 1.0  # Clamped to maximum
    assert out["name"] == "MyText"
    assert out["parentId"] == "layer-1"


def test_validate_text_defaults():
    """validate_text should use defaults for missing fields."""
    data = {"type": "text", "text": "Hello"}
    out = validate_text(data)
    assert out["x"] == 0
    assert out["y"] == 0
    assert out["fontFamily"] == "Sans Serif"
    assert out["fontSize"] == 16
    assert out["textColor"] == "#ffffff"
    assert out["textOpacity"] == 1.0
    assert out["name"] == ""
    assert out["width"] == 100
    assert out["height"] == 0
    assert out["parentId"] is None
    assert out["visible"] is True
    assert out["locked"] is False


def test_validate_text_empty_parent_id_becomes_none():
    """validate_text should convert empty parentId to None."""
    data = {"type": "text", "text": "Hello", "parentId": ""}
    out = validate_text(data)
    assert out["parentId"] is None


def test_validate_text_invalid_numeric_raises():
    """validate_text should raise for invalid numeric fields."""
    data = {"type": "text", "text": "Hello", "fontSize": "not-a-number"}
    with pytest.raises(ItemSchemaError, match="Invalid text numeric field"):
        validate_text(data)


def test_parse_item_returns_concrete_items():
    rect = parse_item({"type": "rectangle", "width": 1, "height": 1})
    assert isinstance(rect, RectangleItem)
    ell = parse_item({"type": "ellipse", "radiusX": 2, "radiusY": 3})
    assert isinstance(ell, EllipseItem)
    layer = parse_item({"type": "layer"})
    assert isinstance(layer, LayerItem)
    path = parse_item(
        {
            "type": "path",
            "points": [{"x": 0, "y": 0}, {"x": 5, "y": 0}],
            "strokeWidth": 1,
        }
    )
    assert isinstance(path, PathItem)
    assert path.closed is False
    text = parse_item({"type": "text", "text": "Hello", "fontSize": 20})
    assert isinstance(text, TextItem)
    assert text.text == "Hello"
    assert text.font_size == 20


def test_item_to_dict_round_trips_rectangle():
    rect = RectangleItem(x=1, y=2, width=3, height=4, name="R", parent_id="p")
    out = item_to_dict(rect)
    assert out["type"] == ItemType.RECTANGLE.value
    assert out["name"] == "R"
    assert out["parentId"] == "p"
    assert out["width"] == 3
    assert out["height"] == 4


def test_item_to_dict_round_trips_ellipse():
    ell = EllipseItem(center_x=1, center_y=2, radius_x=3, radius_y=4, name="E")
    out = item_to_dict(ell)
    assert out["type"] == ItemType.ELLIPSE.value
    assert out["centerX"] == 1
    assert out["radiusY"] == 4
    assert out["name"] == "E"


def test_item_to_dict_round_trips_layer():
    layer = LayerItem(name="L", layer_id="lid")
    out = item_to_dict(layer)
    assert out["type"] == ItemType.LAYER.value
    assert out["name"] == "L"
    assert out["id"] == "lid"


def test_item_to_dict_round_trips_path():
    path = PathItem(
        points=[{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}],
        stroke_width=2,
        stroke_color="#00ff00",
        stroke_opacity=0.5,
        closed=True,
        name="P1",
        parent_id="layer-1",
    )
    out = item_to_dict(path)
    assert out["type"] == ItemType.PATH.value
    assert out["name"] == "P1"
    assert out["parentId"] == "layer-1"
    assert out["strokeWidth"] == 2
    assert out["strokeOpacity"] == 0.5
    assert out["closed"] is True
    assert out["points"][0] == {"x": 0.0, "y": 0.0}


def test_item_to_dict_round_trips_text():
    """item_to_dict should serialize TextItem correctly."""
    text = TextItem(
        x=10,
        y=20,
        text="Hello World",
        font_family="Monospace",
        font_size=24,
        text_color="#ff0000",
        text_opacity=0.8,
        width=200,
        height=50,
        name="T1",
        parent_id="layer-2",
    )
    out = item_to_dict(text)
    assert out["type"] == ItemType.TEXT.value
    assert out["x"] == 10
    assert out["y"] == 20
    assert out["width"] == 200
    assert out["height"] == 50
    assert out["text"] == "Hello World"
    assert out["fontFamily"] == "Monospace"
    assert out["fontSize"] == 24
    assert out["textColor"] == "#ff0000"
    assert out["textOpacity"] == 0.8
    assert out["name"] == "T1"
    assert out["parentId"] == "layer-2"


def test_parse_item_invalid_ellipse_raises():
    with pytest.raises(ItemSchemaError):
        parse_item({"type": "ellipse", "centerX": "bad"})


def test_item_to_dict_rejects_unknown():
    from PySide6.QtCore import QRectF

    class Unknown(CanvasItem):
        def paint(self, painter, zoom_level, offset_x=0, offset_y=0):
            pass

        def get_bounds(self) -> QRectF:
            return QRectF()

        @staticmethod
        def from_dict(data):
            return Unknown()

    with pytest.raises(ItemSchemaError):
        item_to_dict(Unknown())


class TestLockedSerialization:
    """Tests for locked property validation and serialization."""

    def test_validate_rectangle_includes_locked(self):
        """validate_rectangle should include locked in output."""
        data = {
            "type": "rectangle",
            "x": 0,
            "y": 0,
            "width": 10,
            "height": 10,
            "locked": True,
        }
        out = validate_rectangle(data)
        assert out["locked"] is True

    def test_validate_rectangle_locked_defaults_false(self):
        """validate_rectangle should default locked to False."""
        data = {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10}
        out = validate_rectangle(data)
        assert out["locked"] is False

    def test_validate_ellipse_includes_locked(self):
        """validate_ellipse should include locked in output."""
        data = {
            "type": "ellipse",
            "centerX": 0,
            "centerY": 0,
            "radiusX": 10,
            "radiusY": 10,
            "locked": True,
        }
        out = validate_ellipse(data)
        assert out["locked"] is True

    def test_validate_ellipse_locked_defaults_false(self):
        """validate_ellipse should default locked to False."""
        data = {
            "type": "ellipse",
            "centerX": 0,
            "centerY": 0,
            "radiusX": 10,
            "radiusY": 10,
        }
        out = validate_ellipse(data)
        assert out["locked"] is False

    def test_validate_layer_includes_locked(self):
        """validate_layer should include locked in output."""
        data = {"type": "layer", "name": "Test", "locked": True}
        out = validate_layer(data)
        assert out["locked"] is True

    def test_validate_layer_locked_defaults_false(self):
        """validate_layer should default locked to False."""
        data = {"type": "layer", "name": "Test"}
        out = validate_layer(data)
        assert out["locked"] is False

    def test_parse_item_rectangle_preserves_locked(self):
        """parse_item should create RectangleItem with locked property."""
        rect = parse_item(
            {"type": "rectangle", "width": 10, "height": 10, "locked": True}
        )
        assert rect.locked is True

    def test_parse_item_ellipse_preserves_locked(self):
        """parse_item should create EllipseItem with locked property."""
        ell = parse_item(
            {"type": "ellipse", "radiusX": 10, "radiusY": 10, "locked": True}
        )
        assert ell.locked is True

    def test_parse_item_layer_preserves_locked(self):
        """parse_item should create LayerItem with locked property."""
        layer = parse_item({"type": "layer", "locked": True})
        assert layer.locked is True

    def test_item_to_dict_rectangle_includes_locked(self):
        """item_to_dict should include locked for RectangleItem."""
        rect = RectangleItem(x=0, y=0, width=10, height=10, locked=True)
        out = item_to_dict(rect)
        assert out["locked"] is True

    def test_item_to_dict_ellipse_includes_locked(self):
        """item_to_dict should include locked for EllipseItem."""
        ell = EllipseItem(center_x=0, center_y=0, radius_x=10, radius_y=10, locked=True)
        out = item_to_dict(ell)
        assert out["locked"] is True

    def test_item_to_dict_layer_includes_locked(self):
        """item_to_dict should include locked for LayerItem."""
        layer = LayerItem(name="Test", locked=True)
        out = item_to_dict(layer)
        assert out["locked"] is True

    def test_validate_text_includes_locked(self):
        """validate_text should include locked in output."""
        data = {"type": "text", "text": "Hello", "locked": True}
        out = validate_text(data)
        assert out["locked"] is True

    def test_validate_text_locked_defaults_false(self):
        """validate_text should default locked to False."""
        data = {"type": "text", "text": "Hello"}
        out = validate_text(data)
        assert out["locked"] is False

    def test_validate_text_includes_visible(self):
        """validate_text should include visible in output."""
        data = {"type": "text", "text": "Hello", "visible": False}
        out = validate_text(data)
        assert out["visible"] is False

    def test_validate_text_visible_defaults_true(self):
        """validate_text should default visible to True."""
        data = {"type": "text", "text": "Hello"}
        out = validate_text(data)
        assert out["visible"] is True

    def test_parse_item_text_preserves_locked(self):
        """parse_item should create TextItem with locked property."""
        text = parse_item({"type": "text", "text": "Hello", "locked": True})
        assert text.locked is True

    def test_item_to_dict_text_includes_locked(self):
        """item_to_dict should include locked for TextItem."""
        text = TextItem(x=0, y=0, text="Hello", locked=True)
        out = item_to_dict(text)
        assert out["locked"] is True

    def test_item_to_dict_text_includes_visible(self):
        """item_to_dict should include visible for TextItem."""
        text = TextItem(x=0, y=0, text="Hello", visible=False)
        out = item_to_dict(text)
        assert out["visible"] is False
