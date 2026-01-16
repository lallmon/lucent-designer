# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Canvas model for Lucent - manages canvas items."""

from typing import List, Optional, Dict, Any, Union
from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
    Signal,
    Slot,
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
from lucent.model_geometry import (
    apply_bounding_box,
    compute_bounding_box,
    compute_geometry_bounds,
    shape_to_path_data,
)
from lucent.render_query import get_render_items, get_hit_test_items
from lucent.quadtree import SpatialIndex, Rect


class CanvasModel(QAbstractListModel):
    """Manages CanvasItem objects as a Qt list model."""

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

    # Signals for canvas item changes
    itemAdded = Signal(int)
    itemRemoved = Signal(int)
    itemsCleared = Signal()
    itemModified = Signal(int, "QVariant")  # type: ignore[arg-type]
    itemsReordered = Signal()
    itemTransformChanged = Signal(int)  # Emitted when item transform is updated

    def __init__(
        self, history_manager: HistoryManager, parent: Optional[QObject] = None
    ) -> None:
        super().__init__(parent)
        self._items: List[CanvasItem] = []
        self._history = history_manager
        self._transaction_active: bool = False
        self._transaction_snapshot: Dict[int, Dict[str, Any]] = {}
        self._type_counters: Dict[str, int] = {}

        # Spatial index for fast viewport queries
        self._spatial_index = SpatialIndex()

        # Connect signals to update spatial index
        self.itemAdded.connect(self._on_item_added_spatial)
        self.itemRemoved.connect(self._on_item_removed_spatial)
        self.itemModified.connect(self._on_item_modified_spatial)
        self.itemsCleared.connect(self._on_items_cleared_spatial)
        self.itemsReordered.connect(self._rebuild_spatial_index)

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
            # Use first command's description for the transaction label
            label = commands[0].description if len(commands) == 1 else "Edit Properties"
            transaction = TransactionCommand(commands, label)
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

    def _move_single_item(self, idx: int, dx: float, dy: float) -> Optional[Command]:
        """Move a single item by dx, dy. Returns UpdateItemCommand or None."""
        if not (0 <= idx < len(self._items)):
            return None

        item = self._items[idx]

        # Only shapes with geometry can be moved
        if not hasattr(item, "geometry"):
            return None

        old_data = self._itemToDict(item)
        new_data = dict(old_data)
        new_data["geometry"] = item.geometry.translated(dx, dy).to_dict()

        return UpdateItemCommand(self, idx, old_data, new_data)

    @Slot(list, float, float)
    def moveItems(self, indices: List[int], dx: float, dy: float) -> None:
        """Move multiple items by dx, dy, handling groups and avoiding double-moves.

        This method:
        - Moves all selected items by the given delta
        - When a group/layer is selected, moves all its descendants
        - Avoids moving items twice when both container and child are selected
        - Skips locked or effectively locked items
        - Bundles all moves into a single undoable transaction
        """
        if not indices or (dx == 0 and dy == 0):
            return

        # Normalize indices
        valid_indices = sorted(
            {int(i) for i in indices if 0 <= int(i) < len(self._items)}
        )
        if not valid_indices:
            return

        # Identify selected containers to avoid double-moving their children
        selected_container_ids: set[str] = set()
        for idx in valid_indices:
            item = self._items[idx]
            if isinstance(item, (GroupItem, LayerItem)):
                selected_container_ids.add(item.id)

        # Track which items we've already processed
        already_moved: set[int] = set()
        commands: List[Command] = []

        for idx in valid_indices:
            if idx in already_moved:
                continue
            if self._is_effectively_locked(idx):
                continue

            item = self._items[idx]

            if isinstance(item, (GroupItem, LayerItem)):
                # Move all descendants of this container
                descendant_indices = self._get_descendant_indices(item.id)
                for desc_idx in descendant_indices:
                    if desc_idx in already_moved:
                        continue
                    cmd = self._move_single_item(desc_idx, dx, dy)
                    if cmd:
                        commands.append(cmd)
                    already_moved.add(desc_idx)
            else:
                # Regular shape - skip if parent container is in selection
                parent_id = getattr(item, "parent_id", None)
                if parent_id and parent_id in selected_container_ids:
                    continue

                cmd = self._move_single_item(idx, dx, dy)
                if cmd:
                    commands.append(cmd)
                already_moved.add(idx)

        if not commands:
            return

        # If inside a transaction (e.g., drag operation), just execute without
        # recording - the transaction will capture the full change at end
        if self._transaction_active:
            for cmd in commands:
                cmd.execute()
        elif len(commands) == 1:
            self._execute_command(commands[0])
        else:
            transaction = TransactionCommand(commands, "Move Items")
            self._execute_command(transaction)

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
            if hasattr(item, "geometry"):
                item_data = self._itemToDict(item)
                item_data["geometry"] = item.geometry.translated(dx, dy).to_dict()
                self.updateItem(idx, item_data)

    @Slot(int)
    def ungroup(self, group_index: int) -> None:
        """Ungroup a group: move its children to the group's parent and remove it."""
        from lucent.commands import UngroupItemsCommand

        command = UngroupItemsCommand(self, group_index)
        self._execute_command(command)

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

    @Slot(list, result=int)
    def deleteItems(self, indices: List[int]) -> int:
        """Delete multiple items, skipping locked items and removing container children.

        Items are deleted in reverse index order to maintain valid indices.
        Containers (groups/layers) have their descendants deleted automatically.
        All deletions are bundled into a single undoable transaction.

        Args:
            indices: List of item indices to delete.

        Returns:
            Number of items actually deleted.
        """
        if not indices:
            return 0

        # Normalize and deduplicate indices
        valid_indices = sorted(
            {int(i) for i in indices if 0 <= int(i) < len(self._items)},
            reverse=True,  # Delete from highest index first
        )
        if not valid_indices:
            return 0

        # Expand containers to include their descendants
        indices_to_delete: set[int] = set()
        for idx in valid_indices:
            if self._is_effectively_locked(idx):
                continue

            item = self._items[idx]
            indices_to_delete.add(idx)

            # If it's a container, include all descendants
            if isinstance(item, (GroupItem, LayerItem)):
                descendant_indices = self._get_descendant_indices(item.id)
                for desc_idx in descendant_indices:
                    if not self._is_effectively_locked(desc_idx):
                        indices_to_delete.add(desc_idx)

        if not indices_to_delete:
            return 0

        # Create removal commands in reverse order (highest index first)
        commands: List[Command] = []
        for idx in sorted(indices_to_delete, reverse=True):
            commands.append(RemoveItemCommand(self, idx))

        # Execute as single transaction for undo/redo
        if len(commands) == 1:
            self._execute_command(commands[0])
        else:
            transaction = TransactionCommand(commands, "Delete Items")
            self._execute_command(transaction)

        return len(indices_to_delete)

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
            elif insert_index >= 0:
                # Explicit insert position - use as final position (post-removal)
                # Clamp to valid range within parent's children
                target_index = max(0, min(insert_index, parent_index))
            else:
                # Default: place at parent's position (top of children in display)
                target_index = parent_index
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
        self.itemModified.emit(index, self._itemToDict(new_item))

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

    @property
    def canUndo(self) -> bool:
        """Check if undo is available."""
        return self._history.can_undo

    @property
    def canRedo(self) -> bool:
        """Check if redo is available."""
        return self._history.can_redo

    @Slot(result=bool)
    def undo(self) -> bool:
        """Undo the last command."""
        return self._history.undo()

    @Slot(result=bool)
    def redo(self) -> bool:
        """Redo the last undone command."""
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

    def getItem(self, index: int) -> Optional[CanvasItem]:
        """Get the CanvasItem object at the given index.

        Used by SceneGraphRenderer for incremental updates.
        """
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def getItemIndex(self, item: CanvasItem) -> int:
        """Get the index of a CanvasItem in the model.

        Returns -1 if not found.
        """
        try:
            return self._items.index(item)
        except ValueError:
            return -1

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

    @staticmethod
    def _normalizeRotation(degrees: float) -> float:
        """Normalize rotation to 0-360° range.

        Args:
            degrees: Rotation in degrees (any value).

        Returns:
            Rotation normalized to 0 <= value < 360.
        """
        normalized = degrees % 360
        if normalized < 0:
            normalized += 360
        return normalized

    @Slot(int, dict)
    def setItemTransform(self, index: int, transform: Dict[str, Any]) -> None:
        """Set transform properties for an item.

        Rotation values are normalized to 0-360° range.

        Args:
            index: Index of the item.
            transform: Dictionary with transform properties.
        """
        if not (0 <= index < len(self._items)):
            return
        item = self._items[index]
        if not hasattr(item, "transform"):
            return

        # Normalize rotation to 0-360° range
        if "rotate" in transform:
            transform = dict(transform)  # Copy to avoid mutating input
            transform["rotate"] = self._normalizeRotation(transform["rotate"])

        # Get current item data and update transform
        current_data = self._itemToDict(item)
        current_data["transform"] = transform
        self.updateItem(index, current_data)
        self.itemTransformChanged.emit(index)

    @Slot(int, str, float)
    def updateTransformProperty(self, index: int, prop: str, value: float) -> None:
        """Update a single transform property, preserving others.

        Args:
            index: Index of the item.
            prop: Property name (translateX, translateY, rotate, scaleX, scaleY).
            value: New value for the property.
        """
        current = self.getItemTransform(index) or {}
        new_transform = {
            "translateX": current.get("translateX", 0),
            "translateY": current.get("translateY", 0),
            "rotate": current.get("rotate", 0),
            "scaleX": current.get("scaleX", 1),
            "scaleY": current.get("scaleY", 1),
            "originX": current.get("originX", 0),
            "originY": current.get("originY", 0),
        }
        new_transform[prop] = value
        self.setItemTransform(index, new_transform)

    @Slot(int, result="QVariant")  # type: ignore[arg-type]
    def getDisplayedPosition(self, index: int) -> Optional[Dict[str, float]]:
        """Get displayed X, Y position based on geometry, origin, and translation.

        The displayed position is where the origin point appears after transforms.
        Formula: displayedX = geometry.x + geometry.width * originX + translateX

        Args:
            index: Index of the item.

        Returns:
            Dictionary with x, y or None if not applicable.
        """
        if not (0 <= index < len(self._items)):
            return None

        item = self._items[index]
        if not hasattr(item, "transform"):
            return None

        bounds = compute_geometry_bounds(item)
        if not bounds:
            return None

        current = self.getItemTransform(index) or {}
        origin_x = current.get("originX", 0)
        origin_y = current.get("originY", 0)
        translate_x = current.get("translateX", 0)
        translate_y = current.get("translateY", 0)

        return {
            "x": bounds["x"] + bounds["width"] * origin_x + translate_x,
            "y": bounds["y"] + bounds["height"] * origin_y + translate_y,
        }

    @Slot(int, result="QVariant")  # type: ignore[arg-type]
    def getDisplayedSize(self, index: int) -> Optional[Dict[str, float]]:
        """Get displayed width and height based on geometry × scale.

        Args:
            index: Index of the item.

        Returns:
            Dictionary with width, height or None if not applicable.
        """
        if not (0 <= index < len(self._items)):
            return None

        item = self._items[index]
        if not hasattr(item, "transform"):
            return None

        bounds = compute_geometry_bounds(item)
        if not bounds:
            return None

        current = self.getItemTransform(index) or {}
        scale_x = current.get("scaleX", 1)
        scale_y = current.get("scaleY", 1)

        return {
            "width": bounds["width"] * scale_x,
            "height": bounds["height"] * scale_y,
        }

    @Slot(int, result="QVariant")  # type: ignore[arg-type]
    def getTransformedPathPoints(self, index: int) -> Optional[List[Dict[str, Any]]]:
        """Get path points transformed to screen space.

        Uses the same transform logic as rendering to guarantee alignment.

        Args:
            index: Index of the path item.

        Returns:
            List of points with x, y, handleIn, handleOut in screen space,
            or None if not a path item.
        """
        from PySide6.QtCore import QPointF

        if not (0 <= index < len(self._items)):
            return None

        item = self._items[index]
        if not isinstance(item, PathItem):
            return None

        geometry = item.geometry
        points = geometry.points

        if item.transform.is_identity():
            return [self._point_to_dict(pt) for pt in points]

        bounds = geometry.get_bounds()
        origin_x = bounds.x() + bounds.width() * item.transform.origin_x
        origin_y = bounds.y() + bounds.height() * item.transform.origin_y
        qtransform = item.transform.to_qtransform_centered(origin_x, origin_y)

        transformed = []
        for pt in points:
            tp = qtransform.map(QPointF(pt["x"], pt["y"]))
            new_pt: Dict[str, Any] = {"x": tp.x(), "y": tp.y()}
            if "handleIn" in pt and pt["handleIn"]:
                h = qtransform.map(QPointF(pt["handleIn"]["x"], pt["handleIn"]["y"]))
                new_pt["handleIn"] = {"x": h.x(), "y": h.y()}
            if "handleOut" in pt and pt["handleOut"]:
                h = qtransform.map(QPointF(pt["handleOut"]["x"], pt["handleOut"]["y"]))
                new_pt["handleOut"] = {"x": h.x(), "y": h.y()}
            transformed.append(new_pt)
        return transformed

    @staticmethod
    def _point_to_dict(pt: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a path point to a simple dict."""
        result: Dict[str, Any] = {"x": pt["x"], "y": pt["y"]}
        if "handleIn" in pt and pt["handleIn"]:
            result["handleIn"] = {"x": pt["handleIn"]["x"], "y": pt["handleIn"]["y"]}
        if "handleOut" in pt and pt["handleOut"]:
            result["handleOut"] = {
                "x": pt["handleOut"]["x"],
                "y": pt["handleOut"]["y"],
            }
        return result

    @Slot(int, float, float, result="QVariant")  # type: ignore[arg-type]
    def transformPointToGeometry(
        self, index: int, screen_x: float, screen_y: float
    ) -> Optional[Dict[str, float]]:
        """Transform a screen-space point back to geometry space.

        This is the inverse of getTransformedPathPoints, used when dragging
        handles to convert screen positions to geometry coordinates.

        Args:
            index: Index of the path item.
            screen_x: X coordinate in screen space.
            screen_y: Y coordinate in screen space.

        Returns:
            Dictionary with x, y in geometry space, or None if failed.
        """
        from PySide6.QtCore import QPointF

        if not (0 <= index < len(self._items)):
            return None

        item = self._items[index]
        if not hasattr(item, "transform") or not hasattr(item, "geometry"):
            return None

        if item.transform.is_identity():
            return {"x": screen_x, "y": screen_y}

        bounds = item.geometry.get_bounds()
        origin_x = bounds.x() + bounds.width() * item.transform.origin_x
        origin_y = bounds.y() + bounds.height() * item.transform.origin_y
        qtransform = item.transform.to_qtransform_centered(origin_x, origin_y)

        inverted, ok = qtransform.inverted()
        if not ok:
            return {"x": screen_x, "y": screen_y}

        geom_pt = inverted.map(QPointF(screen_x, screen_y))
        return {"x": geom_pt.x(), "y": geom_pt.y()}

    @Slot(int, result=bool)
    def hasNonIdentityTransform(self, index: int) -> bool:
        """Check if an item has a non-identity transform.

        Returns True if rotation, scale, or translation differs from identity.

        Args:
            index: Index of the item.

        Returns:
            True if transform differs from identity, False otherwise.
        """
        if not (0 <= index < len(self._items)):
            return False

        item = self._items[index]
        if not hasattr(item, "transform"):
            return False

        current = self.getItemTransform(index) or {}

        return (
            current.get("rotate", 0) != 0
            or current.get("scaleX", 1) != 1
            or current.get("scaleY", 1) != 1
            or current.get("translateX", 0) != 0
            or current.get("translateY", 0) != 0
        )

    @Slot(int, str, float)
    def setItemPosition(self, index: int, axis: str, value: float) -> None:
        """Set X or Y position, adjusting translation to place origin at target.

        Args:
            index: Index of the item.
            axis: "x" or "y".
            value: New position value in canvas coordinates.
        """
        if not (0 <= index < len(self._items)):
            return

        item = self._items[index]
        if not hasattr(item, "transform"):
            return

        bounds = compute_geometry_bounds(item)
        if not bounds:
            return

        current = self.getItemTransform(index) or {}
        new_transform = {
            "translateX": current.get("translateX", 0),
            "translateY": current.get("translateY", 0),
            "rotate": current.get("rotate", 0),
            "scaleX": current.get("scaleX", 1),
            "scaleY": current.get("scaleY", 1),
            "originX": current.get("originX", 0),
            "originY": current.get("originY", 0),
        }

        # translateX = value - geometry.x - geometry.width * originX
        if axis == "x":
            new_transform["translateX"] = (
                value - bounds["x"] - bounds["width"] * new_transform["originX"]
            )
        else:
            new_transform["translateY"] = (
                value - bounds["y"] - bounds["height"] * new_transform["originY"]
            )

        self.setItemTransform(index, new_transform)

    @Slot(int, str, float, bool)
    def setDisplayedSize(
        self, index: int, dimension: str, value: float, proportional: bool
    ) -> None:
        """Set displayed width or height by adjusting scale.

        Args:
            index: Index of the item.
            dimension: "width" or "height".
            value: Target displayed size in pixels.
            proportional: If True, scale both axes proportionally.
        """
        if not (0 <= index < len(self._items)):
            return

        item = self._items[index]
        if not hasattr(item, "transform"):
            return

        bounds = compute_geometry_bounds(item)
        if not bounds:
            return

        # Prevent division by zero
        if bounds["width"] <= 0 or bounds["height"] <= 0:
            return

        # Minimum displayed size is 1px
        value = max(1.0, value)

        current = self.getItemTransform(index) or {}
        current_scale_x = current.get("scaleX", 1)
        current_scale_y = current.get("scaleY", 1)

        if dimension == "width":
            new_scale_x = value / bounds["width"]
            if proportional:
                ratio = new_scale_x / current_scale_x
                new_scale_y = current_scale_y * ratio
                self.beginTransaction()
                self.updateTransformProperty(index, "scaleX", new_scale_x)
                self.updateTransformProperty(index, "scaleY", new_scale_y)
                self.endTransaction()
            else:
                self.updateTransformProperty(index, "scaleX", new_scale_x)
        else:
            new_scale_y = value / bounds["height"]
            if proportional:
                ratio = new_scale_y / current_scale_y
                new_scale_x = current_scale_x * ratio
                self.beginTransaction()
                self.updateTransformProperty(index, "scaleX", new_scale_x)
                self.updateTransformProperty(index, "scaleY", new_scale_y)
                self.endTransaction()
            else:
                self.updateTransformProperty(index, "scaleY", new_scale_y)

    @Slot(int, float, float)
    def setItemOrigin(self, index: int, new_ox: float, new_oy: float) -> None:
        """Change origin point while maintaining visual position.

        Adjusts translation to compensate for the origin change so the item
        appears in the same position on canvas.

        Args:
            index: Index of the item.
            new_ox: New origin X (0=left, 0.5=center, 1=right).
            new_oy: New origin Y (0=top, 0.5=center, 1=bottom).
        """
        import math

        if not (0 <= index < len(self._items)):
            return

        item = self._items[index]
        if not hasattr(item, "transform"):
            return

        bounds = compute_geometry_bounds(item)
        if not bounds:
            return

        current = self.getItemTransform(index) or {}
        old_ox = current.get("originX", 0)
        old_oy = current.get("originY", 0)
        rotation = current.get("rotate", 0)
        scale_x = current.get("scaleX", 1)
        scale_y = current.get("scaleY", 1)
        old_tx = current.get("translateX", 0)
        old_ty = current.get("translateY", 0)

        # Adjust translation to keep shape visually in place when origin changes
        # Formula: adjustment = delta - R(S(delta))
        dx = (old_ox - new_ox) * bounds["width"]
        dy = (old_oy - new_oy) * bounds["height"]

        scaled_dx = dx * scale_x
        scaled_dy = dy * scale_y

        radians = rotation * math.pi / 180
        cos_r = math.cos(radians)
        sin_r = math.sin(radians)
        rotated_scaled_dx = scaled_dx * cos_r - scaled_dy * sin_r
        rotated_scaled_dy = scaled_dx * sin_r + scaled_dy * cos_r

        new_transform = {
            "translateX": old_tx + dx - rotated_scaled_dx,
            "translateY": old_ty + dy - rotated_scaled_dy,
            "rotate": rotation,
            "scaleX": scale_x,
            "scaleY": scale_y,
            "originX": new_ox,
            "originY": new_oy,
        }

        self.setItemTransform(index, new_transform)

    @Slot(int, float, float, float, float)
    def applyScaleResize(
        self,
        index: int,
        new_scale_x: float,
        new_scale_y: float,
        anchor_x: float,
        anchor_y: float,
    ) -> None:
        """Apply scale-based resize with anchor point.

        Sets scale factors and adjusts origin/translation so the anchor
        point remains visually fixed. Used by resize handles.

        Args:
            index: Item index.
            new_scale_x: New X scale factor.
            new_scale_y: New Y scale factor.
            anchor_x: Anchor point X (0=left, 0.5=center, 1=right).
            anchor_y: Anchor point Y (0=top, 0.5=center, 1=bottom).
        """
        if not (0 <= index < len(self._items)):
            return

        item = self._items[index]
        if not hasattr(item, "transform"):
            return

        current = self.getItemTransform(index) or {}
        bounds = compute_geometry_bounds(item)
        if not bounds:
            return

        old_origin_x = current.get("originX", 0)
        old_origin_y = current.get("originY", 0)
        old_scale_x = current.get("scaleX", 1)
        old_scale_y = current.get("scaleY", 1)
        rotation = current.get("rotate", 0)
        old_tx = current.get("translateX", 0)
        old_ty = current.get("translateY", 0)

        import math

        # Origin points in geometry space
        old_origin_geom_x = bounds["x"] + bounds["width"] * old_origin_x
        old_origin_geom_y = bounds["y"] + bounds["height"] * old_origin_y
        anchor_geom_x = bounds["x"] + bounds["width"] * anchor_x
        anchor_geom_y = bounds["y"] + bounds["height"] * anchor_y

        # Displacement from old origin to anchor in geometry space
        d_x = anchor_geom_x - old_origin_geom_x
        d_y = anchor_geom_y - old_origin_geom_y

        # Scale the displacement
        scaled_d_x = d_x * old_scale_x
        scaled_d_y = d_y * old_scale_y

        # Rotate the scaled displacement
        radians = rotation * math.pi / 180
        cos_r = math.cos(radians)
        sin_r = math.sin(radians)
        rotated_d_x = scaled_d_x * cos_r - scaled_d_y * sin_r
        rotated_d_y = scaled_d_x * sin_r + scaled_d_y * cos_r

        # Formula: T_new = T_old - d + R(S_old * d)
        # where d = anchor - old_origin (in geometry space)
        new_tx = old_tx - d_x + rotated_d_x
        new_ty = old_ty - d_y + rotated_d_y

        new_transform = {
            "translateX": new_tx,
            "translateY": new_ty,
            "rotate": rotation,
            "scaleX": new_scale_x,
            "scaleY": new_scale_y,
            "originX": anchor_x,
            "originY": anchor_y,
        }

        self.setItemTransform(index, new_transform)

    @Slot(int)
    def ensureOriginCentered(self, index: int) -> None:
        """Move transform origin to center without changing visual appearance.

        Should be called before starting rotation to ensure rotation
        happens around center. Adjusts translation to compensate.

        Args:
            index: Item index.
        """
        if not (0 <= index < len(self._items)):
            return

        item = self._items[index]
        if not hasattr(item, "transform"):
            return

        current = self.getItemTransform(index) or {}
        bounds = compute_geometry_bounds(item)
        if not bounds:
            return

        old_origin_x = current.get("originX", 0.5)
        old_origin_y = current.get("originY", 0.5)

        center_x = 0.5
        center_y = 0.5

        # If origin is already at center, nothing to do
        if (
            abs(old_origin_x - center_x) < 0.001
            and abs(old_origin_y - center_y) < 0.001
        ):
            return

        old_scale_x = current.get("scaleX", 1)
        old_scale_y = current.get("scaleY", 1)
        old_rotation = current.get("rotate", 0)
        old_tx = current.get("translateX", 0)
        old_ty = current.get("translateY", 0)

        import math

        # Origin points in geometry space
        old_origin_geom_x = bounds["x"] + bounds["width"] * old_origin_x
        old_origin_geom_y = bounds["y"] + bounds["height"] * old_origin_y
        center_geom_x = bounds["x"] + bounds["width"] * center_x
        center_geom_y = bounds["y"] + bounds["height"] * center_y

        # Displacement from old origin to center in geometry space
        d_x = center_geom_x - old_origin_geom_x
        d_y = center_geom_y - old_origin_geom_y

        # Scale the displacement
        scaled_d_x = d_x * old_scale_x
        scaled_d_y = d_y * old_scale_y

        # Rotate the scaled displacement
        radians = old_rotation * math.pi / 180
        cos_r = math.cos(radians)
        sin_r = math.sin(radians)
        rotated_d_x = scaled_d_x * cos_r - scaled_d_y * sin_r
        rotated_d_y = scaled_d_x * sin_r + scaled_d_y * cos_r

        # Translation adjustment: T_new = T_old - d + R(S * d)
        new_tx = old_tx - d_x + rotated_d_x
        new_ty = old_ty - d_y + rotated_d_y

        new_transform = {
            "translateX": new_tx,
            "translateY": new_ty,
            "rotate": old_rotation,  # Keep rotation unchanged
            "scaleX": old_scale_x,
            "scaleY": old_scale_y,
            "originX": center_x,
            "originY": center_y,
        }

        self.setItemTransform(index, new_transform)

    @Slot(int)
    def bakeTransform(self, index: int) -> None:
        """Apply transform to geometry and reset transform to identity.

        For shapes with rotation, converts to a path with transformed corners.
        For scale/translate only, updates geometry bounds directly.
        The operation is undoable.

        Args:
            index: Item index.
        """
        if not (0 <= index < len(self._items)):
            return

        item = self._items[index]
        if not hasattr(item, "transform"):
            return

        # Skip if already identity
        if item.transform.is_identity():
            return

        # For rotated shapes, convert to path with baked transform
        path_data = shape_to_path_data(item, self._itemToDict)
        if path_data is not None:
            self.beginTransaction()
            # Must use replaceItem since updateItem preserves type
            self._replaceItem(index, path_data)
            self.endTransaction()
            return

        # No rotation - apply scale/translate to geometry bounds
        transformed_bounds = item.get_bounds()
        if transformed_bounds.isEmpty():
            return

        self.beginTransaction()

        self.setBoundingBox(
            index,
            {
                "x": transformed_bounds.x(),
                "y": transformed_bounds.y(),
                "width": transformed_bounds.width(),
                "height": transformed_bounds.height(),
            },
        )

        self.setItemTransform(
            index,
            {
                "translateX": 0,
                "translateY": 0,
                "rotate": 0,
                "scaleX": 1,
                "scaleY": 1,
                "originX": 0.5,
                "originY": 0.5,
            },
        )

        self.endTransaction()

    def _replaceItem(self, index: int, new_data: Dict[str, Any]) -> None:
        """Replace an item at index with a new item (allows type changes)."""
        if not (0 <= index < len(self._items)):
            return

        old_data = self._itemToDict(self._items[index])

        try:
            parsed = parse_item_data(new_data)
            new_item = parse_item(parsed.data)
        except ItemSchemaError as exc:
            print(f"Warning: Failed to replace item: {exc}")
            return

        self._items[index] = new_item

        if not self._transaction_active:
            command = UpdateItemCommand(self, index, old_data, parsed.data)
            self._history.execute(command)

        model_index = self.index(index, 0)
        self.dataChanged.emit(model_index, model_index, [])
        self.itemModified.emit(index, parsed.data)

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
        return compute_bounding_box(self._items, index, self._get_descendant_indices)

    @Slot(list, result="QVariant")  # type: ignore[arg-type]
    def getUnionBoundingBox(self, indices: List[int]) -> Optional[Dict[str, float]]:
        """Return union bounding box for multiple items."""
        from lucent.bounding_box import union_bounds

        bounds_list = []
        for idx in indices:
            bb = self.getBoundingBox(idx)
            if bb:
                bounds_list.append(bb)
        return union_bounds(bounds_list)

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
        return compute_geometry_bounds(self._items[index])

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
        updated = apply_bounding_box(self._items[index], bbox, self._itemToDict)
        if updated is None:
            return False
        self.updateItem(index, updated)
        return True

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

    def getRenderItemsInBounds(
        self, x: float, y: float, width: float, height: float
    ) -> List[CanvasItem]:
        """Return renderable items that intersect the given bounds.

        Uses spatial indexing for O(log n + k) query performance instead of
        iterating all items. Results are filtered for visibility and sorted
        by model order for correct z-ordering.

        Args:
            x, y: Top-left corner of query bounds
            width, height: Size of query bounds

        Returns:
            List of renderable, visible items in model order (bottom to top).
        """
        query_rect = Rect(x, y, width, height)
        candidate_ids = self._spatial_index.query(query_rect)

        # Build set of candidate items
        candidates = {id(item) for item in self._items if id(item) in candidate_ids}

        # Filter and maintain model order
        result: List[CanvasItem] = []
        for idx, item in enumerate(self._items):
            if id(item) not in candidates:
                continue
            if self._is_container(item):
                continue
            if not self._is_renderable(item):
                continue
            if not self._is_effectively_visible(idx):
                continue
            result.append(item)

        return result

    def _itemToDict(self, item: CanvasItem) -> Dict[str, Any]:
        return item_to_dict(item)

    # --- Spatial Index Management ---

    def _get_item_bounds_for_index(self, item: CanvasItem) -> Optional[Rect]:
        """Get item bounds as a Rect for spatial indexing."""
        try:
            qrect = item.get_bounds()
            return Rect(qrect.x(), qrect.y(), qrect.width(), qrect.height())
        except Exception:
            return None

    def _on_item_added_spatial(self, index: int) -> None:
        """Update spatial index when an item is added."""
        if 0 <= index < len(self._items):
            item = self._items[index]
            bounds = self._get_item_bounds_for_index(item)
            if bounds:
                self._spatial_index.insert(id(item), bounds)

    def _on_item_removed_spatial(self, index: int) -> None:
        """Update spatial index when an item is removed.

        Note: The item is already removed from _items when this is called,
        so we need to rebuild the index to handle this case correctly.
        """
        # Since we don't have the removed item, rebuild the index
        self._rebuild_spatial_index()

    def _on_item_modified_spatial(self, index: int, _data: Any) -> None:
        """Update spatial index when an item is modified.

        We rebuild the entire index because updateItem creates a new item
        object (with a different id), so we can't just update the old entry.
        """
        self._rebuild_spatial_index()

    def _on_items_cleared_spatial(self) -> None:
        """Clear spatial index when all items are cleared."""
        self._spatial_index.clear()

    def _rebuild_spatial_index(self) -> None:
        """Rebuild the entire spatial index from current items."""
        self._spatial_index.clear()
        for item in self._items:
            bounds = self._get_item_bounds_for_index(item)
            if bounds:
                self._spatial_index.insert(id(item), bounds)
