"""Unit tests for command classes."""

import pytest
from lucent.commands import (
    Command,
    AddItemCommand,
    RemoveItemCommand,
    UpdateItemCommand,
    ClearCommand,
    TransactionCommand,
)
from lucent.canvas_items import RectangleItem, EllipseItem
from lucent.item_schema import ItemSchemaError


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
        item_data = {"type": "rectangle", "x": 10, "y": 20, "width": 100, "height": 50}
        cmd = AddItemCommand(canvas_model, item_data)

        cmd.execute()

        assert canvas_model.count() == 1
        assert isinstance(canvas_model.getItems()[0], RectangleItem)

    def test_execute_adds_ellipse(self, canvas_model):
        """Test execute adds an ellipse to the model."""
        item_data = {
            "type": "ellipse",
            "centerX": 50,
            "centerY": 50,
            "radiusX": 25,
            "radiusY": 25,
        }
        cmd = AddItemCommand(canvas_model, item_data)

        cmd.execute()

        assert canvas_model.count() == 1
        assert isinstance(canvas_model.getItems()[0], EllipseItem)

    def test_undo_removes_added_item(self, canvas_model):
        """Test undo removes the item that was added."""
        item_data = {"type": "rectangle", "x": 10, "y": 20, "width": 100, "height": 50}
        cmd = AddItemCommand(canvas_model, item_data)
        cmd.execute()
        assert canvas_model.count() == 1

        cmd.undo()

        assert canvas_model.count() == 0

    def test_has_description(self, canvas_model):
        """Test command has a meaningful description."""
        cmd = AddItemCommand(
            canvas_model,
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10},
        )
        assert "Add" in cmd.description

    def test_execute_invalid_type_does_nothing(self, canvas_model):
        """Test invalid item type raises validation error."""
        with pytest.raises(ItemSchemaError):
            AddItemCommand(canvas_model, {"type": "triangle", "x": 0, "y": 0})

    def test_undo_before_execute_does_nothing(self, canvas_model):
        """Test undo before execute does nothing safely."""
        cmd = AddItemCommand(
            canvas_model,
            {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10},
        )
        cmd.undo()
        assert canvas_model.count() == 0


class TestRemoveItemCommand:
    """Tests for RemoveItemCommand."""

    def test_execute_removes_item(self, canvas_model):
        """Test execute removes the item at specified index."""
        canvas_model._items.append(RectangleItem(0, 0, 100, 100))
        cmd = RemoveItemCommand(canvas_model, 0)

        cmd.execute()

        assert canvas_model.count() == 0

    def test_undo_restores_item(self, canvas_model):
        """Test undo restores the removed item."""
        canvas_model._items.append(RectangleItem(10, 20, 100, 50))
        cmd = RemoveItemCommand(canvas_model, 0)
        cmd.execute()
        assert canvas_model.count() == 0

        cmd.undo()

        assert canvas_model.count() == 1
        assert canvas_model.getItems()[0].x == 10

    def test_has_description(self, canvas_model):
        """Test command has a meaningful description."""
        canvas_model._items.append(RectangleItem(0, 0, 100, 100))
        cmd = RemoveItemCommand(canvas_model, 0)
        assert "Delete" in cmd.description or "Remove" in cmd.description

    def test_description_after_execute_shows_type(self, canvas_model):
        """Test description shows correct type after execute."""
        canvas_model._items.append(RectangleItem(0, 0, 100, 100))
        cmd = RemoveItemCommand(canvas_model, 0)
        cmd.execute()
        assert "Rectangle" in cmd.description

    def test_execute_invalid_index_does_nothing(self, canvas_model):
        """Test execute with out-of-bounds index does nothing."""
        cmd = RemoveItemCommand(canvas_model, 99)
        cmd.execute()
        assert canvas_model.count() == 0


class TestUpdateItemCommand:
    """Tests for UpdateItemCommand."""

    def test_execute_updates_properties(self, canvas_model):
        """Test execute applies new properties."""
        canvas_model._items.append(RectangleItem(0, 0, 100, 100))
        old_props = {
            "type": "rectangle",
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 100,
            "strokeWidth": 1,
            "strokeColor": "#ffffff",
            "strokeOpacity": 1.0,
            "fillColor": "#ffffff",
            "fillOpacity": 0.0,
        }
        new_props = {
            "type": "rectangle",
            "x": 50,
            "y": 75,
            "width": 100,
            "height": 100,
            "strokeWidth": 1,
            "strokeColor": "#ffffff",
            "strokeOpacity": 1.0,
            "fillColor": "#ffffff",
            "fillOpacity": 0.0,
        }
        cmd = UpdateItemCommand(canvas_model, 0, old_props, new_props)

        cmd.execute()

        assert canvas_model.getItems()[0].x == 50
        assert canvas_model.getItems()[0].y == 75

    def test_undo_restores_old_properties(self, canvas_model):
        """Test undo restores original properties."""
        canvas_model._items.append(RectangleItem(0, 0, 100, 100))
        old_props = {
            "type": "rectangle",
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 100,
            "strokeWidth": 1,
            "strokeColor": "#ffffff",
            "strokeOpacity": 1.0,
            "fillColor": "#ffffff",
            "fillOpacity": 0.0,
        }
        new_props = {
            "type": "rectangle",
            "x": 50,
            "y": 75,
            "width": 100,
            "height": 100,
            "strokeWidth": 1,
            "strokeColor": "#ffffff",
            "strokeOpacity": 1.0,
            "fillColor": "#ffffff",
            "fillOpacity": 0.0,
        }
        cmd = UpdateItemCommand(canvas_model, 0, old_props, new_props)
        cmd.execute()

        cmd.undo()

        assert canvas_model.getItems()[0].x == 0
        assert canvas_model.getItems()[0].y == 0

    def test_has_description(self, canvas_model):
        """Test command has a meaningful description."""
        canvas_model._items.append(RectangleItem(0, 0, 100, 100))
        base = {
            "type": "rectangle",
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 100,
            "strokeWidth": 1,
            "strokeColor": "#ffffff",
            "strokeOpacity": 1.0,
            "fillColor": "#ffffff",
            "fillOpacity": 0.0,
        }
        cmd = UpdateItemCommand(canvas_model, 0, base, base)
        assert cmd.description

    def test_execute_invalid_index_does_nothing(self, canvas_model):
        """Test execute with out-of-bounds index does nothing."""
        old_props = {
            "type": "rectangle",
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 100,
            "strokeWidth": 1,
            "strokeColor": "#ffffff",
            "strokeOpacity": 1.0,
            "fillColor": "#ffffff",
            "fillOpacity": 0.0,
        }
        cmd = UpdateItemCommand(canvas_model, 99, old_props, old_props)
        cmd.execute()
        assert canvas_model.count() == 0


class TestClearCommand:
    """Tests for ClearCommand."""

    def test_execute_clears_all_items(self, canvas_model):
        """Test execute removes all items."""
        canvas_model._items.append(RectangleItem(0, 0, 100, 100))
        canvas_model._items.append(EllipseItem(50, 50, 25, 25))
        cmd = ClearCommand(canvas_model)

        cmd.execute()

        assert canvas_model.count() == 0

    def test_undo_restores_all_items(self, canvas_model):
        """Test undo restores all items."""
        canvas_model._items.append(RectangleItem(10, 20, 100, 50))
        canvas_model._items.append(EllipseItem(50, 50, 25, 25))
        cmd = ClearCommand(canvas_model)
        cmd.execute()
        assert canvas_model.count() == 0

        cmd.undo()

        assert canvas_model.count() == 2
        assert isinstance(canvas_model.getItems()[0], RectangleItem)
        assert isinstance(canvas_model.getItems()[1], EllipseItem)

    def test_has_description(self, canvas_model):
        """Test command has a meaningful description."""
        cmd = ClearCommand(canvas_model)
        assert "Clear" in cmd.description


class TestTransactionCommand:
    """Tests for TransactionCommand."""

    def test_execute_runs_all_child_commands(self, canvas_model):
        """Test execute runs all contained commands."""
        canvas_model._items.append(RectangleItem(0, 0, 100, 100))
        canvas_model._items.append(RectangleItem(50, 50, 100, 100))

        old1 = {
            "type": "rectangle",
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 100,
            "strokeWidth": 1,
            "strokeColor": "#ffffff",
            "strokeOpacity": 1.0,
            "fillColor": "#ffffff",
            "fillOpacity": 0.0,
        }
        new1 = {
            "type": "rectangle",
            "x": 10,
            "y": 10,
            "width": 100,
            "height": 100,
            "strokeWidth": 1,
            "strokeColor": "#ffffff",
            "strokeOpacity": 1.0,
            "fillColor": "#ffffff",
            "fillOpacity": 0.0,
        }
        old2 = {
            "type": "rectangle",
            "x": 50,
            "y": 50,
            "width": 100,
            "height": 100,
            "strokeWidth": 1,
            "strokeColor": "#ffffff",
            "strokeOpacity": 1.0,
            "fillColor": "#ffffff",
            "fillOpacity": 0.0,
        }
        new2 = {
            "type": "rectangle",
            "x": 60,
            "y": 60,
            "width": 100,
            "height": 100,
            "strokeWidth": 1,
            "strokeColor": "#ffffff",
            "strokeOpacity": 1.0,
            "fillColor": "#ffffff",
            "fillOpacity": 0.0,
        }

        cmd1 = UpdateItemCommand(canvas_model, 0, old1, new1)
        cmd2 = UpdateItemCommand(canvas_model, 1, old2, new2)
        transaction = TransactionCommand([cmd1, cmd2])

        transaction.execute()

        assert canvas_model.getItems()[0].x == 10
        assert canvas_model.getItems()[1].x == 60

    def test_undo_reverses_all_child_commands(self, canvas_model):
        """Test undo reverses all contained commands in reverse order."""
        canvas_model._items.append(RectangleItem(0, 0, 100, 100))

        old = {
            "type": "rectangle",
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 100,
            "strokeWidth": 1,
            "strokeColor": "#ffffff",
            "strokeOpacity": 1.0,
            "fillColor": "#ffffff",
            "fillOpacity": 0.0,
        }
        new = {
            "type": "rectangle",
            "x": 50,
            "y": 50,
            "width": 100,
            "height": 100,
            "strokeWidth": 1,
            "strokeColor": "#ffffff",
            "strokeOpacity": 1.0,
            "fillColor": "#ffffff",
            "fillOpacity": 0.0,
        }

        cmd = UpdateItemCommand(canvas_model, 0, old, new)
        transaction = TransactionCommand([cmd])
        transaction.execute()
        assert canvas_model.getItems()[0].x == 50

        transaction.undo()

        assert canvas_model.getItems()[0].x == 0

    def test_empty_transaction(self, canvas_model):
        """Test empty transaction does nothing."""
        transaction = TransactionCommand([])
        transaction.execute()
        transaction.undo()

    def test_has_description(self, canvas_model):
        """Test transaction has a description."""
        transaction = TransactionCommand([], description="Move Objects")
        assert transaction.description == "Move Objects"

    def test_default_description(self, canvas_model):
        """Test transaction has default description."""
        transaction = TransactionCommand([])
        assert transaction.description


class TestMoveItemCommand:
    """Tests for MoveItemCommand."""

    def test_execute_moves_item_forward(self, canvas_model):
        """Test moving item to higher index."""
        canvas_model._items = [
            RectangleItem(0, 0, 10, 10, name="Rect 1"),
            RectangleItem(10, 0, 10, 10, name="Rect 2"),
            RectangleItem(20, 0, 10, 10, name="Rect 3"),
        ]
        from lucent.commands import MoveItemCommand

        cmd = MoveItemCommand(canvas_model, 0, 2)

        cmd.execute()

        assert canvas_model.getItems()[0].name == "Rect 2"
        assert canvas_model.getItems()[1].name == "Rect 3"
        assert canvas_model.getItems()[2].name == "Rect 1"

    def test_execute_moves_item_backward(self, canvas_model):
        """Test moving item to lower index."""
        canvas_model._items = [
            RectangleItem(0, 0, 10, 10, name="Rect 1"),
            RectangleItem(10, 0, 10, 10, name="Rect 2"),
            RectangleItem(20, 0, 10, 10, name="Rect 3"),
        ]
        from lucent.commands import MoveItemCommand

        cmd = MoveItemCommand(canvas_model, 2, 0)

        cmd.execute()

        assert canvas_model.getItems()[0].name == "Rect 3"
        assert canvas_model.getItems()[1].name == "Rect 1"
        assert canvas_model.getItems()[2].name == "Rect 2"

    def test_undo_restores_original_order(self, canvas_model):
        """Test undo restores original item order."""
        canvas_model._items = [
            RectangleItem(0, 0, 10, 10, name="Rect 1"),
            RectangleItem(10, 0, 10, 10, name="Rect 2"),
            RectangleItem(20, 0, 10, 10, name="Rect 3"),
        ]
        from lucent.commands import MoveItemCommand

        cmd = MoveItemCommand(canvas_model, 0, 2)
        cmd.execute()

        cmd.undo()

        assert canvas_model.getItems()[0].name == "Rect 1"
        assert canvas_model.getItems()[1].name == "Rect 2"
        assert canvas_model.getItems()[2].name == "Rect 3"

    def test_has_description(self, canvas_model):
        """Test command has a meaningful description."""
        from lucent.commands import MoveItemCommand

        cmd = MoveItemCommand(canvas_model, 0, 2)
        assert cmd.description
