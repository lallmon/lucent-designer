"""Geometry helpers for CanvasModel.

This module keeps CanvasModel thinner by providing pure helpers for geometry,
bounding boxes, and transform-friendly updates that can be tested in isolation.
"""

from typing import Any, Callable, Dict, List, Optional

from lucent.bounding_box import (
    bbox_to_ellipse_geometry,
    get_item_bounds,
    translate_path_to_bounds,
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
        current_data["geometry"]["points"] = translate_path_to_bounds(
            points, new_x, new_y
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
