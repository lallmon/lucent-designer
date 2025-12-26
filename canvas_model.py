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
        return None

    def roleNames(self) -> Dict[int, bytes]:
        return {
            self.NameRole: b"name",
            self.TypeRole: b"itemType",
            self.IndexRole: b"itemIndex",
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
        command = MoveItemCommand(self, from_index, to_index)
        self._execute_command(command)

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
                "name": item.name
            }
        return {}
