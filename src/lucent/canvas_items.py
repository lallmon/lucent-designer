"""
Canvas item classes for Lucent.

This module defines the canvas item hierarchy, including:
- CanvasItem: Abstract base class for all drawable items
- ShapeItem: Base class for items with geometry + appearances
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
    QColor,
    QFont,
    QTextDocument,
    QTextOption,
)
from PySide6.QtCore import QRectF

from lucent.geometry import Geometry, RectGeometry, EllipseGeometry, PolylineGeometry
from lucent.appearances import Appearance, Fill, Stroke
from lucent.transforms import Transform

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

    @abstractmethod
    def get_bounds(self) -> QRectF:
        """Return bounding rectangle in canvas coordinates."""
        pass

    @staticmethod
    @abstractmethod
    def from_dict(data: Dict[str, Any]) -> "CanvasItem":
        """Factory method to create item from QML data dictionary"""
        pass


class ShapeItem(CanvasItem):
    """Base class for items with geometry + appearances.

    Provides shared rendering logic for shapes that have:
    - A geometry (defining the shape outline)
    - A list of appearances (fill, stroke, etc.)
    - A transform (non-destructive modifications)
    """

    def __init__(
        self,
        geometry: Geometry,
        appearances: Optional[List[Appearance]] = None,
        transform: Optional[Transform] = None,
        name: str = "",
        parent_id: Optional[str] = None,
        visible: bool = True,
        locked: bool = False,
    ) -> None:
        self.geometry = geometry
        # Default: one fill (transparent) + one stroke
        self.appearances = (
            appearances
            if appearances is not None
            else [
                Fill(color="#ffffff", opacity=0.0),
                Stroke(color="#ffffff", width=1.0, opacity=1.0),
            ]
        )
        self.transform = transform if transform is not None else Transform()
        self.name = name
        self.parent_id = parent_id
        self.visible = bool(visible)
        self.locked = bool(locked)

    @property
    def fill(self) -> Optional[Fill]:
        """Get first fill appearance for backwards compatibility."""
        for app in self.appearances:
            if isinstance(app, Fill):
                return app
        return None

    @property
    def stroke(self) -> Optional[Stroke]:
        """Get first stroke appearance for backwards compatibility."""
        for app in self.appearances:
            if isinstance(app, Stroke):
                return app
        return None

    def paint(
        self,
        painter: QPainter,
        zoom_level: float,
        offset_x: float = CANVAS_OFFSET_X,
        offset_y: float = CANVAS_OFFSET_Y,
    ) -> None:
        """Render this shape using QPainter."""
        if not self.visible:
            return

        # Get base path from geometry
        path = self.geometry.to_painter_path()

        # Apply non-destructive transform if present
        if not self.transform.is_identity():
            path = self.transform.to_qtransform().map(path)

        # Render each appearance in order
        for appearance in self.appearances:
            appearance.render(painter, path, zoom_level, offset_x, offset_y)

    def get_bounds(self) -> QRectF:
        """Return bounding rectangle in canvas coordinates."""
        bounds = self.geometry.get_bounds()
        if not self.transform.is_identity():
            return self.transform.to_qtransform().mapRect(bounds)
        return bounds

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ShapeItem":
        """Factory method - subclasses must override."""
        raise NotImplementedError("ShapeItem.from_dict must be overridden")


class RectangleItem(ShapeItem):
    """Rectangle canvas item with geometry + appearances architecture."""

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
        # New architecture parameters (optional)
        geometry: Optional[RectGeometry] = None,
        appearances: Optional[List[Appearance]] = None,
        transform: Optional[Transform] = None,
    ) -> None:
        # Create geometry from parameters if not provided
        if geometry is None:
            geometry = RectGeometry(
                x=float(x),
                y=float(y),
                width=max(0.0, float(width)),
                height=max(0.0, float(height)),
            )

        # Create appearances from parameters if not provided
        if appearances is None:
            appearances = [
                Fill(
                    color=fill_color,
                    opacity=max(0.0, min(1.0, float(fill_opacity))),
                ),
                Stroke(
                    color=stroke_color,
                    width=max(0.0, min(100.0, float(stroke_width))),
                    opacity=max(0.0, min(1.0, float(stroke_opacity))),
                ),
            ]

        super().__init__(
            geometry=geometry,
            appearances=appearances,
            transform=transform,
            name=name,
            parent_id=parent_id,
            visible=visible,
            locked=locked,
        )

    # Backwards-compatible property accessors for geometry
    @property
    def x(self) -> float:
        return self.geometry.x

    @x.setter
    def x(self, value: float) -> None:
        self.geometry.x = float(value)

    @property
    def y(self) -> float:
        return self.geometry.y

    @y.setter
    def y(self, value: float) -> None:
        self.geometry.y = float(value)

    @property
    def width(self) -> float:
        return self.geometry.width

    @width.setter
    def width(self, value: float) -> None:
        self.geometry.width = max(0.0, float(value))

    @property
    def height(self) -> float:
        return self.geometry.height

    @height.setter
    def height(self, value: float) -> None:
        self.geometry.height = max(0.0, float(value))

    # Backwards-compatible property accessors for fill
    @property
    def fill_color(self) -> str:
        fill = self.fill
        return fill.color if fill else "#ffffff"

    @fill_color.setter
    def fill_color(self, value: str) -> None:
        fill = self.fill
        if fill:
            fill.color = value

    @property
    def fill_opacity(self) -> float:
        fill = self.fill
        return fill.opacity if fill else 0.0

    @fill_opacity.setter
    def fill_opacity(self, value: float) -> None:
        fill = self.fill
        if fill:
            fill.opacity = max(0.0, min(1.0, float(value)))

    # Backwards-compatible property accessors for stroke
    @property
    def stroke_color(self) -> str:
        stroke = self.stroke
        return stroke.color if stroke else "#ffffff"

    @stroke_color.setter
    def stroke_color(self, value: str) -> None:
        stroke = self.stroke
        if stroke:
            stroke.color = value

    @property
    def stroke_width(self) -> float:
        stroke = self.stroke
        return stroke.width if stroke else 1.0

    @stroke_width.setter
    def stroke_width(self, value: float) -> None:
        stroke = self.stroke
        if stroke:
            stroke.width = max(0.0, min(100.0, float(value)))

    @property
    def stroke_opacity(self) -> float:
        stroke = self.stroke
        return stroke.opacity if stroke else 1.0

    @stroke_opacity.setter
    def stroke_opacity(self, value: float) -> None:
        stroke = self.stroke
        if stroke:
            stroke.opacity = max(0.0, min(1.0, float(value)))

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "RectangleItem":
        """Create RectangleItem from QML data dictionary.

        Supports both legacy flat format and new nested format.
        """
        # Check for new nested format
        if "geometry" in data:
            geometry = RectGeometry.from_dict(data["geometry"])
            appearances = [Appearance.from_dict(a) for a in data.get("appearances", [])]
            transform = (
                Transform.from_dict(data["transform"]) if "transform" in data else None
            )
            return RectangleItem(
                x=geometry.x,
                y=geometry.y,
                width=geometry.width,
                height=geometry.height,
                geometry=geometry,
                appearances=appearances if appearances else None,
                transform=transform,
                name=data.get("name", ""),
                parent_id=data.get("parentId"),
                visible=data.get("visible", True),
                locked=data.get("locked", False),
            )

        # Legacy flat format
        width = max(0.0, float(data.get("width", 0)))
        height = max(0.0, float(data.get("height", 0)))
        stroke_width = max(0.0, min(100.0, float(data.get("strokeWidth", 1))))
        stroke_opacity = max(0.0, min(1.0, float(data.get("strokeOpacity", 1.0))))
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


class EllipseItem(ShapeItem):
    """Ellipse canvas item with geometry + appearances architecture."""

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
        # New architecture parameters (optional)
        geometry: Optional[EllipseGeometry] = None,
        appearances: Optional[List[Appearance]] = None,
        transform: Optional[Transform] = None,
    ) -> None:
        # Create geometry from parameters if not provided
        if geometry is None:
            geometry = EllipseGeometry(
                center_x=float(center_x),
                center_y=float(center_y),
                radius_x=max(0.0, float(radius_x)),
                radius_y=max(0.0, float(radius_y)),
            )

        # Create appearances from parameters if not provided
        if appearances is None:
            appearances = [
                Fill(
                    color=fill_color,
                    opacity=max(0.0, min(1.0, float(fill_opacity))),
                ),
                Stroke(
                    color=stroke_color,
                    width=max(0.0, min(100.0, float(stroke_width))),
                    opacity=max(0.0, min(1.0, float(stroke_opacity))),
                ),
            ]

        super().__init__(
            geometry=geometry,
            appearances=appearances,
            transform=transform,
            name=name,
            parent_id=parent_id,
            visible=visible,
            locked=locked,
        )

    # Backwards-compatible property accessors for geometry
    @property
    def center_x(self) -> float:
        return self.geometry.center_x

    @center_x.setter
    def center_x(self, value: float) -> None:
        self.geometry.center_x = float(value)

    @property
    def center_y(self) -> float:
        return self.geometry.center_y

    @center_y.setter
    def center_y(self, value: float) -> None:
        self.geometry.center_y = float(value)

    @property
    def radius_x(self) -> float:
        return self.geometry.radius_x

    @radius_x.setter
    def radius_x(self, value: float) -> None:
        self.geometry.radius_x = max(0.0, float(value))

    @property
    def radius_y(self) -> float:
        return self.geometry.radius_y

    @radius_y.setter
    def radius_y(self, value: float) -> None:
        self.geometry.radius_y = max(0.0, float(value))

    # Backwards-compatible property accessors for fill
    @property
    def fill_color(self) -> str:
        fill = self.fill
        return fill.color if fill else "#ffffff"

    @fill_color.setter
    def fill_color(self, value: str) -> None:
        fill = self.fill
        if fill:
            fill.color = value

    @property
    def fill_opacity(self) -> float:
        fill = self.fill
        return fill.opacity if fill else 0.0

    @fill_opacity.setter
    def fill_opacity(self, value: float) -> None:
        fill = self.fill
        if fill:
            fill.opacity = max(0.0, min(1.0, float(value)))

    # Backwards-compatible property accessors for stroke
    @property
    def stroke_color(self) -> str:
        stroke = self.stroke
        return stroke.color if stroke else "#ffffff"

    @stroke_color.setter
    def stroke_color(self, value: str) -> None:
        stroke = self.stroke
        if stroke:
            stroke.color = value

    @property
    def stroke_width(self) -> float:
        stroke = self.stroke
        return stroke.width if stroke else 1.0

    @stroke_width.setter
    def stroke_width(self, value: float) -> None:
        stroke = self.stroke
        if stroke:
            stroke.width = max(0.0, min(100.0, float(value)))

    @property
    def stroke_opacity(self) -> float:
        stroke = self.stroke
        return stroke.opacity if stroke else 1.0

    @stroke_opacity.setter
    def stroke_opacity(self, value: float) -> None:
        stroke = self.stroke
        if stroke:
            stroke.opacity = max(0.0, min(1.0, float(value)))

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "EllipseItem":
        """Create EllipseItem from QML data dictionary.

        Supports both legacy flat format and new nested format.
        """
        # Check for new nested format
        if "geometry" in data:
            geometry = EllipseGeometry.from_dict(data["geometry"])
            appearances = [Appearance.from_dict(a) for a in data.get("appearances", [])]
            transform = (
                Transform.from_dict(data["transform"]) if "transform" in data else None
            )
            return EllipseItem(
                center_x=geometry.center_x,
                center_y=geometry.center_y,
                radius_x=geometry.radius_x,
                radius_y=geometry.radius_y,
                geometry=geometry,
                appearances=appearances if appearances else None,
                transform=transform,
                name=data.get("name", ""),
                parent_id=data.get("parentId"),
                visible=data.get("visible", True),
                locked=data.get("locked", False),
            )

        # Legacy flat format
        radius_x = max(0.0, float(data.get("radiusX", 0)))
        radius_y = max(0.0, float(data.get("radiusY", 0)))
        stroke_width = max(0.0, min(100.0, float(data.get("strokeWidth", 1))))
        stroke_opacity = max(0.0, min(1.0, float(data.get("strokeOpacity", 1.0))))
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


class PathItem(ShapeItem):
    """Polyline/path canvas item with geometry + appearances architecture."""

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
        # New architecture parameters (optional)
        geometry: Optional[PolylineGeometry] = None,
        appearances: Optional[List[Appearance]] = None,
        transform: Optional[Transform] = None,
    ) -> None:
        # Create geometry from parameters if not provided
        if geometry is None:
            if len(points) < 2:
                raise ValueError("PathItem requires at least two points")
            geometry = PolylineGeometry(points=points, closed=bool(closed))

        # Create appearances from parameters if not provided
        if appearances is None:
            appearances = [
                Fill(
                    color=fill_color,
                    opacity=max(0.0, min(1.0, float(fill_opacity))),
                ),
                Stroke(
                    color=stroke_color,
                    width=max(0.0, min(100.0, float(stroke_width))),
                    opacity=max(0.0, min(1.0, float(stroke_opacity))),
                ),
            ]

        super().__init__(
            geometry=geometry,
            appearances=appearances,
            transform=transform,
            name=name,
            parent_id=parent_id,
            visible=visible,
            locked=locked,
        )

    # Backwards-compatible property accessors for geometry
    @property
    def points(self) -> List[Dict[str, float]]:
        return self.geometry.points

    @points.setter
    def points(self, value: List[Dict[str, float]]) -> None:
        self.geometry.points = [
            {"x": float(p.get("x", 0)), "y": float(p.get("y", 0))} for p in value
        ]

    @property
    def closed(self) -> bool:
        return self.geometry.closed

    @closed.setter
    def closed(self, value: bool) -> None:
        self.geometry.closed = bool(value)

    # Backwards-compatible property accessors for fill
    @property
    def fill_color(self) -> str:
        fill = self.fill
        return fill.color if fill else "#ffffff"

    @fill_color.setter
    def fill_color(self, value: str) -> None:
        fill = self.fill
        if fill:
            fill.color = value

    @property
    def fill_opacity(self) -> float:
        fill = self.fill
        return fill.opacity if fill else 0.0

    @fill_opacity.setter
    def fill_opacity(self, value: float) -> None:
        fill = self.fill
        if fill:
            fill.opacity = max(0.0, min(1.0, float(value)))

    # Backwards-compatible property accessors for stroke
    @property
    def stroke_color(self) -> str:
        stroke = self.stroke
        return stroke.color if stroke else "#ffffff"

    @stroke_color.setter
    def stroke_color(self, value: str) -> None:
        stroke = self.stroke
        if stroke:
            stroke.color = value

    @property
    def stroke_width(self) -> float:
        stroke = self.stroke
        return stroke.width if stroke else 1.0

    @stroke_width.setter
    def stroke_width(self, value: float) -> None:
        stroke = self.stroke
        if stroke:
            stroke.width = max(0.0, min(100.0, float(value)))

    @property
    def stroke_opacity(self) -> float:
        stroke = self.stroke
        return stroke.opacity if stroke else 1.0

    @stroke_opacity.setter
    def stroke_opacity(self, value: float) -> None:
        stroke = self.stroke
        if stroke:
            stroke.opacity = max(0.0, min(1.0, float(value)))

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PathItem":
        """Create PathItem from QML data dictionary.

        Supports both legacy flat format and new nested format.
        """
        # Check for new nested format
        if "geometry" in data:
            geometry = PolylineGeometry.from_dict(data["geometry"])
            appearances = [Appearance.from_dict(a) for a in data.get("appearances", [])]
            transform = (
                Transform.from_dict(data["transform"]) if "transform" in data else None
            )
            return PathItem(
                points=geometry.points,
                closed=geometry.closed,
                geometry=geometry,
                appearances=appearances if appearances else None,
                transform=transform,
                name=data.get("name", ""),
                parent_id=data.get("parentId"),
                visible=data.get("visible", True),
                locked=data.get("locked", False),
            )

        # Legacy flat format
        points = data.get("points") or []
        if not isinstance(points, list):
            raise ValueError("Path points must be a list")
        stroke_width = max(0.0, min(100.0, float(data.get("strokeWidth", 1))))
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

    def get_bounds(self) -> QRectF:
        """Layers have no intrinsic bounds (non-rendering containers)."""
        return QRectF()

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

    def get_bounds(self) -> QRectF:
        """Groups have no intrinsic bounds (non-rendering containers)."""
        return QRectF()

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
        """Render this text item using QTextDocument for rich text support."""
        if not self.text:
            return

        local_x = self.x + offset_x
        local_y = self.y + offset_y

        font = QFont(self.font_family)
        font.setPointSizeF(self.font_size)

        text_qcolor = QColor(self.text_color)
        text_qcolor.setAlphaF(self.text_opacity)

        doc = QTextDocument()
        doc.setDocumentMargin(0)
        doc.setDefaultFont(font)
        if self.width > 0:
            doc.setTextWidth(self.width)

        option = QTextOption()
        option.setWrapMode(QTextOption.WrapMode.WordWrap)
        doc.setDefaultTextOption(option)

        # Apply color via stylesheet, then set HTML to activate it
        doc.setDefaultStyleSheet(
            f"body {{ color: {text_qcolor.name(QColor.NameFormat.HexArgb)}; }}"
        )
        doc.setHtml(f"<body>{self.text.replace(chr(10), '<br>')}</body>")

        painter.save()
        painter.translate(local_x, local_y)
        doc.drawContents(painter)
        painter.restore()

    def get_bounds(self) -> QRectF:
        """Return bounding rectangle in canvas coordinates."""
        if self.height > 0:
            return QRectF(self.x, self.y, self.width, self.height)
        # Auto-height: compute from text
        doc = QTextDocument()
        doc.setDocumentMargin(0)
        font = QFont(self.font_family)
        font.setPointSizeF(self.font_size)
        doc.setDefaultFont(font)
        if self.width > 0:
            doc.setTextWidth(self.width)
        doc.setPlainText(self.text or " ")
        return QRectF(self.x, self.y, self.width, doc.size().height())

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "TextItem":
        """Create TextItem from QML data dictionary."""
        font_size = max(8.0, min(200.0, float(data.get("fontSize", 16))))
        text_opacity = max(0.0, min(1.0, float(data.get("textOpacity", 1.0))))
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
