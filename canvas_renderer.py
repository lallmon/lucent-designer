"""
Canvas renderer component for DesignVibe.

This module provides the CanvasRenderer class, which is a QQuickPaintedItem
that bridges QML and Python, rendering canvas items using QPainter.
"""
from typing import Optional, List, TYPE_CHECKING
from PySide6.QtCore import Property, Signal, Slot, QObject
from PySide6.QtQuick import QQuickPaintedItem
from PySide6.QtGui import QPainter

if TYPE_CHECKING:
    from canvas_model import CanvasModel
    from canvas_items import CanvasItem


class CanvasRenderer(QQuickPaintedItem):
    """Custom QPainter-based renderer for canvas items"""
    
    zoomLevelChanged = Signal()
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._model: Optional['CanvasModel'] = None
        self._zoom_level: float = 1.0
    
    @Slot(QObject)
    def setModel(self, model: QObject) -> None:
        """
        Set the canvas model to render items from.
        
        Args:
            model: CanvasModel instance to get items from
        """
        # Import here to avoid circular dependency
        from canvas_model import CanvasModel
        
        if isinstance(model, CanvasModel):
            self._model = model
            # Connect to model signals for automatic updates
            model.itemAdded.connect(self.update)
            model.itemRemoved.connect(self.update)
            model.itemsCleared.connect(self.update)
            model.itemModified.connect(self.update)
            model.itemsReordered.connect(self.update)
            # Initial render
            self.update()
        
    def paint(self, painter: QPainter) -> None:
        """Render all items from the model using QPainter.
        
        Rendering order respects parent-child relationships:
        - Items are rendered bottom-to-top based on their position in the list
        - When a layer is encountered, its children are rendered immediately after it
        - This groups children visually with their parent layer in Z-order
        """
        # #region agent log
        import json; open('/home/lka/Git/DesignVibe/.cursor/debug.log','a').write(json.dumps({"hypothesisId":"PAINT","location":"canvas_renderer.py:paint","message":"paint called","data":{"has_model":self._model is not None},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session"})+'\n')
        # #endregion
        if not self._model:
            return
            
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Get ordered items respecting parent-child grouping
        ordered_items = self._get_render_order()
        
        # #region agent log
        import json; open('/home/lka/Git/DesignVibe/.cursor/debug.log','a').write(json.dumps({"hypothesisId":"PAINT","location":"canvas_renderer.py:paint:order","message":"render order","data":{"items":[{"name":getattr(it,'name',''),"type":type(it).__name__,"parent_id":getattr(it,'parent_id',None)} for it in ordered_items]},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session"})+'\n')
        # #endregion
        
        # Render each item
        for item in ordered_items:
            item.paint(painter, self._zoom_level)
    
    def _get_render_order(self) -> List['CanvasItem']:
        """Get items in render order - simply use model order.
        
        The model maintains the correct z-order:
        - Items lower in index render first (bottom)
        - Items higher in index render later (top)
        - Layers are skipped (they're organizational, not visual)
        
        Returns:
            List of CanvasItem in the order they should be painted (bottom to top)
        """
        from canvas_items import LayerItem, RectangleItem, EllipseItem
        
        items = self._model.getItems()
        result: List['CanvasItem'] = []
        
        # Render items in model order, skipping layers (they're organizational only)
        for item in items:
            if isinstance(item, (RectangleItem, EllipseItem)):
                result.append(item)
        
        return result
    
    @Property(float, notify=zoomLevelChanged)
    def zoomLevel(self) -> float:
        return self._zoom_level
    
    @zoomLevel.setter
    def zoomLevel(self, value: float) -> None:
        if self._zoom_level != value:
            self._zoom_level = value
            self.zoomLevelChanged.emit()
            self.update()

