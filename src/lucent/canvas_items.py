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
from typing import Dict, Any, Optional
import uuid
from PySide6.QtGui import QPainter, QPen, QBrush, QColor
from PySide6.QtCore import QRectF, Qt

# Canvas coordinate system constants
# The canvas uses a virtual coordinate system centered at (0, 0) in canvas space
# which maps to (CANVAS_OFFSET_X, CANVAS_OFFSET_Y) in renderer local coordinates
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
        # Transform from canvas coordinates to CanvasRenderer local coordinates
        # CanvasRenderer is positioned at (-CANVAS_OFFSET_X, -CANVAS_OFFSET_Y) with size 10000x10000
        # Canvas coordinate (0, 0) maps to local coordinate (CANVAS_OFFSET_X, CANVAS_OFFSET_Y)
        local_x = self.x + offset_x
        local_y = self.y + offset_y

        # Scale stroke width by zoom level
        scaled_stroke_width = self.stroke_width / zoom_level

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

        # Extract and validate stroke width (must be positive, clamped to reasonable range)
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
        # Transform from canvas coordinates to CanvasRenderer local coordinates
        # CanvasRenderer is positioned at (-CANVAS_OFFSET_X, -CANVAS_OFFSET_Y) with size 10000x10000
        # Canvas coordinate (0, 0) maps to local coordinate (CANVAS_OFFSET_X, CANVAS_OFFSET_Y)
        local_center_x = self.center_x + offset_x
        local_center_y = self.center_y + offset_y

        # Scale stroke width by zoom level
        scaled_stroke_width = self.stroke_width / zoom_level

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

        # Extract and validate stroke width (must be positive, clamped to reasonable range)
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
