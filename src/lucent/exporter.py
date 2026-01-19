# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Export functionality for Lucent - exports artboards to PNG and SVG."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING, Union

from PySide6.QtCore import QMarginsF, QRect, QRectF, QSize, QSizeF
from PySide6.QtGui import (
    QImage,
    QPainter,
    QColor,
    QPdfWriter,
    QPageSize,
    QPageLayout,
    QImageWriter,
)
from PySide6.QtSvg import QSvgGenerator

if TYPE_CHECKING:
    from lucent.canvas_items import CanvasItem


@dataclass
class ExportOptions:
    """Configuration options for export operations."""

    document_dpi: int = 72
    target_dpi: int = 72
    padding: float = 0.0
    background: Optional[str] = None

    @property
    def scale(self) -> float:
        """Compute scale factor from DPI ratio."""
        return self.target_dpi / self.document_dpi


def compute_bounds(items: List["CanvasItem"], padding: float = 0.0) -> QRectF:
    """Compute combined bounding box of all items with optional padding."""
    if not items:
        return QRectF()

    combined = QRectF()
    for item in items:
        item_bounds = item.get_bounds()
        if not item_bounds.isEmpty():
            if combined.isEmpty():
                combined = item_bounds
            else:
                combined = combined.united(item_bounds)

    if combined.isEmpty():
        return QRectF()

    if padding > 0:
        combined = QRectF(
            combined.x() - padding,
            combined.y() - padding,
            combined.width() + 2 * padding,
            combined.height() + 2 * padding,
        )

    return combined


def export_png(
    items: List["CanvasItem"],
    bounds: QRectF,
    path: Union[str, Path],
    options: ExportOptions,
) -> bool:
    """Export items to a PNG file.

    Args:
        items: List of canvas items to render
        bounds: Bounding rectangle in canvas coordinates
        path: Output file path
        options: Export options (scale, background, etc.)

    Returns:
        True if export succeeded, False on error
    """
    if bounds.isEmpty():
        return False

    width = int(bounds.width() * options.scale)
    height = int(bounds.height() * options.scale)
    if width <= 0 or height <= 0:
        return False

    image = QImage(width, height, QImage.Format.Format_ARGB32)
    if options.background:
        image.fill(QColor(options.background))
    else:
        image.fill(QColor(0, 0, 0, 0))

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.scale(options.scale, options.scale)
    painter.translate(-bounds.x(), -bounds.y())

    for item in items:
        try:
            item.paint(painter, zoom_level=1.0, offset_x=0, offset_y=0)
        except Exception:
            pass

    painter.end()

    try:
        return image.save(str(path))
    except Exception:
        return False


def export_jpg(
    items: List["CanvasItem"],
    bounds: QRectF,
    path: Union[str, Path],
    options: ExportOptions,
) -> bool:
    """Export items to a JPG file (opaque)."""
    if bounds.isEmpty():
        return False

    width = int(bounds.width() * options.scale)
    height = int(bounds.height() * options.scale)
    if width <= 0 or height <= 0:
        return False

    image = QImage(width, height, QImage.Format.Format_RGB32)
    image.fill(QColor(options.background or "#ffffff"))

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.scale(options.scale, options.scale)
    painter.translate(-bounds.x(), -bounds.y())

    for item in items:
        try:
            item.paint(painter, zoom_level=1.0, offset_x=0, offset_y=0)
        except Exception:
            pass

    painter.end()

    try:
        writer = QImageWriter(str(path), b"jpg")
        return writer.write(image)
    except Exception:
        return False


def export_pdf(
    items: List["CanvasItem"],
    bounds: QRectF,
    path: Union[str, Path],
    options: ExportOptions,
) -> bool:
    """Export items to a PDF file."""
    if bounds.isEmpty():
        return False

    width = int(bounds.width() * options.scale)
    height = int(bounds.height() * options.scale)
    if width <= 0 or height <= 0:
        return False

    writer = QPdfWriter(str(path))
    writer.setResolution(int(options.target_dpi))
    width_points = width * 72.0 / options.target_dpi
    height_points = height * 72.0 / options.target_dpi
    page_size = QPageSize(QSizeF(width_points, height_points), QPageSize.Unit.Point)
    writer.setPageSize(page_size)
    writer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Point)

    painter = QPainter(writer)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.scale(options.scale, options.scale)
    painter.translate(-bounds.x(), -bounds.y())

    if options.background:
        painter.fillRect(bounds, QColor(options.background))

    for item in items:
        try:
            item.paint(painter, zoom_level=1.0, offset_x=0, offset_y=0)
        except Exception:
            pass

    painter.end()
    return True


def export_svg(
    items: List["CanvasItem"],
    bounds: QRectF,
    path: Union[str, Path],
    options: ExportOptions,
) -> bool:
    """Export items to an SVG file.

    Args:
        items: List of canvas items to render
        bounds: Bounding rectangle in canvas coordinates
        path: Output file path
        options: Export options

    Returns:
        True if export succeeded, False on error
    """
    if bounds.isEmpty():
        return False

    width = int(bounds.width())
    height = int(bounds.height())
    if width <= 0 or height <= 0:
        return False

    generator = QSvgGenerator()
    generator.setFileName(str(path))
    generator.setResolution(int(options.target_dpi))
    generator.setSize(QSize(width, height))
    generator.setViewBox(QRect(0, 0, width, height))

    painter = QPainter(generator)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.translate(-bounds.x(), -bounds.y())

    if options.background:
        painter.fillRect(bounds, QColor(options.background))

    for item in items:
        try:
            item.paint(painter, zoom_level=1.0, offset_x=0, offset_y=0)
        except Exception:
            pass

    painter.end()
    return True
