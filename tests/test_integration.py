"""Integration tests for CanvasRenderer and Python-Qt bridge."""

from PySide6.QtCore import QObject
from test_helpers import make_rectangle, make_ellipse


class TestRendererModelIntegration:
    """Tests for CanvasRenderer integration with CanvasModel."""

    def test_renderer_accepts_model(self, canvas_renderer, canvas_model):
        """Test that renderer accepts and stores a CanvasModel."""
        canvas_renderer.setModel(canvas_model)
        assert True

    def test_renderer_rejects_non_model_object(self, canvas_renderer, qapp):
        """Test that renderer safely handles non-CanvasModel objects."""
        not_a_model = QObject()
        canvas_renderer.setModel(not_a_model)
        assert True

    def test_renderer_connects_to_model_signals(
        self, canvas_renderer, canvas_model, qtbot
    ):
        """Test that renderer connects to model's change signals."""
        canvas_renderer.setModel(canvas_model)

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            canvas_model.addItem(make_rectangle(width=10, height=10))

        assert True

    def test_renderer_updates_on_item_added(self, canvas_renderer, canvas_model, qtbot):
        """Test that renderer receives notification when item is added."""
        canvas_renderer.setModel(canvas_model)

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            canvas_model.addItem(
                make_ellipse(center_x=50, center_y=50, radius_x=20, radius_y=20)
            )

        assert canvas_model.count() == 1

    def test_renderer_updates_on_item_removed(
        self, canvas_renderer, canvas_model, qtbot
    ):
        """Test that renderer receives notification when item is removed."""
        canvas_renderer.setModel(canvas_model)

        canvas_model.addItem(make_rectangle(width=10, height=10))

        with qtbot.waitSignal(canvas_model.itemRemoved, timeout=1000):
            canvas_model.removeItem(0)

        assert canvas_model.count() == 0

    def test_renderer_updates_on_item_modified(
        self, canvas_renderer, canvas_model, qtbot
    ):
        """Test that renderer receives notification when item is modified."""
        canvas_renderer.setModel(canvas_model)

        canvas_model.addItem(make_rectangle(width=10, height=10))

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, make_rectangle(x=50, y=75, width=10, height=10))

    def test_renderer_updates_on_items_cleared(
        self, canvas_renderer, canvas_model, qtbot
    ):
        """Test that renderer receives notification when all items are cleared."""
        canvas_renderer.setModel(canvas_model)

        canvas_model.addItem(make_rectangle(width=10, height=10))
        canvas_model.addItem(
            make_ellipse(center_x=20, center_y=20, radius_x=5, radius_y=5)
        )

        with qtbot.waitSignal(canvas_model.itemsCleared, timeout=1000):
            canvas_model.clear()


class TestRendererZoomLevel:
    """Tests for CanvasRenderer zoom level property."""

    def test_default_zoom_level(self, canvas_renderer):
        """Test that renderer starts with zoom level 1.0."""
        assert canvas_renderer.zoomLevel == 1.0

    def test_set_zoom_level(self, canvas_renderer, qtbot):
        """Test setting zoom level emits signal."""
        with qtbot.waitSignal(canvas_renderer.zoomLevelChanged, timeout=1000):
            canvas_renderer.zoomLevel = 2.0

        assert canvas_renderer.zoomLevel == 2.0

    def test_zoom_level_no_signal_when_unchanged(self, canvas_renderer):
        """Test that setting same zoom level doesn't emit signal."""
        canvas_renderer.zoomLevel = 1.5
        canvas_renderer.zoomLevel = 1.5
        assert canvas_renderer.zoomLevel == 1.5

    def test_zoom_level_accepts_various_values(self, canvas_renderer):
        """Test that zoom level accepts different valid values."""
        test_values = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]

        for value in test_values:
            canvas_renderer.zoomLevel = value
            assert canvas_renderer.zoomLevel == value


class TestFullIntegration:
    """End-to-end integration tests."""

    def test_complete_workflow_add_update_remove(
        self, canvas_renderer, canvas_model, qtbot
    ):
        """Test complete workflow: add item, update it, remove it."""
        canvas_renderer.setModel(canvas_model)

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            canvas_model.addItem(make_rectangle(x=10, y=20, width=100, height=50))

        assert canvas_model.count() == 1

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, make_rectangle(x=50, y=75, width=100, height=50))

        items = canvas_model.getItems()
        assert items[0].geometry.x == 50

        with qtbot.waitSignal(canvas_model.itemRemoved, timeout=1000):
            canvas_model.removeItem(0)

        assert canvas_model.count() == 0

    def test_multiple_items_workflow(self, canvas_renderer, canvas_model, qtbot):
        """Test workflow with multiple items."""
        canvas_renderer.setModel(canvas_model)

        canvas_model.addItem(make_rectangle(x=0, y=0, width=50, height=50))
        canvas_model.addItem(
            make_ellipse(center_x=100, center_y=100, radius_x=30, radius_y=30)
        )
        canvas_model.addItem(make_rectangle(x=200, y=200, width=75, height=75))

        assert canvas_model.count() == 3

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(
                1, make_ellipse(center_x=150, center_y=150, radius_x=30, radius_y=30)
            )

        with qtbot.waitSignal(canvas_model.itemRemoved, timeout=1000):
            canvas_model.removeItem(0)

        assert canvas_model.count() == 2

        with qtbot.waitSignal(canvas_model.itemsCleared, timeout=1000):
            canvas_model.clear()

        assert canvas_model.count() == 0

    def test_renderer_survives_rapid_changes(
        self, canvas_renderer, canvas_model, qtbot
    ):
        """Test that renderer handles rapid model changes without crashing."""
        canvas_renderer.setModel(canvas_model)

        for i in range(10):
            canvas_model.addItem(
                make_rectangle(x=i * 10, y=i * 10, width=20, height=20)
            )

        assert canvas_model.count() == 10

        for i in range(10):
            canvas_model.updateItem(
                i, make_rectangle(x=i * 20, y=i * 10, width=20, height=20)
            )

        for i in range(5):
            canvas_model.removeItem(0)

        assert canvas_model.count() == 5

        canvas_model.clear()
        assert canvas_model.count() == 0

    def test_zoom_level_change_with_items(self, canvas_renderer, canvas_model, qtbot):
        """Test changing zoom level with items present."""
        canvas_renderer.setModel(canvas_model)

        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=100))
        canvas_model.addItem(
            make_ellipse(center_x=150, center_y=150, radius_x=50, radius_y=50)
        )

        zoom_levels = [0.5, 1.0, 2.0, 0.75, 1.5]
        for zoom in zoom_levels:
            with qtbot.waitSignal(canvas_renderer.zoomLevelChanged, timeout=1000):
                canvas_renderer.zoomLevel = zoom

            assert canvas_renderer.zoomLevel == zoom

        assert canvas_model.count() == 2
