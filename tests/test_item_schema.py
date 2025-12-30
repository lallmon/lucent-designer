"""Unit tests for item_schema validation and serialization."""

import pytest

from lucent.canvas_items import RectangleItem, EllipseItem, LayerItem, CanvasItem
from lucent.item_schema import (
    ItemSchemaError,
    ItemType,
    parse_item,
    parse_item_data,
    validate_rectangle,
    validate_ellipse,
    validate_layer,
    item_to_dict,
)


def test_parse_item_data_rejects_missing_type():
    with pytest.raises(ItemSchemaError):
        parse_item_data({})


def test_parse_item_data_rejects_unknown_type():
    with pytest.raises(ItemSchemaError):
        parse_item_data({"type": "triangle"})


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
    assert out["strokeWidth"] == 0.1
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


def test_parse_item_returns_concrete_items():
    rect = parse_item({"type": "rectangle", "width": 1, "height": 1})
    assert isinstance(rect, RectangleItem)
    ell = parse_item({"type": "ellipse", "radiusX": 2, "radiusY": 3})
    assert isinstance(ell, EllipseItem)
    layer = parse_item({"type": "layer"})
    assert isinstance(layer, LayerItem)


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


def test_parse_item_invalid_ellipse_raises():
    with pytest.raises(ItemSchemaError):
        parse_item({"type": "ellipse", "centerX": "bad"})


def test_item_to_dict_rejects_unknown():
    class Unknown(CanvasItem):
        def paint(self, painter, zoom_level, offset_x=0, offset_y=0):
            pass

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
