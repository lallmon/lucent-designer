# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Canvas renderer component for Lucent.

This module provides the CanvasRenderer class, which is a QQuickPaintedItem
that bridges QML and Python, rendering canvas items using QPainter.
"""

from typing import Optional, List, TYPE_CHECKING
from PySide6.QtCore import Property, Signal, Slot, QObject
from PySide6.QtQuick import QQuickPaintedItem, QQuickItem
from PySide6.QtGui import QPainter

if TYPE_CHECKING:
    from lucent.canvas_model import CanvasModel
    from lucent.canvas_items import CanvasItem


class CanvasRenderer(QQuickPaintedItem):
    """Custom QPainter-based renderer for canvas items"""

    zoomLevelChanged = Signal()

    def __init__(self, parent: Optional[QQuickItem] = None) -> None:
        super().__init__(parent)
        self._model: Optional["CanvasModel"] = None
        self._zoom_level: float = 1.0

    @Slot(QObject)
    def setModel(self, model: QObject) -> None:
        """
        Set the canvas model to render items from.

        Args:
            model: CanvasModel instance to get items from
        """
        # Import here to avoid circular dependency
        from lucent.canvas_model import CanvasModel

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

        Rendering order follows CanvasModel model order:
        - Lower indices are painted first (further back)
        - Higher indices are painted later (on top)
        - Layers themselves are skipped by getRenderItems
        """
        if not self._model:
            return

        painter.setRenderHint(QPainter.Antialiasing, True)  # type: ignore[attr-defined]

        # Compute offsets so (0,0) maps to the center of the renderer surface.
        offset_x = self.width() / 2.0
        offset_y = self.height() / 2.0

        ordered_items = self._get_render_order()

        # Render each item with dynamic offsets
        for item in ordered_items:
            try:
                item.paint(
                    painter, self._zoom_level, offset_x=offset_x, offset_y=offset_y
                )
            except TypeError:
                # Fallback for items that don't accept offsets (legacy/test doubles)
                item.paint(painter, self._zoom_level)

    def _get_render_order(self) -> List["CanvasItem"]:
        """Get items in render order from the model."""
        return self._model.getRenderItems() if self._model else []

    @Property(float, notify=zoomLevelChanged)
    def zoomLevel(self) -> float:
        return self._zoom_level

    @zoomLevel.setter  # type: ignore[no-redef]
    def zoomLevel(self, value: float) -> None:
        if self._zoom_level != value:
            self._zoom_level = value
            self.zoomLevelChanged.emit()
            self.update()
