# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Texture cache for GPU-accelerated rendering.

Rasterizes canvas items to textures (QImage) which can then be displayed
on the GPU using QSGSimpleTextureNode. This allows transforms to be applied
on the GPU without re-rasterizing the shape.

Key benefits:
- Non-destructive transforms apply as GPU matrix operations (fast)
- Only re-rasterize when appearance changes (fill, stroke, geometry resize)
- Smooth pan/zoom/rotate/scale during interaction
"""

from typing import Dict, Optional, Tuple, TYPE_CHECKING
from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage, QPainter, QColor

if TYPE_CHECKING:
    from lucent.canvas_items import CanvasItem


class TextureCacheEntry:
    """Cached texture for a single canvas item."""

    def __init__(
        self,
        image: QImage,
        bounds: QRectF,
        item_version: int,
        padding: float = 4.0,
    ) -> None:
        self.image = image
        self.bounds = bounds
        self.item_version = item_version
        self.padding = padding

    @property
    def width(self) -> int:
        return self.image.width()

    @property
    def height(self) -> int:
        return self.image.height()


class TextureCache:
    """Cache of rasterized item textures for GPU rendering.

    Items are rasterized at a base scale, then GPU transforms handle
    rotation, scaling, and translation without re-rasterization.
    """

    # Padding around shapes to prevent clipping during rotation
    PADDING = 4

    # Scale factor for high-DPI rendering (2x for retina-quality)
    RENDER_SCALE = 2.0

    def __init__(self) -> None:
        self._cache: Dict[str, TextureCacheEntry] = {}
        self._item_versions: Dict[str, int] = {}

    def get_or_create(
        self,
        item: "CanvasItem",
        item_id: str,
    ) -> Optional[TextureCacheEntry]:
        """Get cached texture or create a new one.

        Returns None for items that can't be textured (layers, groups, etc.)
        """
        from lucent.canvas_items import ShapeItem, TextItem

        if not isinstance(item, (ShapeItem, TextItem)):
            return None

        current_version = self._get_item_version(item)
        cached = self._cache.get(item_id)

        if cached and cached.item_version == current_version:
            return cached

        entry = self._rasterize_item(item, current_version)
        if entry:
            self._cache[item_id] = entry
            self._item_versions[item_id] = current_version

        return entry

    def invalidate(self, item_id: str) -> None:
        """Invalidate cached texture for an item."""
        self._cache.pop(item_id, None)
        self._item_versions.pop(item_id, None)

    def clear(self) -> None:
        """Clear all cached textures."""
        self._cache.clear()
        self._item_versions.clear()

    def _get_item_version(self, item: "CanvasItem") -> int:
        """Compute version hash based on geometry and appearance.

        Transform changes don't invalidate since GPU handles transforms.
        """
        version = 0

        if hasattr(item, "geometry"):
            bounds = item.geometry.get_bounds()
            version ^= hash((bounds.x(), bounds.y(), bounds.width(), bounds.height()))

        if hasattr(item, "fill") and item.fill:
            version ^= hash(item.fill.color)

        if hasattr(item, "stroke") and item.stroke:
            align = getattr(item.stroke, "align", "center")
            version ^= hash((item.stroke.color, item.stroke.width, align))

        return version

    def _rasterize_item(
        self,
        item: "CanvasItem",
        version: int,
    ) -> Optional[TextureCacheEntry]:
        """Rasterize item to QImage. GPU applies transforms separately."""
        from lucent.canvas_items import ShapeItem, TextItem
        from lucent.transforms import Transform

        if not isinstance(item, (ShapeItem, TextItem)):
            return None

        bounds = item.geometry.get_bounds()
        if bounds.isEmpty():
            return None

        padding = float(self.PADDING)
        stroke = getattr(item, "stroke", None)
        if stroke and stroke.visible and stroke.width > 0:
            align = getattr(stroke, "align", "center")
            if align == "outer":
                padding = max(padding, stroke.width + self.PADDING)
            elif align == "center":
                padding = max(padding, stroke.width / 2 + self.PADDING)

        scale = self.RENDER_SCALE

        tex_width = max(int((bounds.width() + padding * 2) * scale), 4)
        tex_height = max(int((bounds.height() + padding * 2) * scale), 4)

        image = QImage(tex_width, tex_height, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(QColor(0, 0, 0, 0))

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.scale(scale, scale)
        painter.translate(padding - bounds.x(), padding - bounds.y())

        original_transform = item.transform
        item.transform = Transform()

        try:
            item.paint(painter, zoom_level=1.0, offset_x=0.0, offset_y=0.0)
        finally:
            item.transform = original_transform

        painter.end()

        return TextureCacheEntry(
            image=image,
            bounds=bounds,
            item_version=version,
            padding=padding,
        )

    def get_texture_offset(self, entry: TextureCacheEntry) -> Tuple[float, float]:
        """Position offset accounting for padding around the shape."""
        return (
            entry.bounds.x() - entry.padding,
            entry.bounds.y() - entry.padding,
        )

    def get_texture_size(self, entry: TextureCacheEntry) -> Tuple[float, float]:
        """Display size accounting for render scale."""
        return (
            entry.width / self.RENDER_SCALE,
            entry.height / self.RENDER_SCALE,
        )
