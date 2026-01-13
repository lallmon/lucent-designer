# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest

from PySide6.QtGui import QImage, QPainter
from PySide6.QtCore import QSize

from lucent.canvas_renderer import CanvasRenderer
from test_helpers import make_rectangle, make_ellipse


class TestCanvasRendererBasics:
    def test_canvas_renderer_properties(self, qapp):
        renderer = CanvasRenderer()

        assert renderer.zoomLevel == 1.0
        renderer.zoomLevel = 2.0
        assert renderer.zoomLevel == 2.0

        renderer.tileOriginX = 100.0
        renderer.tileOriginY = -50.0
        assert renderer.tileOriginX == 100.0
        assert renderer.tileOriginY == -50.0

    def test_canvas_renderer_accepts_model_none(self, qapp):
        renderer = CanvasRenderer()
        renderer.setModel(object())
        assert renderer._model is None


class TestCanvasRendererZOrder:
    """Tests for z-order (render order) in CanvasRenderer."""

    @pytest.fixture(autouse=True)
    def _attach_model(self, canvas_renderer, canvas_model):
        canvas_renderer.setModel(canvas_model)
        return canvas_renderer

    def test_render_order_matches_model_order(self, canvas_renderer, canvas_model):
        """Render order follows model order (higher index paints on top)."""
        canvas_model.addItem(
            make_rectangle(x=0, y=0, width=10, height=10, name="First")
        )
        canvas_model.addItem(
            make_rectangle(x=5, y=5, width=10, height=10, name="Second")
        )
        canvas_model.addItem(
            make_rectangle(x=10, y=10, width=10, height=10, name="Third")
        )

        render_order = canvas_renderer._get_render_order()

        assert len(render_order) == 3
        assert render_order[0].name == "First"
        assert render_order[1].name == "Second"
        assert render_order[2].name == "Third"

    def test_render_order_skips_layers(self, canvas_renderer, canvas_model):
        """Layers should be skipped in render order (they're organizational only)."""
        canvas_model.addLayer()
        canvas_model.addItem(
            make_rectangle(x=0, y=0, width=10, height=10, name="Rect1")
        )
        canvas_model.addLayer()
        canvas_model.addItem(
            make_ellipse(
                center_x=5, center_y=5, radius_x=5, radius_y=5, name="Ellipse1"
            )
        )

        render_order = canvas_renderer._get_render_order()

        assert len(render_order) == 2
        assert render_order[0].name == "Rect1"
        assert render_order[1].name == "Ellipse1"

    def test_render_order_with_parented_items(self, canvas_renderer, canvas_model):
        """Parented items render in model order."""
        canvas_model.addLayer()
        layer = canvas_model.getItems()[0]
        child1 = make_rectangle(x=0, y=0, width=10, height=10, name="Child1")
        child1["parentId"] = layer.id
        canvas_model.addItem(child1)

        child2 = make_rectangle(x=10, y=0, width=10, height=10, name="Child2")
        child2["parentId"] = layer.id
        canvas_model.addItem(child2)

        render_order = canvas_renderer._get_render_order()

        assert len(render_order) == 2
        assert render_order[0].name == "Child1"
        assert render_order[1].name == "Child2"

    def test_render_order_after_layer_move(self, canvas_renderer, canvas_model):
        """After moving a layer, render order should reflect new model order."""
        canvas_model.addLayer()
        layer1 = canvas_model.getItems()[0]
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 0,
                "y": 0,
                "width": 10,
                "height": 10,
                "name": "L1Child",
            }
        )
        canvas_model.setParent(1, layer1.id)

        canvas_model.addLayer()
        layer2 = canvas_model.getItems()[2]
        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 20,
                "y": 0,
                "width": 10,
                "height": 10,
                "name": "L2Child",
            }
        )
        canvas_model.setParent(3, layer2.id)

        render_order = canvas_renderer._get_render_order()
        assert render_order[0].name == "L1Child"
        assert render_order[1].name == "L2Child"

        canvas_model.moveItem(2, 0)

        render_order = canvas_renderer._get_render_order()
        assert render_order[0].name == "L2Child"
        assert render_order[1].name == "L1Child"

    def test_renderer_delegates_render_order_to_model(
        self, canvas_renderer, canvas_model
    ):
        """Renderer should rely on model-provided render order."""
        sentinel = ["sentinel"]
        canvas_model.getRenderItems = lambda: sentinel  # type: ignore[attr-defined]
        canvas_renderer.setModel(canvas_model)
        assert canvas_renderer._get_render_order() is sentinel

    def test_paint_no_model_is_noop(self, canvas_renderer):
        image = QImage(QSize(5, 5), QImage.Format_ARGB32)
        image.fill(0)
        painter = QPainter(image)
        canvas_renderer.paint(painter)
        painter.end()

    def test_paint_invokes_item_paint(self, canvas_renderer, canvas_model):
        """paint should iterate over render items and call their paint methods."""
        calls = []

        from PySide6.QtCore import QRectF

        class DummyItem:
            def get_bounds(self):
                return QRectF(0, 0, 100, 100)

            def paint(self, painter, zoom, offset_x=0, offset_y=0):
                calls.append(("paint", zoom))

        # Use getRenderItemsInBounds (spatial index query)
        canvas_model.getRenderItemsInBounds = lambda x, y, w, h: [DummyItem()]  # type: ignore[attr-defined]
        canvas_renderer.setModel(canvas_model)

        image = QImage(QSize(10, 10), QImage.Format_ARGB32)
        image.fill(0)
        painter = QPainter(image)
        canvas_renderer.paint(painter)
        painter.end()

        assert calls == [("paint", 1.0)]

    def test_empty_model_returns_empty_render_order(
        self, canvas_renderer, canvas_model
    ):
        """Empty model should return empty render order."""
        render_order = canvas_renderer._get_render_order()
        assert render_order == []

    def test_only_layers_returns_empty_render_order(
        self, canvas_renderer, canvas_model
    ):
        """Model with only layers should return empty render order."""
        canvas_model.addLayer()
        canvas_model.addLayer()

        render_order = canvas_renderer._get_render_order()
        assert render_order == []


class TestCanvasRendererTileCulling:
    """Tests for per-tile culling optimization."""

    @pytest.fixture(autouse=True)
    def _attach_model(self, canvas_renderer, canvas_model):
        canvas_renderer.setModel(canvas_model)
        # Set tile size for predictable bounds
        canvas_renderer.setWidth(100)
        canvas_renderer.setHeight(100)
        return canvas_renderer

    def test_get_tile_bounds_at_origin(self, canvas_renderer):
        """Tile at origin should have correct bounds."""
        canvas_renderer.tileOriginX = 0
        canvas_renderer.tileOriginY = 0

        bounds = canvas_renderer._get_tile_bounds()

        assert bounds.x() == -50  # origin - half_width
        assert bounds.y() == -50
        assert bounds.width() == 100
        assert bounds.height() == 100

    def test_get_tile_bounds_offset(self, canvas_renderer):
        """Tile with offset origin should have correct bounds."""
        canvas_renderer.tileOriginX = 500
        canvas_renderer.tileOriginY = 300

        bounds = canvas_renderer._get_tile_bounds()

        assert bounds.x() == 450  # 500 - 50
        assert bounds.y() == 250  # 300 - 50
        assert bounds.width() == 100
        assert bounds.height() == 100

    def test_item_intersects_tile_inside(self, canvas_renderer):
        """Item fully inside tile should intersect."""
        canvas_renderer.tileOriginX = 50
        canvas_renderer.tileOriginY = 50
        tile_bounds = canvas_renderer._get_tile_bounds()  # 0-100, 0-100

        from lucent.canvas_items import RectangleItem
        from lucent.geometry import RectGeometry

        item = RectangleItem(
            geometry=RectGeometry(x=25, y=25, width=50, height=50),
            appearances=[],
        )

        assert canvas_renderer._item_intersects_tile(item, tile_bounds) is True

    def test_item_intersects_tile_overlapping(self, canvas_renderer):
        """Item partially overlapping tile should intersect."""
        canvas_renderer.tileOriginX = 50
        canvas_renderer.tileOriginY = 50
        tile_bounds = canvas_renderer._get_tile_bounds()  # 0-100, 0-100

        from lucent.canvas_items import RectangleItem
        from lucent.geometry import RectGeometry

        # Item at -25 to 25 overlaps tile at 0 to 100
        item = RectangleItem(
            geometry=RectGeometry(x=-25, y=-25, width=50, height=50),
            appearances=[],
        )

        assert canvas_renderer._item_intersects_tile(item, tile_bounds) is True

    def test_item_intersects_tile_outside(self, canvas_renderer):
        """Item outside tile should not intersect."""
        canvas_renderer.tileOriginX = 50
        canvas_renderer.tileOriginY = 50
        tile_bounds = canvas_renderer._get_tile_bounds()  # 0-100, 0-100

        from lucent.canvas_items import RectangleItem
        from lucent.geometry import RectGeometry

        # Item at 200-250 is outside tile at 0-100
        item = RectangleItem(
            geometry=RectGeometry(x=200, y=200, width=50, height=50),
            appearances=[],
        )

        assert canvas_renderer._item_intersects_tile(item, tile_bounds) is False

    def test_paint_culls_items_outside_tile(self, canvas_renderer, canvas_model):
        """Paint should skip items that don't intersect the tile."""
        canvas_renderer.tileOriginX = 50
        canvas_renderer.tileOriginY = 50
        # Tile bounds: 0-100, 0-100

        paint_calls = []

        from PySide6.QtCore import QRectF

        class TrackedItem:
            def __init__(self, name, bounds):
                self.name = name
                self._bounds = bounds

            def get_bounds(self):
                return self._bounds

            def paint(self, painter, zoom, offset_x=0, offset_y=0):
                paint_calls.append(self.name)

        # Item inside tile
        inside_item = TrackedItem("inside", QRectF(25, 25, 50, 50))

        # Spatial index filters to only inside_item (simulates culling outside items)
        canvas_model.getRenderItemsInBounds = lambda x, y, w, h: [inside_item]

        image = QImage(QSize(100, 100), QImage.Format_ARGB32)
        image.fill(0)
        painter = QPainter(image)
        canvas_renderer.paint(painter)
        painter.end()

        # Only the inside item should have been painted
        assert paint_calls == ["inside"]

    def test_paint_renders_intersecting_items(self, canvas_renderer, canvas_model):
        """Paint should render all items that intersect the tile."""
        canvas_renderer.tileOriginX = 50
        canvas_renderer.tileOriginY = 50

        paint_calls = []

        from PySide6.QtCore import QRectF

        class TrackedItem:
            def __init__(self, name, bounds):
                self.name = name
                self._bounds = bounds

            def get_bounds(self):
                return self._bounds

            def paint(self, painter, zoom, offset_x=0, offset_y=0):
                paint_calls.append(self.name)

        # Multiple items inside tile
        items = [
            TrackedItem("first", QRectF(10, 10, 20, 20)),
            TrackedItem("second", QRectF(50, 50, 30, 30)),
            TrackedItem("third", QRectF(80, 80, 15, 15)),
        ]

        # Mock getRenderItemsInBounds to return all items (spatial index simulation)
        canvas_model.getRenderItemsInBounds = lambda x, y, w, h: items

        image = QImage(QSize(100, 100), QImage.Format_ARGB32)
        image.fill(0)
        painter = QPainter(image)
        canvas_renderer.paint(painter)
        painter.end()

        assert paint_calls == ["first", "second", "third"]

    def test_item_without_bounds_still_renders(self, canvas_renderer, canvas_model):
        """Items that fail get_bounds should still render (safety fallback)."""
        canvas_renderer.tileOriginX = 50
        canvas_renderer.tileOriginY = 50

        paint_calls = []

        class BrokenBoundsItem:
            def get_bounds(self):
                raise RuntimeError("No bounds available")

            def paint(self, painter, zoom, offset_x=0, offset_y=0):
                paint_calls.append("broken")

        # Model returns the broken item (spatial index can't filter without bounds)
        canvas_model.getRenderItemsInBounds = lambda x, y, w, h: [BrokenBoundsItem()]

        image = QImage(QSize(100, 100), QImage.Format_ARGB32)
        image.fill(0)
        painter = QPainter(image)
        canvas_renderer.paint(painter)
        painter.end()

        # Should render anyway since we couldn't determine bounds for LOD
        assert paint_calls == ["broken"]


class TestCanvasRendererLOD:
    """Tests for Level of Detail (LOD) skipping optimization."""

    @pytest.fixture(autouse=True)
    def _attach_model(self, canvas_renderer, canvas_model):
        canvas_renderer.setModel(canvas_model)
        canvas_renderer.setWidth(100)
        canvas_renderer.setHeight(100)
        canvas_renderer.tileOriginX = 50
        canvas_renderer.tileOriginY = 50
        return canvas_renderer

    def test_item_too_small_at_low_zoom(self, canvas_renderer):
        """Item smaller than 2px at current zoom should be skipped."""
        # At 1% zoom, a 100x100 canvas item = 1x1 screen pixels
        canvas_renderer.zoomLevel = 0.01

        from lucent.canvas_items import RectangleItem
        from lucent.geometry import RectGeometry

        item = RectangleItem(
            geometry=RectGeometry(x=0, y=0, width=100, height=100),
            appearances=[],
        )

        # 100 * 0.01 = 1px, which is below MIN_RENDER_SIZE_PX (2)
        assert canvas_renderer._item_too_small_to_render(item) is True

    def test_item_large_enough_at_low_zoom(self, canvas_renderer):
        """Item larger than 2px at current zoom should be rendered."""
        canvas_renderer.zoomLevel = 0.01

        from lucent.canvas_items import RectangleItem
        from lucent.geometry import RectGeometry

        # 300 * 0.01 = 3px, which is above MIN_RENDER_SIZE_PX
        item = RectangleItem(
            geometry=RectGeometry(x=0, y=0, width=300, height=300),
            appearances=[],
        )

        assert canvas_renderer._item_too_small_to_render(item) is False

    def test_item_visible_at_normal_zoom(self, canvas_renderer):
        """Even small items should render at normal zoom levels."""
        canvas_renderer.zoomLevel = 1.0

        from lucent.canvas_items import RectangleItem
        from lucent.geometry import RectGeometry

        # 10 * 1.0 = 10px, well above threshold
        item = RectangleItem(
            geometry=RectGeometry(x=0, y=0, width=10, height=10),
            appearances=[],
        )

        assert canvas_renderer._item_too_small_to_render(item) is False

    def test_one_dimension_large_enough_renders(self, canvas_renderer):
        """Item with one dimension >= 2px should still render (e.g., thin lines)."""
        canvas_renderer.zoomLevel = 0.01

        from lucent.canvas_items import RectangleItem
        from lucent.geometry import RectGeometry

        # 1000 * 0.01 = 10px wide, 10 * 0.01 = 0.1px tall
        # Width is >= 2px, so should render
        item = RectangleItem(
            geometry=RectGeometry(x=0, y=0, width=1000, height=10),
            appearances=[],
        )

        assert canvas_renderer._item_too_small_to_render(item) is False

    def test_paint_skips_tiny_items(self, canvas_renderer, canvas_model):
        """Paint should skip items too small to see at current zoom."""
        canvas_renderer.zoomLevel = 0.01

        paint_calls = []

        from PySide6.QtCore import QRectF

        class TrackedItem:
            def __init__(self, name, bounds):
                self.name = name
                self._bounds = bounds

            def get_bounds(self):
                return self._bounds

            def paint(self, painter, zoom, offset_x=0, offset_y=0):
                paint_calls.append(self.name)

        # Large item that will be visible (500 * 0.01 = 5px)
        large_item = TrackedItem("large", QRectF(0, 0, 500, 500))
        # Tiny item that will be invisible (50 * 0.01 = 0.5px)
        tiny_item = TrackedItem("tiny", QRectF(10, 10, 50, 50))

        # Spatial index returns both items (LOD filtering happens in paint)
        canvas_model.getRenderItemsInBounds = lambda x, y, w, h: [
            large_item,
            tiny_item,
        ]

        image = QImage(QSize(100, 100), QImage.Format_ARGB32)
        image.fill(0)
        painter = QPainter(image)
        canvas_renderer.paint(painter)
        painter.end()

        # Only the large item should have been painted (tiny is LOD-skipped)
        assert paint_calls == ["large"]

    def test_item_without_bounds_still_renders_lod(self, canvas_renderer, canvas_model):
        """Items that fail get_bounds should still render (safety fallback)."""
        canvas_renderer.zoomLevel = 0.01

        class BrokenBoundsItem:
            def get_bounds(self):
                raise RuntimeError("No bounds")

            def paint(self, painter, zoom, offset_x=0, offset_y=0):
                pass

        item = BrokenBoundsItem()

        # Should return False (don't skip) when bounds fail
        assert canvas_renderer._item_too_small_to_render(item) is False
