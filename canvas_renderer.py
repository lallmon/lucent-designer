"""
Canvas renderer component for DesignVibe.

This module provides the CanvasRenderer class, which is a QQuickPaintedItem
that bridges QML and Python, rendering canvas items using QPainter.
"""
from typing import Optional, TYPE_CHECKING
from PySide6.QtCore import Property, Signal, Slot, QObject
from PySide6.QtQuick import QQuickPaintedItem
from PySide6.QtGui import QPainter

if TYPE_CHECKING:
    from canvas_model import CanvasModel


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
            # Initial render
            self.update()
        
    def paint(self, painter: QPainter) -> None:
        """Render all items from the model using QPainter"""
        if not self._model:
            return
            
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Get items from model and render each one
        for item in self._model.getItems():
            item.paint(painter, self._zoom_level)
    
    @Property(float, notify=zoomLevelChanged)
    def zoomLevel(self) -> float:
        return self._zoom_level
    
    @zoomLevel.setter
    def zoomLevel(self, value: float) -> None:
        if self._zoom_level != value:
            self._zoom_level = value
            self.zoomLevelChanged.emit()
            self.update()

