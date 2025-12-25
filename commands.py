"""Command pattern classes for undo/redo functionality."""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from canvas_model import CanvasModel

from canvas_items import RectangleItem, EllipseItem


class Command(ABC):
    """Abstract base class for undoable commands."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description for undo history UI."""
        pass

    @abstractmethod
    def execute(self) -> None:
        """Execute the command."""
        pass

    @abstractmethod
    def undo(self) -> None:
        """Reverse the command."""
        pass


class AddItemCommand(Command):
    """Command to add an item to the canvas."""

    def __init__(self, model: "CanvasModel", item_data: Dict[str, Any]) -> None:
        self._model = model
        self._item_data = item_data
        self._index: Optional[int] = None

    @property
    def description(self) -> str:
        item_type = self._item_data.get("type", "item").capitalize()
        return f"Add {item_type}"

    def execute(self) -> None:
        item_type = self._item_data.get("type", "")
        if item_type == "rectangle":
            item = RectangleItem.from_dict(self._item_data)
        elif item_type == "ellipse":
            item = EllipseItem.from_dict(self._item_data)
        else:
            return

        self._model._items.append(item)
        self._index = len(self._model._items) - 1
        self._model.itemAdded.emit(self._index)

    def undo(self) -> None:
        if self._index is not None and 0 <= self._index < len(self._model._items):
            del self._model._items[self._index]
            self._model.itemRemoved.emit(self._index)


class RemoveItemCommand(Command):
    """Command to remove an item from the canvas."""

    def __init__(self, model: "CanvasModel", index: int) -> None:
        self._model = model
        self._index = index
        self._item_data: Optional[Dict[str, Any]] = None

    @property
    def description(self) -> str:
        item_type = "Item"
        if self._item_data:
            item_type = self._item_data.get("type", "item").capitalize()
        return f"Delete {item_type}"

    def execute(self) -> None:
        if 0 <= self._index < len(self._model._items):
            self._item_data = self._model._itemToDict(self._model._items[self._index])
            del self._model._items[self._index]
            self._model.itemRemoved.emit(self._index)

    def undo(self) -> None:
        if self._item_data:
            item_type = self._item_data.get("type", "")
            if item_type == "rectangle":
                item = RectangleItem.from_dict(self._item_data)
            else:
                item = EllipseItem.from_dict(self._item_data)
            self._model._items.insert(self._index, item)
            self._model.itemAdded.emit(self._index)


class UpdateItemCommand(Command):
    """Command to update item properties."""

    def __init__(
        self,
        model: "CanvasModel",
        index: int,
        old_props: Dict[str, Any],
        new_props: Dict[str, Any],
    ) -> None:
        self._model = model
        self._index = index
        self._old_props = old_props
        self._new_props = new_props

    @property
    def description(self) -> str:
        return "Update Properties"

    def execute(self) -> None:
        self._apply_props(self._new_props)

    def undo(self) -> None:
        self._apply_props(self._old_props)

    def _apply_props(self, props: Dict[str, Any]) -> None:
        if not (0 <= self._index < len(self._model._items)):
            return
        item_type = props.get("type", "")
        if item_type == "rectangle":
            item = RectangleItem.from_dict(props)
        else:
            item = EllipseItem.from_dict(props)
        self._model._items[self._index] = item
        self._model.itemModified.emit(self._index)


class ClearCommand(Command):
    """Command to clear all items from the canvas."""

    def __init__(self, model: "CanvasModel") -> None:
        self._model = model
        self._snapshot: List[Dict[str, Any]] = []

    @property
    def description(self) -> str:
        return "Clear Canvas"

    def execute(self) -> None:
        self._snapshot = [self._model._itemToDict(item) for item in self._model._items]
        self._model._items.clear()
        self._model.itemsCleared.emit()

    def undo(self) -> None:
        for item_data in self._snapshot:
            item_type = item_data.get("type", "")
            if item_type == "rectangle":
                self._model._items.append(RectangleItem.from_dict(item_data))
            else:
                self._model._items.append(EllipseItem.from_dict(item_data))
        for i in range(len(self._model._items)):
            self._model.itemAdded.emit(i)


class TransactionCommand(Command):
    """Command that groups multiple commands into a single undoable unit."""

    def __init__(
        self, commands: Optional[List[Command]] = None, description: str = "Edit"
    ) -> None:
        self._commands = commands or []
        self._description = description

    @property
    def description(self) -> str:
        return self._description

    @property
    def commands(self) -> List[Command]:
        return self._commands

    def add(self, command: Command) -> None:
        self._commands.append(command)

    def execute(self) -> None:
        for cmd in self._commands:
            cmd.execute()

    def undo(self) -> None:
        for cmd in reversed(self._commands):
            cmd.undo()

