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
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QImage, QPainter, QColor, QPainterPathStroker

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
        zoom_level: float = 1.0,
    ) -> Optional[TextureCacheEntry]:
        """Get cached texture or create a new one.

        Returns None for items that can't be textured (groups, etc.)
        """
        from lucent.canvas_items import ArtboardItem, ShapeItem, TextItem

        if not isinstance(item, (ShapeItem, TextItem, ArtboardItem)):
            return None

        current_version = self._get_item_version(item, zoom_level)
        cached = self._cache.get(item_id)

        if cached and cached.item_version == current_version:
            return cached

        entry = self._rasterize_item(item, current_version, zoom_level)
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

    def _get_item_version(self, item: "CanvasItem", zoom_level: float) -> int:
        """Compute version hash based on geometry and appearance.

        Transform changes don't invalidate since GPU handles transforms.
        """
        from lucent.canvas_items import ArtboardItem

        version = 0

        # Artboards have simple x, y, width, height
        if isinstance(item, ArtboardItem):
            stroke_width = 2.0 / max(float(zoom_level), 1e-6)
            return hash((item.x, item.y, item.width, item.height, stroke_width))

        if hasattr(item, "geometry"):
            bounds = item.geometry.get_bounds()
            version ^= hash((bounds.x(), bounds.y(), bounds.width(), bounds.height()))

        if hasattr(item, "fill") and item.fill:
            version ^= hash(item.fill.color)

        if hasattr(item, "stroke") and item.stroke:
            align = getattr(item.stroke, "align", "center")
            cap = getattr(item.stroke, "cap", "butt")
            order = getattr(item.stroke, "order", "top")
            scale_with_object = getattr(item.stroke, "scale_with_object", False)
            version ^= hash(
                (
                    item.stroke.color,
                    item.stroke.width,
                    cap,
                    align,
                    order,
                    scale_with_object,
                )
            )
            if not scale_with_object and hasattr(item, "transform"):
                version ^= hash((item.transform.scale_x, item.transform.scale_y))

        return version

    def _get_render_bounds(self, item: "CanvasItem") -> QRectF:
        """Get bounds needed to render item including all stroke effects.

        Uses QPainterPathStroker to compute accurate stroked bounds,
        automatically accounting for width, cap, join, and alignment.
        """
        from lucent.appearances import Stroke
        from lucent.canvas_items import ArtboardItem

        # Artboards have simple bounds
        if isinstance(item, ArtboardItem):
            return QRectF(item.x, item.y, item.width, item.height)

        geometry_bounds = item.geometry.get_bounds()
        stroke = getattr(item, "stroke", None)

        if not stroke or not stroke.visible or stroke.width <= 0:
            return geometry_bounds

        path = item.geometry.to_painter_path()

        # Configure stroker with all stroke properties
        stroker = QPainterPathStroker()
        align = getattr(stroke, "align", "center")

        # For inner/outer alignment, we draw double-width strokes then clip
        if align == "outer":
            stroker.setWidth(stroke.width * 2)
        elif align == "inner":
            # Inner stroke stays within geometry bounds
            return geometry_bounds
        else:
            stroker.setWidth(stroke.width)

        stroker.setCapStyle(Stroke.CAP_STYLES.get(stroke.cap, Qt.PenCapStyle.FlatCap))
        stroker.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        stroker.setMiterLimit(100.0)

        stroked_path = stroker.createStroke(path)
        return stroked_path.boundingRect()

    def _rasterize_item(
        self,
        item: "CanvasItem",
        version: int,
        zoom_level: float,
    ) -> Optional[TextureCacheEntry]:
        """Rasterize item to QImage. GPU applies transforms separately."""
        from lucent.canvas_items import ArtboardItem, ShapeItem, TextItem
        from lucent.transforms import Transform

        if not isinstance(item, (ShapeItem, TextItem, ArtboardItem)):
            return None

        # Handle artboards specially - they have direct x, y, width, height
        if isinstance(item, ArtboardItem):
            return self._rasterize_artboard(item, version, zoom_level)

        geometry_bounds = item.geometry.get_bounds()
        if geometry_bounds.isEmpty():
            return None

        stroke = getattr(item, "stroke", None)
        stroke_ref = None
        original_stroke_width = None
        if stroke and not getattr(stroke, "scale_with_object", False):
            scale_x = getattr(item.transform, "scale_x", 1.0)
            scale_y = getattr(item.transform, "scale_y", 1.0)
            scale_factor = max(abs(scale_x), abs(scale_y), 1e-6)
            original_stroke_width = stroke.width
            stroke.width = max(0.0, min(100.0, original_stroke_width / scale_factor))
            stroke_ref = stroke

        # Get accurate bounds including stroke effects
        render_bounds = self._get_render_bounds(item)

        # Minimal padding for antialiasing
        padding = float(self.PADDING)

        scale = self.RENDER_SCALE

        tex_width = max(int((render_bounds.width() + padding * 2) * scale), 4)
        tex_height = max(int((render_bounds.height() + padding * 2) * scale), 4)

        image = QImage(tex_width, tex_height, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(QColor(0, 0, 0, 0))

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.scale(scale, scale)
        painter.translate(padding - render_bounds.x(), padding - render_bounds.y())

        original_transform = item.transform
        item.transform = Transform()

        try:
            item.paint(painter, zoom_level=1.0, offset_x=0.0, offset_y=0.0)
        finally:
            item.transform = original_transform
            if original_stroke_width is not None and stroke_ref is not None:
                stroke_ref.width = original_stroke_width

        painter.end()

        return TextureCacheEntry(
            image=image,
            bounds=render_bounds,
            item_version=version,
            padding=padding,
        )

    def _rasterize_artboard(
        self,
        item: "CanvasItem",
        version: int,
        zoom_level: float,
    ) -> TextureCacheEntry:
        """Rasterize artboard as transparent rectangle with 2pt outer border."""
        from PySide6.QtGui import QPen
        from PySide6.QtCore import Qt

        stroke_width = 2.0 / max(float(zoom_level), 1e-6)
        # Expand bounds to include outer stroke (stroke is outside the artboard)
        render_bounds = QRectF(
            item.x - stroke_width,
            item.y - stroke_width,
            item.width + stroke_width * 2,
            item.height + stroke_width * 2,
        )
        padding = float(self.PADDING)
        scale = self.RENDER_SCALE

        tex_width = max(int((render_bounds.width() + padding * 2) * scale), 4)
        tex_height = max(int((render_bounds.height() + padding * 2) * scale), 4)

        image = QImage(tex_width, tex_height, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(QColor(0, 0, 0, 0))

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.scale(scale, scale)
        # Translate to account for stroke expansion + padding
        painter.translate(padding + stroke_width, padding + stroke_width)

        # Draw 2pt outer border using themed editSelector color
        pen = QPen(QColor("#fc03d2"))
        pen.setWidthF(stroke_width)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        half = stroke_width / 2
        painter.drawRect(
            QRectF(-half, -half, item.width + stroke_width, item.height + stroke_width)
        )

        painter.end()

        return TextureCacheEntry(
            image=image,
            bounds=render_bounds,
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
