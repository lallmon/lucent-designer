# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Integration tests for spatial indexing with CanvasModel."""

from test_helpers import make_rectangle, make_ellipse


class TestSpatialIndexIntegration:
    """Tests for spatial index integration with CanvasModel."""

    def test_spatial_index_updated_on_add(self, canvas_model, qtbot):
        """Spatial index should be updated when items are added."""
        rect_data = make_rectangle(x=100, y=100, width=50, height=50)

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            canvas_model.addItem(rect_data)

        # Query should find the item
        items = canvas_model.getRenderItemsInBounds(90, 90, 70, 70)
        assert len(items) == 1

    def test_spatial_index_updated_on_remove(self, canvas_model, qtbot):
        """Spatial index should be updated when items are removed."""
        rect_data = make_rectangle(x=100, y=100, width=50, height=50)

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            canvas_model.addItem(rect_data)

        # Verify it exists
        items = canvas_model.getRenderItemsInBounds(90, 90, 70, 70)
        assert len(items) == 1

        # Remove item
        canvas_model.removeItem(0)

        # Query should no longer find the item
        items = canvas_model.getRenderItemsInBounds(90, 90, 70, 70)
        assert len(items) == 0

    def test_spatial_index_updated_on_modify(self, canvas_model, qtbot):
        """Spatial index should be updated when items are modified."""
        rect_data = make_rectangle(x=100, y=100, width=50, height=50)

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            canvas_model.addItem(rect_data)

        # Move item to new location (must use geometry dict format)
        canvas_model.updateItem(
            0, {"geometry": {"x": 500, "y": 500, "width": 50, "height": 50}}
        )

        # Should NOT be found at old location
        items = canvas_model.getRenderItemsInBounds(90, 90, 70, 70)
        assert len(items) == 0

        # Should be found at new location
        items = canvas_model.getRenderItemsInBounds(490, 490, 70, 70)
        assert len(items) == 1

    def test_spatial_query_excludes_non_intersecting(self, canvas_model, qtbot):
        """Spatial query should only return items in the queried region."""
        # Add items in different locations
        rect1 = make_rectangle(x=0, y=0, width=50, height=50)
        rect2 = make_rectangle(x=500, y=500, width=50, height=50)
        rect3 = make_rectangle(x=1000, y=1000, width=50, height=50)

        for r in [rect1, rect2, rect3]:
            with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
                canvas_model.addItem(r)

        # Query near first rect only
        items = canvas_model.getRenderItemsInBounds(-10, -10, 100, 100)
        assert len(items) == 1

        # Query near second rect only
        items = canvas_model.getRenderItemsInBounds(480, 480, 100, 100)
        assert len(items) == 1

        # Query covering all items
        items = canvas_model.getRenderItemsInBounds(-100, -100, 1200, 1200)
        assert len(items) == 3

    def test_spatial_query_returns_items_in_model_order(self, canvas_model, qtbot):
        """Spatial query should return items in model order (bottom to top)."""
        # Add items in specific order
        rects = [
            make_rectangle(x=10, y=10, width=30, height=30, name="First"),
            make_rectangle(x=20, y=20, width=30, height=30, name="Second"),
            make_rectangle(x=30, y=30, width=30, height=30, name="Third"),
        ]

        for r in rects:
            with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
                canvas_model.addItem(r)

        # Query all overlapping items
        items = canvas_model.getRenderItemsInBounds(0, 0, 100, 100)
        assert len(items) == 3

        # Verify model order is preserved
        names = [item.name for item in items]
        assert names == ["First", "Second", "Third"]

    def test_spatial_query_filters_invisible_items(self, canvas_model, qtbot):
        """Spatial query should filter out invisible items."""
        # Add visible rect
        visible_rect = make_rectangle(x=50, y=50, width=50, height=50, name="Visible")
        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            canvas_model.addItem(visible_rect)

        # Add invisible rect
        invisible_rect = make_rectangle(
            x=60, y=60, width=50, height=50, name="Invisible"
        )
        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            canvas_model.addItem(invisible_rect)

        # Hide the second rect
        canvas_model.updateItem(1, {"visible": False})

        # Query should only return visible item
        items = canvas_model.getRenderItemsInBounds(40, 40, 80, 80)
        assert len(items) == 1
        assert items[0].name == "Visible"

    def test_spatial_index_cleared_on_clear(self, canvas_model, qtbot):
        """Spatial index should be cleared when model is cleared."""
        # Add some items
        for i in range(5):
            rect = make_rectangle(x=i * 100, y=i * 100, width=50, height=50)
            with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
                canvas_model.addItem(rect)

        # Verify items exist
        items = canvas_model.getRenderItemsInBounds(-1000, -1000, 2000, 2000)
        assert len(items) == 5

        # Clear model
        canvas_model.clear()

        # Query should return empty
        items = canvas_model.getRenderItemsInBounds(-1000, -1000, 2000, 2000)
        assert len(items) == 0

    def test_spatial_query_with_ellipse(self, canvas_model, qtbot):
        """Spatial query should work with ellipse items."""
        ellipse_data = make_ellipse(
            center_x=100, center_y=100, radius_x=50, radius_y=30
        )

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            canvas_model.addItem(ellipse_data)

        # Query covering ellipse
        items = canvas_model.getRenderItemsInBounds(40, 60, 120, 80)
        assert len(items) == 1

        # Query not covering ellipse
        items = canvas_model.getRenderItemsInBounds(500, 500, 100, 100)
        assert len(items) == 0
