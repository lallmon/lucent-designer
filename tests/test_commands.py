# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Unit tests for command classes."""

import pytest
from lucent.commands import (
    Command,
    AddItemCommand,
    RemoveItemCommand,
    UpdateItemCommand,
    ClearCommand,
    TransactionCommand,
    DuplicateItemCommand,
    MoveItemCommand,
    GroupItemsCommand,
    UngroupItemsCommand,
    DEFAULT_DUPLICATE_OFFSET,
)
from lucent.canvas_items import RectangleItem, EllipseItem, GroupItem
from lucent.item_schema import ItemSchemaError
from test_helpers import (
    make_rectangle,
    make_ellipse,
    make_path,
    make_artboard,
    make_group,
    make_text,
)


class TestCommandBase:
    """Tests for Command base class."""

    def test_command_is_abstract(self):
        """Test that Command cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Command()

    def test_command_requires_execute(self):
        """Test that subclasses must implement execute."""

        class IncompleteCommand(Command):
            def undo(self):
                pass

        with pytest.raises(TypeError):
            IncompleteCommand()

    def test_command_requires_undo(self):
        """Test that subclasses must implement undo."""

        class IncompleteCommand(Command):
            def execute(self):
                pass

        with pytest.raises(TypeError):
            IncompleteCommand()


class TestAddItemCommand:
    """Tests for AddItemCommand."""

    def test_execute_adds_rectangle(self, canvas_model):
        """Test execute adds a rectangle to the model."""
        item_data = make_rectangle(x=10, y=20, width=100, height=50)
        cmd = AddItemCommand(canvas_model, item_data)

        cmd.execute()

        assert canvas_model.count() == 1
        assert isinstance(canvas_model.getItems()[0], RectangleItem)

    def test_execute_adds_ellipse(self, canvas_model):
        """Test execute adds an ellipse to the model."""
        item_data = make_ellipse(center_x=50, center_y=50, radius_x=25, radius_y=25)
        cmd = AddItemCommand(canvas_model, item_data)

        cmd.execute()

        assert canvas_model.count() == 1
        assert isinstance(canvas_model.getItems()[0], EllipseItem)

    def test_undo_removes_added_item(self, canvas_model):
        """Test undo removes the item that was added."""
        item_data = make_rectangle(x=10, y=20, width=100, height=50)
        cmd = AddItemCommand(canvas_model, item_data)
        cmd.execute()
        assert canvas_model.count() == 1

        cmd.undo()

        assert canvas_model.count() == 0

    def test_has_description(self, canvas_model):
        """Test command has a meaningful description."""
        cmd = AddItemCommand(canvas_model, make_rectangle())
        assert "Add" in cmd.description

    def test_execute_invalid_type_does_nothing(self, canvas_model):
        """Test invalid item type raises validation error."""
        with pytest.raises(ItemSchemaError):
            AddItemCommand(canvas_model, {"type": "triangle", "x": 0, "y": 0})

    def test_undo_before_execute_does_nothing(self, canvas_model):
        """Undo before execute should not fail."""
        cmd = AddItemCommand(canvas_model, make_rectangle())
        cmd.undo()  # Should not raise
        assert canvas_model.count() == 0


class TestRemoveItemCommand:
    """Tests for RemoveItemCommand."""

    def test_execute_removes_item(self, canvas_model):
        """Test execute removes the item at index."""
        canvas_model.addItem(make_rectangle(name="ToRemove"))
        cmd = RemoveItemCommand(canvas_model, 0)

        cmd.execute()

        assert canvas_model.count() == 0

    def test_undo_restores_item(self, canvas_model):
        """Test undo restores the removed item."""
        canvas_model.addItem(make_rectangle(name="ToRestore"))
        cmd = RemoveItemCommand(canvas_model, 0)
        cmd.execute()
        assert canvas_model.count() == 0

        cmd.undo()

        assert canvas_model.count() == 1
        assert canvas_model.getItems()[0].name == "ToRestore"

    def test_has_description(self, canvas_model):
        """Test command has a meaningful description."""
        canvas_model.addItem(make_rectangle())
        cmd = RemoveItemCommand(canvas_model, 0)
        assert "Delete" in cmd.description


class TestUpdateItemCommand:
    """Tests for UpdateItemCommand."""

    def test_execute_updates_item(self, canvas_model):
        """Test execute updates item properties."""
        old_data = make_rectangle(x=0, y=0, width=10, height=10, name="Original")
        canvas_model.addItem(old_data)
        new_data = make_rectangle(x=50, y=50, width=20, height=20, name="Updated")
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        cmd.execute()

        item = canvas_model.getItems()[0]
        assert item.geometry.x == 50
        assert item.name == "Updated"

    def test_undo_restores_original(self, canvas_model):
        """Test undo restores original properties."""
        old_data = make_rectangle(x=10, y=10, width=50, height=50, name="Original")
        canvas_model.addItem(old_data)
        new_data = make_rectangle(x=100, y=100, width=200, height=200, name="Changed")
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)
        cmd.execute()

        cmd.undo()

        item = canvas_model.getItems()[0]
        assert item.geometry.x == 10
        assert item.name == "Original"

    def test_has_description(self, canvas_model):
        """Test command has a meaningful description based on what changed."""
        old_data = make_rectangle()
        canvas_model.addItem(old_data)
        new_data = make_rectangle(x=10, y=10)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)
        # Position changed, so description should reflect that
        assert "Move" in cmd.description or "Rectangle" in cmd.description


class TestClearCommand:
    """Tests for ClearCommand."""

    def test_execute_clears_all_items(self, canvas_model):
        """Test execute removes all items."""
        canvas_model.addItem(make_rectangle())
        canvas_model.addItem(make_ellipse())
        cmd = ClearCommand(canvas_model)

        cmd.execute()

        assert canvas_model.count() == 0

    def test_undo_restores_all_items(self, canvas_model):
        """Test undo restores all items."""
        canvas_model.addItem(make_rectangle(name="Rect"))
        canvas_model.addItem(make_ellipse(name="Ellipse"))
        cmd = ClearCommand(canvas_model)
        cmd.execute()

        cmd.undo()

        assert canvas_model.count() == 2
        names = [item.name for item in canvas_model.getItems()]
        assert "Rect" in names
        assert "Ellipse" in names

    def test_has_description(self, canvas_model):
        """Test command has a meaningful description."""
        cmd = ClearCommand(canvas_model)
        assert "Clear" in cmd.description


class TestTransactionCommand:
    """Tests for TransactionCommand."""

    def test_execute_runs_all_commands(self, canvas_model):
        """Test execute runs all sub-commands."""
        cmd1 = AddItemCommand(canvas_model, make_rectangle(name="First"))
        cmd2 = AddItemCommand(canvas_model, make_ellipse(name="Second"))
        transaction = TransactionCommand([cmd1, cmd2], "Add Two Items")

        transaction.execute()

        assert canvas_model.count() == 2

    def test_undo_reverses_all_commands(self, canvas_model):
        """Test undo reverses all sub-commands in reverse order."""
        cmd1 = AddItemCommand(canvas_model, make_rectangle())
        cmd2 = AddItemCommand(canvas_model, make_ellipse())
        transaction = TransactionCommand([cmd1, cmd2], "Add Two Items")
        transaction.execute()

        transaction.undo()

        assert canvas_model.count() == 0


class TestDuplicateItemCommand:
    """Tests for DuplicateItemCommand."""

    def test_execute_duplicates_rectangle(self, canvas_model):
        """Test execute creates a duplicate with offset."""
        canvas_model.addItem(make_rectangle(x=10, y=20, width=50, height=30))
        cmd = DuplicateItemCommand(canvas_model, 0)

        cmd.execute()

        assert canvas_model.count() == 2
        items = canvas_model.getItems()
        assert items[1].geometry.x == 10 + DEFAULT_DUPLICATE_OFFSET
        assert items[1].geometry.y == 20 + DEFAULT_DUPLICATE_OFFSET

    def test_undo_removes_duplicate(self, canvas_model):
        """Test undo removes the duplicate."""
        canvas_model.addItem(make_rectangle())
        cmd = DuplicateItemCommand(canvas_model, 0)
        cmd.execute()
        assert canvas_model.count() == 2

        cmd.undo()

        assert canvas_model.count() == 1

    def test_has_description(self, canvas_model):
        """Test command has a meaningful description."""
        canvas_model.addItem(make_rectangle())
        cmd = DuplicateItemCommand(canvas_model, 0)
        assert "Duplicate" in cmd.description

    def test_duplicate_ellipse(self, canvas_model):
        """Test duplicating an ellipse."""
        canvas_model.addItem(
            make_ellipse(center_x=50, center_y=50, radius_x=25, radius_y=25)
        )
        cmd = DuplicateItemCommand(canvas_model, 0)

        cmd.execute()

        assert canvas_model.count() == 2
        items = canvas_model.getItems()
        assert items[1].geometry.center_x == 50 + DEFAULT_DUPLICATE_OFFSET
        assert items[1].geometry.center_y == 50 + DEFAULT_DUPLICATE_OFFSET

    def test_duplicate_path(self, canvas_model):
        """Test duplicating a path."""
        canvas_model.addItem(
            make_path(
                points=[{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}],
                closed=True,
            )
        )
        cmd = DuplicateItemCommand(canvas_model, 0)

        cmd.execute()

        assert canvas_model.count() == 2
        items = canvas_model.getItems()
        # First point should be offset
        assert items[1].geometry.points[0]["x"] == DEFAULT_DUPLICATE_OFFSET
        assert items[1].geometry.points[0]["y"] == DEFAULT_DUPLICATE_OFFSET

    def test_duplicate_text(self, canvas_model):
        """Test duplicating a text item creates a copy."""
        canvas_model.addItem(make_text(x=10, y=20, text="Hello"))
        cmd = DuplicateItemCommand(canvas_model, 0)

        cmd.execute()

        assert canvas_model.count() == 2
        items = canvas_model.getItems()
        # Text item should have Copy in name
        assert "Copy" in items[1].name or items[1].text == "Hello"

    def test_result_index_property(self, canvas_model):
        """Test result_index property returns the index of duplicated item."""
        canvas_model.addItem(make_rectangle())
        cmd = DuplicateItemCommand(canvas_model, 0)
        cmd.execute()

        assert cmd.result_index == 1

    def test_clone_payloads_property(self, canvas_model):
        """Test clone_payloads returns the cloned data."""
        canvas_model.addItem(make_rectangle(name="Original"))
        cmd = DuplicateItemCommand(canvas_model, 0)

        payloads = cmd.clone_payloads
        assert len(payloads) == 1
        assert "Copy" in payloads[0].get("name", "")

    def test_inserted_indices_property(self, canvas_model):
        """Test inserted_indices returns indices of inserted items."""
        canvas_model.addItem(make_rectangle())
        cmd = DuplicateItemCommand(canvas_model, 0)
        cmd.execute()

        assert cmd.inserted_indices == [1]

    def test_duplicate_invalid_index_does_nothing(self, canvas_model):
        """Test duplicating invalid index does nothing."""
        cmd = DuplicateItemCommand(canvas_model, 999)
        cmd.execute()

        assert canvas_model.count() == 0

    def test_undo_with_no_clones_does_nothing(self, canvas_model):
        """Test undo when no clones were created."""
        cmd = DuplicateItemCommand(canvas_model, 999)
        cmd.undo()  # Should not raise

    def test_duplicate_with_custom_offset(self, canvas_model):
        """Test duplicating with custom offset."""
        canvas_model.addItem(make_rectangle(x=0, y=0))
        cmd = DuplicateItemCommand(canvas_model, 0, offset=(50, 100))

        cmd.execute()

        items = canvas_model.getItems()
        assert items[1].geometry.x == 50
        assert items[1].geometry.y == 100


class TestMoveItemCommand:
    """Tests for MoveItemCommand."""

    def test_execute_moves_item_down(self, canvas_model):
        """Test moving item from index 0 to index 1."""
        canvas_model.addItem(make_rectangle(name="First"))
        canvas_model.addItem(make_rectangle(name="Second"))
        cmd = MoveItemCommand(canvas_model, 0, 1)

        cmd.execute()

        items = canvas_model.getItems()
        assert items[0].name == "Second"
        assert items[1].name == "First"

    def test_execute_moves_item_up(self, canvas_model):
        """Test moving item from index 1 to index 0."""
        canvas_model.addItem(make_rectangle(name="First"))
        canvas_model.addItem(make_rectangle(name="Second"))
        cmd = MoveItemCommand(canvas_model, 1, 0)

        cmd.execute()

        items = canvas_model.getItems()
        assert items[0].name == "Second"
        assert items[1].name == "First"

    def test_undo_restores_original_order(self, canvas_model):
        """Test undo restores original item order."""
        canvas_model.addItem(make_rectangle(name="First"))
        canvas_model.addItem(make_rectangle(name="Second"))
        cmd = MoveItemCommand(canvas_model, 0, 1)
        cmd.execute()

        cmd.undo()

        items = canvas_model.getItems()
        assert items[0].name == "First"
        assert items[1].name == "Second"

    def test_has_description(self, canvas_model):
        """Test command has a meaningful description."""
        canvas_model.addItem(make_rectangle())
        canvas_model.addItem(make_rectangle())
        cmd = MoveItemCommand(canvas_model, 0, 1)

        assert "Reorder" in cmd.description


class TestGroupItemsCommand:
    """Tests for GroupItemsCommand."""

    def test_execute_groups_items(self, canvas_model):
        """Test grouping multiple items."""
        canvas_model.addItem(make_rectangle(name="Rect1"))
        canvas_model.addItem(make_rectangle(name="Rect2"))
        cmd = GroupItemsCommand(canvas_model, [0, 1])

        cmd.execute()

        # Should have 3 items: 2 rects + 1 group
        assert canvas_model.count() == 3
        # Find the group
        groups = [
            item for item in canvas_model.getItems() if isinstance(item, GroupItem)
        ]
        assert len(groups) == 1

    def test_undo_restores_ungrouped_state(self, canvas_model):
        """Test undo restores original ungrouped state."""
        canvas_model.addItem(make_rectangle(name="Rect1"))
        canvas_model.addItem(make_rectangle(name="Rect2"))
        cmd = GroupItemsCommand(canvas_model, [0, 1])
        cmd.execute()

        cmd.undo()

        assert canvas_model.count() == 2
        groups = [
            item for item in canvas_model.getItems() if isinstance(item, GroupItem)
        ]
        assert len(groups) == 0

    def test_has_description(self, canvas_model):
        """Test command has a meaningful description."""
        canvas_model.addItem(make_rectangle())
        canvas_model.addItem(make_rectangle())
        cmd = GroupItemsCommand(canvas_model, [0, 1])

        assert "Group" in cmd.description

    def test_result_index_property(self, canvas_model):
        """Test result_index returns index of created group."""
        canvas_model.addItem(make_rectangle())
        canvas_model.addItem(make_rectangle())
        cmd = GroupItemsCommand(canvas_model, [0, 1])
        cmd.execute()

        assert cmd.result_index is not None

    def test_empty_indices_does_nothing(self, canvas_model):
        """Test grouping empty indices does nothing."""
        canvas_model.addItem(make_rectangle())
        cmd = GroupItemsCommand(canvas_model, [])

        cmd.execute()

        assert canvas_model.count() == 1
        assert cmd.result_index is None

    def test_invalid_indices_does_nothing(self, canvas_model):
        """Test grouping with invalid indices does nothing."""
        canvas_model.addItem(make_rectangle())
        cmd = GroupItemsCommand(canvas_model, [999])

        cmd.execute()

        assert canvas_model.count() == 1


class TestUngroupItemsCommand:
    """Tests for UngroupItemsCommand."""

    def test_execute_ungroups_items(self, canvas_model):
        """Test ungrouping a group."""
        # First create a group
        canvas_model.addItem(make_rectangle(name="Rect1"))
        canvas_model.addItem(make_rectangle(name="Rect2"))
        group_cmd = GroupItemsCommand(canvas_model, [0, 1])
        group_cmd.execute()
        group_index = group_cmd.result_index

        # Now ungroup
        ungroup_cmd = UngroupItemsCommand(canvas_model, group_index)
        ungroup_cmd.execute()

        # Should have 2 items, no groups
        assert canvas_model.count() == 2
        groups = [
            item for item in canvas_model.getItems() if isinstance(item, GroupItem)
        ]
        assert len(groups) == 0

    def test_undo_restores_group(self, canvas_model):
        """Test undo restores the group."""
        canvas_model.addItem(make_rectangle(name="Rect1"))
        canvas_model.addItem(make_rectangle(name="Rect2"))
        group_cmd = GroupItemsCommand(canvas_model, [0, 1])
        group_cmd.execute()
        group_index = group_cmd.result_index

        ungroup_cmd = UngroupItemsCommand(canvas_model, group_index)
        ungroup_cmd.execute()
        ungroup_cmd.undo()

        # Should have 3 items again: 2 rects + 1 group
        assert canvas_model.count() == 3
        groups = [
            item for item in canvas_model.getItems() if isinstance(item, GroupItem)
        ]
        assert len(groups) == 1

    def test_has_description(self, canvas_model):
        """Test command has a meaningful description."""
        canvas_model.addItem(make_group(name="MyGroup", group_id="g1"))
        cmd = UngroupItemsCommand(canvas_model, 0)

        assert "Ungroup" in cmd.description

    def test_ungroup_non_group_does_nothing(self, canvas_model):
        """Test ungrouping a non-group item does nothing."""
        canvas_model.addItem(make_rectangle())
        cmd = UngroupItemsCommand(canvas_model, 0)

        cmd.execute()

        # Item should still be there
        assert canvas_model.count() == 1

    def test_ungroup_invalid_index_does_nothing(self, canvas_model):
        """Test ungrouping invalid index does nothing."""
        cmd = UngroupItemsCommand(canvas_model, 999)
        cmd.execute()  # Should not raise


class TestRemoveItemCommandWithContainers:
    """Tests for RemoveItemCommand with container items."""

    def test_remove_layer_removes_children(self, canvas_model):
        """Test removing a layer also removes its children."""
        layer_data = make_artboard(name="Layer1", artboard_id="layer-1")
        canvas_model.addItem(layer_data)
        canvas_model.addItem(make_rectangle(name="Child1", parent_id="layer-1"))
        canvas_model.addItem(make_rectangle(name="Child2", parent_id="layer-1"))

        cmd = RemoveItemCommand(canvas_model, 0)
        cmd.execute()

        assert canvas_model.count() == 0

    def test_undo_restores_layer_and_children(self, canvas_model):
        """Test undo restores the layer and all children."""
        layer_data = make_artboard(name="Layer1", artboard_id="layer-1")
        canvas_model.addItem(layer_data)
        canvas_model.addItem(make_rectangle(name="Child1", parent_id="layer-1"))
        canvas_model.addItem(make_rectangle(name="Child2", parent_id="layer-1"))

        cmd = RemoveItemCommand(canvas_model, 0)
        cmd.execute()
        cmd.undo()

        assert canvas_model.count() == 3

    def test_remove_group_removes_children(self, canvas_model):
        """Test removing a group also removes its children."""
        canvas_model.addItem(make_group(name="Group1", group_id="group-1"))
        canvas_model.addItem(make_rectangle(name="Child1", parent_id="group-1"))

        cmd = RemoveItemCommand(canvas_model, 0)
        cmd.execute()

        assert canvas_model.count() == 0

    def test_description_before_execute(self, canvas_model):
        """Test description works before execute (no item data yet)."""
        canvas_model.addItem(make_rectangle())
        cmd = RemoveItemCommand(canvas_model, 0)

        # Before execute, item_data is None
        assert "Delete" in cmd.description


class TestUpdateItemCommandDescriptions:
    """Tests for UpdateItemCommand description variations."""

    def test_description_rename(self, canvas_model):
        """Test description for name change."""
        old_data = make_rectangle(name="OldName")
        new_data = make_rectangle(name="NewName")
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Rename" in cmd.description

    def test_description_show(self, canvas_model):
        """Test description for showing item."""
        old_data = make_rectangle(visible=False)
        new_data = make_rectangle(visible=True)
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Show" in cmd.description

    def test_description_hide(self, canvas_model):
        """Test description for hiding item."""
        old_data = make_rectangle(visible=True)
        new_data = make_rectangle(visible=False)
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Hide" in cmd.description

    def test_description_lock(self, canvas_model):
        """Test description for locking item."""
        old_data = make_rectangle(locked=False)
        new_data = make_rectangle(locked=True)
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Lock" in cmd.description

    def test_description_unlock(self, canvas_model):
        """Test description for unlocking item."""
        old_data = make_rectangle(locked=True)
        new_data = make_rectangle(locked=False)
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Unlock" in cmd.description

    def test_description_resize(self, canvas_model):
        """Test description for resizing item."""
        old_data = make_rectangle(width=10, height=10)
        new_data = make_rectangle(width=50, height=50)
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Resize" in cmd.description

    def test_description_move(self, canvas_model):
        """Test description for moving item."""
        old_data = make_rectangle(x=0, y=0)
        new_data = make_rectangle(x=100, y=100)
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Move" in cmd.description

    def test_description_edit_path(self, canvas_model):
        """Test description for editing path points."""
        old_data = make_path(points=[{"x": 0, "y": 0}, {"x": 10, "y": 10}])
        new_data = make_path(points=[{"x": 0, "y": 0}, {"x": 20, "y": 20}])
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Edit Path" in cmd.description

    def test_description_change_stroke_color(self, canvas_model):
        """Test description for changing stroke color."""
        old_data = make_rectangle(stroke_color="#ff0000")
        new_data = make_rectangle(stroke_color="#00ff00")
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Stroke Color" in cmd.description

    def test_description_change_fill_color(self, canvas_model):
        """Test description for changing fill color."""
        old_data = make_rectangle(fill_color="#ff0000")
        new_data = make_rectangle(fill_color="#00ff00")
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Fill Color" in cmd.description

    def test_description_change_stroke_opacity(self, canvas_model):
        """Test description for changing stroke opacity."""
        old_data = make_rectangle(stroke_opacity=1.0)
        new_data = make_rectangle(stroke_opacity=0.5)
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Stroke Opacity" in cmd.description

    def test_description_change_fill_opacity(self, canvas_model):
        """Test description for changing fill opacity."""
        old_data = make_rectangle(fill_opacity=0.0)
        new_data = make_rectangle(fill_opacity=0.5)
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Fill Opacity" in cmd.description

    def test_description_change_stroke_width(self, canvas_model):
        """Test description for changing stroke width."""
        old_data = make_rectangle(stroke_width=1.0)
        new_data = make_rectangle(stroke_width=5.0)
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Stroke Width" in cmd.description

    def test_description_edit_text(self, canvas_model):
        """Test description for editing text content."""
        old_data = make_text(text="Hello")
        new_data = make_text(text="World")
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Edit Text" in cmd.description

    def test_description_change_font(self, canvas_model):
        """Test description for changing font family."""
        old_data = make_text(font_family="Arial")
        new_data = make_text(font_family="Helvetica")
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Change Font" in cmd.description

    def test_description_change_font_size(self, canvas_model):
        """Test description for changing font size."""
        old_data = make_text(font_size=12)
        new_data = make_text(font_size=24)
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Change Font Size" in cmd.description

    def test_description_change_text_color(self, canvas_model):
        """Test description for changing text color."""
        old_data = make_text(text_color="#000000")
        new_data = make_text(text_color="#ffffff")
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Change Text Color" in cmd.description

    def test_description_with_item_name(self, canvas_model):
        """Test description includes item name when present."""
        old_data = make_rectangle(name="MyRect", x=0)
        new_data = make_rectangle(name="MyRect", x=10)
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "MyRect" in cmd.description

    def test_description_fallback_to_edit(self, canvas_model):
        """Test description falls back to Edit when no specific change detected."""
        # Create identical items (edge case)
        old_data = make_rectangle()
        new_data = make_rectangle()
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Edit" in cmd.description

    def test_apply_props_invalid_index(self, canvas_model):
        """Test _apply_props does nothing for invalid index."""
        old_data = make_rectangle()
        new_data = make_rectangle(x=10)
        cmd = UpdateItemCommand(canvas_model, 999, old_data, new_data)

        cmd.execute()  # Should not raise


class TestUpdateItemCommandTransforms:
    """Tests for UpdateItemCommand with transform changes."""

    def test_description_rotate(self, canvas_model):
        """Test description for rotation change."""
        old_data = make_rectangle()
        old_data["transform"] = {
            "rotate": 0,
            "scaleX": 1,
            "scaleY": 1,
            "pivotX": 0,
            "pivotY": 0,
            "translateX": 0,
            "translateY": 0,
        }
        new_data = make_rectangle()
        new_data["transform"] = {
            "rotate": 45,
            "scaleX": 1,
            "scaleY": 1,
            "pivotX": 0,
            "pivotY": 0,
            "translateX": 0,
            "translateY": 0,
        }
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Rotate" in cmd.description

    def test_description_scale(self, canvas_model):
        """Test description for scale change."""
        old_data = make_rectangle()
        old_data["transform"] = {"rotate": 45, "scaleX": 1, "scaleY": 1}
        new_data = make_rectangle()
        new_data["transform"] = {"rotate": 45, "scaleX": 2, "scaleY": 2}
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Scale" in cmd.description

    def test_description_move_origin(self, canvas_model):
        """Test description for origin change."""
        old_data = make_rectangle()
        old_data["transform"] = {"rotate": 45, "scaleX": 1, "scaleY": 1, "pivotX": 0}
        new_data = make_rectangle()
        new_data["transform"] = {"rotate": 45, "scaleX": 1, "scaleY": 1, "pivotX": 50}
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Move Origin" in cmd.description

    def test_description_translate(self, canvas_model):
        """Test description for translation change."""
        old_data = make_rectangle()
        old_data["transform"] = {"rotate": 45, "translateX": 0}
        new_data = make_rectangle()
        new_data["transform"] = {"rotate": 45, "translateX": 10}
        canvas_model.addItem(old_data)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)

        assert "Transform" in cmd.description


class TestTransactionCommandExtended:
    """Extended tests for TransactionCommand."""

    def test_has_description_property(self, canvas_model):
        """Test TransactionCommand has description property."""
        transaction = TransactionCommand([], "My Transaction")

        assert transaction.description == "My Transaction"

    def test_empty_transaction(self, canvas_model):
        """Test empty transaction does nothing."""
        transaction = TransactionCommand([])

        transaction.execute()  # Should not raise
        transaction.undo()  # Should not raise

    def test_default_description(self, canvas_model):
        """Test default description is 'Edit'."""
        transaction = TransactionCommand([])

        assert transaction.description == "Edit"
