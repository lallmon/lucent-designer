"""
Bounding box calculation utilities for canvas items.

This module provides pure functions for calculating and manipulating
bounding boxes without Qt dependencies, making them easily testable.
"""

from typing import Dict, List, Optional, Any, Callable


def rect_bounds(x: float, y: float, width: float, height: float) -> Dict[str, float]:
    """Create a bounding box dictionary.

    Args:
        x: Left edge x-coordinate.
        y: Top edge y-coordinate.
        width: Width of the bounding box.
        height: Height of the bounding box.

    Returns:
        Dictionary with x, y, width, height keys.
    """
    return {"x": x, "y": y, "width": width, "height": height}


def union_bounds(bounds_list: List[Dict[str, float]]) -> Optional[Dict[str, float]]:
    """Compute the union of multiple bounding boxes.

    Args:
        bounds_list: List of bounding box dictionaries.

    Returns:
        A bounding box that contains all input boxes, or None if list is empty.
    """
    if not bounds_list:
        return None

    result = None
    for bounds in bounds_list:
        if bounds is None:
            continue
        if result is None:
            result = dict(bounds)
        else:
            min_x = min(result["x"], bounds["x"])
            min_y = min(result["y"], bounds["y"])
            max_x = max(
                result["x"] + result["width"],
                bounds["x"] + bounds["width"],
            )
            max_y = max(
                result["y"] + result["height"],
                bounds["y"] + bounds["height"],
            )
            result = rect_bounds(min_x, min_y, max_x - min_x, max_y - min_y)
    return result


def get_rectangle_bounds(geometry: Any) -> Dict[str, float]:
    """Get bounding box for a rectangle geometry.

    Args:
        geometry: RectGeometry with x, y, width, height attributes.

    Returns:
        Bounding box dictionary.
    """
    return rect_bounds(geometry.x, geometry.y, geometry.width, geometry.height)


def get_ellipse_bounds(geometry: Any) -> Dict[str, float]:
    """Get bounding box for an ellipse geometry.

    Args:
        geometry: EllipseGeometry with center_x, center_y, radius_x, radius_y.

    Returns:
        Bounding box dictionary.
    """
    return rect_bounds(
        geometry.center_x - geometry.radius_x,
        geometry.center_y - geometry.radius_y,
        geometry.radius_x * 2,
        geometry.radius_y * 2,
    )


def get_path_bounds(points: List[Dict[str, float]]) -> Optional[Dict[str, float]]:
    """Get bounding box for a path defined by points.

    Args:
        points: List of point dictionaries with x, y keys.

    Returns:
        Bounding box dictionary, or None if no points.
    """
    if not points:
        return None
    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    min_x = min(xs)
    max_x = max(xs)
    min_y = min(ys)
    max_y = max(ys)
    return rect_bounds(min_x, min_y, max_x - min_x, max_y - min_y)


def get_text_bounds(
    x: float, y: float, width: float, height: float, font_size: float
) -> Dict[str, float]:
    """Get bounding box for a text item.

    Args:
        x: X position.
        y: Y position.
        width: Text box width.
        height: Text box height (0 means auto).
        font_size: Font size for height estimation.

    Returns:
        Bounding box dictionary.
    """
    actual_height = height if height > 0 else font_size * 1.2
    return rect_bounds(x, y, width, actual_height)


def translate_path_to_bounds(
    points: List[Dict[str, float]],
    new_x: float,
    new_y: float,
) -> List[Dict[str, float]]:
    """Translate path points to align with new bounding box position.

    Args:
        points: Original list of point dictionaries.
        new_x: New left edge x-coordinate.
        new_y: New top edge y-coordinate.

    Returns:
        New list of translated points.
    """
    if not points:
        return []
    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    old_min_x = min(xs)
    old_min_y = min(ys)
    dx = new_x - old_min_x
    dy = new_y - old_min_y
    return [{"x": p["x"] + dx, "y": p["y"] + dy} for p in points]


def bbox_to_ellipse_geometry(bbox: Dict[str, float]) -> Dict[str, float]:
    """Convert bounding box to ellipse geometry parameters.

    Args:
        bbox: Bounding box dictionary.

    Returns:
        Dictionary with centerX, centerY, radiusX, radiusY keys.
    """
    return {
        "centerX": bbox["x"] + bbox["width"] / 2,
        "centerY": bbox["y"] + bbox["height"] / 2,
        "radiusX": bbox["width"] / 2,
        "radiusY": bbox["height"] / 2,
    }


def get_item_bounds(
    item: Any,
    get_descendant_bounds: Optional[Callable[[str], Optional[Dict[str, float]]]] = None,
) -> Optional[Dict[str, float]]:
    """Get bounding box for any canvas item type.

    Args:
        item: A canvas item (Rectangle, Ellipse, Path, Text, Layer, Group).
        get_descendant_bounds: Optional callback to get bounds for container
            descendants.

    Returns:
        Bounding box dictionary, or None if not applicable.
    """
    # Container (Layer/Group): use callback if provided
    # Check this first since containers have an 'id' attribute but no geometry
    if hasattr(item, "id") and not hasattr(item, "geometry") and get_descendant_bounds:
        return get_descendant_bounds(item.id)

    # Use item's get_bounds() method if available - this applies transforms
    if hasattr(item, "get_bounds") and callable(item.get_bounds):
        bounds = item.get_bounds()
        if bounds is not None:
            return rect_bounds(bounds.x(), bounds.y(), bounds.width(), bounds.height())

    return None
