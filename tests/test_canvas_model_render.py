"""Render-related tests for CanvasModel."""

from lucent.canvas_items import RectangleItem, PathItem
from test_helpers import make_rectangle, make_path


class TestCanvasModelRenderItems:
    """Tests for render item ordering and visibility filtering."""

    def test_render_items_respects_visibility(self, canvas_model):
        canvas_model.addItem(make_rectangle(visible=True))
        canvas_model.addItem(make_rectangle(visible=False))

        render_items = canvas_model.getRenderItems()
        assert len(render_items) == 1

    def test_render_items_order(self, canvas_model):
        canvas_model.addItem(make_path(points=[{"x": 0, "y": 0}, {"x": 10, "y": 0}]))
        canvas_model.addItem(make_rectangle())

        items = canvas_model.getRenderItems()
        assert len(items) == 2
        assert isinstance(items[0], PathItem)
        assert isinstance(items[1], RectangleItem)
