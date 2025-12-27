"""Canvas model for DesignVibe - manages canvas items with undo/redo support."""
from typing import List, Optional, Dict, Any
from PySide6.QtCore import (
    QAbstractListModel, QModelIndex, Qt, Signal, Slot, Property, QObject
)
from canvas_items import CanvasItem, RectangleItem, EllipseItem, LayerItem
from commands import (
    Command, AddItemCommand, RemoveItemCommand,
    UpdateItemCommand, ClearCommand, MoveItemCommand, TransactionCommand
)


class CanvasModel(QAbstractListModel):
    """Manages CanvasItem objects as a Qt list model with undo/redo support."""

    # Custom roles for QML data binding
    NameRole = Qt.UserRole + 1
    TypeRole = Qt.UserRole + 2
    IndexRole = Qt.UserRole + 3
    ItemIdRole = Qt.UserRole + 4      # Unique ID for layers
    ParentIdRole = Qt.UserRole + 5    # Parent layer ID for shapes

    # Legacy signals (kept for backward compatibility with CanvasRenderer)
    itemAdded = Signal(int)
    itemRemoved = Signal(int)
    itemsCleared = Signal()
    itemModified = Signal(int, 'QVariant')  # index and item data
    itemsReordered = Signal()
    undoStackChanged = Signal()
    redoStackChanged = Signal()

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._items: List[CanvasItem] = []
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
        self._transaction: Optional[TransactionCommand] = None
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
        return None

    def roleNames(self) -> Dict[int, bytes]:
        return {
            self.NameRole: b"name",
            self.TypeRole: b"itemType",
            self.IndexRole: b"itemIndex",
            self.ItemIdRole: b"itemId",
            self.ParentIdRole: b"parentId",
        }

    def _execute_command(self, command: Command, record: bool = True) -> None:
        command.execute()
        if record:
            self._undo_stack.append(command)
            if self._redo_stack:
                self._redo_stack.clear()
                self.redoStackChanged.emit()
            self.undoStackChanged.emit()

    @Slot()
    def beginTransaction(self) -> None:
        if self._transaction is not None:
            return
        self._transaction = TransactionCommand([], "Edit Properties")
        self._transaction_snapshot = {
            i: self._itemToDict(item) for i, item in enumerate(self._items)
        }

    @Slot()
    def endTransaction(self) -> None:
        if self._transaction is None:
            return

        commands: List[Command] = []
        for index, old_data in self._transaction_snapshot.items():
            if index < len(self._items):
                current_data = self._itemToDict(self._items[index])
                if current_data != old_data:
                    commands.append(UpdateItemCommand(self, index, old_data, current_data))

        self._transaction_snapshot = {}

        if commands:
            transaction = TransactionCommand(commands, "Edit Properties")
            self._undo_stack.append(transaction)
            if self._redo_stack:
                self._redo_stack.clear()
                self.redoStackChanged.emit()
            self.undoStackChanged.emit()

        self._transaction = None

    def _generate_name(self, item_type: str) -> str:
        type_name = item_type.capitalize()
        self._type_counters[item_type] = self._type_counters.get(item_type, 0) + 1
        return f"{type_name} {self._type_counters[item_type]}"

    @Slot(dict)
    def addItem(self, item_data: Dict[str, Any]) -> None:
        item_type = item_data.get("type", "")
        if item_type not in ("rectangle", "ellipse", "layer"):
            print(f"Warning: Unknown item type '{item_type}'")
            return

        if not item_data.get("name"):
            item_data = dict(item_data)
            item_data["name"] = self._generate_name(item_type)

        command = AddItemCommand(self, item_data)
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
        
        # #region agent log
        import json; open('/home/lka/Git/DesignVibe/.cursor/debug.log','a').write(json.dumps({"hypothesisId":"H1","location":"canvas_model.py:moveItem","message":"moveItem called","data":{"from_index":from_index,"to_index":to_index,"item_type":type(item).__name__,"item_name":getattr(item,'name',''),"is_layer":isinstance(item,LayerItem),"items_before":[{"i":i,"type":type(it).__name__,"name":getattr(it,'name',''),"parent_id":getattr(it,'parent_id',None)} for i,it in enumerate(self._items)]},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session"})+'\n')
        # #endregion
        
        # Check if moving a layer - need to move children too
        if isinstance(item, LayerItem):
            children_indices = self._getLayerChildrenIndices(item.id)
            # #region agent log
            import json; open('/home/lka/Git/DesignVibe/.cursor/debug.log','a').write(json.dumps({"hypothesisId":"H2","location":"canvas_model.py:moveItem:layer","message":"Moving layer with children","data":{"layer_id":item.id,"children_indices":children_indices},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session"})+'\n')
            # #endregion
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
            if isinstance(item, (RectangleItem, EllipseItem)) and item.parent_id == layer_id:
                children.append(i)
        return children

    def _moveLayerWithChildren(self, layer_from: int, layer_to: int, children_indices: List[int]) -> None:
        """Move a layer along with all its children as a group.
        
        This maintains the parent-child visual grouping by extracting the layer
        and all its children, then reinserting them at the target position.
        """
        # #region agent log
        import json; open('/home/lka/Git/DesignVibe/.cursor/debug.log','a').write(json.dumps({"hypothesisId":"H2","location":"canvas_model.py:_moveLayerWithChildren","message":"Moving layer group","data":{"layer_from":layer_from,"layer_to":layer_to,"children_indices":children_indices,"items_before":[{"i":i,"type":type(it).__name__,"name":getattr(it,'name','')} for i,it in enumerate(self._items)]},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session"})+'\n')
        # #endregion
        
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
            items_removed_before_target = sum(1 for idx in all_indices if idx < layer_to)
            # +1 to insert AFTER the target position (not before it)
            insert_at = min(layer_to - items_removed_before_target + 1, remaining_count)
        
        # Insert all items at the target position
        for i, item in enumerate(extracted_items):
            self._items.insert(insert_at + i, item)
        
        # Notify model of changes using proper row signals
        self.beginResetModel()
        self.endResetModel()
        self.itemsReordered.emit()
        
        # #region agent log
        import json; open('/home/lka/Git/DesignVibe/.cursor/debug.log','a').write(json.dumps({"hypothesisId":"H2","location":"canvas_model.py:_moveLayerWithChildren:done","message":"Layer group move complete","data":{"insert_at":insert_at,"items_after":[{"i":i,"type":type(it).__name__,"name":getattr(it,'name',''),"parent_id":getattr(it,'parent_id',None)} for i,it in enumerate(self._items)]},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session"})+'\n')
        # #endregion

    @Slot(int, str)
    def reparentItem(self, item_index: int, parent_id: str) -> None:
        """Set parent and move item to be last child of that layer.
        
        This combines setParent + moveItem into a single undoable operation.
        The item is moved to be just before the next top-level item after the layer.
        
        Args:
            item_index: Index of the shape item to reparent
            parent_id: ID of the layer to set as parent, or empty string to unparent
        """
        # #region agent log
        import json; open('/home/lka/Git/DesignVibe/.cursor/debug.log','a').write(json.dumps({"hypothesisId":"REPARENT","location":"canvas_model.py:reparentItem","message":"reparentItem called","data":{"item_index":item_index,"parent_id":parent_id,"items":[{"i":i,"type":type(it).__name__,"name":getattr(it,'name',''),"parent_id":getattr(it,'parent_id',None)} for i,it in enumerate(self._items)]},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session"})+'\n')
        # #endregion
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
        model_index = self.index(target_index if target_index != item_index else item_index, 0)
        self.dataChanged.emit(model_index, model_index, [])

    @Slot(int, dict)
    def updateItem(self, index: int, properties: Dict[str, Any]) -> None:
        if not (0 <= index < len(self._items)):
            print(f"Warning: Cannot update item at invalid index {index}")
            return

        item = self._items[index]
        old_props = self._itemToDict(item)

        try:
            if isinstance(item, RectangleItem):
                if "x" in properties:
                    item.x = float(properties["x"])
                if "y" in properties:
                    item.y = float(properties["y"])
                if "width" in properties:
                    item.width = max(0.0, float(properties["width"]))
                if "height" in properties:
                    item.height = max(0.0, float(properties["height"]))
            elif isinstance(item, EllipseItem):
                if "centerX" in properties:
                    item.center_x = float(properties["centerX"])
                if "centerY" in properties:
                    item.center_y = float(properties["centerY"])
                if "radiusX" in properties:
                    item.radius_x = max(0.0, float(properties["radiusX"]))
                if "radiusY" in properties:
                    item.radius_y = max(0.0, float(properties["radiusY"]))

            # Common shape properties
            if isinstance(item, (RectangleItem, EllipseItem)):
                if "strokeWidth" in properties:
                    item.stroke_width = max(0.1, min(100.0, float(properties["strokeWidth"])))
                if "strokeColor" in properties:
                    item.stroke_color = str(properties["strokeColor"])
                if "strokeOpacity" in properties:
                    item.stroke_opacity = max(0.0, min(1.0, float(properties["strokeOpacity"])))
                if "fillColor" in properties:
                    item.fill_color = str(properties["fillColor"])
                if "fillOpacity" in properties:
                    item.fill_opacity = max(0.0, min(1.0, float(properties["fillOpacity"])))
                if "parentId" in properties:
                    item.parent_id = properties["parentId"]

            new_props = self._itemToDict(item)

            if self._transaction is None:
                command = UpdateItemCommand(self, index, old_props, new_props)
                self._undo_stack.append(command)
                if self._redo_stack:
                    self._redo_stack.clear()
                    self.redoStackChanged.emit()
                self.undoStackChanged.emit()

            model_index = self.index(index, 0)
            self.dataChanged.emit(model_index, model_index, [])
            self.itemModified.emit(index, new_props)

        except (ValueError, TypeError) as e:
            print(f"Warning: Failed to update item: {type(e).__name__}: {e}")

    @Slot(result=int)
    def count(self) -> int:
        return len(self._items)

    def _canUndo(self) -> bool:
        return len(self._undo_stack) > 0

    canUndo = Property(bool, _canUndo, notify=undoStackChanged)

    @Slot(result=bool)
    def undo(self) -> bool:
        if not self._undo_stack:
            return False

        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        self.undoStackChanged.emit()
        self.redoStackChanged.emit()
        return True

    def _canRedo(self) -> bool:
        return len(self._redo_stack) > 0

    canRedo = Property(bool, _canRedo, notify=redoStackChanged)

    @Slot(result=bool)
    def redo(self) -> bool:
        if not self._redo_stack:
            return False

        command = self._redo_stack.pop()
        command.execute()
        self._undo_stack.append(command)
        self.undoStackChanged.emit()
        self.redoStackChanged.emit()
        return True

    def getItems(self) -> List[CanvasItem]:
        return self._items

    @Slot(int, result='QVariant')
    def getItemData(self, index: int) -> Optional[Dict[str, Any]]:
        if 0 <= index < len(self._items):
            return self._itemToDict(self._items[index])
        return None

    @Slot(result='QVariantList')
    def getItemsForHitTest(self) -> List[Dict[str, Any]]:
        return [self._itemToDict(item) for item in self._items]

    def _itemToDict(self, item: CanvasItem) -> Dict[str, Any]:
        if isinstance(item, RectangleItem):
            return {
                "type": "rectangle",
                "name": item.name,
                "parentId": item.parent_id,
                "x": item.x,
                "y": item.y,
                "width": item.width,
                "height": item.height,
                "strokeWidth": item.stroke_width,
                "strokeColor": item.stroke_color,
                "strokeOpacity": item.stroke_opacity,
                "fillColor": item.fill_color,
                "fillOpacity": item.fill_opacity
            }
        elif isinstance(item, EllipseItem):
            return {
                "type": "ellipse",
                "name": item.name,
                "parentId": item.parent_id,
                "centerX": item.center_x,
                "centerY": item.center_y,
                "radiusX": item.radius_x,
                "radiusY": item.radius_y,
                "strokeWidth": item.stroke_width,
                "strokeColor": item.stroke_color,
                "strokeOpacity": item.stroke_opacity,
                "fillColor": item.fill_color,
                "fillOpacity": item.fill_opacity
            }
        elif isinstance(item, LayerItem):
            return {
                "type": "layer",
                "id": item.id,
                "name": item.name
            }
        return {}
