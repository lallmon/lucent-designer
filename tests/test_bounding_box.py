"""Unit tests for bounding_box module - pure math for bounds calculations."""

from lucent.bounding_box import (
    rect_bounds,
    union_bounds,
    get_rectangle_bounds,
    get_ellipse_bounds,
    get_path_bounds,
    get_text_bounds,
    translate_path_to_bounds,
    bbox_to_ellipse_geometry,
    get_item_bounds,
)


class MockRectGeometry:
    """Mock rectangle geometry."""

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class MockEllipseGeometry:
    """Mock ellipse geometry."""

    def __init__(self, center_x, center_y, radius_x, radius_y):
        self.center_x = center_x
        self.center_y = center_y
        self.radius_x = radius_x
        self.radius_y = radius_y


class MockPolylineGeometry:
    """Mock polyline geometry."""

    def __init__(self, points):
        self.points = points


class MockQRectF:
    """Mock QRectF for tests."""

    def __init__(self, x, y, width, height):
        self._x = x
        self._y = y
        self._width = width
        self._height = height

    def x(self):
        return self._x

    def y(self):
        return self._y

    def width(self):
        return self._width

    def height(self):
        return self._height


class MockRectangleItem:
    """Mock rectangle item."""

    def __init__(self, geometry):
        self.geometry = geometry

    def get_bounds(self):
        return MockQRectF(
            self.geometry.x,
            self.geometry.y,
            self.geometry.width,
            self.geometry.height,
        )


class MockEllipseItem:
    """Mock ellipse item."""

    def __init__(self, geometry):
        self.geometry = geometry

    def get_bounds(self):
        return MockQRectF(
            self.geometry.center_x - self.geometry.radius_x,
            self.geometry.center_y - self.geometry.radius_y,
            self.geometry.radius_x * 2,
            self.geometry.radius_y * 2,
        )


class MockPathItem:
    """Mock path item."""

    def __init__(self, geometry):
        self.geometry = geometry

    def get_bounds(self):
        if not self.geometry.points:
            return None
        xs = [p["x"] for p in self.geometry.points]
        ys = [p["y"] for p in self.geometry.points]
        return MockQRectF(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))


class MockTextGeometry:
    """Mock geometry for text item."""

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class MockTextItem:
    """Mock text item with geometry attribute."""

    def __init__(self, x, y, width, height, font_size):
        self.geometry = MockTextGeometry(x, y, width, height)
        self.font_size = font_size

    def get_bounds(self):
        return MockQRectF(
            self.geometry.x,
            self.geometry.y,
            self.geometry.width,
            self.geometry.height,
        )


class MockContainerItem:
    """Mock container item."""

    def __init__(self, item_id):
        self.id = item_id


class TestRectBounds:
    """Tests for rect_bounds function."""

    def test_creates_bounds_dict(self):
        result = rect_bounds(10, 20, 100, 50)
        assert result == {"x": 10, "y": 20, "width": 100, "height": 50}

    def test_handles_negative_coordinates(self):
        result = rect_bounds(-50, -100, 200, 150)
        assert result == {"x": -50, "y": -100, "width": 200, "height": 150}

    def test_handles_zero_dimensions(self):
        result = rect_bounds(0, 0, 0, 0)
        assert result == {"x": 0, "y": 0, "width": 0, "height": 0}


class TestUnionBounds:
    """Tests for union_bounds function."""

    def test_returns_none_for_empty_list(self):
        assert union_bounds([]) is None

    def test_returns_single_bounds(self):
        bounds = {"x": 10, "y": 20, "width": 100, "height": 50}
        result = union_bounds([bounds])
        assert result == bounds

    def test_unions_two_bounds(self):
        b1 = {"x": 0, "y": 0, "width": 50, "height": 50}
        b2 = {"x": 25, "y": 25, "width": 50, "height": 50}
        result = union_bounds([b1, b2])
        assert result == {"x": 0, "y": 0, "width": 75, "height": 75}

    def test_unions_non_overlapping_bounds(self):
        b1 = {"x": 0, "y": 0, "width": 10, "height": 10}
        b2 = {"x": 100, "y": 100, "width": 10, "height": 10}
        result = union_bounds([b1, b2])
        assert result == {"x": 0, "y": 0, "width": 110, "height": 110}

    def test_skips_none_values(self):
        b1 = {"x": 10, "y": 10, "width": 20, "height": 20}
        result = union_bounds([None, b1, None])
        assert result == b1

    def test_returns_none_for_all_none(self):
        result = union_bounds([None, None])
        assert result is None


class TestGetRectangleBounds:
    """Tests for get_rectangle_bounds function."""

    def test_returns_geometry_as_bounds(self):
        geom = MockRectGeometry(10, 20, 100, 50)
        result = get_rectangle_bounds(geom)
        assert result == {"x": 10, "y": 20, "width": 100, "height": 50}


class TestGetEllipseBounds:
    """Tests for get_ellipse_bounds function."""

    def test_converts_center_radius_to_bounds(self):
        geom = MockEllipseGeometry(50, 50, 25, 25)
        result = get_ellipse_bounds(geom)
        assert result == {"x": 25, "y": 25, "width": 50, "height": 50}

    def test_handles_different_radii(self):
        geom = MockEllipseGeometry(100, 100, 50, 25)
        result = get_ellipse_bounds(geom)
        assert result == {"x": 50, "y": 75, "width": 100, "height": 50}


class TestGetPathBounds:
    """Tests for get_path_bounds function."""

    def test_returns_none_for_empty_points(self):
        assert get_path_bounds([]) is None

    def test_calculates_bounds_for_single_point(self):
        points = [{"x": 10, "y": 20}]
        result = get_path_bounds(points)
        assert result == {"x": 10, "y": 20, "width": 0, "height": 0}

    def test_calculates_bounds_for_line(self):
        points = [{"x": 0, "y": 0}, {"x": 100, "y": 50}]
        result = get_path_bounds(points)
        assert result == {"x": 0, "y": 0, "width": 100, "height": 50}

    def test_calculates_bounds_for_polygon(self):
        points = [
            {"x": 0, "y": 0},
            {"x": 100, "y": 0},
            {"x": 100, "y": 100},
            {"x": 0, "y": 100},
        ]
        result = get_path_bounds(points)
        assert result == {"x": 0, "y": 0, "width": 100, "height": 100}

    def test_handles_negative_coordinates(self):
        points = [{"x": -50, "y": -50}, {"x": 50, "y": 50}]
        result = get_path_bounds(points)
        assert result == {"x": -50, "y": -50, "width": 100, "height": 100}


class TestGetTextBounds:
    """Tests for get_text_bounds function."""

    def test_uses_explicit_height(self):
        result = get_text_bounds(10, 20, 100, 50, font_size=16)
        assert result == {"x": 10, "y": 20, "width": 100, "height": 50}

    def test_estimates_height_from_font_size(self):
        result = get_text_bounds(10, 20, 100, 0, font_size=20)
        assert result == {"x": 10, "y": 20, "width": 100, "height": 24.0}


class TestTranslatePathToBounds:
    """Tests for translate_path_to_bounds function."""

    def test_returns_empty_for_empty_points(self):
        assert translate_path_to_bounds([], 100, 100) == []

    def test_translates_points_to_new_origin(self):
        points = [{"x": 0, "y": 0}, {"x": 50, "y": 50}]
        result = translate_path_to_bounds(points, 100, 100)
        assert result == [{"x": 100, "y": 100}, {"x": 150, "y": 150}]

    def test_handles_non_origin_path(self):
        points = [{"x": 50, "y": 50}, {"x": 100, "y": 100}]
        result = translate_path_to_bounds(points, 0, 0)
        assert result == [{"x": 0, "y": 0}, {"x": 50, "y": 50}]


class TestBboxToEllipseGeometry:
    """Tests for bbox_to_ellipse_geometry function."""

    def test_converts_bounds_to_ellipse_params(self):
        bbox = {"x": 0, "y": 0, "width": 100, "height": 50}
        result = bbox_to_ellipse_geometry(bbox)
        assert result == {
            "centerX": 50,
            "centerY": 25,
            "radiusX": 50,
            "radiusY": 25,
        }

    def test_handles_offset_bounds(self):
        bbox = {"x": 100, "y": 100, "width": 50, "height": 50}
        result = bbox_to_ellipse_geometry(bbox)
        assert result == {
            "centerX": 125,
            "centerY": 125,
            "radiusX": 25,
            "radiusY": 25,
        }


class TestGetItemBounds:
    """Tests for get_item_bounds function."""

    def test_returns_rectangle_bounds(self):
        geom = MockRectGeometry(10, 20, 100, 50)
        item = MockRectangleItem(geom)
        result = get_item_bounds(item)
        assert result == {"x": 10, "y": 20, "width": 100, "height": 50}

    def test_returns_ellipse_bounds(self):
        geom = MockEllipseGeometry(50, 50, 25, 25)
        item = MockEllipseItem(geom)
        result = get_item_bounds(item)
        assert result == {"x": 25, "y": 25, "width": 50, "height": 50}

    def test_returns_path_bounds(self):
        geom = MockPolylineGeometry([{"x": 0, "y": 0}, {"x": 100, "y": 100}])
        item = MockPathItem(geom)
        result = get_item_bounds(item)
        assert result == {"x": 0, "y": 0, "width": 100, "height": 100}

    def test_returns_text_bounds(self):
        item = MockTextItem(10, 20, 100, 50, 16)
        result = get_item_bounds(item)
        assert result == {"x": 10, "y": 20, "width": 100, "height": 50}

    def test_uses_callback_for_container(self):
        container = MockContainerItem("layer-1")
        expected = {"x": 0, "y": 0, "width": 200, "height": 200}

        def get_descendant_bounds(container_id):
            return expected if container_id == "layer-1" else None

        result = get_item_bounds(container, get_descendant_bounds)
        assert result == expected

    def test_returns_none_for_container_without_callback(self):
        container = MockContainerItem("layer-1")
        result = get_item_bounds(container)
        assert result is None
