"""Unit tests for item_schema validation and serialization."""

import pytest

from lucent.canvas_items import (
    RectangleItem,
    EllipseItem,
    LayerItem,
    CanvasItem,
    PathItem,
    TextItem,
    GroupItem,
)
from lucent.geometry import (
    RectGeometry,
    EllipseGeometry,
    PolylineGeometry,
    TextGeometry,
)
from lucent.appearances import Fill, Stroke
from lucent.transforms import Transform
from lucent.item_schema import (
    ItemSchemaError,
    ItemType,
    parse_item,
    parse_item_data,
    validate_rectangle,
    validate_ellipse,
    validate_layer,
    validate_group,
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


def test_validate_path_new_format():
    """validate_path should handle new format with geometry and appearances."""
    data = {
        "type": "path",
        "geometry": {
            "points": [{"x": 1, "y": 2}, {"x": -3, "y": 4}],
            "closed": True,
        },
        "appearances": [
            {"type": "fill", "color": "#abcdef", "opacity": 0.8, "visible": True},
            {
                "type": "stroke",
                "color": "#123456",
                "width": 2.0,
                "opacity": 0.5,
                "visible": True,
            },
        ],
    }
    out = validate_path(data)
    assert out["geometry"]["points"] == [{"x": 1.0, "y": 2.0}, {"x": -3.0, "y": 4.0}]
    assert out["geometry"]["closed"] is True
    assert len(out["appearances"]) == 2


def test_validate_path_clamps_appearances():
    """validate_path should clamp appearance values."""
    data = {
        "type": "path",
        "geometry": {
            "points": [{"x": 1, "y": 2}, {"x": -3, "y": 4}],
            "closed": True,
        },
        "appearances": [
            {"type": "fill", "color": "#abcdef", "opacity": 2.0},  # Over max
            {"type": "stroke", "color": "#123456", "width": -1, "opacity": 5.0},
        ],
    }
    out = validate_path(data)
    fill = next(a for a in out["appearances"] if a["type"] == "fill")
    stroke = next(a for a in out["appearances"] if a["type"] == "stroke")
    assert fill["opacity"] == 1.0  # Clamped
    assert stroke["width"] == 0.0  # Clamped to min
    assert stroke["opacity"] == 1.0  # Clamped


def test_validate_path_requires_two_points():
    with pytest.raises(ItemSchemaError):
        validate_path(
            {
                "type": "path",
                "geometry": {"points": [{"x": 0, "y": 0}], "closed": False},
            }
        )


def test_validate_rectangle_new_format():
    """validate_rectangle should handle new format with geometry and appearances."""
    data = {
        "type": "rectangle",
        "geometry": {"x": 1, "y": 2, "width": 100, "height": 50},
        "appearances": [
            {"type": "fill", "color": "#def", "opacity": 0.5, "visible": True},
            {
                "type": "stroke",
                "color": "#abc",
                "width": 2.0,
                "opacity": 0.8,
                "visible": True,
            },
        ],
        "name": "Rect",
        "parentId": "layer-1",
    }
    out = validate_rectangle(data)
    assert out["geometry"]["x"] == 1
    assert out["geometry"]["y"] == 2
    assert out["geometry"]["width"] == 100
    assert out["geometry"]["height"] == 50
    assert out["name"] == "Rect"
    assert out["parentId"] == "layer-1"
    assert len(out["appearances"]) == 2


def test_validate_rectangle_clamps_geometry():
    """validate_rectangle should clamp negative width/height to 0."""
    data = {
        "type": "rectangle",
        "geometry": {"x": 1, "y": 2, "width": -5, "height": 10},
    }
    out = validate_rectangle(data)
    assert out["geometry"]["width"] == 0.0
    assert out["geometry"]["height"] == 10


def test_validate_ellipse_new_format():
    """validate_ellipse should handle new format with geometry and appearances."""
    data = {
        "type": "ellipse",
        "geometry": {"centerX": 3, "centerY": 4, "radiusX": 20, "radiusY": 15},
        "appearances": [
            {"type": "fill", "color": "#222", "opacity": 0.5, "visible": True},
            {
                "type": "stroke",
                "color": "#111",
                "width": 3.0,
                "opacity": 0.7,
                "visible": True,
            },
        ],
        "name": "Ell",
    }
    out = validate_ellipse(data)
    assert out["geometry"]["centerX"] == 3
    assert out["geometry"]["centerY"] == 4
    assert out["geometry"]["radiusX"] == 20
    assert out["geometry"]["radiusY"] == 15
    assert out["name"] == "Ell"


def test_validate_ellipse_clamps_radius():
    """validate_ellipse should clamp negative radii to 0."""
    data = {
        "type": "ellipse",
        "geometry": {"centerX": 0, "centerY": 0, "radiusX": -1, "radiusY": 5},
    }
    out = validate_ellipse(data)
    assert out["geometry"]["radiusX"] == 0.0
    assert out["geometry"]["radiusY"] == 5


def test_validate_layer_defaults_and_preserves_id():
    out = validate_layer({"type": "layer", "name": "Layer", "id": "custom"})
    assert out["name"] == "Layer"
    assert out["id"] == "custom"

    out2 = validate_layer({"type": "layer"})
    assert out2["name"] == ""
    assert out2["id"] is None


def test_validate_group():
    """validate_group should handle group data."""
    out = validate_group(
        {"type": "group", "name": "Group", "id": "grp-1", "parentId": "layer-1"}
    )
    assert out["name"] == "Group"
    assert out["id"] == "grp-1"
    assert out["parentId"] == "layer-1"


def test_validate_text_clamps_and_defaults():
    """validate_text should clamp font size and opacity values."""
    data = {
        "type": "text",
        "geometry": {"x": 10, "y": 20, "width": 100, "height": 0},
        "text": "Hello",
        "fontFamily": "Monospace",
        "fontSize": 5,  # Below minimum
        "textColor": "#ff0000",
        "textOpacity": 2.0,  # Above maximum
        "name": "MyText",
        "parentId": "layer-1",
    }
    out = validate_text(data)
    assert out["geometry"]["x"] == 10
    assert out["geometry"]["y"] == 20
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
    assert out["geometry"]["x"] == 0
    assert out["geometry"]["y"] == 0
    assert out["geometry"]["width"] == 100
    assert out["geometry"]["height"] == 0
    assert out["fontFamily"] == "Sans Serif"
    assert out["fontSize"] == 16
    assert out["textColor"] == "#ffffff"
    assert out["textOpacity"] == 1.0
    assert out["name"] == ""
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
    """parse_item should return concrete item instances."""
    rect = parse_item(
        {
            "type": "rectangle",
            "geometry": {"x": 0, "y": 0, "width": 10, "height": 10},
            "appearances": [
                {"type": "fill", "color": "#fff", "opacity": 0.5, "visible": True},
                {
                    "type": "stroke",
                    "color": "#000",
                    "width": 1,
                    "opacity": 1.0,
                    "visible": True,
                },
            ],
        }
    )
    assert isinstance(rect, RectangleItem)

    ell = parse_item(
        {
            "type": "ellipse",
            "geometry": {"centerX": 0, "centerY": 0, "radiusX": 10, "radiusY": 10},
        }
    )
    assert isinstance(ell, EllipseItem)

    layer = parse_item({"type": "layer"})
    assert isinstance(layer, LayerItem)

    path = parse_item(
        {
            "type": "path",
            "geometry": {
                "points": [{"x": 0, "y": 0}, {"x": 5, "y": 0}],
                "closed": False,
            },
        }
    )
    assert isinstance(path, PathItem)
    assert path.geometry.closed is False

    text = parse_item({"type": "text", "text": "Hello", "fontSize": 20})
    assert isinstance(text, TextItem)
    assert text.text == "Hello"
    assert text.font_size == 20

    group = parse_item({"type": "group", "name": "G1"})
    assert isinstance(group, GroupItem)


def test_item_to_dict_round_trips_rectangle():
    """item_to_dict should serialize RectangleItem to new format."""
    geometry = RectGeometry(x=1, y=2, width=3, height=4)
    appearances = [
        Fill(color="#ff0000", opacity=0.5),
        Stroke(color="#00ff00", width=2.0, opacity=0.8),
    ]
    rect = RectangleItem(
        geometry=geometry, appearances=appearances, name="R", parent_id="p"
    )
    out = item_to_dict(rect)
    assert out["type"] == ItemType.RECTANGLE.value
    assert out["name"] == "R"
    assert out["parentId"] == "p"
    assert out["geometry"]["x"] == 1
    assert out["geometry"]["y"] == 2
    assert out["geometry"]["width"] == 3
    assert out["geometry"]["height"] == 4
    assert len(out["appearances"]) == 2


def test_item_to_dict_round_trips_ellipse():
    """item_to_dict should serialize EllipseItem to new format."""
    geometry = EllipseGeometry(center_x=1, center_y=2, radius_x=3, radius_y=4)
    appearances = [
        Fill(color="#abcdef", opacity=0.8),
        Stroke(color="#123456", width=3.5, opacity=0.4),
    ]
    ell = EllipseItem(geometry=geometry, appearances=appearances, name="E")
    out = item_to_dict(ell)
    assert out["type"] == ItemType.ELLIPSE.value
    assert out["geometry"]["centerX"] == 1
    assert out["geometry"]["centerY"] == 2
    assert out["geometry"]["radiusX"] == 3
    assert out["geometry"]["radiusY"] == 4
    assert out["name"] == "E"


def test_item_to_dict_round_trips_layer():
    layer = LayerItem(name="L", layer_id="lid")
    out = item_to_dict(layer)
    assert out["type"] == ItemType.LAYER.value
    assert out["name"] == "L"
    assert out["id"] == "lid"


def test_item_to_dict_round_trips_group():
    group = GroupItem(name="G", group_id="gid", parent_id="layer-1")
    out = item_to_dict(group)
    assert out["type"] == ItemType.GROUP.value
    assert out["name"] == "G"
    assert out["id"] == "gid"
    assert out["parentId"] == "layer-1"


def test_item_to_dict_round_trips_path():
    """item_to_dict should serialize PathItem to new format."""
    geometry = PolylineGeometry(
        points=[{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}], closed=True
    )
    appearances = [
        Fill(color="#112233", opacity=0.4),
        Stroke(color="#00ff00", width=2.0, opacity=0.5),
    ]
    path = PathItem(
        geometry=geometry, appearances=appearances, name="P1", parent_id="layer-1"
    )
    out = item_to_dict(path)
    assert out["type"] == ItemType.PATH.value
    assert out["name"] == "P1"
    assert out["parentId"] == "layer-1"
    assert out["geometry"]["closed"] is True
    assert len(out["geometry"]["points"]) == 3
    assert len(out["appearances"]) == 2


def test_item_to_dict_round_trips_text():
    """item_to_dict should serialize TextItem correctly."""
    geometry = TextGeometry(x=10, y=20, width=200, height=50)
    text = TextItem(
        geometry=geometry,
        text="Hello World",
        font_family="Monospace",
        font_size=24,
        text_color="#ff0000",
        text_opacity=0.8,
        name="T1",
        parent_id="layer-2",
    )
    out = item_to_dict(text)
    assert out["type"] == ItemType.TEXT.value
    assert out["geometry"]["x"] == 10
    assert out["geometry"]["y"] == 20
    assert out["geometry"]["width"] == 200
    assert out["geometry"]["height"] == 50
    assert out["text"] == "Hello World"
    assert out["fontFamily"] == "Monospace"
    assert out["fontSize"] == 24
    assert out["textColor"] == "#ff0000"
    assert out["textOpacity"] == 0.8
    assert out["name"] == "T1"
    assert out["parentId"] == "layer-2"


def test_parse_item_invalid_ellipse_raises():
    with pytest.raises(ItemSchemaError):
        parse_item({"type": "ellipse", "geometry": {"centerX": "bad"}})


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
            "geometry": {"x": 0, "y": 0, "width": 10, "height": 10},
            "locked": True,
        }
        out = validate_rectangle(data)
        assert out["locked"] is True

    def test_validate_rectangle_locked_defaults_false(self):
        """validate_rectangle should default locked to False."""
        data = {
            "type": "rectangle",
            "geometry": {"x": 0, "y": 0, "width": 10, "height": 10},
        }
        out = validate_rectangle(data)
        assert out["locked"] is False

    def test_validate_ellipse_includes_locked(self):
        """validate_ellipse should include locked in output."""
        data = {
            "type": "ellipse",
            "geometry": {"centerX": 0, "centerY": 0, "radiusX": 10, "radiusY": 10},
            "locked": True,
        }
        out = validate_ellipse(data)
        assert out["locked"] is True

    def test_validate_layer_includes_locked(self):
        """validate_layer should include locked in output."""
        data = {"type": "layer", "name": "Test", "locked": True}
        out = validate_layer(data)
        assert out["locked"] is True

    def test_parse_item_rectangle_preserves_locked(self):
        """parse_item should create RectangleItem with locked property."""
        rect = parse_item(
            {
                "type": "rectangle",
                "geometry": {"x": 0, "y": 0, "width": 10, "height": 10},
                "locked": True,
            }
        )
        assert rect.locked is True

    def test_item_to_dict_rectangle_includes_locked(self):
        """item_to_dict should include locked for RectangleItem."""
        geometry = RectGeometry(x=0, y=0, width=10, height=10)
        rect = RectangleItem(
            geometry=geometry,
            appearances=[Fill("#fff", 0.5), Stroke("#000", 1.0, 1.0)],
            locked=True,
        )
        out = item_to_dict(rect)
        assert out["locked"] is True

    def test_item_to_dict_ellipse_includes_locked(self):
        """item_to_dict should include locked for EllipseItem."""
        geometry = EllipseGeometry(center_x=0, center_y=0, radius_x=10, radius_y=10)
        ell = EllipseItem(
            geometry=geometry,
            appearances=[Fill("#fff", 0.5), Stroke("#000", 1.0, 1.0)],
            locked=True,
        )
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

    def test_validate_text_includes_visible(self):
        """validate_text should include visible in output."""
        data = {"type": "text", "text": "Hello", "visible": False}
        out = validate_text(data)
        assert out["visible"] is False

    def test_item_to_dict_text_includes_locked(self):
        """item_to_dict should include locked for TextItem."""
        geometry = TextGeometry(x=0, y=0, width=100, height=0)
        text = TextItem(geometry=geometry, text="Hello", locked=True)
        out = item_to_dict(text)
        assert out["locked"] is True

    def test_item_to_dict_text_includes_visible(self):
        """item_to_dict should include visible for TextItem."""
        geometry = TextGeometry(x=0, y=0, width=100, height=0)
        text = TextItem(geometry=geometry, text="Hello", visible=False)
        out = item_to_dict(text)
        assert out["visible"] is False


class TestTransformSerialization:
    """Tests for transform property validation and serialization."""

    def test_validate_rectangle_includes_transform(self):
        """validate_rectangle should include transform when provided."""
        data = {
            "type": "rectangle",
            "geometry": {"x": 0, "y": 0, "width": 10, "height": 10},
            "transform": {
                "translateX": 5,
                "translateY": 10,
                "rotate": 45,
                "scaleX": 2.0,
                "scaleY": 0.5,
            },
        }
        out = validate_rectangle(data)
        assert out["transform"]["translateX"] == 5
        assert out["transform"]["translateY"] == 10
        assert out["transform"]["rotate"] == 45
        assert out["transform"]["scaleX"] == 2.0
        assert out["transform"]["scaleY"] == 0.5

    def test_validate_rectangle_transform_defaults_none(self):
        """validate_rectangle should have no transform key when not provided."""
        data = {
            "type": "rectangle",
            "geometry": {"x": 0, "y": 0, "width": 10, "height": 10},
        }
        out = validate_rectangle(data)
        assert out.get("transform") is None

    def test_validate_rectangle_identity_transform_becomes_none(self):
        """Identity transforms should be omitted from output."""
        data = {
            "type": "rectangle",
            "geometry": {"x": 0, "y": 0, "width": 10, "height": 10},
            "transform": {
                "translateX": 0,
                "translateY": 0,
                "rotate": 0,
                "scaleX": 1,
                "scaleY": 1,
            },
        }
        out = validate_rectangle(data)
        assert out.get("transform") is None

    def test_validate_ellipse_includes_transform(self):
        """validate_ellipse should include transform when provided."""
        data = {
            "type": "ellipse",
            "geometry": {"centerX": 0, "centerY": 0, "radiusX": 10, "radiusY": 10},
            "transform": {"rotate": 90},
        }
        out = validate_ellipse(data)
        assert out["transform"]["rotate"] == 90
        # Defaults for missing fields
        assert out["transform"]["translateX"] == 0
        assert out["transform"]["scaleX"] == 1

    def test_validate_path_includes_transform(self):
        """validate_path should include transform when provided."""
        data = {
            "type": "path",
            "geometry": {
                "points": [{"x": 0, "y": 0}, {"x": 10, "y": 10}],
                "closed": False,
            },
            "transform": {"scaleX": 2, "scaleY": 2},
        }
        out = validate_path(data)
        assert out["transform"]["scaleX"] == 2
        assert out["transform"]["scaleY"] == 2

    def test_parse_item_rectangle_creates_transform(self):
        """parse_item should create RectangleItem with Transform object."""
        rect = parse_item(
            {
                "type": "rectangle",
                "geometry": {"x": 0, "y": 0, "width": 10, "height": 10},
                "transform": {"rotate": 45, "scaleX": 1.5},
            }
        )
        assert rect.transform.rotate == 45
        assert rect.transform.scale_x == 1.5
        assert rect.transform.scale_y == 1  # Default

    def test_parse_item_no_transform_uses_identity(self):
        """parse_item without transform should use identity transform."""
        rect = parse_item(
            {
                "type": "rectangle",
                "geometry": {"x": 0, "y": 0, "width": 10, "height": 10},
            }
        )
        assert rect.transform.is_identity()

    def test_item_to_dict_includes_non_identity_transform(self):
        """item_to_dict should include transform when not identity."""
        geometry = RectGeometry(x=0, y=0, width=10, height=10)
        transform = Transform(rotate=90)
        rect = RectangleItem(
            geometry=geometry,
            appearances=[Fill("#fff", 0.5), Stroke("#000", 1.0, 1.0)],
            transform=transform,
        )
        out = item_to_dict(rect)
        assert "transform" in out
        assert out["transform"]["rotate"] == 90

    def test_item_to_dict_omits_identity_transform(self):
        """item_to_dict should not include identity transform."""
        geometry = RectGeometry(x=0, y=0, width=10, height=10)
        rect = RectangleItem(
            geometry=geometry,
            appearances=[Fill("#fff", 0.5), Stroke("#000", 1.0, 1.0)],
        )
        out = item_to_dict(rect)
        assert "transform" not in out

    def test_transform_round_trip_rectangle(self):
        """Transform should survive serialize/deserialize round trip."""
        original = {
            "type": "rectangle",
            "geometry": {"x": 5, "y": 10, "width": 100, "height": 50},
            "transform": {
                "translateX": 15,
                "translateY": -20,
                "rotate": 180,
                "scaleX": 0.5,
                "scaleY": 2.0,
            },
        }
        item = parse_item(original)
        serialized = item_to_dict(item)
        assert serialized["transform"]["translateX"] == 15
        assert serialized["transform"]["translateY"] == -20
        assert serialized["transform"]["rotate"] == 180
        assert serialized["transform"]["scaleX"] == 0.5
        assert serialized["transform"]["scaleY"] == 2.0

    def test_transform_round_trip_ellipse(self):
        """Ellipse transform should survive round trip."""
        original = {
            "type": "ellipse",
            "geometry": {"centerX": 50, "centerY": 50, "radiusX": 25, "radiusY": 15},
            "transform": {"rotate": 45},
        }
        item = parse_item(original)
        serialized = item_to_dict(item)
        assert serialized["transform"]["rotate"] == 45

    def test_transform_round_trip_path(self):
        """Path transform should survive round trip."""
        original = {
            "type": "path",
            "geometry": {
                "points": [{"x": 0, "y": 0}, {"x": 50, "y": 50}],
                "closed": True,
            },
            "transform": {"scaleX": 3, "scaleY": 3, "rotate": 270},
        }
        item = parse_item(original)
        serialized = item_to_dict(item)
        assert serialized["transform"]["scaleX"] == 3
        assert serialized["transform"]["scaleY"] == 3
        assert serialized["transform"]["rotate"] == 270
