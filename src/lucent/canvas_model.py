"""Canvas model for Lucent - manages canvas items with undo/redo support."""

from typing import List, Optional, Dict, Any
from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    Qt,
    Signal,
    Slot,
    Property,
    QObject,
)
from lucent.canvas_items import CanvasItem, RectangleItem, EllipseItem, LayerItem
from lucent.commands import (
    Command,
    AddItemCommand,
    RemoveItemCommand,
    UpdateItemCommand,
    ClearCommand,
    MoveItemCommand,
    TransactionCommand,
)
from lucent.history_manager import HistoryManager
from lucent.item_schema import (
    parse_item,
    parse_item_data,
    item_to_dict,
    ItemSchemaError,
    ItemType,
)


class CanvasModel(QAbstractListModel):
    """Manages CanvasItem objects as a Qt list model with undo/redo support."""

    # Custom roles for QML data binding
    NameRole = Qt.UserRole + 1
    TypeRole = Qt.UserRole + 2
    IndexRole = Qt.UserRole + 3
    ItemIdRole = Qt.UserRole + 4  # Unique ID for layers
    ParentIdRole = Qt.UserRole + 5  # Parent layer ID for shapes
    VisibleRole = Qt.UserRole + 6
    EffectiveVisibleRole = Qt.UserRole + 7
    LockedRole = Qt.UserRole + 8
    EffectiveLockedRole = Qt.UserRole + 9

    # Legacy signals (kept for backward compatibility with CanvasRenderer)
    itemAdded = Signal(int)
    itemRemoved = Signal(int)
    itemsCleared = Signal()
    itemModified = Signal(int, "QVariant")  # index and item data
    itemsReordered = Signal()
    undoStackChanged = Signal()
    redoStackChanged = Signal()

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._items: List[CanvasItem] = []
        self._history = HistoryManager(
            on_undo_stack_changed=self.undoStackChanged.emit,
            on_redo_stack_changed=self.redoStackChanged.emit,
        )
        self._transaction_active: bool = False
        self._transaction_snapshot: Dict[int, Dict[str, Any]] = {}
        self._type_counters: Dict[str, int] = {}

    # QAbstractListModel required methods
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self._items)):
            return None

        item = self._items[index.row()]
        if role == self.NameRole:
            return item.name
        elif role == self.TypeRole:
            if isinstance(item, RectangleItem):
                return "rectangle"
            elif isinstance(item, EllipseItem):
                return "ellipse"
            elif isinstance(item, LayerItem):
                return "layer"
            return "unknown"
        elif role == self.IndexRole:
            return index.row()
        elif role == self.ItemIdRole:
            # Only layers have IDs
            if isinstance(item, LayerItem):
                return item.id
            return None
        elif role == self.ParentIdRole:
            # Only shapes have parent IDs
            if isinstance(item, (RectangleItem, EllipseItem)):
                return item.parent_id
            return None
        elif role == self.VisibleRole:
            return getattr(item, "visible", True)
        elif role == self.EffectiveVisibleRole:
            return self._is_effectively_visible(index.row())
        elif role == self.LockedRole:
            return getattr(item, "locked", False)
        elif role == self.EffectiveLockedRole:
            return self._is_effectively_locked(index.row())
        return None

    def roleNames(self) -> Dict[int, bytes]:
        return {
            self.NameRole: b"name",
            self.TypeRole: b"itemType",
            self.IndexRole: b"itemIndex",
            self.ItemIdRole: b"itemId",
            self.ParentIdRole: b"parentId",
            self.VisibleRole: b"modelVisible",
            self.EffectiveVisibleRole: b"modelEffectiveVisible",
            self.LockedRole: b"modelLocked",
            self.EffectiveLockedRole: b"modelEffectiveLocked",
        }

    def _execute_command(self, command: Command, record: bool = True) -> None:
        if record:
            self._history.execute(command)
        else:
            command.execute()

    @Slot()
    def beginTransaction(self) -> None:
        if self._transaction_active:
            return
        self._transaction_active = True
        self._transaction_snapshot = {
            i: self._itemToDict(item) for i, item in enumerate(self._items)
        }

    @Slot()
    def endTransaction(self) -> None:
        if not self._transaction_active:
            return

        commands: List[Command] = []
        for index, old_data in self._transaction_snapshot.items():
            if index < len(self._items):
                current_data = self._itemToDict(self._items[index])
                if current_data != old_data:
                    commands.append(
                        UpdateItemCommand(self, index, old_data, current_data)
                    )

        self._transaction_snapshot = {}

        if commands:
            transaction = TransactionCommand(commands, "Edit Properties")
            self._history.execute(transaction)

        self._transaction_active = False

    def _generate_name(self, item_type: str) -> str:
        type_name = item_type.capitalize()
        self._type_counters[item_type] = self._type_counters.get(item_type, 0) + 1
        return f"{type_name} {self._type_counters[item_type]}"

    def _is_effectively_visible(self, index: int) -> bool:
        if not (0 <= index < len(self._items)):
            return False
        item = self._items[index]
        visible = getattr(item, "visible", True)
        if not visible:
            return False
        # Shapes respect parent layer visibility
        if isinstance(item, (RectangleItem, EllipseItem)):
            parent_id = item.parent_id
            if parent_id:
                parent_visible = self._is_layer_visible(parent_id)
                return parent_visible and visible
        return visible

    def _is_layer_visible(self, layer_id: str) -> bool:
        for candidate in self._items:
            if isinstance(candidate, LayerItem) and candidate.id == layer_id:
                return getattr(candidate, "visible", True)
        return True

    def _is_effectively_locked(self, index: int) -> bool:
        if not (0 <= index < len(self._items)):
            return False
        item = self._items[index]
        locked = getattr(item, "locked", False)
        if locked:
            return True
        # Shapes respect parent layer locked state
        if isinstance(item, (RectangleItem, EllipseItem)):
            parent_id = item.parent_id
            if parent_id:
                return self._is_layer_locked(parent_id)
        return locked

    def _is_layer_locked(self, layer_id: str) -> bool:
        for candidate in self._items:
            if isinstance(candidate, LayerItem) and candidate.id == layer_id:
                return getattr(candidate, "locked", False)
        return False

    @Slot(dict)
    def addItem(self, item_data: Dict[str, Any]) -> None:
        item_type = item_data.get("type", "")
        if item_type not in (
            ItemType.RECTANGLE.value,
            ItemType.ELLIPSE.value,
            ItemType.LAYER.value,
        ):
            print(f"Warning: Unknown item type '{item_type}'")
            return

        working = dict(item_data)
        if not working.get("name"):
            working["name"] = self._generate_name(item_type)

        try:
            parsed = parse_item_data(working)
        except ItemSchemaError as exc:
            print(f"Warning: Failed to add item: {exc}")
            return

        command = AddItemCommand(self, parsed.data)
        self._execute_command(command)

    @Slot()
    def addLayer(self) -> None:
        """Create a new layer with an auto-generated name."""
        self.addItem({"type": "layer"})

    @Slot(int)
    def removeItem(self, index: int) -> None:
        if not (0 <= index < len(self._items)):
            print(f"Warning: Cannot remove item at invalid index {index}")
            return

        command = RemoveItemCommand(self, index)
        self._execute_command(command)

    @Slot()
    def clear(self) -> None:
        if not self._items:
            self.itemsCleared.emit()
            return

        command = ClearCommand(self)
        self._execute_command(command)
        self._type_counters.clear()

    @Slot(int, int)
    def moveItem(self, from_index: int, to_index: int) -> None:
        if from_index == to_index:
            return
        if not (0 <= from_index < len(self._items)):
            return
        if not (0 <= to_index < len(self._items)):
            return

        item = self._items[from_index]

        # Check if moving a layer - need to move children too
        if isinstance(item, LayerItem):
            children_indices = self._getLayerChildrenIndices(item.id)
            if children_indices:
                self._moveLayerWithChildren(from_index, to_index, children_indices)
                return

        command = MoveItemCommand(self, from_index, to_index)
        self._execute_command(command)

    @Slot(int, str)
    def setParent(self, item_index: int, parent_id: str) -> None:
        """Set the parent layer for a shape item.

        Args:
            item_index: Index of the shape item to reparent
            parent_id: ID of the layer to set as parent, or empty string to make top-level
        """
        if not (0 <= item_index < len(self._items)):
            return

        item = self._items[item_index]
        # Only shapes can have parents
        if not isinstance(item, (RectangleItem, EllipseItem)):
            return

        # Convert empty string to None for top-level items
        new_parent_id = parent_id if parent_id else None

        # Update via updateItem to get proper undo/redo support
        self.updateItem(item_index, {"parentId": new_parent_id})

    @Slot(str, result=int)
    def getLayerIndex(self, layer_id: str) -> int:
        """Get the index of a layer by its ID."""
        for i, item in enumerate(self._items):
            if isinstance(item, LayerItem) and item.id == layer_id:
                return i
        return -1

    def _findLastChildPosition(self, layer_id: str) -> int:
        """Find the position where a new child of the layer should be inserted.

        Returns the index just before the next top-level item after the layer,
        or the end of the list if no such item exists.
        """
        layer_index = self.getLayerIndex(layer_id)
        if layer_index < 0:
            return len(self._items)

        # Scan from after the layer to find the next top-level item
        for i in range(layer_index + 1, len(self._items)):
            item = self._items[i]
            if isinstance(item, LayerItem):
                # Next layer found - insert before it
                return i
            elif isinstance(item, (RectangleItem, EllipseItem)):
                if item.parent_id is None:
                    # Top-level shape found - insert before it
                    return i

        # No top-level item found after layer, insert at end
        return len(self._items)

    def _getLayerChildrenIndices(self, layer_id: str) -> List[int]:
        """Get indices of all children belonging to a layer."""
        children = []
        for i, item in enumerate(self._items):
            if (
                isinstance(item, (RectangleItem, EllipseItem))
                and item.parent_id == layer_id
            ):
                children.append(i)
        return children

    def _moveLayerWithChildren(
        self, layer_from: int, layer_to: int, children_indices: List[int]
    ) -> None:
        """Move a layer along with all its children as a group.

        This maintains the parent-child visual grouping by extracting the layer
        and all its children, then reinserting them at the target position.
        """
        # Collect all indices to move (layer + children), sorted descending for safe removal
        all_indices = sorted([layer_from] + children_indices, reverse=True)

        # Extract items in order (we'll reverse after extraction)
        extracted_items = []
        for idx in all_indices:
            extracted_items.append(self._items.pop(idx))

        # Reverse to get original order (layer first, then children)
        extracted_items.reverse()

        # Calculate insertion point
        # The goal: place the group so it ends up at/near the target position
        # When moving up (to lower index): insert at layer_to
        # When moving down (to higher index): insert AFTER the target position
        remaining_count = len(self._items)  # After extraction

        if layer_to < layer_from:
            # Moving up - insert at the target position
            insert_at = layer_to
        else:
            # Moving down - account for removed items and insert at end of target area
            items_removed_before_target = sum(
                1 for idx in all_indices if idx < layer_to
            )
            # +1 to insert AFTER the target position (not before it)
            insert_at = min(layer_to - items_removed_before_target + 1, remaining_count)

        # Insert all items at the target position
        for i, item in enumerate(extracted_items):
            self._items.insert(insert_at + i, item)

        # Notify model of changes using proper row signals
        self.beginResetModel()
        self.endResetModel()
        self.itemsReordered.emit()

    @Slot(int, str)
    def reparentItem(self, item_index: int, parent_id: str) -> None:
        """Set parent and move item to be last child of that layer.

        This combines setParent + moveItem into a single undoable operation.
        The item is moved to be just before the next top-level item after the layer.

        Args:
            item_index: Index of the shape item to reparent
            parent_id: ID of the layer to set as parent, or empty string to unparent
        """
        if not (0 <= item_index < len(self._items)):
            return

        item = self._items[item_index]
        # Only shapes can have parents
        if not isinstance(item, (RectangleItem, EllipseItem)):
            return

        # Convert empty string to None for top-level items
        new_parent_id = parent_id if parent_id else None

        # If already has this parent and we're not unparenting, skip
        if item.parent_id == new_parent_id:
            return

        # Calculate target position
        if new_parent_id:
            # Moving into a layer - position as last child
            target_index = self._findLastChildPosition(new_parent_id)
            # Adjust if item is before target (it will be removed first)
            if item_index < target_index:
                target_index -= 1
        else:
            # Unparenting - keep at current position (just clear parent)
            target_index = item_index

        # Use a transaction to group both operations for single undo
        # Store old state
        old_props = self._itemToDict(item)
        old_index = item_index

        # Set parent
        item.parent_id = new_parent_id
        new_props = self._itemToDict(item)

        # Create commands
        commands: List[Command] = []

        # Add update command for parent change
        commands.append(UpdateItemCommand(self, item_index, old_props, new_props))

        # Add move command if position changes
        if target_index != item_index:
            commands.append(MoveItemCommand(self, item_index, target_index))

        # Execute as transaction
        if len(commands) == 1:
            self._execute_command(commands[0])
        else:
            transaction = TransactionCommand(commands, "Reparent Item")
            self._execute_command(transaction)

        # Emit signals for UI update
        model_index = self.index(
            target_index if target_index != item_index else item_index, 0
        )
        self.dataChanged.emit(model_index, model_index, [])

    @Slot(int, dict)
    def updateItem(self, index: int, properties: Dict[str, Any]) -> None:
        if not (0 <= index < len(self._items)):
            print(f"Warning: Cannot update item at invalid index {index}")
            return

        item = self._items[index]
        old_props = self._itemToDict(item)

        # Merge incoming properties onto existing canonical dict for validation
        merged_props = dict(old_props)
        merged_props.update(properties)
        merged_props["type"] = old_props.get("type")

        try:
            parsed = parse_item_data(merged_props)
            new_item = parse_item(parsed.data)
        except ItemSchemaError as exc:
            print(f"Warning: Failed to update item: {exc}")
            return

        self._items[index] = new_item
        new_props = parsed.data

        if not self._transaction_active:
            command = UpdateItemCommand(self, index, old_props, new_props)
            self._history.execute(command)

        model_index = self.index(index, 0)
        self.dataChanged.emit(model_index, model_index, [])
        self.itemModified.emit(index, new_props)

    @Slot(int, str)
    def renameItem(self, index: int, name: str) -> None:
        """Rename an item by index, preserving undo/redo semantics."""
        if not (0 <= index < len(self._items)):
            return

        new_name = str(name)
        current_name = getattr(self._items[index], "name", "")
        if new_name == current_name:
            return

        self.updateItem(index, {"name": new_name})

    @Slot(int)
    def toggleVisibility(self, index: int) -> None:
        """Toggle visibility for an item with undo/redo support."""
        if not (0 <= index < len(self._items)):
            return
        item = self._items[index]
        current_visible = getattr(item, "visible", True)
        self.updateItem(index, {"visible": not current_visible})

    @Slot(int)
    def toggleLocked(self, index: int) -> None:
        """Toggle locked state for an item with undo/redo support."""
        if not (0 <= index < len(self._items)):
            return
        item = self._items[index]
        current_locked = getattr(item, "locked", False)
        self.updateItem(index, {"locked": not current_locked})

    @Slot(int, result=bool)
    def isEffectivelyLocked(self, index: int) -> bool:
        """Check if item is effectively locked (own state or parent layer locked)."""
        return self._is_effectively_locked(index)

    @Slot(result=int)
    def count(self) -> int:
        return len(self._items)

    def _canUndo(self) -> bool:
        return self._history.can_undo

    canUndo = Property(bool, _canUndo, notify=undoStackChanged)

    @Slot(result=bool)
    def undo(self) -> bool:
        return self._history.undo()

    def _canRedo(self) -> bool:
        return self._history.can_redo

    canRedo = Property(bool, _canRedo, notify=redoStackChanged)

    @Slot(result=bool)
    def redo(self) -> bool:
        return self._history.redo()

    def getItems(self) -> List[CanvasItem]:
        return self._items

    @Slot(int, result="QVariant")
    def getItemData(self, index: int) -> Optional[Dict[str, Any]]:
        if 0 <= index < len(self._items):
            return self._itemToDict(self._items[index])
        return None

    @Slot(result="QVariantList")
    def getItemsForHitTest(self) -> List[Dict[str, Any]]:
        visible_items: List[Dict[str, Any]] = []
        for idx, item in enumerate(self._items):
            if self._is_effectively_visible(idx):
                visible_items.append(self._itemToDict(item))
        return visible_items

    def getRenderItems(self) -> List[CanvasItem]:
        """Return items in render order (front to back) skipping layers.

        Groups children under their layer, reversing order within each group so
        the latest-added child paints above earlier siblings. Layers retain
        their model order.
        """
        from lucent.canvas_items import LayerItem, RectangleItem, EllipseItem

        groups: List[List[CanvasItem]] = []
        current_group: List[CanvasItem] = []

        def flush_group():
            if current_group:
                # reverse within group so later siblings are on top
                groups.append(list(reversed(current_group)))

        for idx, item in enumerate(self._items):
            if isinstance(item, LayerItem):
                flush_group()
                current_group = []
                continue

            if isinstance(item, (RectangleItem, EllipseItem)):
                if not self._is_effectively_visible(idx):
                    continue
                current_group.append(item)
                continue

        flush_group()

        # Flatten groups in encounter order (top-first)
        ordered: List[CanvasItem] = []
        for group in groups:
            ordered.extend(group)
        return ordered

    def _itemToDict(self, item: CanvasItem) -> Dict[str, Any]:
        return item_to_dict(item)
