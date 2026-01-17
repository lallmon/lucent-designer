# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Appearance classes for Lucent canvas items.

This module provides appearance classes that define how geometry is rendered
(fill, stroke, etc.) independently of the geometry itself.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QColor,
    QPainterPath,
)

if TYPE_CHECKING:
    pass


class Appearance(ABC):
    """Abstract base class for visual appearances applied to geometry."""

    def __init__(self, visible: bool = True) -> None:
        self.visible = bool(visible)

    @abstractmethod
    def render(
        self,
        painter: QPainter,
        path: QPainterPath,
        zoom_level: float,
        offset_x: float,
        offset_y: float,
    ) -> None:
        """Render this appearance for the given path."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize appearance to dictionary."""
        pass

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Appearance":
        """Factory method to create appearance from dictionary."""
        appearance_type = data.get("type")
        if appearance_type == "fill":
            return Fill.from_dict(data)
        elif appearance_type == "stroke":
            return Stroke.from_dict(data)
        else:
            raise ValueError(f"Unknown appearance type: {appearance_type}")

    def get_sg_color(self) -> Optional[QColor]:
        """Get color with opacity for scene graph rendering.

        Returns None if this appearance should not be rendered.
        Subclasses override to provide their specific color.
        """
        return None

    def should_render(self) -> bool:
        """Check if this appearance should be rendered."""
        return self.visible

    def get_stroke_width(self) -> float:
        """Get stroke width (0 for non-stroke appearances)."""
        return 0.0


class Fill(Appearance):
    """Fill appearance for shapes."""

    def __init__(
        self,
        color: str = "#ffffff",
        opacity: float = 0.0,
        visible: bool = True,
    ) -> None:
        super().__init__(visible)
        self.color = color
        self.opacity = max(0.0, min(1.0, float(opacity)))

    def render(
        self,
        painter: QPainter,
        path: QPainterPath,
        zoom_level: float,
        offset_x: float,
        offset_y: float,
    ) -> None:
        """Render fill for the given path."""
        if not self.visible or self.opacity <= 0:
            return

        # Set up brush
        qcolor = QColor(self.color)
        qcolor.setAlphaF(self.opacity)
        painter.setBrush(QBrush(qcolor))
        painter.setPen(Qt.PenStyle.NoPen)

        # Apply offset and draw
        translated = path.translated(offset_x, offset_y)
        painter.drawPath(translated)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "type": "fill",
            "color": self.color,
            "opacity": self.opacity,
            "visible": self.visible,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Fill":
        """Deserialize from dictionary."""
        return Fill(
            color=data.get("color", "#ffffff"),
            opacity=float(data.get("opacity", 0.0)),
            visible=data.get("visible", True),
        )

    def get_sg_color(self) -> Optional[QColor]:
        """Get fill color with opacity for scene graph rendering."""
        if not self.visible or self.opacity <= 0:
            return None
        qcolor = QColor(self.color)
        qcolor.setAlphaF(self.opacity)
        return qcolor

    def should_render(self) -> bool:
        """Check if fill should be rendered."""
        return self.visible and self.opacity > 0


class Stroke(Appearance):
    """Stroke appearance for shapes."""

    VALID_ALIGNS = ("center", "inner", "outer")
    VALID_CAPS = ("butt", "square", "round")
    VALID_ORDERS = ("top", "bottom")
    CAP_STYLES = {
        "butt": Qt.PenCapStyle.FlatCap,
        "square": Qt.PenCapStyle.SquareCap,
        "round": Qt.PenCapStyle.RoundCap,
    }

    def __init__(
        self,
        color: str = "#ffffff",
        width: float = 1.0,
        opacity: float = 1.0,
        visible: bool = True,
        cap: str = "butt",
        align: str = "center",
        order: str = "top",
        scale_with_object: bool = False,
    ) -> None:
        super().__init__(visible)
        self.color = color
        self.width = max(0.0, min(100.0, float(width)))
        self.opacity = max(0.0, min(1.0, float(opacity)))
        self.cap = cap if cap in self.VALID_CAPS else "butt"
        self.align = align if align in self.VALID_ALIGNS else "center"
        self.order = order if order in self.VALID_ORDERS else "top"
        self.scale_with_object = bool(scale_with_object)

    def render(
        self,
        painter: QPainter,
        path: QPainterPath,
        zoom_level: float,
        offset_x: float,
        offset_y: float,
    ) -> None:
        """Render stroke for the given path."""
        if not self.visible or self.width <= 0:
            return

        stroke_px = self.width * zoom_level
        clamped_px = max(0.3, min(100.0, stroke_px))
        scaled_width = clamped_px / max(zoom_level, 0.0001)

        qcolor = QColor(self.color)
        qcolor.setAlphaF(self.opacity)

        translated = path.translated(offset_x, offset_y)

        pen = QPen(qcolor, scaled_width)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        pen.setMiterLimit(100.0)
        pen.setCapStyle(self.CAP_STYLES.get(self.cap, Qt.PenCapStyle.FlatCap))

        if self.align == "center":
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(translated)
        else:
            painter.save()

            if self.align == "inner":
                painter.setClipPath(translated)
            else:
                bounds = translated.boundingRect()
                margin = scaled_width * 2 + 100
                outer_rect = QPainterPath()
                outer_rect.addRect(
                    bounds.x() - margin,
                    bounds.y() - margin,
                    bounds.width() + 2 * margin,
                    bounds.height() + 2 * margin,
                )
                inverse_clip = outer_rect.subtracted(translated)
                painter.setClipPath(inverse_clip)

            pen.setWidthF(scaled_width * 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(translated)

            painter.restore()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "type": "stroke",
            "color": self.color,
            "width": self.width,
            "opacity": self.opacity,
            "visible": self.visible,
            "cap": self.cap,
            "align": self.align,
            "order": self.order,
            "scaleWithObject": self.scale_with_object,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Stroke":
        """Deserialize from dictionary."""
        return Stroke(
            color=data.get("color", "#ffffff"),
            width=float(data.get("width", 1.0)),
            opacity=float(data.get("opacity", 1.0)),
            visible=data.get("visible", True),
            cap=data.get("cap", "butt"),
            align=data.get("align", "center"),
            order=data.get("order", "top"),
            scale_with_object=bool(data.get("scaleWithObject", False)),
        )

    def get_sg_color(self) -> Optional[QColor]:
        """Get stroke color with opacity for scene graph rendering."""
        if not self.visible or self.width <= 0 or self.opacity <= 0:
            return None
        qcolor = QColor(self.color)
        qcolor.setAlphaF(self.opacity)
        return qcolor

    def should_render(self) -> bool:
        """Check if stroke should be rendered."""
        return self.visible and self.width > 0 and self.opacity > 0

    def get_stroke_width(self) -> float:
        """Get stroke width for geometry generation."""
        return self.width

    def get_scaled_width(self, zoom_level: float) -> float:
        """Get stroke width scaled for current zoom level.

        Matches the existing QPainter behavior with clamping.
        """
        stroke_px = self.width * zoom_level
        clamped_px = max(0.3, min(100.0, stroke_px))
        return clamped_px / max(zoom_level, 0.0001)
