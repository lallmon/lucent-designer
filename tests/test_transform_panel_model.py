# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for transform panel model methods - position, size, and origin control."""

from test_helpers import make_rectangle, make_layer


class TestGetDisplayedPosition:
    """Tests for getDisplayedPosition - get X,Y based on geometry + origin."""

    def test_displayed_position_no_transform(self, canvas_model):
        """Displayed position matches geometry when no transform applied."""
        canvas_model.addItem(make_rectangle(x=10, y=20, width=100, height=50))

        pos = canvas_model.getDisplayedPosition(0)

        # With pivot at center and no translation, displayed pos = center
        assert pos["x"] == 60
        assert pos["y"] == 45

    def test_displayed_position_with_translation(self, canvas_model):
        """Displayed position accounts for translation."""
        rect_data = make_rectangle(x=10, y=20, width=100, height=50)
        rect_data["transform"] = {"translateX": 5, "translateY": 15}
        canvas_model.addItem(rect_data)

        pos = canvas_model.getDisplayedPosition(0)

        # displayedX = pivotX + translateX (pivot defaults to center)
        assert pos["x"] == 65
        assert pos["y"] == 60

    def test_displayed_position_with_origin_offset(self, canvas_model):
        """Displayed position accounts for origin point in geometry."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=100)
        rect_data["transform"] = {"pivotX": 50, "pivotY": 50}
        canvas_model.addItem(rect_data)

        pos = canvas_model.getDisplayedPosition(0)

        # displayedX = 0 + 100 * 0.5 + 0 = 50
        # displayedY = 0 + 100 * 0.5 + 0 = 50
        assert pos["x"] == 50
        assert pos["y"] == 50

    def test_displayed_position_with_origin_and_translation(self, canvas_model):
        """Displayed position combines origin offset and translation."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=100)
        rect_data["transform"] = {
            "pivotX": 50,
            "pivotY": 50,
            "translateX": 10,
            "translateY": -20,
        }
        canvas_model.addItem(rect_data)

        pos = canvas_model.getDisplayedPosition(0)

        # displayedX = 0 + 100 * 0.5 + 10 = 60
        # displayedY = 0 + 100 * 0.5 + (-20) = 30
        assert pos["x"] == 60
        assert pos["y"] == 30

    def test_displayed_position_invalid_index(self, canvas_model):
        """Returns None for invalid index."""
        assert canvas_model.getDisplayedPosition(-1) is None
        assert canvas_model.getDisplayedPosition(999) is None

    def test_displayed_position_layer_returns_none(self, canvas_model):
        """Layers have no displayed position."""
        canvas_model.addItem(make_layer(name="Test Layer"))
        assert canvas_model.getDisplayedPosition(0) is None


class TestSetItemPosition:
    """Tests for setItemPosition - set X or Y position based on origin."""

    def test_set_position_x_no_origin(self, canvas_model):
        """Setting X position adjusts translation to place origin at target."""
        canvas_model.addItem(make_rectangle(x=10, y=20, width=100, height=50))

        canvas_model.setItemPosition(0, "x", 50)

        pos = canvas_model.getDisplayedPosition(0)
        assert pos["x"] == 50
        assert pos["y"] == 45  # Y unchanged (pivot defaults to center)

    def test_set_position_y_no_origin(self, canvas_model):
        """Setting Y position adjusts translation."""
        canvas_model.addItem(make_rectangle(x=10, y=20, width=100, height=50))

        canvas_model.setItemPosition(0, "y", 100)

        pos = canvas_model.getDisplayedPosition(0)
        assert pos["x"] == 60  # X unchanged (pivot defaults to center)
        assert pos["y"] == 100

    def test_set_position_with_origin_at_center(self, canvas_model):
        """Position is relative to origin point."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=100)
        rect_data["transform"] = {"pivotX": 50, "pivotY": 50}
        canvas_model.addItem(rect_data)

        canvas_model.setItemPosition(0, "x", 200)

        pos = canvas_model.getDisplayedPosition(0)
        # Origin (center) should now be at x=200
        assert pos["x"] == 200

    def test_set_position_preserves_other_transform_properties(self, canvas_model):
        """Setting position should preserve rotation, scale, etc."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=100)
        rect_data["transform"] = {
            "rotate": 45,
            "scaleX": 2.0,
            "scaleY": 1.5,
            "pivotX": 50,
            "pivotY": 50,
        }
        canvas_model.addItem(rect_data)

        canvas_model.setItemPosition(0, "x", 100)

        transform = canvas_model.getItemTransform(0)
        assert transform["rotate"] == 45
        assert transform["scaleX"] == 2.0
        assert transform["scaleY"] == 1.5

    def test_set_position_invalid_index(self, canvas_model):
        """Setting position on invalid index should not raise."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))
        canvas_model.setItemPosition(-1, "x", 50)
        canvas_model.setItemPosition(999, "y", 50)

    def test_set_position_layer_no_op(self, canvas_model):
        """Setting position on layer should do nothing."""
        canvas_model.addItem(make_layer(name="Test Layer"))
        canvas_model.setItemPosition(0, "x", 50)


class TestSetDisplayedSize:
    """Tests for setDisplayedSize - set displayed width/height via scale."""

    def test_set_displayed_width_scales_x(self, canvas_model):
        """Setting displayed width modifies scaleX."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

        canvas_model.setDisplayedSize(0, "width", 200, False)

        transform = canvas_model.getItemTransform(0)
        # To display 200px from 100px geometry, scaleX = 2.0
        assert transform["scaleX"] == 2.0
        assert transform["scaleY"] == 1  # Unchanged

    def test_set_displayed_height_scales_y(self, canvas_model):
        """Setting displayed height modifies scaleY."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

        canvas_model.setDisplayedSize(0, "height", 100, False)

        transform = canvas_model.getItemTransform(0)
        # To display 100px from 50px geometry, scaleY = 2.0
        assert transform["scaleX"] == 1  # Unchanged
        assert transform["scaleY"] == 2.0

    def test_set_displayed_width_proportional(self, canvas_model):
        """Proportional mode scales both axes equally."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

        canvas_model.setDisplayedSize(0, "width", 200, True)

        transform = canvas_model.getItemTransform(0)
        # Width doubles, so scaleX = 2.0, and proportionally scaleY = 2.0
        assert transform["scaleX"] == 2.0
        assert transform["scaleY"] == 2.0

    def test_set_displayed_height_proportional(self, canvas_model):
        """Proportional mode from height scales both axes."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

        canvas_model.setDisplayedSize(0, "height", 100, True)

        transform = canvas_model.getItemTransform(0)
        # Height doubles, so scaleY = 2.0, and proportionally scaleX = 2.0
        assert transform["scaleX"] == 2.0
        assert transform["scaleY"] == 2.0

    def test_set_displayed_size_proportional_from_existing_scale(self, canvas_model):
        """Proportional scaling works from non-identity scale."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=50)
        rect_data["transform"] = {"scaleX": 1.5, "scaleY": 3.0}
        canvas_model.addItem(rect_data)

        # Current displayed: 150 x 150
        # Set width to 300 (double), should double both scales
        canvas_model.setDisplayedSize(0, "width", 300, True)

        transform = canvas_model.getItemTransform(0)
        # scaleX: 1.5 * 2 = 3.0, scaleY: 3.0 * 2 = 6.0
        assert transform["scaleX"] == 3.0
        assert transform["scaleY"] == 6.0

    def test_set_displayed_size_minimum_1px(self, canvas_model):
        """Minimum displayed size is clamped to 1px."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

        canvas_model.setDisplayedSize(0, "width", 0, False)

        transform = canvas_model.getItemTransform(0)
        # Clamped to 1px, so scaleX = 1/100 = 0.01
        assert transform["scaleX"] == 0.01

    def test_set_displayed_size_preserves_other_properties(self, canvas_model):
        """Setting size preserves rotation, translation, origin."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=100)
        rect_data["transform"] = {
            "rotate": 30,
            "translateX": 10,
            "translateY": 20,
            "pivotX": 50,
            "pivotY": 50,
        }
        canvas_model.addItem(rect_data)

        canvas_model.setDisplayedSize(0, "width", 200, False)

        transform = canvas_model.getItemTransform(0)
        assert transform["rotate"] == 30
        assert transform["translateX"] == 10
        assert transform["translateY"] == 20
        assert transform["originX"] == 0.5
        assert transform["originY"] == 0.5

    def test_set_displayed_size_invalid_index(self, canvas_model):
        """Setting size on invalid index should not raise."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))
        canvas_model.setDisplayedSize(-1, "width", 200, False)
        canvas_model.setDisplayedSize(999, "height", 100, False)

    def test_set_displayed_size_layer_no_op(self, canvas_model):
        """Setting size on layer should do nothing."""
        canvas_model.addItem(make_layer(name="Test Layer"))
        canvas_model.setDisplayedSize(0, "width", 200, False)

    def test_set_displayed_size_zero_geometry_no_op(self, canvas_model):
        """Setting size on zero-dimension geometry should not crash."""
        rect_data = make_rectangle(x=0, y=0, width=0, height=50)
        canvas_model.addItem(rect_data)
        # Should not raise
        canvas_model.setDisplayedSize(0, "width", 100, False)


class TestGetDisplayedSize:
    """Tests for getDisplayedSize - get displayed width/height via geometry × scale."""

    def test_displayed_size_no_transform(self, canvas_model):
        """Displayed size equals geometry when no scale applied."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

        size = canvas_model.getDisplayedSize(0)

        assert size["width"] == 100
        assert size["height"] == 50

    def test_displayed_size_with_scale(self, canvas_model):
        """Displayed size is geometry × scale."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=50)
        rect_data["transform"] = {"scaleX": 2.0, "scaleY": 3.0}
        canvas_model.addItem(rect_data)

        size = canvas_model.getDisplayedSize(0)

        assert size["width"] == 200  # 100 * 2
        assert size["height"] == 150  # 50 * 3

    def test_displayed_size_with_partial_scale(self, canvas_model):
        """Displayed size works with only one scale axis specified."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=50)
        rect_data["transform"] = {"scaleX": 1.5}  # scaleY defaults to 1
        canvas_model.addItem(rect_data)

        size = canvas_model.getDisplayedSize(0)

        assert size["width"] == 150
        assert size["height"] == 50

    def test_displayed_size_invalid_index(self, canvas_model):
        """Returns None for invalid index."""
        assert canvas_model.getDisplayedSize(-1) is None
        assert canvas_model.getDisplayedSize(999) is None

    def test_displayed_size_layer_returns_none(self, canvas_model):
        """Layers have no displayed size."""
        canvas_model.addItem(make_layer(name="Test Layer"))
        assert canvas_model.getDisplayedSize(0) is None


class TestHasNonIdentityTransform:
    """Tests for hasNonIdentityTransform - check if transform differs from identity."""

    def test_identity_transform_returns_false(self, canvas_model):
        """Identity transform (no transform) returns False."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

        assert canvas_model.hasNonIdentityTransform(0) is False

    def test_explicit_identity_returns_false(self, canvas_model):
        """Explicitly set identity values return False."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=50)
        rect_data["transform"] = {
            "translateX": 0,
            "translateY": 0,
            "rotate": 0,
            "scaleX": 1,
            "scaleY": 1,
        }
        canvas_model.addItem(rect_data)

        assert canvas_model.hasNonIdentityTransform(0) is False

    def test_rotation_returns_true(self, canvas_model):
        """Non-zero rotation returns True."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=50)
        rect_data["transform"] = {"rotate": 45}
        canvas_model.addItem(rect_data)

        assert canvas_model.hasNonIdentityTransform(0) is True

    def test_scale_x_returns_true(self, canvas_model):
        """Non-identity scaleX returns True."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=50)
        rect_data["transform"] = {"scaleX": 2.0}
        canvas_model.addItem(rect_data)

        assert canvas_model.hasNonIdentityTransform(0) is True

    def test_scale_y_returns_true(self, canvas_model):
        """Non-identity scaleY returns True."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=50)
        rect_data["transform"] = {"scaleY": 0.5}
        canvas_model.addItem(rect_data)

        assert canvas_model.hasNonIdentityTransform(0) is True

    def test_translate_x_returns_true(self, canvas_model):
        """Non-zero translateX returns True."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=50)
        rect_data["transform"] = {"translateX": 10}
        canvas_model.addItem(rect_data)

        assert canvas_model.hasNonIdentityTransform(0) is True

    def test_translate_y_returns_true(self, canvas_model):
        """Non-zero translateY returns True."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=50)
        rect_data["transform"] = {"translateY": -5}
        canvas_model.addItem(rect_data)

        assert canvas_model.hasNonIdentityTransform(0) is True

    def test_invalid_index_returns_false(self, canvas_model):
        """Invalid index returns False."""
        assert canvas_model.hasNonIdentityTransform(-1) is False
        assert canvas_model.hasNonIdentityTransform(999) is False

    def test_layer_returns_false(self, canvas_model):
        """Layers have no transform, return False."""
        canvas_model.addItem(make_layer(name="Test Layer"))
        assert canvas_model.hasNonIdentityTransform(0) is False


class TestSetItemOrigin:
    """Tests for setItemOrigin - change origin while maintaining visual position."""

    def test_set_origin_updates_origin_values(self, canvas_model):
        """setItemOrigin should update originX and originY."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=100))

        canvas_model.setItemOrigin(0, 0.5, 0.5)

        transform = canvas_model.getItemTransform(0)
        assert transform["originX"] == 0.5
        assert transform["originY"] == 0.5

    def test_set_origin_preserves_visual_position_no_rotation(self, canvas_model):
        """Visual bounds should remain same after origin change (no rotation)."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=100))

        bounds_before = canvas_model.getBoundingBox(0)

        canvas_model.setItemOrigin(0, 0.5, 0.5)

        bounds_after = canvas_model.getBoundingBox(0)

        assert abs(bounds_before["x"] - bounds_after["x"]) < 0.01
        assert abs(bounds_before["y"] - bounds_after["y"]) < 0.01

    def test_set_origin_preserves_visual_position_with_rotation(self, canvas_model):
        """Visual bounds should remain same after origin change (with rotation)."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=100)
        rect_data["transform"] = {
            "rotate": 45,
            "pivotX": 0,
            "pivotY": 0,
        }
        canvas_model.addItem(rect_data)

        bounds_before = canvas_model.getBoundingBox(0)

        canvas_model.setItemOrigin(0, 0.5, 0.5)

        bounds_after = canvas_model.getBoundingBox(0)

        assert abs(bounds_before["x"] - bounds_after["x"]) < 0.01
        assert abs(bounds_before["y"] - bounds_after["y"]) < 0.01

    def test_set_origin_preserves_visual_position_with_scale(self, canvas_model):
        """Visual bounds should remain same after origin change (with scale)."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=100)
        rect_data["transform"] = {
            "scaleX": 2.0,
            "scaleY": 1.5,
            "pivotX": 0,
            "pivotY": 0,
        }
        canvas_model.addItem(rect_data)

        bounds_before = canvas_model.getBoundingBox(0)

        canvas_model.setItemOrigin(0, 1.0, 1.0)

        bounds_after = canvas_model.getBoundingBox(0)

        assert abs(bounds_before["x"] - bounds_after["x"]) < 0.01
        assert abs(bounds_before["y"] - bounds_after["y"]) < 0.01

    def test_set_origin_preserves_visual_position_with_rotation_and_scale(
        self, canvas_model
    ):
        """Visual bounds should remain same after origin change (rotation + scale)."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=100)
        rect_data["transform"] = {
            "rotate": 30,
            "scaleX": 2.0,
            "scaleY": 1.5,
            "pivotX": 0,
            "pivotY": 0,
        }
        canvas_model.addItem(rect_data)

        bounds_before = canvas_model.getBoundingBox(0)

        canvas_model.setItemOrigin(0, 0.5, 0.5)

        bounds_after = canvas_model.getBoundingBox(0)

        assert abs(bounds_before["x"] - bounds_after["x"]) < 0.01
        assert abs(bounds_before["y"] - bounds_after["y"]) < 0.01

    def test_set_origin_preserves_rotation_and_scale(self, canvas_model):
        """setItemOrigin should preserve rotation and scale values."""
        rect_data = make_rectangle(x=0, y=0, width=100, height=100)
        rect_data["transform"] = {
            "rotate": 45,
            "scaleX": 2.0,
            "scaleY": 1.5,
        }
        canvas_model.addItem(rect_data)

        canvas_model.setItemOrigin(0, 0.5, 0.5)

        transform = canvas_model.getItemTransform(0)
        assert transform["rotate"] == 45
        assert transform["scaleX"] == 2.0
        assert transform["scaleY"] == 1.5

    def test_set_origin_invalid_index(self, canvas_model):
        """setItemOrigin on invalid index should not raise."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))
        canvas_model.setItemOrigin(-1, 0.5, 0.5)
        canvas_model.setItemOrigin(999, 0.5, 0.5)

    def test_set_origin_layer_no_op(self, canvas_model):
        """setItemOrigin on layer should do nothing."""
        canvas_model.addItem(make_layer(name="Test Layer"))
        canvas_model.setItemOrigin(0, 0.5, 0.5)

    def test_set_origin_emits_transform_changed(self, canvas_model, qtbot):
        """setItemOrigin should emit itemTransformChanged signal."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=100))

        with qtbot.waitSignal(
            canvas_model.itemTransformChanged, timeout=1000
        ) as blocker:
            canvas_model.setItemOrigin(0, 0.5, 0.5)

        assert blocker.args == [0]
