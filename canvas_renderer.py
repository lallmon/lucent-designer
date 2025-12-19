from PySide6.QtCore import Property, Signal, Slot
from PySide6.QtQuick import QQuickPaintedItem
from PySide6.QtGui import QPainter
from canvas_items import CanvasItem, RectangleItem


class CanvasRenderer(QQuickPaintedItem):
    """Custom QPainter-based renderer for canvas items"""
    
    itemsChanged = Signal()
    zoomLevelChanged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._zoom_level = 1.0
        
    def paint(self, painter):
        """Render all items using QPainter"""
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Each item knows how to paint itself
        for item in self._items:
            item.paint(painter, self._zoom_level)
    # Use `list` for QML arrays to enable automatic JavaScript→Python conversion.
    # PySide6 does not expose a `QVariant` class to import like PyQt/PySide2 did.
    @Property(list, notify=itemsChanged)
    def items(self):
        return self._items
    
    @items.setter
    def items(self, value):
        # Convert QML list to Python list of CanvasItem objects
        converted_items = []
        if value:
            for item_data in value:
                # Ensure we have a dict (handle both dict and QML JS objects)
                if not isinstance(item_data, dict):
                    # Try to convert JS object to dict via duck-typing
                    try:
                        item_data = {
                            "type": item_data.get("type") if hasattr(item_data, "get") else item_data.property("type"),
                            "x": float(item_data.get("x", 0) if hasattr(item_data, "get") else item_data.property("x")),
                            "y": float(item_data.get("y", 0) if hasattr(item_data, "get") else item_data.property("y")),
                            "width": float(item_data.get("width", 0) if hasattr(item_data, "get") else item_data.property("width")),
                            "height": float(item_data.get("height", 0) if hasattr(item_data, "get") else item_data.property("height")),
                            "strokeWidth": float(item_data.get("strokeWidth", 1) if hasattr(item_data, "get") else item_data.property("strokeWidth")),
                            "strokeColor": item_data.get("strokeColor", "#ffffff") if hasattr(item_data, "get") else item_data.property("strokeColor"),
                            "fillColor": item_data.get("fillColor", "#ffffff") if hasattr(item_data, "get") else item_data.property("fillColor"),
                            "fillOpacity": float(item_data.get("fillOpacity", 0.0) if hasattr(item_data, "get") else item_data.property("fillOpacity")),
                        }
                    except Exception:
                        # Skip items that can't be converted
                        continue
                
                # Use factory method to create appropriate item object
                try:
                    item_type = item_data.get("type", "")
                    if item_type == "rectangle":
                        item_obj = RectangleItem.from_dict(item_data)
                        converted_items.append(item_obj)
                    # else: Unknown item type, skip
                except Exception:
                    # Skip items that can't be created
                    continue
        
        self._items = converted_items
        self.itemsChanged.emit()
        self.update()
    
    @Property(float, notify=zoomLevelChanged)
    def zoomLevel(self):
        return self._zoom_level
    
    @zoomLevel.setter
    def zoomLevel(self, value):
        if self._zoom_level != value:
            self._zoom_level = value
            self.zoomLevelChanged.emit()
            self.update()

