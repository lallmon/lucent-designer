"""Command pattern classes for undo/redo functionality."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Mapping
from PySide6.QtCore import QModelIndex

if TYPE_CHECKING:
    from lucent.canvas_model import CanvasModel

from lucent.canvas_items import CanvasItem, GroupItem, LayerItem
from lucent.item_schema import item_to_dict, parse_item, parse_item_data
import uuid


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
        self._original_index = index
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

            # If removing a container, also remove its descendants
            if isinstance(item, (LayerItem, GroupItem)):
                container_id = item.id
                self._removed_children = []
                descendant_indices = self._model._get_descendant_indices(container_id)
                descendant_indices.sort(reverse=True)
                removed_before = 0
                for child_index in descendant_indices:
                    if child_index < self._index:
                        removed_before += 1
                    child = self._model._items[child_index]
                    self._removed_children.append(
                        (child_index, self._model._itemToDict(child))
                    )
                    self._model.beginRemoveRows(QModelIndex(), child_index, child_index)
                    del self._model._items[child_index]
                    self._model.endRemoveRows()
                    # Do not emit itemRemoved for children; primary removal will
                    # emit once for the container
                # Adjust container index after prior removals
                self._index = self._index - removed_before

            # Clamp to valid range after child removals
            if self._index < 0 or self._index >= len(self._model._items):
                return
            self._model.beginRemoveRows(QModelIndex(), self._index, self._index)
            del self._model._items[self._index]
            self._model.endRemoveRows()
            self._model.itemRemoved.emit(self._index)

    def undo(self) -> None:
        if self._item_data:
            # Reinsert primary item
            insert_at = min(self._original_index, len(self._model._items))
            self._model.beginInsertRows(QModelIndex(), insert_at, insert_at)
            self._model._items.insert(insert_at, _create_item(self._item_data))
            self._model.endInsertRows()
            self._model.itemAdded.emit(insert_at)

            # Reinsert previously removed children, preserving order
            # Insert children after the layer to keep grouping reasonable
            for child_index, child_data in sorted(
                self._removed_children, key=lambda x: x[0]
            ):
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
        dest_row = (
            self._to_index + 1 if self._to_index > self._from_index else self._to_index
        )
        self._model.beginMoveRows(
            QModelIndex(), self._from_index, self._from_index, QModelIndex(), dest_row
        )
        item = items.pop(self._from_index)
        items.insert(self._to_index, item)
        self._model.endMoveRows()
        self._model.itemsReordered.emit()

    def undo(self) -> None:
        items = self._model._items
        dest_row = (
            self._from_index + 1
            if self._from_index > self._to_index
            else self._from_index
        )
        self._model.beginMoveRows(
            QModelIndex(), self._to_index, self._to_index, QModelIndex(), dest_row
        )
        item = items.pop(self._to_index)
        items.insert(self._from_index, item)
        self._model.endMoveRows()
        self._model.itemsReordered.emit()


class GroupItemsCommand(Command):
    """Group a set of items into a new group in a single undoable action."""

    def __init__(self, model: "CanvasModel", indices: List[int]) -> None:
        self._model = model
        self._indices = sorted(
            set(int(i) for i in indices if i is not None and int(i) >= 0)
        )
        self._snapshot: List[Dict[str, Any]] = []
        self._group_id = str(uuid.uuid4())
        self._result_index: Optional[int] = None

    @property
    def description(self) -> str:
        return "Group Selection"

    def execute(self) -> None:
        self._result_index = None
        if not self._indices:
            return
        if any(i >= len(self._model._items) for i in self._indices):
            return

        self._snapshot = [item_to_dict(item) for item in self._model._items]

        grouped_items: List[Dict[str, Any]] = []
        for idx in self._indices:
            grouped_items.append(item_to_dict(self._model._items[idx]))

        parent_id = grouped_items[0].get("parentId") or None
        group_data: Dict[str, Any] = {
            "type": "group",
            "id": self._group_id,
            "name": "Group",
            "parentId": parent_id,
            "visible": True,
            "locked": False,
        }

        insert_at = max(self._indices)
        new_items: List[Dict[str, Any]] = []

        def append_group_and_children() -> None:
            for child in grouped_items:
                child_copy = dict(child)
                child_copy["parentId"] = self._group_id
                new_items.append(child_copy)
            new_items.append(group_data)

        appended = False
        current_pos = 0
        for idx, item in enumerate(self._model._items):
            if idx in self._indices:
                continue
            if not appended and current_pos >= insert_at:
                append_group_and_children()
                appended = True
            new_items.append(item_to_dict(item))
            current_pos += 1
        if not appended:
            append_group_and_children()

        self._reset_model_from_dicts(new_items)
        # Locate new group index
        for idx, item in enumerate(self._model._items):
            if (
                isinstance(item, GroupItem)
                and getattr(item, "id", None) == self._group_id
            ):
                self._result_index = idx
                break

    def undo(self) -> None:
        if not self._snapshot:
            return
        self._reset_model_from_dicts(self._snapshot)
        self._result_index = None

    def _reset_model_from_dicts(self, items_data: List[Dict[str, Any]]) -> None:
        self._model.beginResetModel()
        self._model._items = [parse_item(data) for data in items_data]
        self._model.endResetModel()
        self._model.itemsReordered.emit()

    @property
    def result_index(self) -> Optional[int]:
        return self._result_index


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
