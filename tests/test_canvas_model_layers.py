"""CanvasModel layer and parent/child behaviours."""

from lucent.canvas_items import RectangleItem, LayerItem
from test_helpers import (
    make_rectangle,
    make_ellipse,
    make_layer,
    make_layer_with_children,
)


class TestCanvasModelLayers:
    """Tests for layer functionality."""

    def test_add_layer(self, canvas_model, qtbot):
        layer_data = make_layer(name="Background")

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            canvas_model.addItem(layer_data)

        assert canvas_model.count() == 1
        items = canvas_model.getItems()
        assert isinstance(items[0], LayerItem)
        assert items[0].name == "Background"

    def test_items_with_parent_layer(self, canvas_model):
        layer_and_child = make_layer_with_children(
            [make_rectangle(name="Rect1")], name="Layer1", layer_id="layer-1"
        )
        for item in layer_and_child:
            canvas_model.addItem(item)

        items = canvas_model.getItems()
        assert items[1].parent_id == "layer-1"


class TestCanvasModelEffectivelyLocked:
    """Effective locked semantics with layer ancestry."""

    def test_is_effectively_locked_item_locked(self, canvas_model):
        canvas_model.addItem(make_rectangle(locked=True))
        assert canvas_model.isEffectivelyLocked(0) is True

    def test_is_effectively_locked_parent_locked(self, canvas_model):
        canvas_model.addItem(make_layer(layer_id="layer-1", locked=True))
        canvas_model.addItem(make_rectangle(parent_id="layer-1", locked=False))
        assert canvas_model.isEffectivelyLocked(1) is True

    def test_is_effectively_locked_unlocked(self, canvas_model):
        canvas_model.addItem(make_layer(layer_id="layer-1", locked=False))
        canvas_model.addItem(make_rectangle(parent_id="layer-1", locked=False))
        assert canvas_model.isEffectivelyLocked(1) is False


class TestCanvasModelGetLayerItems:
    """Tests for getLayerItems method."""

    def test_get_layer_items(self, canvas_model):
        layer_with_children = make_layer_with_children(
            [make_rectangle(name="A"), make_rectangle(name="B")],
            name="Layer1",
            layer_id="layer-1",
        )
        for item in layer_with_children:
            canvas_model.addItem(item)
        canvas_model.addItem(make_rectangle(name="C"))

        layer_items = canvas_model.getLayerItems("layer-1")
        assert len(layer_items) == 2
        names = [i.name for i in layer_items]
        assert "A" in names
        assert "B" in names


class TestCanvasModelLayerBounds:
    """Tests for getLayerBounds method."""

    def test_get_layer_bounds(self, canvas_model):
        canvas_model.addItem(make_layer(layer_id="layer-1", name="Layer1"))
        canvas_model.addItem(
            make_rectangle(x=0, y=0, width=50, height=50, parent_id="layer-1")
        )
        canvas_model.addItem(
            make_rectangle(x=100, y=100, width=50, height=50, parent_id="layer-1")
        )

        bounds = canvas_model.getLayerBounds("layer-1")
        assert bounds["x"] == 0
        assert bounds["y"] == 0
        assert bounds["width"] == 150
        assert bounds["height"] == 150


class TestCanvasModelReparent:
    """Tests for reparenting items."""

    def test_reparent_item_to_layer(self, canvas_model):
        canvas_model.addItem(make_layer(name="Layer1", layer_id="layer-1"))
        canvas_model.addItem(make_rectangle(name="Rect"))

        canvas_model.reparentItem(1, "layer-1")

        items = canvas_model.getItems()
        rect = [i for i in items if isinstance(i, RectangleItem)][0]
        assert rect.parent_id == "layer-1"

    def test_reparent_invalid_index(self, canvas_model):
        canvas_model.addItem(make_layer(layer_id="layer-1"))
        canvas_model.reparentItem(999, "layer-1")


class TestCanvasModelSetParent:
    """Tests for setParent method."""

    def test_set_parent_rectangle(self, canvas_model):
        canvas_model.addItem(make_layer(name="Parent Layer"))
        canvas_model.addItem(make_rectangle(x=0, y=0, width=50, height=50))

        layer = canvas_model.getItems()[0]
        canvas_model.setParent(1, layer.id)

        rect = canvas_model.getItems()[1]
        assert rect.parent_id == layer.id

    def test_set_parent_ellipse(self, canvas_model):
        canvas_model.addItem(make_layer(name="Parent Layer"))
        canvas_model.addItem(
            make_ellipse(center_x=50, center_y=50, radius_x=30, radius_y=20)
        )

        layer = canvas_model.getItems()[0]
        canvas_model.setParent(1, layer.id)

        ellipse = canvas_model.getItems()[1]
        assert ellipse.parent_id == layer.id

    def test_set_parent_empty_string_removes_parent(self, canvas_model):
        canvas_model.addItem(make_layer(name="Parent Layer"))
        layer = canvas_model.getItems()[0]

        rect_data = make_rectangle(x=0, y=0, width=50, height=50)
        rect_data["parentId"] = layer.id
        canvas_model.addItem(rect_data)

        canvas_model.setParent(1, "")

        rect = canvas_model.getItems()[1]
        assert rect.parent_id is None

    def test_set_parent_invalid_index(self, canvas_model):
        canvas_model.addItem(make_layer(name="Layer"))
        layer = canvas_model.getItems()[0]
        canvas_model.setParent(-1, layer.id)
        canvas_model.setParent(999, layer.id)

    def test_set_parent_layer_no_op(self, canvas_model):
        canvas_model.addItem(make_layer(name="Layer 1"))
        canvas_model.addItem(make_layer(name="Layer 2"))

        layer1 = canvas_model.getItems()[0]
        canvas_model.setParent(1, layer1.id)

        layer2 = canvas_model.getItems()[1]
        assert not hasattr(layer2, "parent_id") or layer2.parent_id is None
