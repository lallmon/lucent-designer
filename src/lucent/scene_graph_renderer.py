# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""
GPU-accelerated scene graph renderer using texture-based approach.

This renderer rasterizes shapes to textures, then uses GPU nodes for:
- QSGSimpleTextureNode: Display the rasterized shape
- QSGTransformNode: Apply rotation/scale/translate on GPU

Key benefits:
- Smooth transforms during interaction (GPU-only, no re-rasterization)
- Non-destructive editing preserved (transforms stay in model)
- All shape types supported (anything that can paint to QPainter)
"""

from typing import Any, Optional, List, TYPE_CHECKING
from PySide6.QtCore import Property, Signal, Slot, QObject, QRectF
from PySide6.QtQuick import (
    QQuickItem,
    QSGNode,
    QSGSimpleTextureNode,
    QSGTransformNode,
    QSGTexture,
)

from lucent.texture_cache import TextureCache
from lucent.item_schema import parse_item

if TYPE_CHECKING:
    from lucent.canvas_model import CanvasModel
    from lucent.canvas_items import CanvasItem


class SceneGraphRenderer(QQuickItem):
    """GPU-accelerated renderer using texture-based scene graph.

    Shapes are rasterized to textures once, then displayed via GPU nodes.
    Transforms (rotate, scale, translate) are applied on the GPU without
    re-rasterizing, enabling smooth 60fps interactions.
    """

    zoomLevelChanged = Signal()
    tileOriginChanged = Signal()
    previewItemChanged = Signal()

    def __init__(self, parent: Optional[QQuickItem] = None) -> None:
        super().__init__(parent)
        self.setFlag(QQuickItem.ItemHasContents, True)  # type: ignore[attr-defined]

        self._model: Optional["CanvasModel"] = None
        self._zoom_level: float = 1.0
        self._tile_origin_x: float = 0.0
        self._tile_origin_y: float = 0.0
        self._texture_cache = TextureCache()
        self._needs_full_rebuild: bool = True

        # Preview item for tool drawing (rendered on top of all items)
        self._preview_item: Optional["CanvasItem"] = None
        self._preview_cache = TextureCache()

        # Prevent GC of GPU resources
        self._textures: List[QSGTexture] = []
        self._texture_nodes: List[QSGSimpleTextureNode] = []
        self._transform_nodes: List[QSGTransformNode] = []

    @Slot(QObject)
    def setModel(self, model: QObject) -> None:
        """Connect to canvas model for rendering."""
        from lucent.canvas_model import CanvasModel

        if isinstance(model, CanvasModel):
            self._model = model
            model.itemAdded.connect(self._on_structure_changed)
            model.itemRemoved.connect(self._on_structure_changed)
            model.itemsCleared.connect(self._on_items_cleared)
            model.itemsReordered.connect(self._on_structure_changed)
            model.itemModified.connect(self._on_item_modified)
            self._needs_full_rebuild = True
            self.update()

    @Slot(int)
    def _on_structure_changed(self, index: int = -1) -> None:
        self._needs_full_rebuild = True
        self.update()

    @Slot()
    def _on_items_cleared(self) -> None:
        self._texture_cache.clear()
        self._needs_full_rebuild = True
        self.update()

    @Slot(int, "QVariant")  # type: ignore[arg-type]
    def _on_item_modified(self, index: int, changed_props: object = None) -> None:
        if self._model:
            item = self._model.getItem(index)
            if item and hasattr(item, "id"):
                self._texture_cache.invalidate(item.id)
        self._needs_full_rebuild = True
        self.update()

    @Slot("QVariant")  # type: ignore[arg-type]
    def setPreviewItem(self, item_data: Any) -> None:
        """Set preview item for tool drawing. Rendered on top of all items."""
        from PySide6.QtQml import QJSValue

        if isinstance(item_data, QJSValue):
            item_data = item_data.toVariant()

        if not item_data:
            self.clearPreview()
            return
        try:
            self._preview_item = parse_item(item_data)
            self._preview_cache.clear()
            self._needs_full_rebuild = True
            self.previewItemChanged.emit()
            self.update()
        except Exception:
            self._preview_item = None

    @Slot()
    def clearPreview(self) -> None:
        """Clear the preview item."""
        if self._preview_item is not None:
            self._preview_item = None
            self._preview_cache.clear()
            self._needs_full_rebuild = True
            self.previewItemChanged.emit()
            self.update()

    def updatePaintNode(  # type: ignore[override]
        self, old_node: Optional[QSGNode], update_data: QQuickItem.UpdatePaintNodeData
    ) -> Optional[QSGNode]:
        if not self._model:
            return old_node

        if old_node is None:
            old_node = QSGNode()
            self._needs_full_rebuild = True

        if self._needs_full_rebuild:
            self._rebuild_nodes(old_node)
            self._needs_full_rebuild = False

        return old_node

    def _rebuild_nodes(self, root: QSGNode) -> None:
        while root.childCount() > 0:
            child = root.firstChild()
            root.removeChildNode(child)

        self._textures.clear()
        self._texture_nodes.clear()
        self._transform_nodes.clear()

        offset_x = self.width() / 2.0 - self._tile_origin_x
        offset_y = self.height() / 2.0 - self._tile_origin_y

        window = self.window()
        if not window:
            return

        if self._model:
            count = self._model.count()
            for i in range(count):
                item = self._model.getItem(i)
                if item is None:
                    continue
                background_node = self._create_artboard_background_node(
                    item, offset_x, offset_y, window
                )
                if background_node:
                    root.appendChildNode(background_node)
            for i in range(count):
                item = self._model.getItem(i)
                if item is None:
                    continue

                node = self._create_node_for_item(
                    item, offset_x, offset_y, window, self._texture_cache
                )
                if node:
                    root.appendChildNode(node)

        if self._preview_item:
            preview_node = self._create_node_for_item(
                self._preview_item, offset_x, offset_y, window, self._preview_cache
            )
            if preview_node:
                root.appendChildNode(preview_node)

    def _create_artboard_background_node(
        self,
        item: "CanvasItem",
        offset_x: float,
        offset_y: float,
        window: object,
    ) -> Optional[QSGNode]:
        """Create a background node for artboards."""
        from lucent.canvas_items import ArtboardItem
        from PySide6.QtGui import QImage, QColor

        if not isinstance(item, ArtboardItem):
            return None
        if hasattr(item, "visible") and not item.visible:
            return None

        background_color = getattr(item, "background_color", "")
        if not background_color:
            return None

        image = QImage(1, 1, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(QColor(background_color))

        texture = window.createTextureFromImage(image)  # type: ignore[attr-defined]
        if not texture:
            return None

        self._textures.append(texture)

        node = QSGSimpleTextureNode()
        node.setTexture(texture)
        node.setRect(
            QRectF(
                item.x + offset_x,
                item.y + offset_y,
                item.width,
                item.height,
            )
        )

        self._texture_nodes.append(node)
        return node

    def _create_node_for_item(
        self,
        item: "CanvasItem",
        offset_x: float,
        offset_y: float,
        window: object,
        texture_cache: TextureCache,
    ) -> Optional[QSGNode]:
        """Create texture node for item, wrapped in transform node if needed."""
        from lucent.canvas_items import GroupItem

        if hasattr(item, "visible") and not item.visible:
            return None

        # Groups don't render directly (they're organizational containers)
        if isinstance(item, GroupItem):
            return None

        item_id = item.id if hasattr(item, "id") else str(id(item))
        cache_entry = texture_cache.get_or_create(item, item_id, self._zoom_level)

        if not cache_entry:
            return None

        texture = window.createTextureFromImage(cache_entry.image)  # type: ignore[attr-defined]
        if not texture:
            return None

        self._textures.append(texture)

        tex_node = QSGSimpleTextureNode()
        tex_node.setTexture(texture)

        tex_offset = texture_cache.get_texture_offset(cache_entry)
        tex_size = texture_cache.get_texture_size(cache_entry)

        tex_node.setRect(
            QRectF(
                tex_offset[0] + offset_x,
                tex_offset[1] + offset_y,
                tex_size[0],
                tex_size[1],
            )
        )

        self._texture_nodes.append(tex_node)

        if (
            hasattr(item, "transform")
            and item.transform
            and not item.transform.is_identity()
        ):
            transform_node = self._create_transform_wrapper(
                item, tex_node, offset_x, offset_y, cache_entry.bounds
            )
            if transform_node:
                return transform_node

        return tex_node

    def _create_transform_wrapper(
        self,
        item: "CanvasItem",
        child_node: QSGNode,
        offset_x: float,
        offset_y: float,
        geometry_bounds: QRectF,
    ) -> Optional[QSGTransformNode]:
        """Wrap node in QSGTransformNode for GPU-accelerated transforms."""
        transform = item.transform

        origin_x = transform.pivot_x + offset_x
        origin_y = transform.pivot_y + offset_y

        matrix = transform.to_qmatrix4x4_centered(origin_x, origin_y)

        transform_node = QSGTransformNode()
        transform_node.setMatrix(matrix)
        transform_node.appendChildNode(child_node)
        self._transform_nodes.append(transform_node)

        return transform_node

    @Property(float, notify=zoomLevelChanged)
    def zoomLevel(self) -> float:
        return self._zoom_level

    @zoomLevel.setter  # type: ignore[no-redef]
    def zoomLevel(self, value: float) -> None:
        if self._zoom_level != value:
            self._zoom_level = value
            self.zoomLevelChanged.emit()
            self._needs_full_rebuild = True
            self.update()

    @Property(float, notify=tileOriginChanged)
    def tileOriginX(self) -> float:
        return self._tile_origin_x

    @tileOriginX.setter  # type: ignore[no-redef]
    def tileOriginX(self, value: float) -> None:
        if self._tile_origin_x != value:
            self._tile_origin_x = value
            self.tileOriginChanged.emit()
            self._needs_full_rebuild = True
            self.update()

    @Property(float, notify=tileOriginChanged)
    def tileOriginY(self) -> float:
        return self._tile_origin_y

    @tileOriginY.setter  # type: ignore[no-redef]
    def tileOriginY(self, value: float) -> None:
        if self._tile_origin_y != value:
            self._tile_origin_y = value
            self.tileOriginChanged.emit()
            self._needs_full_rebuild = True
            self.update()
