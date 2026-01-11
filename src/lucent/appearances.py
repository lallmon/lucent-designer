# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Appearance classes for Lucent canvas items.

This module provides appearance classes that define how geometry is rendered
(fill, stroke, etc.) independently of the geometry itself.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath


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


class Stroke(Appearance):
    """Stroke appearance for shapes."""

    def __init__(
        self,
        color: str = "#ffffff",
        width: float = 1.0,
        opacity: float = 1.0,
        visible: bool = True,
    ) -> None:
        super().__init__(visible)
        self.color = color
        self.width = max(0.0, min(100.0, float(width)))
        self.opacity = max(0.0, min(1.0, float(opacity)))

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

        # Stroke width scaling with zoom (matches existing behavior)
        stroke_px = self.width * zoom_level
        clamped_px = max(0.3, min(6.0, stroke_px))
        scaled_width = clamped_px / max(zoom_level, 0.0001)

        # Set up pen
        qcolor = QColor(self.color)
        qcolor.setAlphaF(self.opacity)
        pen = QPen(qcolor)
        pen.setWidthF(scaled_width)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Apply offset and draw
        translated = path.translated(offset_x, offset_y)
        painter.drawPath(translated)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "type": "stroke",
            "color": self.color,
            "width": self.width,
            "opacity": self.opacity,
            "visible": self.visible,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Stroke":
        """Deserialize from dictionary."""
        return Stroke(
            color=data.get("color", "#ffffff"),
            width=float(data.get("width", 1.0)),
            opacity=float(data.get("opacity", 1.0)),
            visible=data.get("visible", True),
        )
