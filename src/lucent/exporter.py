# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Export functionality for Lucent - exports layers to PNG and SVG."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING, Union

from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage, QPainter, QColor

if TYPE_CHECKING:
    from lucent.canvas_items import CanvasItem

SVG_NS = "http://www.w3.org/2000/svg"


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


def _item_to_svg_element(item: "CanvasItem") -> Optional[ET.Element]:
    """Convert a canvas item to an SVG element."""
    from lucent.canvas_items import (
        RectangleItem,
        EllipseItem,
        PathItem,
        TextItem,
    )

    if isinstance(item, RectangleItem):
        geom = item.geometry
        tl, tr, br, bl = geom.effective_corner_radii_pixels
        stroke = item.stroke
        fill = item.fill

        if tl == tr == br == bl:
            # Uniform corners - use rect element
            elem = ET.Element("rect")
            elem.set("x", str(geom.x))
            elem.set("y", str(geom.y))
            elem.set("width", str(geom.width))
            elem.set("height", str(geom.height))
            if tl > 0:
                elem.set("rx", str(tl))
                elem.set("ry", str(tl))
        else:
            # Per-corner radii - use path element
            elem = ET.Element("path")
            x, y, w, h = geom.x, geom.y, geom.width, geom.height
            d_parts = [f"M {x + tl} {y}"]
            d_parts.append(f"L {x + w - tr} {y}")
            if tr > 0:
                d_parts.append(f"A {tr} {tr} 0 0 1 {x + w} {y + tr}")
            d_parts.append(f"L {x + w} {y + h - br}")
            if br > 0:
                d_parts.append(f"A {br} {br} 0 0 1 {x + w - br} {y + h}")
            d_parts.append(f"L {x + bl} {y + h}")
            if bl > 0:
                d_parts.append(f"A {bl} {bl} 0 0 1 {x} {y + h - bl}")
            d_parts.append(f"L {x} {y + tl}")
            if tl > 0:
                d_parts.append(f"A {tl} {tl} 0 0 1 {x + tl} {y}")
            d_parts.append("Z")
            elem.set("d", " ".join(d_parts))

        elem.set("stroke", stroke.color if stroke else "none")
        elem.set("stroke-width", str(stroke.width if stroke else 0))
        elem.set("stroke-opacity", str(stroke.opacity if stroke else 0))
        elem.set("fill", fill.color if fill else "none")
        elem.set("fill-opacity", str(fill.opacity if fill else 0))
        return elem

    if isinstance(item, EllipseItem):
        elem = ET.Element("ellipse")
        elem.set("cx", str(item.geometry.center_x))
        elem.set("cy", str(item.geometry.center_y))
        elem.set("rx", str(item.geometry.radius_x))
        elem.set("ry", str(item.geometry.radius_y))
        stroke = item.stroke
        fill = item.fill
        elem.set("stroke", stroke.color if stroke else "none")
        elem.set("stroke-width", str(stroke.width if stroke else 0))
        elem.set("stroke-opacity", str(stroke.opacity if stroke else 0))
        elem.set("fill", fill.color if fill else "none")
        elem.set("fill-opacity", str(fill.opacity if fill else 0))
        return elem

    if isinstance(item, PathItem):
        elem = ET.Element("path")
        points = item.geometry.points
        if points:
            d_parts = [f"M {points[0]['x']} {points[0]['y']}"]
            for p in points[1:]:
                d_parts.append(f"L {p['x']} {p['y']}")
            if item.geometry.closed:
                d_parts.append("Z")
            elem.set("d", " ".join(d_parts))
        stroke = item.stroke
        fill = item.fill
        fill_opacity = fill.opacity if fill else 0
        elem.set("stroke", stroke.color if stroke else "none")
        elem.set("stroke-width", str(stroke.width if stroke else 0))
        elem.set("stroke-opacity", str(stroke.opacity if stroke else 0))
        elem.set("fill", fill.color if fill and fill_opacity > 0 else "none")
        elem.set("fill-opacity", str(fill_opacity))
        return elem

    if isinstance(item, TextItem):
        elem = ET.Element("text")
        elem.set("x", str(item.x))
        elem.set("y", str(item.y + item.font_size))  # SVG text y is baseline
        elem.set("font-family", item.font_family)
        elem.set("font-size", str(item.font_size))
        elem.set("fill", item.text_color)
        elem.set("fill-opacity", str(item.text_opacity))
        elem.text = item.text
        return elem

    return None


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

    ET.register_namespace("", SVG_NS)
    svg = ET.Element("svg")
    svg.set("xmlns", SVG_NS)
    viewbox = (
        f"{int(bounds.x())} {int(bounds.y())} "
        f"{int(bounds.width())} {int(bounds.height())}"
    )
    svg.set("viewBox", viewbox)
    svg.set("width", str(bounds.width()))
    svg.set("height", str(bounds.height()))

    if options.background:
        bg = ET.Element("rect")
        bg.set("x", str(bounds.x()))
        bg.set("y", str(bounds.y()))
        bg.set("width", str(bounds.width()))
        bg.set("height", str(bounds.height()))
        bg.set("fill", options.background)
        svg.append(bg)

    for item in items:
        elem = _item_to_svg_element(item)
        if elem is not None:
            svg.append(elem)

    try:
        tree = ET.ElementTree(svg)
        tree.write(str(path), encoding="unicode", xml_declaration=True)
        return True
    except Exception:
        return False
