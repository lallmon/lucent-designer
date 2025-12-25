"""
Canvas model for DesignVibe.

This module provides the CanvasModel class, which manages canvas items
as a proper Qt model with incremental updates and proper change signals.
"""
from typing import List, Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, Slot, Property
from canvas_items import CanvasItem, RectangleItem, EllipseItem
from commands import (
    Command, AddItemCommand, RemoveItemCommand,
    UpdateItemCommand, ClearCommand, TransactionCommand
)


class CanvasModel(QObject):
    """
    Canvas model that manages CanvasItem objects.
    
    Provides efficient incremental updates by converting items once
    and emitting granular change signals. Acts as single source of truth
    for canvas items.
    """

    itemAdded = Signal(int)
    itemRemoved = Signal(int)
    itemsCleared = Signal()
    itemModified = Signal(int)
    undoStackChanged = Signal()
    redoStackChanged = Signal()

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._items: List[CanvasItem] = []
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
        self._transaction: Optional[TransactionCommand] = None

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

    @Slot(dict)
    def addItem(self, item_data: Dict[str, Any]) -> None:
        """Add a new item to the canvas."""
        item_type = item_data.get("type", "")
        if item_type not in ("rectangle", "ellipse"):
            print(f"Warning: Unknown item type '{item_type}'")
            return

        command = AddItemCommand(self, item_data)
        self._execute_command(command)

    @Slot(int)
    def removeItem(self, index: int) -> None:
        """Remove an item from the canvas by index."""
        if not (0 <= index < len(self._items)):
            print(f"Warning: Cannot remove item at invalid index {index}")
            return

        command = RemoveItemCommand(self, index)
        self._execute_command(command)

    @Slot()
    def clear(self) -> None:
        """Clear all items from the canvas."""
        if not self._items:
            self.itemsCleared.emit()
            return

        command = ClearCommand(self)
        self._execute_command(command)

    @Slot(int, dict)
    def updateItem(self, index: int, properties: Dict[str, Any]) -> None:
        """Update properties of an existing item."""
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

            self.itemModified.emit(index)

        except (ValueError, TypeError) as e:
            print(f"Warning: Failed to update item: {type(e).__name__}: {e}")

    @Slot(result=int)
    def count(self) -> int:
        """Get the number of items in the canvas."""
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
        """Get all canvas items for rendering."""
        return self._items

    @Slot(int, result='QVariant')
    def getItemData(self, index: int) -> Optional[Dict[str, Any]]:
        """Get item data as a dictionary for QML queries."""
        if 0 <= index < len(self._items):
            return self._itemToDict(self._items[index])
        return None

    @Slot(result='QVariantList')
    def getItemsForHitTest(self) -> List[Dict[str, Any]]:
        """Get all items as dictionaries for hit testing in QML."""
        return [self._itemToDict(item) for item in self._items]

    def _itemToDict(self, item: CanvasItem) -> Dict[str, Any]:
        """Convert a CanvasItem to a dictionary for QML."""
        if isinstance(item, RectangleItem):
            return {
                "type": "rectangle",
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
        return {}
