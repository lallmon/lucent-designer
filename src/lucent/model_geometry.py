# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Geometry helpers for CanvasModel.

This module keeps CanvasModel thinner by providing pure helpers for geometry,
bounding boxes, and transform-friendly updates that can be tested in isolation.
"""

import math
from typing import Any, Callable, Dict, List, Optional

from lucent.bounding_box import (
    bbox_to_ellipse_geometry,
    get_item_bounds,
    scale_path_to_bounds,
    union_bounds,
)
from lucent.canvas_items import (
    EllipseItem,
    GroupItem,
    LayerItem,
    PathItem,
    RectangleItem,
    TextItem,
)


def compute_bounding_box(
    items: List[Any],
    index: int,
    get_descendant_indices: Callable[[str], List[int]],
) -> Optional[Dict[str, float]]:
    """Return axis-aligned bounding box for an item (or its descendants)."""
    if not (0 <= index < len(items)):
        return None
    item = items[index]

    def _descendant_bounds(container_id: str) -> Optional[Dict[str, float]]:
        descendants = get_descendant_indices(container_id)
        bounds_list = [
            compute_bounding_box(items, idx, get_descendant_indices)
            for idx in descendants
        ]
        return union_bounds([b for b in bounds_list if b is not None])

    return get_item_bounds(item, _descendant_bounds)


def compute_geometry_bounds(item: Any) -> Optional[Dict[str, float]]:
    """Return untransformed geometry bounds for an item."""
    if not hasattr(item, "geometry"):
        return None
    bounds = item.geometry.get_bounds()
    return {
        "x": bounds.x(),
        "y": bounds.y(),
        "width": bounds.width(),
        "height": bounds.height(),
    }


def apply_bounding_box(
    item: Any,
    bbox: Dict[str, float],
    item_to_dict: Callable[[Any], Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Return updated item dict after applying a bounding box.

    The caller is responsible for persisting the returned dict (e.g., via
    CanvasModel.updateItem). Returns None when the item type does not support
    bounding-box application.
    """
    new_x = float(bbox.get("x", 0))
    new_y = float(bbox.get("y", 0))
    new_width = float(bbox.get("width", 0))
    new_height = float(bbox.get("height", 0))

    current_data = item_to_dict(item)

    if isinstance(item, RectangleItem):
        current_data["geometry"]["x"] = new_x
        current_data["geometry"]["y"] = new_y
        current_data["geometry"]["width"] = new_width
        current_data["geometry"]["height"] = new_height
        return current_data

    if isinstance(item, EllipseItem):
        ellipse_geom = bbox_to_ellipse_geometry(bbox)
        current_data["geometry"]["centerX"] = ellipse_geom["centerX"]
        current_data["geometry"]["centerY"] = ellipse_geom["centerY"]
        current_data["geometry"]["radiusX"] = ellipse_geom["radiusX"]
        current_data["geometry"]["radiusY"] = ellipse_geom["radiusY"]
        return current_data

    if isinstance(item, PathItem):
        points = item.geometry.points
        if not points:
            return None
        current_data["geometry"]["points"] = scale_path_to_bounds(
            points, new_x, new_y, new_width, new_height
        )
        return current_data

    if isinstance(item, TextItem):
        current_data["geometry"]["x"] = new_x
        current_data["geometry"]["y"] = new_y
        current_data["geometry"]["width"] = new_width
        current_data["geometry"]["height"] = new_height
        return current_data

    # Layers and groups are non-renderable containers
    if isinstance(item, (LayerItem, GroupItem)):
        return None

    return None


def shape_to_path_data(
    item: Any,
    item_to_dict: Callable[[Any], Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Convert a rotated shape to path data with transform baked into geometry.

    For rectangles and ellipses with rotation, converts to a path with the
    transformed corner/point positions. The resulting path has identity transform.

    Returns None if the item is not a shape or has no rotation.
    """
    if not hasattr(item, "transform") or not hasattr(item, "geometry"):
        return None

    transform = item.transform
    if transform is None or transform.rotate == 0:
        return None

    current_data = item_to_dict(item)
    geom = item.geometry
    bounds = geom.get_bounds()

    # Compute transform origin in world coordinates
    origin_x = bounds.x() + bounds.width() * transform.origin_x
    origin_y = bounds.y() + bounds.height() * transform.origin_y

    def apply_transform(x: float, y: float) -> Dict[str, float]:
        """Apply scale, rotation, and translation to a point."""
        # Translate to origin, scale, rotate, translate back
        dx = x - origin_x
        dy = y - origin_y

        # Apply scale
        dx *= transform.scale_x
        dy *= transform.scale_y

        # Apply rotation
        angle_rad = math.radians(transform.rotate)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        rx = dx * cos_a - dy * sin_a
        ry = dx * sin_a + dy * cos_a

        # Translate back and add translation offset
        return {
            "x": origin_x + rx + transform.translate_x,
            "y": origin_y + ry + transform.translate_y,
        }

    points: List[Dict[str, float]] = []

    if isinstance(item, RectangleItem):
        # 4 corners of rectangle
        corners = [
            (bounds.x(), bounds.y()),
            (bounds.x() + bounds.width(), bounds.y()),
            (bounds.x() + bounds.width(), bounds.y() + bounds.height()),
            (bounds.x(), bounds.y() + bounds.height()),
        ]
        points = [apply_transform(x, y) for x, y in corners]

    elif isinstance(item, EllipseItem):
        # Approximate ellipse with points (32 points for smooth curve)
        num_points = 32
        cx, cy = geom.center_x, geom.center_y
        rx, ry = geom.radius_x, geom.radius_y
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            x = cx + rx * math.cos(angle)
            y = cy + ry * math.sin(angle)
            points.append(apply_transform(x, y))

    elif isinstance(item, PathItem):
        # Apply transform to existing path points AND bezier handles
        for p in geom.points:
            new_point: Dict[str, Any] = apply_transform(p["x"], p["y"])
            if "handleIn" in p and p["handleIn"]:
                h = apply_transform(p["handleIn"]["x"], p["handleIn"]["y"])
                new_point["handleIn"] = h
            if "handleOut" in p and p["handleOut"]:
                h = apply_transform(p["handleOut"]["x"], p["handleOut"]["y"])
                new_point["handleOut"] = h
            points.append(new_point)

    else:
        return None

    if not points:
        return None

    # Determine if path should be closed
    is_closed = geom.closed if isinstance(item, PathItem) else True

    # Create path data with identity transform
    path_data = {
        "type": "path",
        "geometry": {
            "points": points,
            "closed": is_closed,
        },
        "appearances": current_data.get("appearances", []),
        "transform": {
            "translateX": 0,
            "translateY": 0,
            "rotate": 0,
            "scaleX": 1,
            "scaleY": 1,
            "originX": 0.5,
            "originY": 0.5,
        },
        "name": current_data.get("name", ""),
        "visible": current_data.get("visible", True),
        "locked": current_data.get("locked", False),
    }

    if current_data.get("parentId"):
        path_data["parentId"] = current_data["parentId"]

    return path_data
