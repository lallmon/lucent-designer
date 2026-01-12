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

        class DummyItem:
            def paint(self, painter, zoom):
                calls.append(("paint", zoom))

        canvas_model.getRenderItems = lambda: [DummyItem()]  # type: ignore[attr-defined]
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
