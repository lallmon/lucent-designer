"""Core CanvasModel behaviour tests: add/update/remove, roles, state, undo."""

from typing import Callable

import pytest
from lucent.canvas_items import RectangleItem, EllipseItem, PathItem, TextItem
from test_helpers import (
    make_rectangle,
    make_ellipse,
    make_path,
    make_layer,
    make_text,
)


class TestCanvasModelBasics:
    """Tests for basic CanvasModel operations."""

    def test_initial_state_empty(self, canvas_model):
        """A new CanvasModel starts empty."""
        assert canvas_model.count() == 0
        assert canvas_model.getItems() == []

    def test_add_rectangle_item(self, canvas_model, qtbot):
        """Adding a rectangle inserts the item and emits itemAdded."""
        item_data = make_rectangle(
            x=10, y=20, width=100, height=50, stroke_color="#ff0000"
        )

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000) as blocker:
            canvas_model.addItem(item_data)

        assert canvas_model.count() == 1
        assert blocker.args == [0]

        items = canvas_model.getItems()
        assert len(items) == 1
        assert isinstance(items[0], RectangleItem)
        assert items[0].geometry.x == 10
        assert items[0].geometry.y == 20

    def test_add_ellipse_item(self, canvas_model, qtbot):
        """Adding an ellipse inserts the item and emits itemAdded."""
        item_data = make_ellipse(center_x=50, center_y=75, radius_x=30, radius_y=20)

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000) as blocker:
            canvas_model.addItem(item_data)

        assert canvas_model.count() == 1
        assert blocker.args == [0]

        items = canvas_model.getItems()
        assert len(items) == 1
        assert isinstance(items[0], EllipseItem)
        assert items[0].geometry.center_x == 50
        assert items[0].geometry.center_y == 75

    def test_add_multiple_items(self, canvas_model, qtbot):
        """Adding multiple items preserves order."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=10, height=10))
        canvas_model.addItem(
            make_ellipse(center_x=20, center_y=20, radius_x=5, radius_y=5)
        )

        assert canvas_model.count() == 2
        items = canvas_model.getItems()
        assert isinstance(items[0], RectangleItem)
        assert isinstance(items[1], EllipseItem)

    def test_add_path_item(self, canvas_model, qtbot):
        """Adding a path inserts the item."""
        item_data = make_path(
            points=[{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}],
            closed=True,
            stroke_width=1.5,
        )

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            canvas_model.addItem(item_data)

        assert canvas_model.count() == 1
        items = canvas_model.getItems()
        assert isinstance(items[0], PathItem)
        assert items[0].geometry.closed is True

    def test_add_unknown_item_type_ignored(self, canvas_model, qtbot):
        """Unknown item types are ignored."""
        item_data = {"type": "triangle", "x": 0, "y": 0}
        canvas_model.addItem(item_data)
        assert canvas_model.count() == 0

    def test_data_invalid_index_returns_none(self, canvas_model):
        """data() returns None for invalid index."""
        canvas_model.addItem(make_rectangle())
        index = canvas_model.index(999, 0)
        assert canvas_model.data(index, canvas_model.NameRole) is None


class TestCanvasModelRemove:
    """Tests for removing items from CanvasModel."""

    def test_remove_item(self, canvas_model, qtbot):
        """Removing by index emits itemRemoved and updates order."""
        canvas_model.addItem(make_rectangle(name="Rect1"))
        canvas_model.addItem(make_ellipse(name="Ellipse1"))

        with qtbot.waitSignal(canvas_model.itemRemoved, timeout=1000) as blocker:
            canvas_model.removeItem(0)

        assert canvas_model.count() == 1
        assert blocker.args == [0]
        assert canvas_model.getItems()[0].name == "Ellipse1"

    def test_remove_invalid_index_no_op(self, canvas_model):
        """Removing invalid index is a no-op."""
        canvas_model.addItem(make_rectangle())
        canvas_model.removeItem(999)
        assert canvas_model.count() == 1


class TestCanvasModelUpdate:
    """Tests for updating items in CanvasModel."""

    def test_update_item(self, canvas_model, qtbot):
        """Updating properties replaces the item and emits itemModified."""
        canvas_model.addItem(
            make_rectangle(x=0, y=0, width=10, height=10, name="Original")
        )

        new_data = make_rectangle(x=50, y=50, width=20, height=20, name="Updated")

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, new_data)

        item = canvas_model.getItems()[0]
        assert item.geometry.x == 50
        assert item.name == "Updated"


class TestCanvasModelDataRoles:
    """Tests for data roles in CanvasModel."""

    def test_name_role(self, canvas_model):
        canvas_model.addItem(make_rectangle(name="MyRect"))
        index = canvas_model.index(0, 0)
        assert canvas_model.data(index, canvas_model.NameRole) == "MyRect"

    @pytest.mark.parametrize(
        "maker, expected_type",
        [
            (make_rectangle, "rectangle"),
            (make_ellipse, "ellipse"),
            (lambda: make_path(points=[{"x": 0, "y": 0}, {"x": 1, "y": 1}]), "path"),
            (make_layer, "layer"),
            (make_text, "text"),
        ],
    )
    def test_type_role_parametrized(
        self, canvas_model, maker: Callable[..., dict], expected_type: str
    ):
        canvas_model.addItem(maker())
        index = canvas_model.index(0, 0)
        assert canvas_model.data(index, canvas_model.TypeRole) == expected_type

    def test_visible_role(self, canvas_model):
        canvas_model.addItem(make_rectangle(visible=False))
        index = canvas_model.index(0, 0)
        assert canvas_model.data(index, canvas_model.VisibleRole) is False

    def test_locked_role(self, canvas_model):
        canvas_model.addItem(make_rectangle(locked=True))
        index = canvas_model.index(0, 0)
        assert canvas_model.data(index, canvas_model.LockedRole) is True


class TestCanvasModelDataRolesExtended:
    """Tests for additional data roles and types."""

    def test_type_role_group(self, canvas_model):
        canvas_model.addItem(make_rectangle(x=0, y=0, width=50, height=50))
        canvas_model.addItem(make_rectangle(x=60, y=0, width=50, height=50))
        group_idx = canvas_model.groupItems([0, 1])
        index = canvas_model.index(group_idx, 0)
        assert canvas_model.data(index, canvas_model.TypeRole) == "group"

    def test_index_role(self, canvas_model):
        canvas_model.addItem(make_rectangle(x=0, y=0, width=50, height=50))
        canvas_model.addItem(make_rectangle(x=60, y=0, width=50, height=50))
        index0 = canvas_model.index(0, 0)
        index1 = canvas_model.index(1, 0)
        assert canvas_model.data(index0, canvas_model.IndexRole) == 0
        assert canvas_model.data(index1, canvas_model.IndexRole) == 1

    @pytest.mark.parametrize(
        "setup_items, index, role, expectation",
        [
            (
                lambda: [make_layer(name="Test Layer")],
                0,
                "item_id",
                lambda model, idx: isinstance(
                    model.data(model.index(idx, 0), model.ItemIdRole), str
                ),
            ),
            (
                lambda: [
                    make_rectangle(x=0, y=0, width=50, height=50),
                    make_rectangle(x=60, y=0, width=50, height=50),
                ],
                lambda model: model.groupItems([0, 1]),
                "item_id",
                lambda model, idx: isinstance(
                    model.data(model.index(idx, 0), model.ItemIdRole), str
                ),
            ),
            (
                lambda: [make_rectangle(x=0, y=0, width=50, height=50)],
                0,
                "item_id_none",
                lambda model, idx: model.data(model.index(idx, 0), model.ItemIdRole)
                is None,
            ),
            (
                lambda: [
                    make_layer(name="Parent Layer"),
                    {**make_rectangle(x=0, y=0, width=50, height=50), "parentId": None},
                ],
                1,
                "parent_none",
                lambda model, idx: model.data(model.index(idx, 0), model.ParentIdRole)
                is None,
            ),
        ],
    )
    def test_item_and_parent_roles(
        self,
        canvas_model,
        setup_items: Callable[[], list[dict]],
        index,
        role,
        expectation: Callable[[object, int], bool],
    ):
        items = setup_items()
        for item in items:
            canvas_model.addItem(item)

        idx = index(canvas_model) if callable(index) else index
        assert expectation(canvas_model, idx)

    def test_effective_visible_role(self, canvas_model):
        canvas_model.addItem(make_rectangle(x=0, y=0, width=50, height=50))
        index = canvas_model.index(0, 0)
        assert canvas_model.data(index, canvas_model.EffectiveVisibleRole) is True

        canvas_model.toggleVisibility(0)
        assert canvas_model.data(index, canvas_model.EffectiveVisibleRole) is False

    def test_effective_locked_role(self, canvas_model):
        canvas_model.addItem(make_rectangle(x=0, y=0, width=50, height=50))
        index = canvas_model.index(0, 0)
        assert canvas_model.data(index, canvas_model.EffectiveLockedRole) is False

        canvas_model.toggleLocked(0)
        assert canvas_model.data(index, canvas_model.EffectiveLockedRole) is True


class TestCanvasModelClear:
    """Tests for clearing the model."""

    def test_clear_removes_all_items(self, canvas_model, qtbot):
        canvas_model.addItem(make_rectangle())
        canvas_model.addItem(make_ellipse())
        canvas_model.addItem(make_path(points=[{"x": 0, "y": 0}, {"x": 1, "y": 1}]))

        with qtbot.waitSignal(canvas_model.modelReset, timeout=1000):
            canvas_model.clear()

        assert canvas_model.count() == 0


class TestCanvasModelMoveItems:
    """Tests for moving items in the model order."""

    def test_move_item_up(self, canvas_model):
        canvas_model.addItem(make_rectangle(name="A"))
        canvas_model.addItem(make_rectangle(name="B"))
        canvas_model.addItem(make_rectangle(name="C"))

        canvas_model.moveItem(2, 0)

        items = canvas_model.getItems()
        assert items[0].name == "C"
        assert items[1].name == "A"
        assert items[2].name == "B"


class TestCanvasModelText:
    """Tests for text items in the model."""

    def test_add_text_item(self, canvas_model, qtbot):
        item_data = make_text(x=10, y=20, text="Hello World", font_size=24)

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            canvas_model.addItem(item_data)

        assert canvas_model.count() == 1
        items = canvas_model.getItems()
        assert isinstance(items[0], TextItem)
        assert items[0].text == "Hello World"
        assert items[0].font_size == 24


class TestCanvasModelItemData:
    """Tests for getItemData method."""

    def test_get_item_data_rectangle(self, canvas_model):
        canvas_model.addItem(
            make_rectangle(x=10, y=20, width=100, height=50, name="MyRect")
        )

        data = canvas_model.getItemData(0)
        assert data["type"] == "rectangle"
        assert data["name"] == "MyRect"
        assert data["geometry"]["x"] == 10
        assert data["geometry"]["width"] == 100

    def test_get_item_data_invalid_index(self, canvas_model):
        assert canvas_model.getItemData(999) is None


class TestCanvasModelVisibility:
    """Tests for visibility toggling."""

    def test_toggle_visibility(self, canvas_model, qtbot):
        canvas_model.addItem(make_rectangle(visible=True))

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.toggleVisibility(0)

        items = canvas_model.getItems()
        assert items[0].visible is False


class TestCanvasModelLock:
    """Tests for lock toggling."""

    def test_toggle_lock(self, canvas_model, qtbot):
        canvas_model.addItem(make_rectangle(locked=False))

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.toggleLocked(0)

        items = canvas_model.getItems()
        assert items[0].locked is True


class TestCanvasModelRenameItem:
    """Tests for renaming items."""

    def test_rename_item(self, canvas_model, qtbot):
        canvas_model.addItem(make_rectangle(name="Original"))

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.renameItem(0, "Renamed")

        items = canvas_model.getItems()
        assert items[0].name == "Renamed"

    def test_rename_invalid_index(self, canvas_model):
        canvas_model.addItem(make_rectangle(name="Original"))
        canvas_model.renameItem(999, "Renamed")
        items = canvas_model.getItems()
        assert items[0].name == "Original"


class TestCanvasModelUndoRedo:
    """Tests for undo/redo functionality."""

    def test_undo_add_item(self, canvas_model):
        canvas_model.addItem(make_rectangle())
        assert canvas_model.count() == 1

        result = canvas_model.undo()
        assert result is True
        assert canvas_model.count() == 0

    def test_redo_add_item(self, canvas_model):
        canvas_model.addItem(make_rectangle())
        canvas_model.undo()
        assert canvas_model.count() == 0

        result = canvas_model.redo()
        assert result is True
        assert canvas_model.count() == 1

    def test_can_undo_property(self, canvas_model):
        assert canvas_model.canUndo is False
        canvas_model.addItem(make_rectangle())
        assert canvas_model.canUndo is True

    def test_can_redo_property(self, canvas_model):
        canvas_model.addItem(make_rectangle())
        assert canvas_model.canRedo is False
        canvas_model.undo()
        assert canvas_model.canRedo is True


class TestCanvasModelTransaction:
    """Tests for transaction batching."""

    def test_transaction_batches_updates(self, canvas_model, qtbot):
        canvas_model.addItem(make_rectangle(x=0, y=0, name="A"))
        canvas_model.addItem(make_rectangle(x=10, y=10, name="B"))
        assert canvas_model.count() == 2

        canvas_model.beginTransaction()

        item_data_a = canvas_model.getItemData(0)
        item_data_a["geometry"]["x"] = 100
        canvas_model.updateItem(0, item_data_a)

        item_data_b = canvas_model.getItemData(1)
        item_data_b["geometry"]["x"] = 200
        canvas_model.updateItem(1, item_data_b)

        canvas_model.endTransaction()

        items = canvas_model.getItems()
        assert items[0].geometry.x == 100
        assert items[1].geometry.x == 200

        canvas_model.undo()
        items = canvas_model.getItems()
        assert items[0].geometry.x == 0
        assert items[1].geometry.x == 10


class TestCanvasModelRoleNames:
    """Tests for roleNames method."""

    def test_role_names_returns_dict(self, canvas_model):
        role_names = canvas_model.roleNames()
        assert isinstance(role_names, dict)
        assert len(role_names) > 0

    def test_role_names_contains_expected_roles(self, canvas_model):
        role_names = canvas_model.roleNames()
        assert canvas_model.NameRole in role_names
        assert canvas_model.TypeRole in role_names
        assert canvas_model.VisibleRole in role_names
        assert canvas_model.LockedRole in role_names
