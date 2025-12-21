"""
Canvas model for DesignVibe.

This module provides the CanvasModel class, which manages canvas items
as a proper Qt model with incremental updates and proper change signals.
"""
from typing import List, Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, Slot
from canvas_items import CanvasItem, RectangleItem, EllipseItem


class CanvasModel(QObject):
    """
    Canvas model that manages CanvasItem objects.
    
    Provides efficient incremental updates by converting items once
    and emitting granular change signals. Acts as single source of truth
    for canvas items.
    """
    
    # Signals for incremental updates
    itemAdded = Signal(int)      # Emitted when item added (with index)
    itemRemoved = Signal(int)    # Emitted when item removed (with index)
    itemsCleared = Signal()      # Emitted when all items cleared
    itemModified = Signal(int)   # Emitted when item properties change
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._items: List[CanvasItem] = []
    
    @Slot(dict)
    def addItem(self, item_data: Dict[str, Any]) -> None:
        """
        Add a new item to the canvas.
        
        Args:
            item_data: Dictionary containing item properties from QML
                      Must include 'type' field ('rectangle' or 'ellipse')
        
        Emits:
            itemAdded: Signal with the index of the newly added item
        """
        try:
            item_type = item_data.get("type", "")
            item: Optional[CanvasItem] = None
            
            if item_type == "rectangle":
                item = RectangleItem.from_dict(item_data)
            elif item_type == "ellipse":
                item = EllipseItem.from_dict(item_data)
            else:
                print(f"Warning: Unknown item type '{item_type}'")
                return
            
            self._items.append(item)
            new_index = len(self._items) - 1
            self.itemAdded.emit(new_index)
            
        except (KeyError, ValueError, TypeError) as e:
            print(f"Warning: Failed to create item: {type(e).__name__}: {e}")
    
    @Slot(int)
    def removeItem(self, index: int) -> None:
        """
        Remove an item from the canvas by index.
        
        Args:
            index: Index of the item to remove
        
        Emits:
            itemRemoved: Signal with the index of the removed item
        """
        if 0 <= index < len(self._items):
            del self._items[index]
            self.itemRemoved.emit(index)
        else:
            print(f"Warning: Cannot remove item at invalid index {index}")
    
    @Slot()
    def clear(self) -> None:
        """
        Clear all items from the canvas.
        
        Emits:
            itemsCleared: Signal indicating all items were cleared
        """
        self._items.clear()
        self.itemsCleared.emit()
    
    @Slot(result=int)
    def count(self) -> int:
        """
        Get the number of items in the canvas.
        
        Returns:
            Number of items
        """
        return len(self._items)
    
    def getItems(self) -> List[CanvasItem]:
        """
        Get all canvas items for rendering.
        
        Returns:
            List of CanvasItem objects
        """
        return self._items
    
    @Slot(int, result='QVariant')
    def getItemData(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Get item data as a dictionary for QML queries.
        
        Args:
            index: Index of the item to retrieve
        
        Returns:
            Dictionary representation of the item, or None if invalid index
        """
        if 0 <= index < len(self._items):
            item = self._items[index]
            return self._itemToDict(item)
        return None
    
    @Slot(result='QVariantList')
    def getItemsForHitTest(self) -> List[Dict[str, Any]]:
        """
        Get all items as dictionaries for hit testing in QML.
        
        Returns:
            List of dictionaries representing all items
        """
        return [self._itemToDict(item) for item in self._items]
    
    def _itemToDict(self, item: CanvasItem) -> Dict[str, Any]:
        """
        Convert a CanvasItem to a dictionary for QML.
        
        Args:
            item: CanvasItem to convert
        
        Returns:
            Dictionary representation of the item
        """
        if isinstance(item, RectangleItem):
            return {
                "type": "rectangle",
                "x": item.x,
                "y": item.y,
                "width": item.width,
                "height": item.height,
                "strokeWidth": item.stroke_width,
                "strokeColor": item.stroke_color,
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
                "fillColor": item.fill_color,
                "fillOpacity": item.fill_opacity
            }
        return {}

