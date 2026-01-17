# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Geometry classes for Lucent canvas items.

This module provides geometry classes that define shapes independently
of their visual appearance (fill, stroke, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
import math

from PySide6.QtCore import QRectF, QPointF
from PySide6.QtGui import QPainterPath


# Type alias for vertex data: list of (x, y) tuples
VertexList = List[Tuple[float, float]]


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

    @abstractmethod
    def to_fill_vertices(self) -> VertexList:
        """Return vertices for GPU fill rendering (triangle strip).

        Returns a list of (x, y) tuples suitable for QSGGeometry with
        DrawTriangleStrip mode.
        """
        pass

    @abstractmethod
    def to_stroke_vertices(self, stroke_width: float = 1.0) -> VertexList:
        """Return vertices for GPU stroke rendering.

        Returns a list of (x, y) tuples forming a triangle strip that
        represents the stroked outline of the geometry.
        """
        pass

    @abstractmethod
    def translated(self, dx: float, dy: float) -> "Geometry":
        """Return a new geometry translated by dx, dy."""
        pass


class RectGeometry(Geometry):
    """Rectangle geometry defined by position and dimensions."""

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        corner_radius: float = 0.0,
        corner_radius_tl: Optional[float] = None,
        corner_radius_tr: Optional[float] = None,
        corner_radius_br: Optional[float] = None,
        corner_radius_bl: Optional[float] = None,
    ) -> None:
        self.x = float(x)
        self.y = float(y)
        self.width = max(0.0, float(width))
        self.height = max(0.0, float(height))
        self.corner_radius = max(0.0, min(50.0, float(corner_radius)))
        self.corner_radius_tl = (
            max(0.0, min(50.0, float(corner_radius_tl)))
            if corner_radius_tl is not None
            else None
        )
        self.corner_radius_tr = (
            max(0.0, min(50.0, float(corner_radius_tr)))
            if corner_radius_tr is not None
            else None
        )
        self.corner_radius_br = (
            max(0.0, min(50.0, float(corner_radius_br)))
            if corner_radius_br is not None
            else None
        )
        self.corner_radius_bl = (
            max(0.0, min(50.0, float(corner_radius_bl)))
            if corner_radius_bl is not None
            else None
        )

    @property
    def has_per_corner_radius(self) -> bool:
        """Return True if any per-corner radius is set."""
        return any(
            r is not None
            for r in [
                self.corner_radius_tl,
                self.corner_radius_tr,
                self.corner_radius_br,
                self.corner_radius_bl,
            ]
        )

    @property
    def corner_radius_pixels(self) -> float:
        """Return uniform corner radius in pixels (percentage of smaller dimension)."""
        return (self.corner_radius / 100.0) * min(self.width, self.height)

    @property
    def effective_corner_radii_pixels(self) -> Tuple[float, float, float, float]:
        """Return (tl, tr, br, bl) corner radii in pixels."""
        min_dim = min(self.width, self.height)
        tl = (
            (self.corner_radius_tl / 100.0) * min_dim
            if self.corner_radius_tl is not None
            else self.corner_radius_pixels
        )
        tr = (
            (self.corner_radius_tr / 100.0) * min_dim
            if self.corner_radius_tr is not None
            else self.corner_radius_pixels
        )
        br = (
            (self.corner_radius_br / 100.0) * min_dim
            if self.corner_radius_br is not None
            else self.corner_radius_pixels
        )
        bl = (
            (self.corner_radius_bl / 100.0) * min_dim
            if self.corner_radius_bl is not None
            else self.corner_radius_pixels
        )
        return (tl, tr, br, bl)

    def to_painter_path(self) -> QPainterPath:
        """Convert to QPainterPath."""
        path = QPainterPath()
        tl, tr, br, bl = self.effective_corner_radii_pixels

        if tl == tr == br == bl:
            if tl > 0:
                path.addRoundedRect(self.x, self.y, self.width, self.height, tl, tl)
            else:
                path.addRect(self.x, self.y, self.width, self.height)
        else:
            # Per-corner radii: build path manually
            x, y, w, h = self.x, self.y, self.width, self.height
            path.moveTo(x + tl, y)
            path.lineTo(x + w - tr, y)
            if tr > 0:
                path.arcTo(x + w - 2 * tr, y, 2 * tr, 2 * tr, 90, -90)
            path.lineTo(x + w, y + h - br)
            if br > 0:
                path.arcTo(x + w - 2 * br, y + h - 2 * br, 2 * br, 2 * br, 0, -90)
            path.lineTo(x + bl, y + h)
            if bl > 0:
                path.arcTo(x, y + h - 2 * bl, 2 * bl, 2 * bl, -90, -90)
            path.lineTo(x, y + tl)
            if tl > 0:
                path.arcTo(x, y, 2 * tl, 2 * tl, 180, -90)
            path.closeSubpath()
        return path

    def get_bounds(self) -> QRectF:
        """Return bounding rectangle."""
        return QRectF(self.x, self.y, self.width, self.height)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        result: Dict[str, Any] = {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "cornerRadius": self.corner_radius,
        }
        if self.corner_radius_tl is not None:
            result["cornerRadiusTL"] = self.corner_radius_tl
        if self.corner_radius_tr is not None:
            result["cornerRadiusTR"] = self.corner_radius_tr
        if self.corner_radius_br is not None:
            result["cornerRadiusBR"] = self.corner_radius_br
        if self.corner_radius_bl is not None:
            result["cornerRadiusBL"] = self.corner_radius_bl
        return result

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "RectGeometry":
        """Deserialize from dictionary."""
        return RectGeometry(
            x=float(data.get("x", 0)),
            y=float(data.get("y", 0)),
            width=float(data.get("width", 0)),
            height=float(data.get("height", 0)),
            corner_radius=float(data.get("cornerRadius", 0)),
            corner_radius_tl=(
                float(data["cornerRadiusTL"]) if "cornerRadiusTL" in data else None
            ),
            corner_radius_tr=(
                float(data["cornerRadiusTR"]) if "cornerRadiusTR" in data else None
            ),
            corner_radius_br=(
                float(data["cornerRadiusBR"]) if "cornerRadiusBR" in data else None
            ),
            corner_radius_bl=(
                float(data["cornerRadiusBL"]) if "cornerRadiusBL" in data else None
            ),
        )

    def to_fill_vertices(self) -> VertexList:
        """Return vertices for filled rectangle (triangle strip: TL, BL, TR, BR)."""
        return [
            (self.x, self.y),  # Top-left
            (self.x, self.y + self.height),  # Bottom-left
            (self.x + self.width, self.y),  # Top-right
            (self.x + self.width, self.y + self.height),  # Bottom-right
        ]

    def to_stroke_vertices(self, stroke_width: float = 1.0) -> VertexList:
        """Return vertices for stroked rectangle outline.

        Creates a triangle strip forming the outline with the given stroke width.
        """
        hw = stroke_width / 2.0  # Half width

        # Outer corners
        ox1, oy1 = self.x - hw, self.y - hw
        ox2, oy2 = self.x + self.width + hw, self.y + self.height + hw

        # Inner corners
        ix1, iy1 = self.x + hw, self.y + hw
        ix2, iy2 = self.x + self.width - hw, self.y + self.height - hw

        # Triangle strip forming the outline (outer/inner pairs around rectangle)
        return [
            (ox1, oy1),
            (ix1, iy1),  # Top-left
            (ox2, oy1),
            (ix2, iy1),  # Top-right
            (ox2, oy2),
            (ix2, iy2),  # Bottom-right
            (ox1, oy2),
            (ix1, iy2),  # Bottom-left
            (ox1, oy1),
            (ix1, iy1),  # Close loop back to top-left
        ]

    def translated(self, dx: float, dy: float) -> "RectGeometry":
        """Return a new rectangle translated by dx, dy."""
        return RectGeometry(
            self.x + dx,
            self.y + dy,
            self.width,
            self.height,
            self.corner_radius,
            self.corner_radius_tl,
            self.corner_radius_tr,
            self.corner_radius_br,
            self.corner_radius_bl,
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

    def _get_segment_count(self) -> int:
        """Calculate number of segments for smooth ellipse based on size."""
        # More segments for larger ellipses
        max_radius = max(self.radius_x, self.radius_y)
        # Between 16 and 64 segments depending on size
        return max(16, min(64, int(max_radius / 4) + 16))

    def to_fill_vertices(self) -> VertexList:
        """Return vertices for filled ellipse (triangle fan from center)."""
        segments = self._get_segment_count()
        vertices: VertexList = []

        # Center point first for triangle fan
        vertices.append((self.center_x, self.center_y))

        # Points around the ellipse
        for i in range(segments + 1):  # +1 to close the loop
            angle = 2.0 * math.pi * i / segments
            x = self.center_x + self.radius_x * math.cos(angle)
            y = self.center_y + self.radius_y * math.sin(angle)
            vertices.append((x, y))

        return vertices

    def to_stroke_vertices(self, stroke_width: float = 1.0) -> VertexList:
        """Return vertices for stroked ellipse outline.

        Creates a triangle strip with inner and outer edge pairs.
        """
        segments = self._get_segment_count()
        hw = stroke_width / 2.0
        vertices: VertexList = []

        for i in range(segments + 1):  # +1 to close the loop
            angle = 2.0 * math.pi * i / segments
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)

            # Outer point
            ox = self.center_x + (self.radius_x + hw) * cos_a
            oy = self.center_y + (self.radius_y + hw) * sin_a

            # Inner point
            ix = self.center_x + (self.radius_x - hw) * cos_a
            iy = self.center_y + (self.radius_y - hw) * sin_a

            vertices.append((ox, oy))
            vertices.append((ix, iy))

        return vertices

    def translated(self, dx: float, dy: float) -> "EllipseGeometry":
        """Return a new ellipse translated by dx, dy."""
        return EllipseGeometry(
            self.center_x + dx, self.center_y + dy, self.radius_x, self.radius_y
        )


class PathGeometry(Geometry):
    """Path geometry with bezier curve support.

    Each point can optionally have handleIn and handleOut control points
    for cubic bezier curves. Points without handles render as straight lines.
    """

    def __init__(self, points: List[Dict[str, Any]], closed: bool = False) -> None:
        if len(points) < 2:
            raise ValueError("PathGeometry requires at least two points")

        self.points: List[Dict[str, Any]] = []
        for p in points:
            normalized: Dict[str, Any] = {
                "x": float(p.get("x", 0)),
                "y": float(p.get("y", 0)),
            }
            if p.get("handleIn") is not None:
                h = p["handleIn"]
                normalized["handleIn"] = {
                    "x": float(h.get("x", 0)),
                    "y": float(h.get("y", 0)),
                }
            if p.get("handleOut") is not None:
                h = p["handleOut"]
                normalized["handleOut"] = {
                    "x": float(h.get("x", 0)),
                    "y": float(h.get("y", 0)),
                }
            self.points.append(normalized)

        self.closed = bool(closed)

    def _has_handles(
        self, prev_point: Dict[str, Any], curr_point: Dict[str, Any]
    ) -> bool:
        """Check if a segment between two points should use bezier curve."""
        return (
            prev_point.get("handleOut") is not None
            or curr_point.get("handleIn") is not None
        )

    def _get_control_points(
        self, prev_point: Dict[str, Any], curr_point: Dict[str, Any]
    ) -> tuple[float, float, float, float]:
        """Get control points for cubic bezier between two points.

        Returns (cp1_x, cp1_y, cp2_x, cp2_y) where:
        - cp1 is the outgoing handle from prev_point (or prev anchor if none)
        - cp2 is the incoming handle to curr_point (or curr anchor if none)
        """
        if prev_point.get("handleOut"):
            cp1_x = prev_point["handleOut"]["x"]
            cp1_y = prev_point["handleOut"]["y"]
        else:
            cp1_x = prev_point["x"]
            cp1_y = prev_point["y"]

        if curr_point.get("handleIn"):
            cp2_x = curr_point["handleIn"]["x"]
            cp2_y = curr_point["handleIn"]["y"]
        else:
            cp2_x = curr_point["x"]
            cp2_y = curr_point["y"]

        return (cp1_x, cp1_y, cp2_x, cp2_y)

    def to_painter_path(self) -> QPainterPath:
        """Convert to QPainterPath using cubicTo for segments with handles."""
        if not self.points:
            return QPainterPath()

        first = self.points[0]
        path = QPainterPath(QPointF(first["x"], first["y"]))

        for i in range(1, len(self.points)):
            prev = self.points[i - 1]
            curr = self.points[i]

            if self._has_handles(prev, curr):
                cp1_x, cp1_y, cp2_x, cp2_y = self._get_control_points(prev, curr)
                path.cubicTo(cp1_x, cp1_y, cp2_x, cp2_y, curr["x"], curr["y"])
            else:
                path.lineTo(curr["x"], curr["y"])

        if self.closed and len(self.points) >= 2:
            last = self.points[-1]
            first = self.points[0]

            if self._has_handles(last, first):
                cp1_x, cp1_y, cp2_x, cp2_y = self._get_control_points(last, first)
                path.cubicTo(cp1_x, cp1_y, cp2_x, cp2_y, first["x"], first["y"])
            path.closeSubpath()

        return path

    def get_bounds(self) -> QRectF:
        """Return bounding rectangle using QPainterPath for accurate bezier bounds."""
        if not self.points:
            return QRectF()

        # Use QPainterPath.boundingRect() for accurate bounds including curves
        path = self.to_painter_path()
        return path.boundingRect()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary, including handle data."""
        return {
            "points": self.points,
            "closed": self.closed,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PathGeometry":
        """Deserialize from dictionary."""
        points = data.get("points")
        if not isinstance(points, list):
            raise ValueError("PathGeometry points must be a list")
        if len(points) < 2:
            raise ValueError("PathGeometry requires at least two points")

        return PathGeometry(
            points=points,
            closed=bool(data.get("closed", False)),
        )

    def _flatten_bezier(
        self,
        p0: Tuple[float, float],
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float],
        tolerance: float = 1.0,
    ) -> List[Tuple[float, float]]:
        """Flatten a cubic bezier curve into line segments.

        Uses recursive subdivision until segments are within tolerance.
        """

        def subdivide(
            a: Tuple[float, float],
            b: Tuple[float, float],
            c: Tuple[float, float],
            d: Tuple[float, float],
            depth: int,
        ) -> List[Tuple[float, float]]:
            # Check if curve is flat enough
            ax, ay = a
            dx, dy = d
            bx, by = b
            cx, cy = c

            # Distance from control points to line a-d
            line_len = math.sqrt((dx - ax) ** 2 + (dy - ay) ** 2)
            if line_len < 0.001:
                return [d]

            # Perpendicular distances of b and c from line a-d
            def point_line_dist(px: float, py: float) -> float:
                return (
                    abs((dy - ay) * px - (dx - ax) * py + dx * ay - dy * ax) / line_len
                )

            dist_b = point_line_dist(bx, by)
            dist_c = point_line_dist(cx, cy)

            if max(dist_b, dist_c) < tolerance or depth > 10:
                return [d]

            # Subdivide at midpoint
            ab = ((ax + bx) / 2, (ay + by) / 2)
            bc = ((bx + cx) / 2, (by + cy) / 2)
            cd = ((cx + dx) / 2, (cy + dy) / 2)
            abc = ((ab[0] + bc[0]) / 2, (ab[1] + bc[1]) / 2)
            bcd = ((bc[0] + cd[0]) / 2, (bc[1] + cd[1]) / 2)
            abcd = ((abc[0] + bcd[0]) / 2, (abc[1] + bcd[1]) / 2)

            return subdivide(a, ab, abc, abcd, depth + 1) + subdivide(
                abcd, bcd, cd, d, depth + 1
            )

        return subdivide(p0, p1, p2, p3, 0)

    def _get_flattened_points(self) -> VertexList:
        """Get all points with bezier curves flattened to line segments."""
        if not self.points:
            return []

        result: VertexList = [(self.points[0]["x"], self.points[0]["y"])]

        for i in range(1, len(self.points)):
            prev = self.points[i - 1]
            curr = self.points[i]

            if self._has_handles(prev, curr):
                p0 = (prev["x"], prev["y"])
                cp1_x, cp1_y, cp2_x, cp2_y = self._get_control_points(prev, curr)
                p1 = (cp1_x, cp1_y)
                p2 = (cp2_x, cp2_y)
                p3 = (curr["x"], curr["y"])
                result.extend(self._flatten_bezier(p0, p1, p2, p3))
            else:
                result.append((curr["x"], curr["y"]))

        if self.closed and len(self.points) >= 2:
            last = self.points[-1]
            first = self.points[0]
            if self._has_handles(last, first):
                p0 = (last["x"], last["y"])
                cp1_x, cp1_y, cp2_x, cp2_y = self._get_control_points(last, first)
                p1 = (cp1_x, cp1_y)
                p2 = (cp2_x, cp2_y)
                p3 = (first["x"], first["y"])
                result.extend(self._flatten_bezier(p0, p1, p2, p3))

        return result

    def to_fill_vertices(self) -> VertexList:
        """Return vertices for filled path.

        For closed paths, uses ear clipping triangulation.
        For open paths, returns empty (paths need closing to fill).
        """
        if not self.closed:
            return []

        # Simple approach: use triangle fan from centroid
        # A proper implementation would use ear clipping
        flat = self._get_flattened_points()
        if len(flat) < 3:
            return []

        # Calculate centroid
        cx = sum(p[0] for p in flat) / len(flat)
        cy = sum(p[1] for p in flat) / len(flat)

        # Triangle fan from centroid
        vertices: VertexList = [(cx, cy)]
        for p in flat:
            vertices.append(p)
        # Close the fan
        if flat:
            vertices.append(flat[0])

        return vertices

    def to_stroke_vertices(self, stroke_width: float = 1.0) -> VertexList:
        """Return vertices for stroked path outline.

        Creates a triangle strip with offset pairs along the path.
        """
        flat = self._get_flattened_points()
        if len(flat) < 2:
            return []

        hw = stroke_width / 2.0
        vertices: VertexList = []

        for i, pt in enumerate(flat):
            # Calculate normal direction
            if i == 0:
                # First point: use direction to next
                dx = flat[1][0] - pt[0]
                dy = flat[1][1] - pt[1]
            elif i == len(flat) - 1:
                # Last point: use direction from previous
                dx = pt[0] - flat[i - 1][0]
                dy = pt[1] - flat[i - 1][1]
            else:
                # Middle: average of incoming and outgoing
                dx1 = pt[0] - flat[i - 1][0]
                dy1 = pt[1] - flat[i - 1][1]
                dx2 = flat[i + 1][0] - pt[0]
                dy2 = flat[i + 1][1] - pt[1]
                dx = dx1 + dx2
                dy = dy1 + dy2

            # Normalize and get perpendicular
            length = math.sqrt(dx * dx + dy * dy)
            if length < 0.001:
                nx, ny = 0.0, 1.0
            else:
                nx, ny = -dy / length, dx / length

            # Add offset points
            vertices.append((pt[0] + nx * hw, pt[1] + ny * hw))
            vertices.append((pt[0] - nx * hw, pt[1] - ny * hw))

        return vertices

    def translated(self, dx: float, dy: float) -> "PathGeometry":
        """Return a new path translated by dx, dy, preserving all handles."""
        new_points: List[Dict[str, Any]] = []
        for p in self.points:
            new_point: Dict[str, Any] = {"x": p["x"] + dx, "y": p["y"] + dy}
            if "handleIn" in p:
                new_point["handleIn"] = {
                    "x": p["handleIn"]["x"] + dx,
                    "y": p["handleIn"]["y"] + dy,
                }
            if "handleOut" in p:
                new_point["handleOut"] = {
                    "x": p["handleOut"]["x"] + dx,
                    "y": p["handleOut"]["y"] + dy,
                }
            new_points.append(new_point)
        return PathGeometry(new_points, self.closed)


# Alias for backward compatibility during transition
PolylineGeometry = PathGeometry


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

    def to_fill_vertices(self) -> VertexList:
        """Return vertices for text background (if needed).

        Text rendering uses textures (Phase 6), but this provides
        a bounding box for background fills.
        """
        return [
            (self.x, self.y),  # Top-left
            (self.x, self.y + self.height),  # Bottom-left
            (self.x + self.width, self.y),  # Top-right
            (self.x + self.width, self.y + self.height),  # Bottom-right
        ]

    def to_stroke_vertices(self, stroke_width: float = 1.0) -> VertexList:
        """Return vertices for text box outline (not typically used)."""
        hw = stroke_width / 2.0

        ox1, oy1 = self.x - hw, self.y - hw
        ox2, oy2 = self.x + self.width + hw, self.y + self.height + hw
        ix1, iy1 = self.x + hw, self.y + hw
        ix2, iy2 = self.x + self.width - hw, self.y + self.height - hw

        return [
            (ox1, oy1),
            (ix1, iy1),
            (ox2, oy1),
            (ix2, iy1),
            (ox2, oy2),
            (ix2, iy2),
            (ox1, oy2),
            (ix1, iy2),
            (ox1, oy1),
            (ix1, iy1),
        ]

    def translated(self, dx: float, dy: float) -> "TextGeometry":
        """Return a new text geometry translated by dx, dy."""
        return TextGeometry(self.x + dx, self.y + dy, self.width, self.height)
