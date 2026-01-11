# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Unit tests for model_geometry module."""

import math
from lucent.model_geometry import shape_to_path_data
from lucent.canvas_items import RectangleItem, EllipseItem, PathItem, LayerItem
from lucent.geometry import RectGeometry, EllipseGeometry, PolylineGeometry
from lucent.transforms import Transform
from lucent.item_schema import item_to_dict


class TestShapeToPathData:
    """Tests for shape_to_path_data function."""

    def test_rectangle_with_rotation_returns_4_points(self):
        """Rotated rectangle should convert to 4-point path."""
        geometry = RectGeometry(x=0, y=0, width=100, height=100)
        transform = Transform(rotate=45, origin_x=0.5, origin_y=0.5)
        item = RectangleItem(geometry=geometry, appearances=[], transform=transform)

        result = shape_to_path_data(item, item_to_dict)

        assert result is not None
        assert result["type"] == "path"
        assert len(result["geometry"]["points"]) == 4
        assert result["geometry"]["closed"] is True
        assert result["transform"]["rotate"] == 0

    def test_ellipse_with_rotation_returns_32_points(self):
        """Rotated ellipse should convert to 32-point path."""
        geometry = EllipseGeometry(center_x=50, center_y=50, radius_x=40, radius_y=20)
        transform = Transform(rotate=30, origin_x=0.5, origin_y=0.5)
        item = EllipseItem(geometry=geometry, appearances=[], transform=transform)

        result = shape_to_path_data(item, item_to_dict)

        assert result is not None
        assert result["type"] == "path"
        assert len(result["geometry"]["points"]) == 32
        assert result["geometry"]["closed"] is True

    def test_path_with_rotation_transforms_points(self):
        """Rotated path should have all points transformed."""
        points = [{"x": 0, "y": 0}, {"x": 100, "y": 0}, {"x": 50, "y": 100}]
        geometry = PolylineGeometry(points=points, closed=True)
        transform = Transform(rotate=90, origin_x=0.5, origin_y=0.5)
        item = PathItem(geometry=geometry, appearances=[], transform=transform)

        result = shape_to_path_data(item, item_to_dict)

        assert result is not None
        assert result["type"] == "path"
        assert len(result["geometry"]["points"]) == 3

    def test_no_rotation_returns_none(self):
        """Item with no rotation should return None (no conversion needed)."""
        geometry = RectGeometry(x=0, y=0, width=100, height=100)
        transform = Transform(scale_x=2.0, translate_x=10)  # No rotation
        item = RectangleItem(geometry=geometry, appearances=[], transform=transform)

        result = shape_to_path_data(item, item_to_dict)

        assert result is None

    def test_identity_transform_returns_none(self):
        """Item with identity transform should return None."""
        geometry = RectGeometry(x=0, y=0, width=100, height=100)
        item = RectangleItem(geometry=geometry, appearances=[])

        result = shape_to_path_data(item, item_to_dict)

        assert result is None

    def test_item_without_transform_returns_none(self):
        """Item without transform attribute should return None."""
        # LayerItem has no transform
        item = LayerItem(name="Test Layer")

        result = shape_to_path_data(item, item_to_dict)

        assert result is None

    def test_rotated_rectangle_points_are_correct(self):
        """Verify rotated rectangle corner points are mathematically correct."""
        # 100x100 square at origin, rotated 45° around center (50, 50)
        geometry = RectGeometry(x=0, y=0, width=100, height=100)
        transform = Transform(rotate=45, origin_x=0.5, origin_y=0.5)
        item = RectangleItem(geometry=geometry, appearances=[], transform=transform)

        result = shape_to_path_data(item, item_to_dict)
        points = result["geometry"]["points"]

        # After 45° rotation around center, the corners should form a diamond
        # The diagonal half-length is 50*sqrt(2) ≈ 70.71
        half_diag = 50 * math.sqrt(2)

        xs = [p["x"] for p in points]
        ys = [p["y"] for p in points]

        # Bounding box of rotated square should be approximately ±70.71 from center
        assert abs(min(xs) - (50 - half_diag)) < 0.01
        assert abs(max(xs) - (50 + half_diag)) < 0.01
        assert abs(min(ys) - (50 - half_diag)) < 0.01
        assert abs(max(ys) - (50 + half_diag)) < 0.01

    def test_preserves_appearances(self):
        """Converted path should preserve original appearances."""
        from lucent.appearances import Fill, Stroke

        geometry = RectGeometry(x=0, y=0, width=100, height=100)
        transform = Transform(rotate=45, origin_x=0.5, origin_y=0.5)
        appearances = [
            Fill(color="#ff0000", opacity=0.5),
            Stroke(color="#00ff00", width=2.0),
        ]
        item = RectangleItem(
            geometry=geometry, appearances=appearances, transform=transform
        )

        result = shape_to_path_data(item, item_to_dict)

        assert len(result["appearances"]) == 2
        assert result["appearances"][0]["type"] == "fill"
        assert result["appearances"][0]["color"] == "#ff0000"
        assert result["appearances"][1]["type"] == "stroke"
        assert result["appearances"][1]["width"] == 2.0

    def test_preserves_name_and_visibility(self):
        """Converted path should preserve name, visibility, locked state."""
        geometry = RectGeometry(x=0, y=0, width=100, height=100)
        transform = Transform(rotate=45)
        item = RectangleItem(
            geometry=geometry,
            appearances=[],
            transform=transform,
            name="My Shape",
            visible=False,
            locked=True,
        )

        result = shape_to_path_data(item, item_to_dict)

        assert result["name"] == "My Shape"
        assert result["visible"] is False
        assert result["locked"] is True

    def test_preserves_parent_id(self):
        """Converted path should preserve parentId if present."""
        geometry = RectGeometry(x=0, y=0, width=100, height=100)
        transform = Transform(rotate=45)
        item = RectangleItem(
            geometry=geometry,
            appearances=[],
            transform=transform,
            parent_id="layer-123",
        )

        result = shape_to_path_data(item, item_to_dict)

        assert result["parentId"] == "layer-123"
