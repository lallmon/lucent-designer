"""Command pattern classes for undo/redo functionality."""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Mapping
from PySide6.QtCore import QModelIndex

if TYPE_CHECKING:
    from canvas_model import CanvasModel

from canvas_items import CanvasItem, RectangleItem, EllipseItem, LayerItem
from item_schema import parse_item, parse_item_data, item_to_dict, ItemSchemaError


def _create_item(item_data: Dict[str, Any]) -> CanvasItem:
    """Create a CanvasItem from a dictionary."""
    return parse_item(item_data)


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

    def __init__(self, model: "CanvasModel", item_data: Mapping[str, Any]) -> None:
        self._model = model
        # Validate immediately so construction fails fast for bad payloads
        parsed = parse_item_data(dict(item_data))
        self._item_data = parsed.data
        self._index: Optional[int] = None

    @property
    def description(self) -> str:
        item_type = self._item_data.get("type", "item").capitalize()
        return f"Add {item_type}"

    def execute(self) -> None:
        self._index = len(self._model._items)
        self._model.beginInsertRows(QModelIndex(), self._index, self._index)
        self._model._items.append(_create_item(self._item_data))
        self._model.endInsertRows()
        self._model.itemAdded.emit(self._index)

    def undo(self) -> None:
        if self._index is not None and 0 <= self._index < len(self._model._items):
            self._model.beginRemoveRows(QModelIndex(), self._index, self._index)
            del self._model._items[self._index]
            self._model.endRemoveRows()
            self._model.itemRemoved.emit(self._index)


class RemoveItemCommand(Command):
    """Command to remove an item from the canvas."""

    def __init__(self, model: "CanvasModel", index: int) -> None:
        self._model = model
        self._index = index
        self._item_data: Optional[Dict[str, Any]] = None
        # Track removed children for undo (list of (index, child_item_data))
        self._removed_children: List[tuple] = []

    @property
    def description(self) -> str:
        item_type = "Item"
        if self._item_data:
            item_type = self._item_data.get("type", "item").capitalize()
        return f"Delete {item_type}"

    def execute(self) -> None:
        if 0 <= self._index < len(self._model._items):
            item = self._model._items[self._index]
            self._item_data = self._model._itemToDict(item)
            
            # If removing a layer, also remove its children
            if isinstance(item, LayerItem):
                layer_id = item.id
                self._removed_children = []
                # Collect child indices descending to remove safely
                child_indices = [i for i, child in enumerate(self._model._items)
                                 if isinstance(child, (RectangleItem, EllipseItem)) and child.parent_id == layer_id]
                child_indices.sort(reverse=True)
                for child_index in child_indices:
                    child = self._model._items[child_index]
                    self._removed_children.append((child_index, self._model._itemToDict(child)))
                    self._model.beginRemoveRows(QModelIndex(), child_index, child_index)
                    del self._model._items[child_index]
                    self._model.endRemoveRows()
                    # Do not emit itemRemoved for children; primary removal will emit once for the layer
            
            self._model.beginRemoveRows(QModelIndex(), self._index, self._index)
            del self._model._items[self._index]
            self._model.endRemoveRows()
            self._model.itemRemoved.emit(self._index)

    def undo(self) -> None:
        if self._item_data:
            # Reinsert primary item
            self._model.beginInsertRows(QModelIndex(), self._index, self._index)
            self._model._items.insert(self._index, _create_item(self._item_data))
            self._model.endInsertRows()
            self._model.itemAdded.emit(self._index)

            # Reinsert previously removed children, preserving order
            # Insert children after the layer to keep grouping reasonable
            for child_index, child_data in sorted(self._removed_children, key=lambda x: x[0]):
                insert_at = min(child_index, len(self._model._items))
                self._model.beginInsertRows(QModelIndex(), insert_at, insert_at)
                self._model._items.insert(insert_at, _create_item(child_data))
                self._model.endInsertRows()
                self._model.itemAdded.emit(insert_at)


class UpdateItemCommand(Command):
    """Command to update item properties."""

    def __init__(
        self,
        model: "CanvasModel",
        index: int,
        old_props: Mapping[str, Any],
        new_props: Mapping[str, Any],
    ) -> None:
        self._model = model
        self._index = index
        # Validate both payloads eagerly; they should represent valid items
        self._old_props = parse_item_data(dict(old_props)).data
        self._new_props = parse_item_data(dict(new_props)).data

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
        self._model._items[self._index] = _create_item(props)
        index = self._model.index(self._index, 0)
        self._model.dataChanged.emit(index, index, [])
        self._model.itemModified.emit(self._index, props)


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
        self._model.beginResetModel()
        self._model._items.clear()
        self._model.endResetModel()
        self._model.itemsCleared.emit()

    def undo(self) -> None:
        self._model.beginResetModel()
        for item_data in self._snapshot:
            self._model._items.append(_create_item(item_data))
        self._model.endResetModel()
        for i in range(len(self._model._items)):
            self._model.itemAdded.emit(i)


class MoveItemCommand(Command):
    """Command to move an item from one index to another."""

    def __init__(self, model: "CanvasModel", from_index: int, to_index: int) -> None:
        self._model = model
        self._from_index = from_index
        self._to_index = to_index

    @property
    def description(self) -> str:
        return "Reorder Item"

    def execute(self) -> None:
        items = self._model._items
        # For beginMoveRows, destRow is the index BEFORE which the item will be inserted
        dest_row = self._to_index + 1 if self._to_index > self._from_index else self._to_index
        self._model.beginMoveRows(QModelIndex(), self._from_index, self._from_index,
                                   QModelIndex(), dest_row)
        item = items.pop(self._from_index)
        items.insert(self._to_index, item)
        self._model.endMoveRows()
        self._model.itemsReordered.emit()

    def undo(self) -> None:
        items = self._model._items
        dest_row = self._from_index + 1 if self._from_index > self._to_index else self._from_index
        self._model.beginMoveRows(QModelIndex(), self._to_index, self._to_index,
                                   QModelIndex(), dest_row)
        item = items.pop(self._to_index)
        items.insert(self._from_index, item)
        self._model.endMoveRows()
        self._model.itemsReordered.emit()


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

    def execute(self) -> None:
        for cmd in self._commands:
            cmd.execute()

    def undo(self) -> None:
        for cmd in reversed(self._commands):
            cmd.undo()

