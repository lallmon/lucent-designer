"""
Geometry classes for Lucent canvas items.

This module provides geometry classes that define shapes independently
of their visual appearance (fill, stroke, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List

from PySide6.QtCore import QRectF, QPointF
from PySide6.QtGui import QPainterPath


class Geometry(ABC):
    """Abstract base class for all geometry types."""

    @abstractmethod
    def to_painter_path(self) -> QPainterPath:
        """Convert geometry to QPainterPath for rendering."""
        pass

    @abstractmethod
    def get_bounds(self) -> QRectF:
        """Return axis-aligned bounding box."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize geometry to dictionary."""
        pass

    @staticmethod
    @abstractmethod
    def from_dict(data: Dict[str, Any]) -> "Geometry":
        """Deserialize geometry from dictionary."""
        pass


class RectGeometry(Geometry):
    """Rectangle geometry defined by position and dimensions."""

    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        self.x = float(x)
        self.y = float(y)
        self.width = max(0.0, float(width))
        self.height = max(0.0, float(height))

    def to_painter_path(self) -> QPainterPath:
        """Convert to QPainterPath."""
        path = QPainterPath()
        path.addRect(self.x, self.y, self.width, self.height)
        return path

    def get_bounds(self) -> QRectF:
        """Return bounding rectangle."""
        return QRectF(self.x, self.y, self.width, self.height)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "RectGeometry":
        """Deserialize from dictionary."""
        return RectGeometry(
            x=float(data.get("x", 0)),
            y=float(data.get("y", 0)),
            width=float(data.get("width", 0)),
            height=float(data.get("height", 0)),
        )


class EllipseGeometry(Geometry):
    """Ellipse geometry defined by center and radii."""

    def __init__(
        self,
        center_x: float,
        center_y: float,
        radius_x: float,
        radius_y: float,
    ) -> None:
        self.center_x = float(center_x)
        self.center_y = float(center_y)
        self.radius_x = max(0.0, float(radius_x))
        self.radius_y = max(0.0, float(radius_y))

    def to_painter_path(self) -> QPainterPath:
        """Convert to QPainterPath."""
        path = QPainterPath()
        path.addEllipse(
            QPointF(self.center_x, self.center_y),
            self.radius_x,
            self.radius_y,
        )
        return path

    def get_bounds(self) -> QRectF:
        """Return bounding rectangle."""
        return QRectF(
            self.center_x - self.radius_x,
            self.center_y - self.radius_y,
            2 * self.radius_x,
            2 * self.radius_y,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "centerX": self.center_x,
            "centerY": self.center_y,
            "radiusX": self.radius_x,
            "radiusY": self.radius_y,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "EllipseGeometry":
        """Deserialize from dictionary."""
        return EllipseGeometry(
            center_x=float(data.get("centerX", 0)),
            center_y=float(data.get("centerY", 0)),
            radius_x=float(data.get("radiusX", 0)),
            radius_y=float(data.get("radiusY", 0)),
        )


class PolylineGeometry(Geometry):
    """Polyline/path geometry defined by a list of points."""

    def __init__(self, points: List[Dict[str, float]], closed: bool = False) -> None:
        if len(points) < 2:
            raise ValueError("PolylineGeometry requires at least two points")

        # Normalize points to float values
        self.points: List[Dict[str, float]] = [
            {"x": float(p.get("x", 0)), "y": float(p.get("y", 0))} for p in points
        ]
        self.closed = bool(closed)

    def to_painter_path(self) -> QPainterPath:
        """Convert to QPainterPath."""
        if not self.points:
            return QPainterPath()

        first = self.points[0]
        path = QPainterPath(QPointF(first["x"], first["y"]))

        for p in self.points[1:]:
            path.lineTo(p["x"], p["y"])

        if self.closed:
            path.closeSubpath()

        return path

    def get_bounds(self) -> QRectF:
        """Return bounding rectangle of all points."""
        if not self.points:
            return QRectF()

        xs = [p["x"] for p in self.points]
        ys = [p["y"] for p in self.points]

        min_x = min(xs)
        min_y = min(ys)
        max_x = max(xs)
        max_y = max(ys)

        return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "points": self.points,
            "closed": self.closed,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PolylineGeometry":
        """Deserialize from dictionary."""
        points = data.get("points")
        if not isinstance(points, list):
            raise ValueError("PolylineGeometry points must be a list")
        if len(points) < 2:
            raise ValueError("PolylineGeometry requires at least two points")

        return PolylineGeometry(
            points=points,
            closed=bool(data.get("closed", False)),
        )


class TextGeometry(Geometry):
    """Text geometry defined by position and dimensions."""

    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        self.x = float(x)
        self.y = float(y)
        self.width = max(1.0, float(width))  # Minimum width of 1
        self.height = max(0.0, float(height))

    def to_painter_path(self) -> QPainterPath:
        """Convert to QPainterPath (rectangle representing text bounds)."""
        path = QPainterPath()
        path.addRect(self.x, self.y, self.width, self.height)
        return path

    def get_bounds(self) -> QRectF:
        """Return bounding rectangle."""
        return QRectF(self.x, self.y, self.width, self.height)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "TextGeometry":
        """Deserialize from dictionary."""
        return TextGeometry(
            x=float(data.get("x", 0)),
            y=float(data.get("y", 0)),
            width=float(data.get("width", 1)),  # Default minimum width
            height=float(data.get("height", 0)),
        )
