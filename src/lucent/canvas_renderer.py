# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Canvas renderer component for Lucent.

This module provides the CanvasRenderer class, which is a QQuickPaintedItem
that bridges QML and Python, rendering canvas items using QPainter.
"""

from typing import Optional, List, TYPE_CHECKING
from PySide6.QtCore import Property, Signal, Slot, QObject, QRectF
from PySide6.QtQuick import QQuickPaintedItem, QQuickItem
from PySide6.QtGui import QPainter

if TYPE_CHECKING:
    from lucent.canvas_model import CanvasModel
    from lucent.canvas_items import CanvasItem

# Minimum screen size in pixels for an item to be rendered (LOD threshold)
MIN_RENDER_SIZE_PX = 2.0


class CanvasRenderer(QQuickPaintedItem):
    """Custom QPainter-based renderer for canvas items"""

    zoomLevelChanged = Signal()
    tileOriginChanged = Signal()

    def __init__(self, parent: Optional[QQuickItem] = None) -> None:
        super().__init__(parent)
        self._model: Optional["CanvasModel"] = None
        self._zoom_level: float = 1.0
        self._tile_origin_x: float = 0.0
        self._tile_origin_y: float = 0.0

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

    def _get_tile_bounds(self) -> QRectF:
        """Calculate this tile's bounds in canvas coordinates."""
        half_w = self.width() / 2.0
        half_h = self.height() / 2.0
        return QRectF(
            self._tile_origin_x - half_w,
            self._tile_origin_y - half_h,
            self.width(),
            self.height(),
        )

    def _item_intersects_tile(self, item: "CanvasItem", tile_bounds: QRectF) -> bool:
        """Check if an item's bounds intersect the tile bounds."""
        try:
            item_bounds = item.get_bounds()
            return tile_bounds.intersects(item_bounds)
        except Exception:
            # If we can't get bounds, render it to be safe
            return True

    def _item_too_small_to_render(self, item: "CanvasItem") -> bool:
        """Check if an item is too small on screen to be worth rendering (LOD).

        Items whose screen-space size would be below MIN_RENDER_SIZE_PX in both
        dimensions are skipped, improving performance at low zoom levels where
        tiny shapes would be invisible anyway.
        """
        try:
            item_bounds = item.get_bounds()
            # Calculate screen size (canvas size * zoom)
            screen_width = item_bounds.width() * self._zoom_level
            screen_height = item_bounds.height() * self._zoom_level
            # Skip if both dimensions are below threshold
            return (
                screen_width < MIN_RENDER_SIZE_PX and screen_height < MIN_RENDER_SIZE_PX
            )
        except Exception:
            # If we can't get bounds, render it to be safe
            return False

    def paint(self, painter: QPainter) -> None:
        """Render items from the model that intersect this tile.

        Performance optimizations:
        1. Spatial indexing: O(log n + k) query for items in tile bounds
        2. LOD skipping: Items too small on screen (< 2px) are skipped

        Rendering order follows CanvasModel model order:
        - Lower indices are painted first (further back)
        - Higher indices are painted later (on top)
        - Layers themselves are skipped by getRenderItemsInBounds
        """
        if not self._model:
            return

        painter.setRenderHint(QPainter.Antialiasing, True)  # type: ignore[attr-defined]

        # Compute offsets so (0,0) maps to the global canvas origin, adjusted by tile.
        offset_x = (self.width() / 2.0) - self._tile_origin_x
        offset_y = (self.height() / 2.0) - self._tile_origin_y

        # Get tile bounds for spatial query
        tile_bounds = self._get_tile_bounds()

        # Use spatial index for O(log n + k) query instead of O(n)
        ordered_items = self._get_render_items_in_bounds(tile_bounds)

        # Render items that are large enough to see
        for item in ordered_items:
            # Skip items too small to see at current zoom (LOD)
            if self._item_too_small_to_render(item):
                continue

            try:
                item.paint(
                    painter, self._zoom_level, offset_x=offset_x, offset_y=offset_y
                )
            except TypeError:
                # Fallback for items that don't accept offsets (legacy/test doubles)
                item.paint(painter, self._zoom_level)

    def _get_render_items_in_bounds(self, bounds: QRectF) -> List["CanvasItem"]:
        """Get renderable items that intersect bounds using spatial index."""
        if not self._model:
            return []
        return self._model.getRenderItemsInBounds(
            bounds.x(), bounds.y(), bounds.width(), bounds.height()
        )

    def _get_render_order(self) -> List["CanvasItem"]:
        """Get items in render order from the model (legacy, for tests)."""
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

    @Property(float, notify=tileOriginChanged)
    def tileOriginX(self) -> float:
        return self._tile_origin_x

    @tileOriginX.setter  # type: ignore[no-redef]
    def tileOriginX(self, value: float) -> None:
        if self._tile_origin_x != value:
            self._tile_origin_x = value
            self.tileOriginChanged.emit()
            self.update()

    @Property(float, notify=tileOriginChanged)
    def tileOriginY(self) -> float:
        return self._tile_origin_y

    @tileOriginY.setter  # type: ignore[no-redef]
    def tileOriginY(self, value: float) -> None:
        if self._tile_origin_y != value:
            self._tile_origin_y = value
            self.tileOriginChanged.emit()
            self.update()
