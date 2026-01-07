"""Canvas model for Lucent - manages canvas items with undo/redo support."""

from typing import List, Optional, Dict, Any, Union
from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
    Signal,
    Slot,
    Property,
    QObject,
    QByteArray,
)
from lucent.canvas_items import (
    CanvasItem,
    RectangleItem,
    EllipseItem,
    LayerItem,
    GroupItem,
    PathItem,
    TextItem,
)
from lucent.commands import (
    Command,
    AddItemCommand,
    RemoveItemCommand,
    UpdateItemCommand,
    ClearCommand,
    MoveItemCommand,
    TransactionCommand,
    GroupItemsCommand,
    DuplicateItemCommand,
)
from lucent.history_manager import HistoryManager
from lucent.item_schema import (
    parse_item,
    parse_item_data,
    item_to_dict,
    ItemSchemaError,
    ItemType,
)
from lucent.hierarchy import (
    get_container_by_id,
    get_direct_children_indices,
    get_descendant_indices,
    is_descendant_of,
    is_effectively_visible,
    is_effectively_locked,
)
from lucent.bounding_box import (
    union_bounds,
    get_item_bounds,
    translate_path_to_bounds,
    bbox_to_ellipse_geometry,
)
from lucent.render_query import get_render_items, get_hit_test_items


class CanvasModel(QAbstractListModel):
    """Manages CanvasItem objects as a Qt list model with undo/redo support."""

    # Custom roles for QML data binding
    NameRole = Qt.UserRole + 1  # type: ignore[attr-defined]
    TypeRole = Qt.UserRole + 2  # type: ignore[attr-defined]
    IndexRole = Qt.UserRole + 3  # type: ignore[attr-defined]
    ItemIdRole = Qt.UserRole + 4  # type: ignore[attr-defined]
    ParentIdRole = Qt.UserRole + 5  # type: ignore[attr-defined]
    VisibleRole = Qt.UserRole + 6  # type: ignore[attr-defined]
    EffectiveVisibleRole = Qt.UserRole + 7  # type: ignore[attr-defined]
    LockedRole = Qt.UserRole + 8  # type: ignore[attr-defined]
    EffectiveLockedRole = Qt.UserRole + 9  # type: ignore[attr-defined]

    # Legacy signals (kept for backward compatibility with CanvasRenderer)
    itemAdded = Signal(int)
    itemRemoved = Signal(int)
    itemsCleared = Signal()
    itemModified = Signal(int, "QVariant")  # type: ignore[arg-type]
    itemsReordered = Signal()
    undoStackChanged = Signal()
    redoStackChanged = Signal()
    itemTransformChanged = Signal(int)  # Emitted when item transform is updated

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
    def rowCount(
        self, parent: Union[QModelIndex, QPersistentModelIndex] = QModelIndex()
    ) -> int:
        if parent.isValid():
            return 0
        return len(self._items)

    def data(
        self,
        index: Union[QModelIndex, QPersistentModelIndex],
        role: int = Qt.DisplayRole,  # type: ignore[attr-defined]
    ) -> Any:
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
            elif isinstance(item, PathItem):
                return "path"
            elif isinstance(item, LayerItem):
                return "layer"
            elif isinstance(item, GroupItem):
                return "group"
            elif isinstance(item, TextItem):
                return "text"
            return "unknown"
        elif role == self.IndexRole:
            return index.row()
        elif role == self.ItemIdRole:
            if isinstance(item, (LayerItem, GroupItem)):
                return item.id
            return None
        elif role == self.ParentIdRole:
            if isinstance(
                item, (RectangleItem, EllipseItem, GroupItem, PathItem, TextItem)
            ):
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

    def roleNames(self) -> Dict[int, QByteArray]:
        return {
            self.NameRole: QByteArray(b"name"),
            self.TypeRole: QByteArray(b"itemType"),
            self.IndexRole: QByteArray(b"itemIndex"),
            self.ItemIdRole: QByteArray(b"itemId"),
            self.ParentIdRole: QByteArray(b"parentId"),
            self.VisibleRole: QByteArray(b"modelVisible"),
            self.EffectiveVisibleRole: QByteArray(b"modelEffectiveVisible"),
            self.LockedRole: QByteArray(b"modelLocked"),
            self.EffectiveLockedRole: QByteArray(b"modelEffectiveLocked"),
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

    @staticmethod
    def _is_container(item: CanvasItem) -> bool:
        """Check if an item is a container (Layer or Group)."""
        return isinstance(item, (LayerItem, GroupItem))

    @staticmethod
    def _is_renderable(item: CanvasItem) -> bool:
        """Check if an item is renderable (not a container)."""
        return isinstance(item, (RectangleItem, EllipseItem, PathItem, TextItem))

    def _get_container_by_id(self, container_id: Optional[str]) -> Optional[CanvasItem]:
        return get_container_by_id(self._items, container_id, self._is_container)

    def _is_layer_visible(self, layer_id: str) -> bool:
        container = self._get_container_by_id(layer_id)
        return getattr(container, "visible", True) if container else True

    def _is_layer_locked(self, layer_id: str) -> bool:
        container = self._get_container_by_id(layer_id)
        return getattr(container, "locked", False) if container else False

    def _is_descendant_of(self, candidate_id: Optional[str], ancestor_id: str) -> bool:
        """Check if container with candidate_id is a descendant of ancestor_id."""
        return is_descendant_of(
            self._items, candidate_id, ancestor_id, self._is_container
        )

    def _get_direct_children_indices(self, container_id: str) -> List[int]:
        return get_direct_children_indices(self._items, container_id)

    def _get_descendant_indices(self, container_id: str) -> List[int]:
        """Return indices of all descendants (any depth) of a container."""
        return get_descendant_indices(self._items, container_id, self._is_container)

    @Slot(int, float, float)
    def moveGroup(self, group_index: int, dx: float, dy: float) -> None:
        """Translate all descendant shapes of a group/layer by dx, dy."""
        if not (0 <= group_index < len(self._items)):
            return
        container = self._items[group_index]
        if not isinstance(container, (GroupItem, LayerItem)):
            return
        # Apply deltas to descendant shapes
        for idx in self._get_descendant_indices(container.id):
            item = self._items[idx]
            item_data = self._itemToDict(item)
            if isinstance(item, RectangleItem):
                item_data["geometry"]["x"] = item.geometry.x + dx
                item_data["geometry"]["y"] = item.geometry.y + dy
                self.updateItem(idx, item_data)
            elif isinstance(item, EllipseItem):
                item_data["geometry"]["centerX"] = item.geometry.center_x + dx
                item_data["geometry"]["centerY"] = item.geometry.center_y + dy
                self.updateItem(idx, item_data)
            elif isinstance(item, TextItem):
                item_data["geometry"]["x"] = item.x + dx
                item_data["geometry"]["y"] = item.y + dy
                self.updateItem(idx, item_data)
            elif isinstance(item, PathItem):
                new_points = [
                    {"x": p["x"] + dx, "y": p["y"] + dy} for p in item.geometry.points
                ]
                item_data["geometry"]["points"] = new_points
                self.updateItem(idx, item_data)

    @Slot(int)
    def ungroup(self, group_index: int) -> None:
        """Ungroup a group: move its children to the group's parent and remove it."""
        if not (0 <= group_index < len(self._items)):
            return
        group = self._items[group_index]
        if not isinstance(group, GroupItem):
            return
        parent_id = getattr(group, "parent_id", None) or ""

        # Reparent direct children to the group's parent
        child_indices = []
        for i in range(len(self._items)):
            child = self._items[i]
            if getattr(child, "parent_id", None) == group.id:
                child_indices.append(i)

        # Reparent children (bottom-up to keep indices stable)
        for idx in reversed(child_indices):
            self.reparentItem(idx, parent_id)

        # Remove the group itself
        self.removeItem(group_index)

    @Slot(list, result=int)
    def groupItems(self, indices: list[int]) -> int:
        """Group items in one undoable action; returns group index or -1."""
        command = GroupItemsCommand(self, indices)
        self._execute_command(command)
        return command.result_index if command.result_index is not None else -1

    def _is_effectively_visible(self, index: int) -> bool:
        return is_effectively_visible(self._items, index, self._is_container)

    def _is_effectively_locked(self, index: int) -> bool:
        return is_effectively_locked(self._items, index, self._is_container)

    @Slot(dict)
    def addItem(self, item_data: Dict[str, Any]) -> None:
        item_type = item_data.get("type", "")
        if item_type not in (
            ItemType.RECTANGLE.value,
            ItemType.ELLIPSE.value,
            ItemType.LAYER.value,
            ItemType.GROUP.value,
            ItemType.PATH.value,
            ItemType.TEXT.value,
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

    @Slot(int, result=int)
    def duplicateItem(self, index: int) -> int:
        """Duplicate an item (and its descendants) returning the new index."""
        if not (0 <= index < len(self._items)):
            return -1
        if self._is_effectively_locked(index):
            return -1

        command = DuplicateItemCommand(self, index)
        self._execute_command(command)
        return command.result_index if command.result_index is not None else -1

    @Slot(list, result="QVariant")  # type: ignore[arg-type]
    def duplicateItems(self, indices: list[int]) -> List[int]:
        """Duplicate multiple selected items; returns list of new top-level indices."""
        if not indices:
            return []

        # Normalize and validate indices
        unique_indices = sorted(
            {int(i) for i in indices if 0 <= int(i) < len(self._items)}
        )
        if not unique_indices:
            return []

        # Skip locked or effectively locked items
        unlocked_indices = [
            i for i in unique_indices if not self._is_effectively_locked(i)
        ]
        if not unlocked_indices:
            return []

        # Drop descendants when their ancestor container is selected to avoid
        # double duplication
        selected_containers = {
            getattr(self._items[i], "id", None)
            for i in unlocked_indices
            if isinstance(self._items[i], (LayerItem, GroupItem))
        }
        descendant_skip: set[int] = set()
        for container_id in selected_containers:
            if not container_id:
                continue
            descendant_skip.update(self._get_descendant_indices(container_id))

        filtered_indices = [i for i in unlocked_indices if i not in descendant_skip]
        if not filtered_indices:
            return []

        # Execute duplications in one transaction, from highest index down to
        # keep positions stable
        commands: List[DuplicateItemCommand] = []
        index_to_command: Dict[int, DuplicateItemCommand] = {}
        for idx in sorted(filtered_indices):
            cmd = DuplicateItemCommand(self, idx)
            commands.append(cmd)
            index_to_command[idx] = cmd

        transaction = TransactionCommand(commands, "Duplicate Items")
        self._execute_command(transaction)

        # Consume recorded insertion indices per command; order results by
        # original selection order.
        new_indices: List[int] = []
        for idx in sorted(filtered_indices):
            cmd = index_to_command.get(idx)
            if not cmd:
                continue
            parent_idx = cmd.inserted_parent_index
            if parent_idx is not None:
                new_indices.append(parent_idx)
        return new_indices

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

        # If moving a container, move its descendants together to keep grouping tidy
        if isinstance(item, (LayerItem, GroupItem)):
            descendants = self._get_descendant_indices(item.id)
            if descendants:
                self._moveContainerWithChildren(from_index, to_index, descendants)
                return

        command = MoveItemCommand(self, from_index, to_index)
        self._execute_command(command)

    @Slot(int, str)
    def setParent(self, item_index: int, parent_id: str) -> None:  # type: ignore[override]
        """Set the parent layer for a shape item.

        Args:
            item_index: Index of the shape item to reparent
            parent_id: ID of the layer to set as parent, or empty string to make
                top-level
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
        return self._get_container_index(layer_id, LayerItem)

    def _get_container_index(
        self, container_id: str, container_type: Optional[type] = None
    ) -> int:
        for i, item in enumerate(self._items):
            if container_type and not isinstance(item, container_type):
                continue
            if isinstance(item, (LayerItem, GroupItem)) and item.id == container_id:
                return i
        return -1

    def _findLastChildPosition(self, container_id: str) -> int:
        """Return position immediately after the last descendant of container."""
        container_index = self._get_container_index(container_id)
        if container_index < 0:
            return len(self._items)
        descendants = self._get_descendant_indices(container_id)
        if not descendants:
            return container_index + 1
        return max(descendants) + 1

    def _getLayerChildrenIndices(self, layer_id: str) -> List[int]:
        """Backwards-compatible helper to get direct children indices of a layer."""
        return [
            i
            for i, item in enumerate(self._items)
            if getattr(item, "parent_id", None) == layer_id
        ]

    def _moveContainerWithChildren(
        self, container_from: int, container_to: int, descendant_indices: List[int]
    ) -> None:
        """Move a container and its descendants as one contiguous block."""
        all_indices = sorted([container_from] + descendant_indices, reverse=True)

        extracted_items = []
        for idx in all_indices:
            extracted_items.append(self._items.pop(idx))
        extracted_items.reverse()

        remaining_count = len(self._items)
        if container_to < container_from:
            insert_at = container_to
        else:
            items_removed_before_target = sum(
                1 for idx in all_indices if idx < container_to
            )
            insert_at = min(
                container_to - items_removed_before_target + 1, remaining_count
            )

        for i, item in enumerate(extracted_items):
            self._items.insert(insert_at + i, item)

        self.beginResetModel()
        self.endResetModel()
        self.itemsReordered.emit()

    @Slot(int, str, int)
    @Slot(int, str)
    def reparentItem(
        self, item_index: int, parent_id: str, insert_index: int = -1
    ) -> None:
        """Set parent and move item to be last child of that layer.

        This combines setParent + moveItem into a single undoable operation.
        The item is moved to the requested insert position. For layers, the
        default insert position is directly below the layer (top of its child
        list in the UI).

        Args:
            item_index: Index of the shape item to reparent
            parent_id: ID of the layer to set as parent, or empty string to unparent
            insert_index: Optional target model index to place the item. Defaults
                to directly below the layer for a new parent, or to current
                position when unparenting.
        """
        if not (0 <= item_index < len(self._items)):
            return

        item = self._items[item_index]
        # Shapes and groups can have parents; layers cannot
        if isinstance(item, LayerItem):
            return

        # Convert empty string to None for top-level items
        new_parent_id = parent_id if parent_id else None

        if new_parent_id:
            parent = self._get_container_by_id(new_parent_id)
            if not parent:
                return
            if isinstance(item, GroupItem) and self._is_descendant_of(
                new_parent_id, item.id
            ):
                return

            parent_index = self._get_container_index(new_parent_id)
            if parent_index < 0:
                return

            if (
                insert_index < 0
                and isinstance(item, GroupItem)
                and item_index == parent_index + 1
            ):
                target_index = item_index
            else:
                target_index = insert_index if insert_index >= 0 else parent_index
                target_index = max(0, min(target_index, parent_index))
            if item_index < target_index:
                target_index -= 1
        else:
            target_index = insert_index if insert_index >= 0 else item_index

        # Use a transaction to group both operations for single undo
        # Store old state
        old_props = self._itemToDict(item)

        parent_changed = item.parent_id != new_parent_id
        if parent_changed:
            item.parent_id = new_parent_id
        new_props = self._itemToDict(item)

        # Create commands
        commands: List[Command] = []

        # Add update command for parent change
        if parent_changed:
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

    @Slot(str, result="QVariant")  # type: ignore[arg-type]
    def getLayerItems(self, layer_id: str) -> List[CanvasItem]:
        """Get all items belonging to a layer (for export)."""
        return [
            item for item in self._items if getattr(item, "parent_id", None) == layer_id
        ]

    @Slot(str, result="QVariant")  # type: ignore[arg-type]
    def getLayerBounds(self, layer_id: str) -> Dict[str, float]:
        """Compute combined bounding box of all items in a layer."""
        from PySide6.QtCore import QRectF

        children = self.getLayerItems(layer_id)
        if not children:
            return {"x": 0, "y": 0, "width": 0, "height": 0}

        combined = QRectF()
        for child in children:
            child_bounds = child.get_bounds()
            if not child_bounds.isEmpty():
                if combined.isEmpty():
                    combined = child_bounds
                else:
                    combined = combined.united(child_bounds)

        return {
            "x": combined.x(),
            "y": combined.y(),
            "width": combined.width(),
            "height": combined.height(),
        }

    @Slot(int, result="QVariant")  # type: ignore[arg-type]
    def getItemData(self, index: int) -> Optional[Dict[str, Any]]:
        if 0 <= index < len(self._items):
            return self._itemToDict(self._items[index])
        return None

    @Slot(int, result="QVariant")  # type: ignore[arg-type]
    def getItemTransform(self, index: int) -> Optional[Dict[str, Any]]:
        """Get transform properties for an item.

        Args:
            index: Index of the item.

        Returns:
            Dictionary with translateX, translateY, rotate, scaleX, scaleY
            or None if item doesn't support transforms.
        """
        if not (0 <= index < len(self._items)):
            return None
        item = self._items[index]
        if not hasattr(item, "transform"):
            return None
        return item.transform.to_dict()

    @Slot(int, dict)
    def setItemTransform(self, index: int, transform: Dict[str, Any]) -> None:
        """Set transform properties for an item.

        Args:
            index: Index of the item.
            transform: Dictionary with transform properties.
        """
        if not (0 <= index < len(self._items)):
            return
        item = self._items[index]
        if not hasattr(item, "transform"):
            return

        # Get current item data and update transform
        current_data = self._itemToDict(item)
        current_data["transform"] = transform
        self.updateItem(index, current_data)
        self.itemTransformChanged.emit(index)

    @Slot(result="QVariant")  # type: ignore[arg-type]
    def getItemsForHitTest(self) -> List[Dict[str, Any]]:
        return get_hit_test_items(
            self._items,
            self._is_effectively_visible,
            self._itemToDict,
        )

    @Slot(int, result="QVariant")  # type: ignore[arg-type]
    def getBoundingBox(self, index: int) -> Optional[Dict[str, float]]:
        """Return axis-aligned bounding box for an item (or its descendants)."""
        if not (0 <= index < len(self._items)):
            return None
        item = self._items[index]

        def get_descendant_bounds(container_id: str) -> Optional[Dict[str, float]]:
            """Get union of bounds for all descendants of a container."""
            descendants = self._get_descendant_indices(container_id)
            bounds_list = [self.getBoundingBox(idx) for idx in descendants]
            return union_bounds([b for b in bounds_list if b is not None])

        return get_item_bounds(item, get_descendant_bounds)

    @Slot(int, result="QVariant")  # type: ignore[arg-type]
    def getGeometryBounds(self, index: int) -> Optional[Dict[str, float]]:
        """Return untransformed geometry bounds for an item.

        Unlike getBoundingBox which returns transformed bounds, this returns
        the raw geometry bounds ignoring any transforms. Useful for UI overlays
        that need to apply transforms separately.

        Args:
            index: Index of the item.

        Returns:
            Dictionary with x, y, width, height or None if not applicable.
        """
        if not (0 <= index < len(self._items)):
            return None
        item = self._items[index]

        # Only shape items have geometry
        if not hasattr(item, "geometry"):
            return None

        bounds = item.geometry.get_bounds()
        return {
            "x": bounds.x(),
            "y": bounds.y(),
            "width": bounds.width(),
            "height": bounds.height(),
        }

    @Slot(int, dict, result=bool)
    def setBoundingBox(self, index: int, bbox: Dict[str, float]) -> bool:
        """Set bounding box for an item, translating to native properties.

        For rectangles and text: updates x, y, width, height directly.
        For ellipses: converts to centerX, centerY, radiusX, radiusY.
        For paths: translates all points to match the new position.
        For layers/groups: returns False (non-renderable containers).

        Args:
            index: Index of the item to update.
            bbox: Dictionary with x, y, width, height values.

        Returns:
            True if the bounding box was set successfully, False otherwise.
        """
        if not (0 <= index < len(self._items)):
            return False

        item = self._items[index]
        new_x = float(bbox.get("x", 0))
        new_y = float(bbox.get("y", 0))
        new_width = float(bbox.get("width", 0))
        new_height = float(bbox.get("height", 0))

        # Get current item data as base
        current_data = self._itemToDict(item)

        if isinstance(item, RectangleItem):
            current_data["geometry"]["x"] = new_x
            current_data["geometry"]["y"] = new_y
            current_data["geometry"]["width"] = new_width
            current_data["geometry"]["height"] = new_height
            self.updateItem(index, current_data)
            return True

        if isinstance(item, EllipseItem):
            ellipse_geom = bbox_to_ellipse_geometry(bbox)
            current_data["geometry"]["centerX"] = ellipse_geom["centerX"]
            current_data["geometry"]["centerY"] = ellipse_geom["centerY"]
            current_data["geometry"]["radiusX"] = ellipse_geom["radiusX"]
            current_data["geometry"]["radiusY"] = ellipse_geom["radiusY"]
            self.updateItem(index, current_data)
            return True

        if isinstance(item, PathItem):
            points = item.geometry.points
            if not points:
                return False
            new_points = translate_path_to_bounds(points, new_x, new_y)
            current_data["geometry"]["points"] = new_points
            self.updateItem(index, current_data)
            return True

        if isinstance(item, TextItem):
            current_data["geometry"]["x"] = new_x
            current_data["geometry"]["y"] = new_y
            current_data["geometry"]["width"] = new_width
            current_data["geometry"]["height"] = new_height
            self.updateItem(index, current_data)
            return True

        # Layers and groups are non-renderable containers
        if isinstance(item, (LayerItem, GroupItem)):
            return False

        return False

    def getRenderItems(self) -> List[CanvasItem]:
        """Return items in model order (bottom to top) skipping layers.

        Model order is treated as bottom-to-top z-order: lower indices are
        beneath higher indices. Rendering should therefore iterate this list in
        order so later items naturally paint over earlier ones. Layers are not
        rendered, so they are skipped but the relative order of shapes is
        preserved exactly as in the model.
        """
        return get_render_items(
            self._items,
            self._is_container,
            self._is_renderable,
            self._is_effectively_visible,
        )

    def _itemToDict(self, item: CanvasItem) -> Dict[str, Any]:
        return item_to_dict(item)
