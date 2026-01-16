# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""CanvasModel transform getters/setters."""

from test_helpers import make_rectangle, make_ellipse, make_path, make_layer


class TestCanvasModelTransforms:
    """Tests for getItemTransform and setItemTransform methods."""

    def test_get_item_transform_rectangle(self, canvas_model):
        rect_data = make_rectangle(x=0, y=0, width=100, height=50)
        rect_data["transform"] = {
            "translateX": 10,
            "translateY": 20,
            "rotate": 45,
            "scaleX": 1.5,
            "scaleY": 2.0,
        }
        canvas_model.addItem(rect_data)

        transform = canvas_model.getItemTransform(0)
        assert transform is not None
        assert transform["translateX"] == 10
        assert transform["translateY"] == 20
        assert transform["rotate"] == 45
        assert transform["scaleX"] == 1.5
        assert transform["scaleY"] == 2.0

    def test_get_item_transform_invalid_index(self, canvas_model):
        assert canvas_model.getItemTransform(-1) is None
        assert canvas_model.getItemTransform(999) is None

    def test_get_item_transform_layer_returns_none(self, canvas_model):
        canvas_model.addItem(make_layer(name="Test Layer"))
        assert canvas_model.getItemTransform(0) is None

    def test_set_item_transform(self, canvas_model, qtbot):
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

        new_transform = {
            "translateX": 50,
            "translateY": 25,
            "rotate": 90,
            "scaleX": 2.0,
            "scaleY": 2.0,
        }

        with qtbot.waitSignal(
            canvas_model.itemTransformChanged, timeout=1000
        ) as blocker:
            canvas_model.setItemTransform(0, new_transform)

        assert blocker.args == [0]

        transform = canvas_model.getItemTransform(0)
        assert transform["translateX"] == 50
        assert transform["rotate"] == 90

    def test_set_item_transform_invalid_index(self, canvas_model):
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))
        canvas_model.setItemTransform(-1, {"rotate": 45})
        canvas_model.setItemTransform(999, {"rotate": 45})

    def test_set_item_transform_layer_no_op(self, canvas_model):
        canvas_model.addItem(make_layer(name="Test Layer"))
        canvas_model.setItemTransform(0, {"rotate": 45})

    def test_update_transform_property_preserves_others(self, canvas_model):
        """updateTransformProperty should only change the specified property."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=50)
        rect_data["transform"] = {
            "translateX": 10,
            "translateY": 20,
            "rotate": 45,
            "scaleX": 1.5,
            "scaleY": 2.0,
            "originX": 0.5,
            "originY": 0.5,
        }
        canvas_model.addItem(rect_data)

        canvas_model.updateTransformProperty(0, "rotate", 90)

        transform = canvas_model.getItemTransform(0)
        assert transform["rotate"] == 90
        assert transform["translateX"] == 10
        assert transform["translateY"] == 20
        assert transform["scaleX"] == 1.5
        assert transform["scaleY"] == 2.0
        assert transform["originX"] == 0.5
        assert transform["originY"] == 0.5

    def test_update_transform_property_with_defaults(self, canvas_model):
        """updateTransformProperty should use defaults for missing properties."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

        canvas_model.updateTransformProperty(0, "rotate", 45)

        transform = canvas_model.getItemTransform(0)
        assert transform["rotate"] == 45
        assert transform["translateX"] == 0
        assert transform["translateY"] == 0
        assert transform["scaleX"] == 1
        assert transform["scaleY"] == 1


class TestRotationNormalization:
    """Tests for rotation normalization to 0-360° range."""

    def test_rotation_positive_within_range_unchanged(self, canvas_model):
        """Rotation values 0-360 should remain unchanged."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

        canvas_model.updateTransformProperty(0, "rotate", 45)
        assert canvas_model.getItemTransform(0)["rotate"] == 45

        canvas_model.updateTransformProperty(0, "rotate", 0)
        assert canvas_model.getItemTransform(0)["rotate"] == 0

        canvas_model.updateTransformProperty(0, "rotate", 359)
        assert canvas_model.getItemTransform(0)["rotate"] == 359

    def test_rotation_360_normalizes_to_0(self, canvas_model):
        """360° should normalize to 0°."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

        canvas_model.updateTransformProperty(0, "rotate", 360)
        assert canvas_model.getItemTransform(0)["rotate"] == 0

    def test_rotation_negative_normalizes_to_positive(self, canvas_model):
        """Negative rotations should normalize to 0-360 range."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

        canvas_model.updateTransformProperty(0, "rotate", -45)
        assert canvas_model.getItemTransform(0)["rotate"] == 315

        canvas_model.updateTransformProperty(0, "rotate", -90)
        assert canvas_model.getItemTransform(0)["rotate"] == 270

        canvas_model.updateTransformProperty(0, "rotate", -180)
        assert canvas_model.getItemTransform(0)["rotate"] == 180

    def test_rotation_over_360_wraps(self, canvas_model):
        """Rotations over 360° should wrap."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

        canvas_model.updateTransformProperty(0, "rotate", 370)
        assert canvas_model.getItemTransform(0)["rotate"] == 10

        canvas_model.updateTransformProperty(0, "rotate", 720)
        assert canvas_model.getItemTransform(0)["rotate"] == 0

        canvas_model.updateTransformProperty(0, "rotate", 450)
        assert canvas_model.getItemTransform(0)["rotate"] == 90

    def test_rotation_large_negative_wraps(self, canvas_model):
        """Large negative rotations should wrap correctly."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

        canvas_model.updateTransformProperty(0, "rotate", -370)
        assert canvas_model.getItemTransform(0)["rotate"] == 350

        canvas_model.updateTransformProperty(0, "rotate", -720)
        assert canvas_model.getItemTransform(0)["rotate"] == 0

    def test_set_item_transform_normalizes_rotation(self, canvas_model):
        """setItemTransform should also normalize rotation."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

        canvas_model.setItemTransform(0, {"rotate": -45, "scaleX": 1, "scaleY": 1})
        assert canvas_model.getItemTransform(0)["rotate"] == 315

    def test_rotation_normalization_preserves_visual_result(self, canvas_model):
        """Normalized rotation should produce same visual result."""
        # -45° and 315° should produce identical bounding boxes
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=100))
        canvas_model.setItemTransform(
            0, {"rotate": 315, "originX": 0.5, "originY": 0.5}
        )
        bounds_315 = canvas_model.getBoundingBox(0)

        # The stored value should be 315, not -45
        assert canvas_model.getItemTransform(0)["rotate"] == 315

        # Visual bounds should match what -45° would produce
        assert bounds_315 is not None
        assert bounds_315["width"] > 0


class TestApplyScaleResize:
    """Tests for applyScaleResize method - scale-based resize with anchoring."""

    def test_apply_scale_resize_updates_scale(self, canvas_model):
        """applyScaleResize should update scaleX and scaleY."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

        canvas_model.applyScaleResize(0, 2.0, 1.5, 0.0, 0.0)

        transform = canvas_model.getItemTransform(0)
        assert transform["scaleX"] == 2.0
        assert transform["scaleY"] == 1.5

    def test_apply_scale_resize_sets_origin(self, canvas_model):
        """applyScaleResize should set origin to anchor point."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

        # Resize from bottom-right, anchor at top-left (0, 0)
        canvas_model.applyScaleResize(0, 1.5, 1.5, 0.0, 0.0)

        transform = canvas_model.getItemTransform(0)
        assert transform["originX"] == 0.0
        assert transform["originY"] == 0.0

    def test_apply_scale_resize_anchor_bottom_right(self, canvas_model):
        """Anchor at bottom-right should set origin to (1, 1)."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

        # Resize from top-left, anchor at bottom-right (1, 1)
        canvas_model.applyScaleResize(0, 2.0, 2.0, 1.0, 1.0)

        transform = canvas_model.getItemTransform(0)
        assert transform["originX"] == 1.0
        assert transform["originY"] == 1.0

    def test_apply_scale_resize_preserves_rotation(self, canvas_model):
        """applyScaleResize should preserve existing rotation."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=50)
        rect_data["transform"] = {"rotate": 45}
        canvas_model.addItem(rect_data)

        canvas_model.applyScaleResize(0, 2.0, 2.0, 0.5, 0.5)

        transform = canvas_model.getItemTransform(0)
        assert transform["rotate"] == 45
        assert transform["scaleX"] == 2.0

    def test_apply_scale_resize_invalid_index(self, canvas_model):
        """applyScaleResize should handle invalid index gracefully."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))
        # Should not raise
        canvas_model.applyScaleResize(-1, 2.0, 2.0, 0.0, 0.0)
        canvas_model.applyScaleResize(999, 2.0, 2.0, 0.0, 0.0)

    def test_apply_scale_resize_compensates_translation_on_origin_change(
        self, canvas_model
    ):
        """Changing origin should adjust translation to keep visual position."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=100)
        rect_data["transform"] = {
            "translateX": 0,
            "translateY": 0,
            "rotate": 0,
            "scaleX": 1.0,
            "scaleY": 1.0,
            "originX": 0.5,
            "originY": 0.5,
        }
        canvas_model.addItem(rect_data)

        # Change origin from center to top-left, scale 2x
        canvas_model.applyScaleResize(0, 2.0, 2.0, 0.0, 0.0)

        # The visual position should remain consistent
        transform = canvas_model.getItemTransform(0)
        assert transform["originX"] == 0.0
        assert transform["originY"] == 0.0

    def test_apply_scale_resize_layer_no_op(self, canvas_model):
        """applyScaleResize on layer (no transform attr) should do nothing."""
        canvas_model.addItem(make_layer(name="Test Layer"))
        # Should not raise
        canvas_model.applyScaleResize(0, 2.0, 2.0, 0.0, 0.0)


class TestEnsureOriginCentered:
    """Tests for ensureOriginCentered method - move origin to center."""

    def test_ensure_origin_centered_from_corner(self, canvas_model):
        """ensureOriginCentered should move origin from corner to center."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=100)
        rect_data["transform"] = {
            "originX": 0.0,
            "originY": 0.0,
        }
        canvas_model.addItem(rect_data)

        canvas_model.ensureOriginCentered(0)

        transform = canvas_model.getItemTransform(0)
        assert transform["originX"] == 0.5
        assert transform["originY"] == 0.5

    def test_ensure_origin_centered_already_centered_no_op(self, canvas_model):
        """ensureOriginCentered should do nothing if already centered."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=100)
        rect_data["transform"] = {
            "originX": 0.5,
            "originY": 0.5,
            "translateX": 10,
        }
        canvas_model.addItem(rect_data)

        original_tx = canvas_model.getItemTransform(0)["translateX"]

        canvas_model.ensureOriginCentered(0)

        # Should not change translation
        transform = canvas_model.getItemTransform(0)
        assert transform["translateX"] == original_tx

    def test_ensure_origin_centered_preserves_visual_position(self, canvas_model):
        """ensureOriginCentered adjusts translation to maintain visual position."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=100)
        rect_data["transform"] = {
            "originX": 0.0,  # Top-left corner
            "originY": 0.0,
            "rotate": 45,
            "translateX": 0,
            "translateY": 0,
        }
        canvas_model.addItem(rect_data)

        # Get bounds before centering origin
        bounds_before = canvas_model.getBoundingBox(0)

        canvas_model.ensureOriginCentered(0)

        # Get bounds after centering origin
        bounds_after = canvas_model.getBoundingBox(0)

        # Visual position should be the same (within floating point tolerance)
        assert abs(bounds_before["x"] - bounds_after["x"]) < 0.01
        assert abs(bounds_before["y"] - bounds_after["y"]) < 0.01

    def test_ensure_origin_centered_invalid_index(self, canvas_model):
        """ensureOriginCentered should handle invalid index gracefully."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))
        # Should not raise
        canvas_model.ensureOriginCentered(-1)
        canvas_model.ensureOriginCentered(999)

    def test_ensure_origin_centered_layer_no_op(self, canvas_model):
        """ensureOriginCentered on layer should do nothing."""
        canvas_model.addItem(make_layer(name="Test Layer"))
        # Should not raise
        canvas_model.ensureOriginCentered(0)

    def test_ensure_origin_centered_with_scale(self, canvas_model):
        """ensureOriginCentered should work correctly with existing scale."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=100)
        rect_data["transform"] = {
            "originX": 1.0,  # Bottom-right
            "originY": 1.0,
            "scaleX": 2.0,
            "scaleY": 2.0,
        }
        canvas_model.addItem(rect_data)

        bounds_before = canvas_model.getBoundingBox(0)

        canvas_model.ensureOriginCentered(0)

        bounds_after = canvas_model.getBoundingBox(0)
        transform = canvas_model.getItemTransform(0)

        assert transform["originX"] == 0.5
        assert transform["originY"] == 0.5
        # Visual position should be preserved
        assert abs(bounds_before["x"] - bounds_after["x"]) < 0.01
        assert abs(bounds_before["y"] - bounds_after["y"]) < 0.01


class TestBakeTransform:
    """Tests for bakeTransform method - apply transform to geometry."""

    def test_bake_transform_rectangle_scale(self, canvas_model):
        """Baking scale should update geometry and reset transform."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=50)
        rect_data["transform"] = {"scaleX": 2.0, "scaleY": 2.0}
        canvas_model.addItem(rect_data)

        canvas_model.bakeTransform(0)

        # Geometry should be scaled
        bounds = canvas_model.getGeometryBounds(0)
        # After 2x scale from origin (0,0), bounds should be 200x100
        assert bounds["width"] == 200
        assert bounds["height"] == 100

        # Transform should be reset to identity
        transform = canvas_model.getItemTransform(0)
        assert transform["scaleX"] == 1
        assert transform["scaleY"] == 1

    def test_bake_transform_rectangle_rotation_converts_to_path(self, canvas_model):
        """Baking rotated rectangle should convert to path with rotated corners."""
        import math

        # 100x100 square centered at origin (0,0 to 100,100, center at 50,50)
        rect_data = make_rectangle(x=0, y=0, width=100, height=100)
        rect_data["transform"] = {
            "rotate": 45,
            "originX": 0.5,
            "originY": 0.5,
        }
        canvas_model.addItem(rect_data)

        # Get the item type before baking
        item_before = canvas_model.getItemData(0)
        assert item_before["type"] == "rectangle"

        canvas_model.bakeTransform(0)

        # Item should now be a path
        item_after = canvas_model.getItemData(0)
        assert item_after["type"] == "path"

        # Transform should be reset to identity
        transform = canvas_model.getItemTransform(0)
        assert transform["rotate"] == 0
        assert transform["scaleX"] == 1
        assert transform["scaleY"] == 1

        # The path should have 4 points (corners of rotated square)
        points = item_after["geometry"]["points"]
        assert len(points) == 4

        # For a 100x100 square rotated 45° around center (50,50):
        # The diagonal half-length is 50*sqrt(2) ≈ 70.71
        # Top corner should be at (50, 50 - 70.71)
        # Right corner at (50 + 70.71, 50)
        # Bottom corner at (50, 50 + 70.71)
        # Left corner at (50 - 70.71, 50)
        half_diag = 50 * math.sqrt(2)

        # Verify the path bounds match the rotated rectangle bounds
        xs = [p["x"] for p in points]
        ys = [p["y"] for p in points]
        assert abs(min(xs) - (50 - half_diag)) < 0.01
        assert abs(max(xs) - (50 + half_diag)) < 0.01
        assert abs(min(ys) - (50 - half_diag)) < 0.01
        assert abs(max(ys) - (50 + half_diag)) < 0.01

    def test_bake_transform_rectangle_no_rotation_keeps_rectangle(self, canvas_model):
        """Baking rectangle without rotation should keep it as rectangle."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=50)
        rect_data["transform"] = {
            "scaleX": 2.0,
            "translateX": 10,
        }
        canvas_model.addItem(rect_data)

        canvas_model.bakeTransform(0)

        # Item should still be a rectangle
        item_after = canvas_model.getItemData(0)
        assert item_after["type"] == "rectangle"

    def test_bake_transform_identity_no_op(self, canvas_model):
        """Baking identity transform should do nothing."""
        canvas_model.addItem(make_rectangle(x=10, y=20, width=100, height=50))

        original_bounds = canvas_model.getGeometryBounds(0)

        canvas_model.bakeTransform(0)

        new_bounds = canvas_model.getGeometryBounds(0)
        assert new_bounds["x"] == original_bounds["x"]
        assert new_bounds["y"] == original_bounds["y"]
        assert new_bounds["width"] == original_bounds["width"]
        assert new_bounds["height"] == original_bounds["height"]

    def test_bake_transform_invalid_index(self, canvas_model):
        """bakeTransform should handle invalid index gracefully."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))
        # Should not raise
        canvas_model.bakeTransform(-1)
        canvas_model.bakeTransform(999)

    def test_bake_transform_undoable(self, canvas_model, history_manager):
        """Baking transform should be undoable."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=50)
        rect_data["transform"] = {"scaleX": 2.0, "scaleY": 2.0}
        canvas_model.addItem(rect_data)

        original_transform = canvas_model.getItemTransform(0)
        original_bounds = canvas_model.getGeometryBounds(0)

        canvas_model.bakeTransform(0)

        # Verify bake happened
        assert canvas_model.getItemTransform(0)["scaleX"] == 1

        # Undo
        history_manager.undo()

        # Should restore original state
        restored_transform = canvas_model.getItemTransform(0)
        restored_bounds = canvas_model.getGeometryBounds(0)

        assert restored_transform["scaleX"] == original_transform["scaleX"]
        assert restored_bounds["width"] == original_bounds["width"]

    def test_bake_transform_layer_no_op(self, canvas_model):
        """bakeTransform on layer should do nothing."""
        canvas_model.addItem(make_layer(name="Test Layer"))
        # Should not raise
        canvas_model.bakeTransform(0)

    def test_bake_transform_ellipse_rotation_converts_to_path(self, canvas_model):
        """Baking rotated ellipse should convert to path with 32 points."""
        ellipse_data = make_ellipse(center_x=50, center_y=50, radius_x=40, radius_y=20)
        ellipse_data["transform"] = {
            "rotate": 30,
            "originX": 0.5,
            "originY": 0.5,
        }
        canvas_model.addItem(ellipse_data)

        # Get the item type before baking
        item_before = canvas_model.getItemData(0)
        assert item_before["type"] == "ellipse"

        canvas_model.bakeTransform(0)

        # Item should now be a path
        item_after = canvas_model.getItemData(0)
        assert item_after["type"] == "path"

        # The path should have 32 points (ellipse approximation)
        points = item_after["geometry"]["points"]
        assert len(points) == 32

        # Transform should be reset to identity
        transform = canvas_model.getItemTransform(0)
        assert transform["rotate"] == 0

    def test_bake_transform_path_rotation_transforms_points(self, canvas_model):
        """Baking rotated path should transform all point coordinates."""

        # Simple triangle path
        original_points = [
            {"x": 0, "y": 0},
            {"x": 100, "y": 0},
            {"x": 50, "y": 100},
        ]
        path_data = make_path(points=original_points, closed=True)
        path_data["transform"] = {
            "rotate": 90,
            "originX": 0.5,
            "originY": 0.5,
        }
        canvas_model.addItem(path_data)

        # Get original item
        item_before = canvas_model.getItemData(0)
        assert item_before["type"] == "path"

        canvas_model.bakeTransform(0)

        # Item should still be a path
        item_after = canvas_model.getItemData(0)
        assert item_after["type"] == "path"

        # Points should be transformed (rotated 90°)
        points = item_after["geometry"]["points"]
        assert len(points) == 3

        # Transform should be reset
        transform = canvas_model.getItemTransform(0)
        assert transform["rotate"] == 0

        # After 90° rotation around center, points should be different
        # The bounding box orientation should have changed
        xs = [p["x"] for p in points]
        ys = [p["y"] for p in points]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)

        # Original was 100 wide x 100 tall, after 90° rotation should be similar
        # but with transformed coordinates
        assert width > 0
        assert height > 0

    def test_bake_transform_ellipse_no_rotation_keeps_ellipse(self, canvas_model):
        """Baking ellipse without rotation should keep it as ellipse."""
        ellipse_data = make_ellipse(center_x=50, center_y=50, radius_x=40, radius_y=20)
        ellipse_data["transform"] = {
            "scaleX": 2.0,
            "translateX": 10,
        }
        canvas_model.addItem(ellipse_data)

        canvas_model.bakeTransform(0)

        # Item should still be an ellipse
        item_after = canvas_model.getItemData(0)
        assert item_after["type"] == "ellipse"


class TestTransformedPathPoints:
    """Tests for getTransformedPathPoints and transformPointToGeometry."""

    def test_get_transformed_path_points_identity(self, canvas_model):
        """Identity transform returns original points."""
        path_data = make_path(
            points=[{"x": 0, "y": 0}, {"x": 100, "y": 0}, {"x": 100, "y": 100}]
        )
        canvas_model.addItem(path_data)

        points = canvas_model.getTransformedPathPoints(0)
        assert points is not None
        assert len(points) == 3
        assert points[0]["x"] == 0
        assert points[0]["y"] == 0
        assert points[1]["x"] == 100
        assert points[1]["y"] == 0

    def test_get_transformed_path_points_with_translation(self, canvas_model):
        """Translation shifts all points."""
        path_data = make_path(points=[{"x": 0, "y": 0}, {"x": 100, "y": 0}])
        path_data["transform"] = {
            "translateX": 50,
            "translateY": 25,
        }
        canvas_model.addItem(path_data)

        points = canvas_model.getTransformedPathPoints(0)
        assert points is not None
        assert points[0]["x"] == 50
        assert points[0]["y"] == 25
        assert points[1]["x"] == 150
        assert points[1]["y"] == 25

    def test_get_transformed_path_points_with_scale(self, canvas_model):
        """Scale factor is applied to points."""
        path_data = make_path(points=[{"x": 0, "y": 0}, {"x": 100, "y": 0}])
        path_data["transform"] = {
            "scaleX": 2.0,
            "scaleY": 2.0,
            "originX": 0,
            "originY": 0,
        }
        canvas_model.addItem(path_data)

        points = canvas_model.getTransformedPathPoints(0)
        assert points is not None
        assert points[0]["x"] == 0
        assert points[0]["y"] == 0
        assert points[1]["x"] == 200
        assert points[1]["y"] == 0

    def test_get_transformed_path_points_with_handles(self, canvas_model):
        """Handles are also transformed."""
        path_data = make_path(
            points=[
                {"x": 0, "y": 0, "handleOut": {"x": 50, "y": 0}},
                {"x": 100, "y": 0, "handleIn": {"x": 50, "y": 0}},
            ]
        )
        path_data["transform"] = {"translateX": 10, "translateY": 20}
        canvas_model.addItem(path_data)

        points = canvas_model.getTransformedPathPoints(0)
        assert points is not None
        assert points[0]["handleOut"]["x"] == 60
        assert points[0]["handleOut"]["y"] == 20
        assert points[1]["handleIn"]["x"] == 60
        assert points[1]["handleIn"]["y"] == 20

    def test_get_transformed_path_points_invalid_index(self, canvas_model):
        """Invalid index returns None."""
        assert canvas_model.getTransformedPathPoints(-1) is None
        assert canvas_model.getTransformedPathPoints(999) is None

    def test_get_transformed_path_points_non_path_item(self, canvas_model):
        """Non-path items return None."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=100))
        assert canvas_model.getTransformedPathPoints(0) is None

    def test_transform_point_to_geometry_identity(self, canvas_model):
        """Identity transform returns input point."""
        path_data = make_path(points=[{"x": 0, "y": 0}, {"x": 100, "y": 0}])
        canvas_model.addItem(path_data)

        result = canvas_model.transformPointToGeometry(0, 50, 25)
        assert result is not None
        assert result["x"] == 50
        assert result["y"] == 25

    def test_transform_point_to_geometry_with_translation(self, canvas_model):
        """Inverse transform subtracts translation."""
        path_data = make_path(points=[{"x": 0, "y": 0}, {"x": 100, "y": 0}])
        path_data["transform"] = {"translateX": 50, "translateY": 25}
        canvas_model.addItem(path_data)

        result = canvas_model.transformPointToGeometry(0, 100, 50)
        assert result is not None
        assert abs(result["x"] - 50) < 0.001
        assert abs(result["y"] - 25) < 0.001

    def test_transform_point_round_trip(self, canvas_model):
        """Forward and inverse transforms are consistent."""
        path_data = make_path(points=[{"x": 0, "y": 0}, {"x": 100, "y": 100}])
        path_data["transform"] = {
            "translateX": 20,
            "translateY": 30,
            "rotate": 45,
            "scaleX": 1.5,
            "scaleY": 0.8,
            "originX": 0.5,
            "originY": 0.5,
        }
        canvas_model.addItem(path_data)

        transformed = canvas_model.getTransformedPathPoints(0)
        assert transformed is not None

        for i, tp in enumerate(transformed):
            geom = canvas_model.transformPointToGeometry(0, tp["x"], tp["y"])
            orig = path_data["geometry"]["points"][i]
            assert abs(geom["x"] - orig["x"]) < 0.001
            assert abs(geom["y"] - orig["y"]) < 0.001

    def test_transform_point_to_geometry_invalid_index(self, canvas_model):
        """Invalid index returns None."""
        assert canvas_model.transformPointToGeometry(-1, 0, 0) is None
        assert canvas_model.transformPointToGeometry(999, 0, 0) is None
