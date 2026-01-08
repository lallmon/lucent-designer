"""CanvasModel geometry and bounding-box related behaviour."""

import pytest

from test_helpers import make_rectangle, make_ellipse, make_path, make_layer, make_text


@pytest.mark.parametrize(
    "item_data, expected",
    [
        (
            make_rectangle(x=10, y=20, width=100, height=50),
            {"x": 10.0, "y": 20.0, "width": 100.0, "height": 50.0},
        ),
        (
            make_ellipse(center_x=100, center_y=100, radius_x=50, radius_y=30),
            {"x": 50.0, "y": 70.0, "width": 100.0, "height": 60.0},
        ),
        (
            make_path(points=[{"x": -2, "y": 3}, {"x": 4, "y": 5}, {"x": 1, "y": -1}]),
            {"x": -2.0, "y": -1.0, "width": 6.0, "height": 6.0},
        ),
    ],
)
def test_bounding_box_shapes(canvas_model, item_data, expected):
    """Bounding boxes for basic shapes."""
    canvas_model.addItem(item_data)
    bbox = canvas_model.getBoundingBox(0)
    assert bbox == expected


class TestCanvasModelSetBoundingBox:
    """Tests for setBoundingBox method."""

    def test_set_rectangle_bounding_box(self, canvas_model):
        canvas_model.addItem(make_rectangle(x=0, y=0, width=50, height=50))

        result = canvas_model.setBoundingBox(
            0, {"x": 100, "y": 100, "width": 75, "height": 25}
        )
        assert result is True

        item = canvas_model.getItems()[0]
        assert item.geometry.x == 100
        assert item.geometry.y == 100
        assert item.geometry.width == 75
        assert item.geometry.height == 25

    def test_set_ellipse_bounding_box(self, canvas_model):
        canvas_model.addItem(
            make_ellipse(center_x=50, center_y=50, radius_x=25, radius_y=25)
        )

        result = canvas_model.setBoundingBox(
            0, {"x": 0, "y": 0, "width": 100, "height": 50}
        )
        assert result is True

        item = canvas_model.getItems()[0]
        assert item.geometry.center_x == 50
        assert item.geometry.center_y == 25
        assert item.geometry.radius_x == 50
        assert item.geometry.radius_y == 25

    def test_set_path_bounding_box(self, canvas_model):
        canvas_model.addItem(make_path(points=[{"x": 0, "y": 0}, {"x": 10, "y": 10}]))

        result = canvas_model.setBoundingBox(
            0, {"x": 100, "y": 100, "width": 10, "height": 10}
        )
        assert result is True

        item = canvas_model.getItems()[0]
        assert item.geometry.points[0]["x"] == 100
        assert item.geometry.points[0]["y"] == 100
        assert item.geometry.points[1]["x"] == 110
        assert item.geometry.points[1]["y"] == 110

    def test_set_text_bounding_box(self, canvas_model):
        canvas_model.addItem(make_text(x=0, y=0, text="Hello"))

        result = canvas_model.setBoundingBox(
            0, {"x": 50, "y": 50, "width": 200, "height": 30}
        )
        assert result is True

        item = canvas_model.getItems()[0]
        assert item.x == 50
        assert item.y == 50
        assert item.width == 200
        assert item.height == 30

    def test_set_bounding_box_invalid_index(self, canvas_model):
        result = canvas_model.setBoundingBox(
            999, {"x": 0, "y": 0, "width": 10, "height": 10}
        )
        assert result is False

    def test_set_bounding_box_layer_returns_false(self, canvas_model):
        canvas_model.addItem(make_layer())

        result = canvas_model.setBoundingBox(
            0, {"x": 0, "y": 0, "width": 10, "height": 10}
        )
        assert result is False

    def test_set_path_bounding_box_empty_points(self, canvas_model):
        canvas_model.addItem(make_path(points=[]))

        result = canvas_model.setBoundingBox(
            0, {"x": 0, "y": 0, "width": 10, "height": 10}
        )
        assert result is False


class TestCanvasModelBoundingBoxEdgeCases:
    """Edge case tests for bounding box methods."""

    def test_get_bounding_box_invalid_index(self, canvas_model):
        result = canvas_model.getBoundingBox(999)
        assert result is None

    def test_get_bounding_box_text_auto_height(self, canvas_model):
        canvas_model.addItem(make_text(x=10, y=20, text="Test", height=0, font_size=20))
        bbox = canvas_model.getBoundingBox(0)
        assert bbox["x"] == 10
        assert bbox["y"] == 20
        assert bbox["height"] > 0

    def test_get_bounding_box_group_union(self, canvas_model):
        canvas_model.addItem(make_rectangle(x=0, y=0, width=50, height=50, name="A"))
        canvas_model.addItem(
            make_rectangle(x=100, y=100, width=50, height=50, name="B")
        )

        group_idx = canvas_model.groupItems([0, 1])
        bbox = canvas_model.getBoundingBox(group_idx)

        assert bbox["x"] == 0
        assert bbox["y"] == 0
        assert bbox["width"] == 150
        assert bbox["height"] == 150


class TestCanvasModelGetGeometryBounds:
    """Tests for getGeometryBounds method (untransformed bounds)."""

    def test_get_geometry_bounds_rectangle(self, canvas_model):
        canvas_model.addItem(make_rectangle(x=10, y=20, width=100, height=50))
        bounds = canvas_model.getGeometryBounds(0)
        assert bounds["x"] == 10
        assert bounds["y"] == 20
        assert bounds["width"] == 100
        assert bounds["height"] == 50

    def test_get_geometry_bounds_ellipse(self, canvas_model):
        canvas_model.addItem(
            make_ellipse(center_x=50, center_y=50, radius_x=30, radius_y=20)
        )
        bounds = canvas_model.getGeometryBounds(0)
        assert bounds["x"] == 20
        assert bounds["y"] == 30
        assert bounds["width"] == 60
        assert bounds["height"] == 40

    def test_get_geometry_bounds_path(self, canvas_model):
        canvas_model.addItem(
            make_path(points=[{"x": 10, "y": 20}, {"x": 110, "y": 70}])
        )
        bounds = canvas_model.getGeometryBounds(0)
        assert bounds["x"] == 10
        assert bounds["y"] == 20
        assert bounds["width"] == 100
        assert bounds["height"] == 50

    def test_get_geometry_bounds_ignores_transform(self, canvas_model):
        data = make_rectangle(x=0, y=0, width=100, height=50)
        data["transform"] = {"translateX": 50, "translateY": 25, "rotate": 45}
        canvas_model.addItem(data)
        bounds = canvas_model.getGeometryBounds(0)
        assert bounds["x"] == 0
        assert bounds["y"] == 0
        assert bounds["width"] == 100
        assert bounds["height"] == 50

    def test_get_geometry_bounds_ignores_scale(self, canvas_model):
        data = make_rectangle(x=10, y=20, width=100, height=50)
        data["transform"] = {"scaleX": 2.0, "scaleY": 3.0}
        canvas_model.addItem(data)
        bounds = canvas_model.getGeometryBounds(0)
        assert bounds["x"] == 10
        assert bounds["y"] == 20
        assert bounds["width"] == 100
        assert bounds["height"] == 50

    def test_get_geometry_bounds_ignores_all_transforms(self, canvas_model):
        data = make_rectangle(x=0, y=0, width=100, height=100)
        data["transform"] = {
            "translateX": 50,
            "translateY": 50,
            "rotate": 45,
            "scaleX": 2.0,
            "scaleY": 0.5,
            "originX": 0.5,
            "originY": 0.5,
        }
        canvas_model.addItem(data)
        bounds = canvas_model.getGeometryBounds(0)
        assert bounds["x"] == 0
        assert bounds["y"] == 0
        assert bounds["width"] == 100
        assert bounds["height"] == 100

    def test_get_geometry_bounds_invalid_index(self, canvas_model):
        assert canvas_model.getGeometryBounds(-1) is None
        assert canvas_model.getGeometryBounds(999) is None

    def test_get_geometry_bounds_layer_returns_none(self, canvas_model):
        canvas_model.addItem(make_layer(name="Layer"))
        assert canvas_model.getGeometryBounds(0) is None


class TestCanvasModelBoundingBoxWithTransforms:
    """Tests for getBoundingBox with transformed items."""

    def test_bounding_box_with_translation(self, canvas_model):
        rect_data = make_rectangle(x=0, y=0, width=100, height=50)
        rect_data["transform"] = {"translateX": 50, "translateY": 25}
        canvas_model.addItem(rect_data)

        bbox = canvas_model.getBoundingBox(0)
        assert bbox["x"] == 50
        assert bbox["y"] == 25
        assert bbox["width"] == 100
        assert bbox["height"] == 50

    def test_bounding_box_with_rotation(self, canvas_model):
        rect_data = make_rectangle(x=0, y=0, width=100, height=50)
        rect_data["transform"] = {"rotate": 45, "originX": 0.5, "originY": 0.5}
        canvas_model.addItem(rect_data)

        bbox = canvas_model.getBoundingBox(0)
        assert bbox["width"] > 100
        assert bbox["height"] > 50

    def test_bounding_box_90_degree_rotation(self, canvas_model):
        rect_data = make_rectangle(x=0, y=0, width=100, height=50)
        rect_data["transform"] = {"rotate": 90, "originX": 0.5, "originY": 0.5}
        canvas_model.addItem(rect_data)

        bbox = canvas_model.getBoundingBox(0)
        assert abs(bbox["width"] - 50) < 0.01
        assert abs(bbox["height"] - 100) < 0.01

    def test_bounding_box_with_origin_affects_position(self, canvas_model):
        rect_tl = make_rectangle(x=0, y=0, width=100, height=100)
        rect_tl["transform"] = {"rotate": 180, "originX": 0, "originY": 0}
        canvas_model.addItem(rect_tl)
        bbox_tl = canvas_model.getBoundingBox(0)

        canvas_model.removeItem(0)

        rect_center = make_rectangle(x=0, y=0, width=100, height=100)
        rect_center["transform"] = {"rotate": 180, "originX": 0.5, "originY": 0.5}
        canvas_model.addItem(rect_center)
        bbox_center = canvas_model.getBoundingBox(0)

        assert bbox_tl["x"] == -100
        assert bbox_tl["y"] == -100
        assert abs(bbox_center["x"]) < 0.01
        assert abs(bbox_center["y"]) < 0.01

    def test_geometry_bounds_unchanged_by_transform(self, canvas_model):
        rect_data = make_rectangle(x=10, y=20, width=100, height=50)
        rect_data["transform"] = {"translateX": 50, "translateY": 25, "rotate": 45}
        canvas_model.addItem(rect_data)

        geom_bounds = canvas_model.getGeometryBounds(0)
        assert geom_bounds["x"] == 10
        assert geom_bounds["y"] == 20
        assert geom_bounds["width"] == 100
        assert geom_bounds["height"] == 50

        bbox = canvas_model.getBoundingBox(0)
        assert bbox["x"] != 10 or bbox["y"] != 20
