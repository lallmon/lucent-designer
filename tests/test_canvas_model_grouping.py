"""Grouping, duplication, and hierarchy movement tests for CanvasModel."""

from lucent.canvas_items import RectangleItem
from lucent.commands import DEFAULT_DUPLICATE_OFFSET
from test_helpers import make_rectangle, make_ellipse, make_path, make_text, make_layer


class TestCanvasModelDuplicate:
    """Tests for duplicating single items."""

    def test_duplicate_rectangle(self, canvas_model, qtbot):
        canvas_model.addItem(
            make_rectangle(x=10, y=20, width=50, height=30, name="Original")
        )

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            canvas_model.duplicateItem(0)

        assert canvas_model.count() == 2
        items = canvas_model.getItems()
        assert items[1].geometry.x == 10 + DEFAULT_DUPLICATE_OFFSET
        assert items[1].geometry.y == 20 + DEFAULT_DUPLICATE_OFFSET


class TestCanvasModelDuplicateItems:
    """Tests for duplicating multiple items."""

    def test_duplicate_multiple_items(self, canvas_model):
        canvas_model.addItem(make_rectangle(x=10, y=10, name="A"))
        canvas_model.addItem(make_rectangle(x=20, y=20, name="B"))

        new_indices = canvas_model.duplicateItems([0, 1])

        assert len(new_indices) == 2
        assert canvas_model.count() == 4


class TestCanvasModelGrouping:
    """Tests for grouping and ungrouping items."""

    def test_group_items(self, canvas_model):
        canvas_model.addItem(make_rectangle(name="A"))
        canvas_model.addItem(make_rectangle(name="B"))

        group_idx = canvas_model.groupItems([0, 1])
        assert group_idx >= 0
        assert canvas_model.count() == 3

    def test_ungroup_items(self, canvas_model):
        canvas_model.addItem(make_rectangle(name="A"))
        canvas_model.addItem(make_rectangle(name="B"))

        group_idx = canvas_model.groupItems([0, 1])

        canvas_model.ungroup(group_idx)
        items = canvas_model.getItems()
        shapes = [i for i in items if isinstance(i, RectangleItem)]
        assert len(shapes) == 2

    def test_ungroup_invalid_index(self, canvas_model):
        canvas_model.addItem(make_rectangle())
        canvas_model.ungroup(999)
        assert canvas_model.count() == 1

    def test_ungroup_non_group_item(self, canvas_model):
        canvas_model.addItem(make_rectangle())
        canvas_model.ungroup(0)
        assert canvas_model.count() == 1


class TestCanvasModelMoveGroup:
    """Tests for moving groups."""

    def test_move_group_translates_children(self, canvas_model):
        canvas_model.addItem(make_rectangle(x=0, y=0, width=10, height=10, name="A"))
        canvas_model.addItem(make_rectangle(x=20, y=20, width=10, height=10, name="B"))

        group_idx = canvas_model.groupItems([0, 1])

        canvas_model.moveGroup(group_idx, 100, 50)

        items = canvas_model.getItems()
        rects = [i for i in items if isinstance(i, RectangleItem)]
        assert rects[0].geometry.x == 100
        assert rects[0].geometry.y == 50
        assert rects[1].geometry.x == 120
        assert rects[1].geometry.y == 70

    def test_move_group_invalid_index(self, canvas_model):
        canvas_model.addItem(make_rectangle(x=0, y=0, width=10, height=10))
        canvas_model.moveGroup(999, 100, 50)
        item = canvas_model.getItems()[0]
        assert item.geometry.x == 0

    def test_move_group_non_container(self, canvas_model):
        canvas_model.addItem(make_rectangle(x=0, y=0, width=10, height=10))
        canvas_model.moveGroup(0, 100, 50)
        item = canvas_model.getItems()[0]
        assert item.geometry.x == 0


class TestCanvasModelMoveGroupExtended:
    """Extended tests for moveGroup with different item types."""

    def test_move_group_with_ellipse(self, canvas_model):
        canvas_model.addItem(make_layer(name="Layer", layer_id="layer-1"))
        layer = canvas_model.getItems()[0]

        ellipse_data = make_ellipse(center_x=50, center_y=50, radius_x=30, radius_y=20)
        ellipse_data["parentId"] = layer.id
        canvas_model.addItem(ellipse_data)

        canvas_model.moveGroup(0, 10, 20)

        ellipse = canvas_model.getItems()[1]
        assert ellipse.geometry.center_x == 60
        assert ellipse.geometry.center_y == 70

    def test_move_group_with_text(self, canvas_model):
        canvas_model.addItem(make_layer(name="Layer", layer_id="layer-1"))
        layer = canvas_model.getItems()[0]

        text_data = make_text(x=100, y=200, width=150, text="Hello")
        text_data["parentId"] = layer.id
        canvas_model.addItem(text_data)

        canvas_model.moveGroup(0, 15, 25)

        text = canvas_model.getItems()[1]
        assert text.x == 115
        assert text.y == 225

    def test_move_group_with_path(self, canvas_model):
        canvas_model.addItem(make_layer(name="Layer", layer_id="layer-1"))
        layer = canvas_model.getItems()[0]

        path_data = make_path(points=[{"x": 10, "y": 20}, {"x": 110, "y": 70}])
        path_data["parentId"] = layer.id
        canvas_model.addItem(path_data)

        canvas_model.moveGroup(0, 5, 10)

        path = canvas_model.getItems()[1]
        assert path.geometry.points[0]["x"] == 15
        assert path.geometry.points[0]["y"] == 30
        assert path.geometry.points[1]["x"] == 115
        assert path.geometry.points[1]["y"] == 80
