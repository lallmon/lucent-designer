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
    DEFAULT_DUPLICATE_OFFSET,
)
from lucent.canvas_items import RectangleItem, EllipseItem
from lucent.item_schema import ItemSchemaError
from test_helpers import make_rectangle, make_ellipse, make_path


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
        """Test command has a meaningful description."""
        old_data = make_rectangle()
        canvas_model.addItem(old_data)
        new_data = make_rectangle(x=10, y=10)
        cmd = UpdateItemCommand(canvas_model, 0, old_data, new_data)
        assert "Update" in cmd.description


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
