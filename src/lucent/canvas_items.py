"""
Canvas item classes for Lucent.

This module defines the canvas item hierarchy, including:
- CanvasItem: Abstract base class for all drawable items
- RectangleItem: Rectangular shapes
- EllipseItem: Elliptical shapes
- LayerItem: Organizational layers for grouping items

All items use QPainter for rendering and support stroke/fill styling.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import uuid
from PySide6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QColor,
    QPainterPath,
    QFont,
    QFontMetricsF,
)
from PySide6.QtCore import QRectF, Qt, QPointF

# Canvas coordinate system defaults.
# Renderers typically pass dynamic offsets (width/2, height/2) so these serve
# as fallbacks for tests and any non-viewport-based usage.
CANVAS_OFFSET_X = 5000
CANVAS_OFFSET_Y = 5000


class CanvasItem(ABC):
    """Base class for all canvas items"""

    @abstractmethod
    def paint(
        self,
        painter: QPainter,
        zoom_level: float,
        offset_x: float = CANVAS_OFFSET_X,
        offset_y: float = CANVAS_OFFSET_Y,
    ) -> None:
        """Paint this item using the provided QPainter"""
        pass

    @staticmethod
    @abstractmethod
    def from_dict(data: Dict[str, Any]) -> "CanvasItem":
        """Factory method to create item from QML data dictionary"""
        pass


class RectangleItem(CanvasItem):
    """Rectangle canvas item"""

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        stroke_width: float = 1,
        stroke_color: str = "#ffffff",
        fill_color: str = "#ffffff",
        fill_opacity: float = 0.0,
        stroke_opacity: float = 1.0,
        name: str = "",
        parent_id: Optional[str] = None,
        visible: bool = True,
        locked: bool = False,
    ) -> None:
        self.name = name
        self.parent_id = parent_id  # ID of parent layer, or None if top-level
        self.visible = bool(visible)
        self.locked = bool(locked)
        self.x = x
        self.y = y
        # Validate dimensions (must be non-negative)
        self.width = max(0.0, width)
        self.height = max(0.0, height)
        # Validate stroke width (must be positive, clamped to reasonable range)
        self.stroke_width = max(0.1, min(100.0, stroke_width))
        self.stroke_color = stroke_color
        # Validate stroke opacity (must be in range 0.0-1.0)
        self.stroke_opacity = max(0.0, min(1.0, stroke_opacity))
        self.fill_color = fill_color
        # Validate fill opacity (must be in range 0.0-1.0)
        self.fill_opacity = max(0.0, min(1.0, fill_opacity))

    def paint(
        self,
        painter: QPainter,
        zoom_level: float,
        offset_x: float = CANVAS_OFFSET_X,
        offset_y: float = CANVAS_OFFSET_Y,
    ) -> None:
        """Render this rectangle using QPainter"""
        local_x = self.x + offset_x
        local_y = self.y + offset_y

        # Keep stroke width in world space, but clamp screen size at extremes.
        stroke_px = self.stroke_width * zoom_level
        clamped_px = max(0.3, min(6.0, stroke_px))
        scaled_stroke_width = clamped_px / max(zoom_level, 0.0001)

        # Set up pen for stroke
        stroke_qcolor = QColor(self.stroke_color)
        stroke_qcolor.setAlphaF(self.stroke_opacity)
        pen = QPen(stroke_qcolor)
        pen.setWidthF(scaled_stroke_width)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)

        # Set up brush for fill
        fill_qcolor = QColor(self.fill_color)
        fill_qcolor.setAlphaF(self.fill_opacity)
        brush = QBrush(fill_qcolor)
        painter.setBrush(brush)

        # Draw rectangle
        painter.drawRect(QRectF(local_x, local_y, self.width, self.height))

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "RectangleItem":
        """Create RectangleItem from QML data dictionary"""
        # Extract and validate dimensions (must be non-negative)
        width = max(0.0, float(data.get("width", 0)))
        height = max(0.0, float(data.get("height", 0)))

        # Extract stroke width (positive, clamped to a reasonable range)
        stroke_width = max(0.1, min(100.0, float(data.get("strokeWidth", 1))))

        # Extract and validate stroke opacity (must be in range 0.0-1.0)
        stroke_opacity = max(0.0, min(1.0, float(data.get("strokeOpacity", 1.0))))

        # Extract and validate fill opacity (must be in range 0.0-1.0)
        fill_opacity = max(0.0, min(1.0, float(data.get("fillOpacity", 0.0))))

        return RectangleItem(
            x=float(data.get("x", 0)),
            y=float(data.get("y", 0)),
            width=width,
            height=height,
            stroke_width=stroke_width,
            stroke_color=data.get("strokeColor", "#ffffff"),
            fill_color=data.get("fillColor", "#ffffff"),
            fill_opacity=fill_opacity,
            stroke_opacity=stroke_opacity,
            name=data.get("name", ""),
            parent_id=data.get("parentId"),
            visible=data.get("visible", True),
            locked=data.get("locked", False),
        )


class EllipseItem(CanvasItem):
    """Ellipse canvas item"""

    def __init__(
        self,
        center_x: float,
        center_y: float,
        radius_x: float,
        radius_y: float,
        stroke_width: float = 1,
        stroke_color: str = "#ffffff",
        fill_color: str = "#ffffff",
        fill_opacity: float = 0.0,
        stroke_opacity: float = 1.0,
        name: str = "",
        parent_id: Optional[str] = None,
        visible: bool = True,
        locked: bool = False,
    ) -> None:
        self.name = name
        self.parent_id = parent_id  # ID of parent layer, or None if top-level
        self.visible = bool(visible)
        self.locked = bool(locked)
        self.center_x = center_x
        self.center_y = center_y
        # Validate radii (must be non-negative)
        self.radius_x = max(0.0, radius_x)
        self.radius_y = max(0.0, radius_y)
        # Validate stroke width (must be positive, clamped to reasonable range)
        self.stroke_width = max(0.1, min(100.0, stroke_width))
        self.stroke_color = stroke_color
        # Validate stroke opacity (must be in range 0.0-1.0)
        self.stroke_opacity = max(0.0, min(1.0, stroke_opacity))
        self.fill_color = fill_color
        # Validate fill opacity (must be in range 0.0-1.0)
        self.fill_opacity = max(0.0, min(1.0, fill_opacity))

    def paint(
        self,
        painter: QPainter,
        zoom_level: float,
        offset_x: float = CANVAS_OFFSET_X,
        offset_y: float = CANVAS_OFFSET_Y,
    ) -> None:
        """Render this ellipse using QPainter"""
        local_center_x = self.center_x + offset_x
        local_center_y = self.center_y + offset_y

        # Keep stroke width in world space, but clamp screen size at extremes.
        stroke_px = self.stroke_width * zoom_level
        clamped_px = max(0.3, min(6.0, stroke_px))
        scaled_stroke_width = clamped_px / max(zoom_level, 0.0001)

        # Set up pen for stroke
        stroke_qcolor = QColor(self.stroke_color)
        stroke_qcolor.setAlphaF(self.stroke_opacity)
        pen = QPen(stroke_qcolor)
        pen.setWidthF(scaled_stroke_width)
        painter.setPen(pen)

        # Set up brush for fill
        fill_qcolor = QColor(self.fill_color)
        fill_qcolor.setAlphaF(self.fill_opacity)
        brush = QBrush(fill_qcolor)
        painter.setBrush(brush)

        # Draw ellipse (QRectF defines bounding box)
        painter.drawEllipse(
            QRectF(
                local_center_x - self.radius_x,
                local_center_y - self.radius_y,
                2 * self.radius_x,
                2 * self.radius_y,
            )
        )

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "EllipseItem":
        """Create EllipseItem from QML data dictionary"""
        # Extract and validate radii (must be non-negative)
        radius_x = max(0.0, float(data.get("radiusX", 0)))
        radius_y = max(0.0, float(data.get("radiusY", 0)))

        # Extract stroke width (positive, clamped to a reasonable range)
        stroke_width = max(0.1, min(100.0, float(data.get("strokeWidth", 1))))

        # Extract and validate stroke opacity (must be in range 0.0-1.0)
        stroke_opacity = max(0.0, min(1.0, float(data.get("strokeOpacity", 1.0))))

        # Extract and validate fill opacity (must be in range 0.0-1.0)
        fill_opacity = max(0.0, min(1.0, float(data.get("fillOpacity", 0.0))))

        return EllipseItem(
            center_x=float(data.get("centerX", 0)),
            center_y=float(data.get("centerY", 0)),
            radius_x=radius_x,
            radius_y=radius_y,
            stroke_width=stroke_width,
            stroke_color=data.get("strokeColor", "#ffffff"),
            fill_color=data.get("fillColor", "#ffffff"),
            fill_opacity=fill_opacity,
            stroke_opacity=stroke_opacity,
            name=data.get("name", ""),
            parent_id=data.get("parentId"),
            visible=data.get("visible", True),
            locked=data.get("locked", False),
        )


class PathItem(CanvasItem):
    """Polyline/path canvas item rendered as stroke with optional fill."""

    def __init__(
        self,
        points: List[Dict[str, float]],
        stroke_width: float = 1,
        stroke_color: str = "#ffffff",
        stroke_opacity: float = 1.0,
        fill_color: str = "#ffffff",
        fill_opacity: float = 0.0,
        closed: bool = False,
        name: str = "",
        parent_id: Optional[str] = None,
        visible: bool = True,
        locked: bool = False,
    ) -> None:
        if len(points) < 2:
            raise ValueError("PathItem requires at least two points")
        self.name = name
        self.parent_id = parent_id
        self.visible = bool(visible)
        self.locked = bool(locked)

        # Normalize points to float tuples
        normalized: List[Dict[str, float]] = []
        for p in points:
            normalized.append({"x": float(p.get("x", 0)), "y": float(p.get("y", 0))})
        self.points = normalized
        self.closed = bool(closed)

        # Validate stroke values
        self.stroke_width = max(0.1, min(100.0, stroke_width))
        self.stroke_color = stroke_color
        self.stroke_opacity = max(0.0, min(1.0, stroke_opacity))

        # Optional fill (defaults to stroke-only)
        self.fill_color = fill_color
        self.fill_opacity = max(0.0, min(1.0, fill_opacity))

    def paint(
        self,
        painter: QPainter,
        zoom_level: float,
        offset_x: float = CANVAS_OFFSET_X,
        offset_y: float = CANVAS_OFFSET_Y,
    ) -> None:
        """Render the polyline/path."""
        # Keep stroke width in world space, clamped similar to other shapes
        stroke_px = self.stroke_width * zoom_level
        clamped_px = max(0.3, min(6.0, stroke_px))
        scaled_stroke_width = clamped_px / max(zoom_level, 0.0001)

        stroke_qcolor = QColor(self.stroke_color)
        stroke_qcolor.setAlphaF(self.stroke_opacity)
        pen = QPen(stroke_qcolor)
        pen.setWidthF(scaled_stroke_width)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        fill_qcolor = QColor(self.fill_color)
        fill_qcolor.setAlphaF(self.fill_opacity)
        painter.setBrush(QBrush(fill_qcolor))

        # Build path
        if not self.points:
            return
        first = self.points[0]
        path = QPainterPath(QPointF(first["x"] + offset_x, first["y"] + offset_y))
        for p in self.points[1:]:
            path.lineTo(p["x"] + offset_x, p["y"] + offset_y)
        if self.closed:
            path.closeSubpath()
        painter.drawPath(path)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PathItem":
        """Create PathItem from QML data dictionary."""
        points = data.get("points") or []
        if not isinstance(points, list):
            raise ValueError("Path points must be a list")
        stroke_width = max(0.1, min(100.0, float(data.get("strokeWidth", 1))))
        stroke_opacity = max(0.0, min(1.0, float(data.get("strokeOpacity", 1.0))))
        fill_opacity = max(0.0, min(1.0, float(data.get("fillOpacity", 0.0))))
        return PathItem(
            points=points,
            stroke_width=stroke_width,
            stroke_color=data.get("strokeColor", "#ffffff"),
            stroke_opacity=stroke_opacity,
            fill_color=data.get("fillColor", "#ffffff"),
            fill_opacity=fill_opacity,
            closed=bool(data.get("closed", False)),
            name=data.get("name", ""),
            parent_id=data.get("parentId"),
            visible=data.get("visible", True),
            locked=data.get("locked", False),
        )


class LayerItem(CanvasItem):
    """Layer item for organizing canvas items.

    Layers provide a way to group and organize items for Z-ordering.
    They don't render directly but serve as organizational containers.
    Each layer has a unique ID that child items reference via parent_id.
    """

    def __init__(
        self,
        name: str = "",
        layer_id: Optional[str] = None,
        visible: bool = True,
        locked: bool = False,
    ) -> None:
        self.name = name
        self.visible = bool(visible)
        self.locked = bool(locked)
        # Generate unique ID if not provided (for new layers)
        self.id = layer_id if layer_id else str(uuid.uuid4())

    def paint(
        self,
        painter: QPainter,
        zoom_level: float,
        offset_x: float = CANVAS_OFFSET_X,
        offset_y: float = CANVAS_OFFSET_Y,
    ) -> None:
        """Layers don't render directly - they are organizational containers."""
        pass

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "LayerItem":
        """Create LayerItem from QML data dictionary."""
        return LayerItem(
            name=data.get("name", ""),
            layer_id=data.get("id"),
            visible=data.get("visible", True),
            locked=data.get("locked", False),
        )


class GroupItem(CanvasItem):
    """Group item for nesting shapes or other groups under a parent container.

    Groups are non-rendering; they carry visibility/locking state and an ID for
    parent-child relationships. A group can be parented to a layer or another
    group. Rendering skips groups; only leaf shapes paint.
    """

    def __init__(
        self,
        name: str = "",
        group_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        visible: bool = True,
        locked: bool = False,
    ) -> None:
        self.name = name
        self.visible = bool(visible)
        self.locked = bool(locked)
        self.parent_id = parent_id
        self.id = group_id if group_id else str(uuid.uuid4())

    def paint(
        self,
        painter: QPainter,
        zoom_level: float,
        offset_x: float = CANVAS_OFFSET_X,
        offset_y: float = CANVAS_OFFSET_Y,
    ) -> None:
        """Groups do not render directly."""
        pass

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "GroupItem":
        """Create GroupItem from data dictionary."""
        return GroupItem(
            name=data.get("name", ""),
            group_id=data.get("id"),
            parent_id=data.get("parentId"),
            visible=data.get("visible", True),
            locked=data.get("locked", False),
        )


class TextItem(CanvasItem):
    """Text canvas item for rendering text on the canvas."""

    def __init__(
        self,
        x: float,
        y: float,
        text: str,
        font_family: str = "Sans Serif",
        font_size: float = 16,
        text_color: str = "#ffffff",
        text_opacity: float = 1.0,
        width: float = 100,
        height: float = 0,
        name: str = "",
        parent_id: Optional[str] = None,
        visible: bool = True,
        locked: bool = False,
    ) -> None:
        self.name = name
        self.parent_id = parent_id
        self.visible = bool(visible)
        self.locked = bool(locked)
        self.x = x
        self.y = y
        self.text = text
        self.font_family = font_family
        # Validate font size (must be in range 8-200)
        self.font_size = max(8.0, min(200.0, font_size))
        self.text_color = text_color
        # Validate text opacity (must be in range 0.0-1.0)
        self.text_opacity = max(0.0, min(1.0, text_opacity))
        # Text box dimensions (width >= 1, height >= 0 where 0 means auto)
        self.width = max(1.0, width)
        self.height = max(0.0, height)

    def paint(
        self,
        painter: QPainter,
        zoom_level: float,
        offset_x: float = CANVAS_OFFSET_X,
        offset_y: float = CANVAS_OFFSET_Y,
    ) -> None:
        """Render this text item using QPainter."""
        local_x = self.x + offset_x
        local_y = self.y + offset_y

        # Set up font (use point size for typography standard)
        font = QFont(self.font_family)
        font.setPointSizeF(self.font_size)
        painter.setFont(font)

        # Set up pen for text color
        text_qcolor = QColor(self.text_color)
        text_qcolor.setAlphaF(self.text_opacity)
        pen = QPen(text_qcolor)
        painter.setPen(pen)

        # No brush needed for text
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Get font metrics to calculate baseline from top
        # y is stored as the TOP of the text, but drawText uses baseline
        fm = QFontMetricsF(font)
        baseline_y = local_y + fm.ascent()

        # Draw text at position (x is left edge, y is baseline)
        painter.drawText(QPointF(local_x, baseline_y), self.text)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "TextItem":
        """Create TextItem from QML data dictionary."""
        # Extract and validate font size (must be in range 8-200)
        font_size = max(8.0, min(200.0, float(data.get("fontSize", 16))))

        # Extract and validate text opacity (must be in range 0.0-1.0)
        text_opacity = max(0.0, min(1.0, float(data.get("textOpacity", 1.0))))

        # Extract and validate text box dimensions
        width = max(1.0, float(data.get("width", 100)))
        height = max(0.0, float(data.get("height", 0)))

        return TextItem(
            x=float(data.get("x", 0)),
            y=float(data.get("y", 0)),
            text=str(data.get("text", "")),
            font_family=str(data.get("fontFamily", "Sans Serif")),
            font_size=font_size,
            text_color=str(data.get("textColor", "#ffffff")),
            width=width,
            height=height,
            text_opacity=text_opacity,
            name=str(data.get("name", "")),
            parent_id=data.get("parentId"),
            visible=data.get("visible", True),
            locked=data.get("locked", False),
        )
