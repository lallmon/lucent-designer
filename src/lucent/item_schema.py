"""Shared item validation and serialization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

from lucent.canvas_items import (
    CanvasItem,
    RectangleItem,
    EllipseItem,
    LayerItem,
    GroupItem,
    PathItem,
    TextItem,
)


class ItemSchemaError(ValueError):
    """Raised when incoming item data is invalid or unsupported."""


class ItemType(str, Enum):
    RECTANGLE = "rectangle"
    ELLIPSE = "ellipse"
    LAYER = "layer"
    GROUP = "group"
    PATH = "path"
    TEXT = "text"


@dataclass
class ParsedItem:
    type: ItemType
    name: str
    data: Dict[str, Any]


def _clamp_min(value: float, minimum: float) -> float:
    return value if value >= minimum else minimum


def _clamp_range(value: float, minimum: float, maximum: float) -> float:
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


def _parse_type(type_value: Any) -> ItemType:
    if not type_value:
        raise ItemSchemaError("Missing item type")
    try:
        normalized = str(type_value).lower()
        return ItemType(normalized)
    except Exception as exc:
        raise ItemSchemaError(f"Unknown item type: {type_value}") from exc


def validate_rectangle(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate rectangle data, supporting both flat and nested formats."""
    try:
        # Check for new nested format
        if "geometry" in data:
            geom = data["geometry"]
            x = float(geom.get("x", 0))
            y = float(geom.get("y", 0))
            width = _clamp_min(float(geom.get("width", 0)), 0.0)
            height = _clamp_min(float(geom.get("height", 0)), 0.0)

            # Extract appearances
            appearances = data.get("appearances", [])
            fill_data: Dict[str, Any] = next(
                (a for a in appearances if a.get("type") == "fill"), {}
            )
            stroke_data: Dict[str, Any] = next(
                (a for a in appearances if a.get("type") == "stroke"), {}
            )

            fill_color = str(fill_data.get("color", "#ffffff"))
            fill_opacity = _clamp_range(float(fill_data.get("opacity", 0.0)), 0.0, 1.0)
            stroke_color = str(stroke_data.get("color", "#ffffff"))
            stroke_width = _clamp_range(float(stroke_data.get("width", 1)), 0.0, 100.0)
            stroke_opacity = _clamp_range(
                float(stroke_data.get("opacity", 1.0)), 0.0, 1.0
            )
        else:
            # Legacy flat format
            x = float(data.get("x", 0))
            y = float(data.get("y", 0))
            width = _clamp_min(float(data.get("width", 0)), 0.0)
            height = _clamp_min(float(data.get("height", 0)), 0.0)
            stroke_width = _clamp_range(float(data.get("strokeWidth", 1)), 0.0, 100.0)
            stroke_opacity = _clamp_range(
                float(data.get("strokeOpacity", 1.0)), 0.0, 1.0
            )
            fill_opacity = _clamp_range(float(data.get("fillOpacity", 0.0)), 0.0, 1.0)
            stroke_color = str(data.get("strokeColor", "#ffffff"))
            fill_color = str(data.get("fillColor", "#ffffff"))
    except (TypeError, ValueError) as exc:
        raise ItemSchemaError(f"Invalid rectangle numeric field: {exc}") from exc

    name = str(data.get("name", ""))
    parent_id = data.get("parentId") or None
    visible = bool(data.get("visible", True))
    locked = bool(data.get("locked", False))

    return {
        "type": ItemType.RECTANGLE.value,
        "name": name,
        "parentId": parent_id,
        "visible": visible,
        "locked": locked,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "strokeWidth": stroke_width,
        "strokeColor": stroke_color,
        "strokeOpacity": stroke_opacity,
        "fillColor": fill_color,
        "fillOpacity": fill_opacity,
    }


def validate_ellipse(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate ellipse data, supporting both flat and nested formats."""
    try:
        # Check for new nested format
        if "geometry" in data:
            geom = data["geometry"]
            center_x = float(geom.get("centerX", 0))
            center_y = float(geom.get("centerY", 0))
            radius_x = _clamp_min(float(geom.get("radiusX", 0)), 0.0)
            radius_y = _clamp_min(float(geom.get("radiusY", 0)), 0.0)

            # Extract appearances
            appearances = data.get("appearances", [])
            fill_data: Dict[str, Any] = next(
                (a for a in appearances if a.get("type") == "fill"), {}
            )
            stroke_data: Dict[str, Any] = next(
                (a for a in appearances if a.get("type") == "stroke"), {}
            )

            fill_color = str(fill_data.get("color", "#ffffff"))
            fill_opacity = _clamp_range(float(fill_data.get("opacity", 0.0)), 0.0, 1.0)
            stroke_color = str(stroke_data.get("color", "#ffffff"))
            stroke_width = _clamp_range(float(stroke_data.get("width", 1)), 0.0, 100.0)
            stroke_opacity = _clamp_range(
                float(stroke_data.get("opacity", 1.0)), 0.0, 1.0
            )
        else:
            # Legacy flat format
            center_x = float(data.get("centerX", 0))
            center_y = float(data.get("centerY", 0))
            radius_x = _clamp_min(float(data.get("radiusX", 0)), 0.0)
            radius_y = _clamp_min(float(data.get("radiusY", 0)), 0.0)
            stroke_width = _clamp_range(float(data.get("strokeWidth", 1)), 0.0, 100.0)
            stroke_opacity = _clamp_range(
                float(data.get("strokeOpacity", 1.0)), 0.0, 1.0
            )
            fill_opacity = _clamp_range(float(data.get("fillOpacity", 0.0)), 0.0, 1.0)
            stroke_color = str(data.get("strokeColor", "#ffffff"))
            fill_color = str(data.get("fillColor", "#ffffff"))
    except (TypeError, ValueError) as exc:
        raise ItemSchemaError(f"Invalid ellipse numeric field: {exc}") from exc

    name = str(data.get("name", ""))
    parent_id = data.get("parentId") or None
    visible = bool(data.get("visible", True))
    locked = bool(data.get("locked", False))

    return {
        "type": ItemType.ELLIPSE.value,
        "name": name,
        "parentId": parent_id,
        "visible": visible,
        "locked": locked,
        "centerX": center_x,
        "centerY": center_y,
        "radiusX": radius_x,
        "radiusY": radius_y,
        "strokeWidth": stroke_width,
        "strokeColor": stroke_color,
        "strokeOpacity": stroke_opacity,
        "fillColor": fill_color,
        "fillOpacity": fill_opacity,
    }


def validate_path(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate path data, supporting both flat and nested formats."""
    try:
        # Check for new nested format
        if "geometry" in data:
            geom = data["geometry"]
            points_raw = geom.get("points") or []
            closed = bool(geom.get("closed", False))

            # Extract appearances
            appearances = data.get("appearances", [])
            fill_data: Dict[str, Any] = next(
                (a for a in appearances if a.get("type") == "fill"), {}
            )
            stroke_data: Dict[str, Any] = next(
                (a for a in appearances if a.get("type") == "stroke"), {}
            )

            fill_color = str(fill_data.get("color", "#ffffff"))
            fill_opacity = _clamp_range(float(fill_data.get("opacity", 0.0)), 0.0, 1.0)
            stroke_color = str(stroke_data.get("color", "#ffffff"))
            stroke_width = _clamp_range(float(stroke_data.get("width", 1)), 0.0, 100.0)
            stroke_opacity = _clamp_range(
                float(stroke_data.get("opacity", 1.0)), 0.0, 1.0
            )
        else:
            # Legacy flat format
            points_raw = data.get("points") or []
            closed = bool(data.get("closed", False))
            stroke_width = _clamp_range(float(data.get("strokeWidth", 1)), 0.0, 100.0)
            stroke_opacity = _clamp_range(
                float(data.get("strokeOpacity", 1.0)), 0.0, 1.0
            )
            fill_opacity = _clamp_range(float(data.get("fillOpacity", 0.0)), 0.0, 1.0)
            stroke_color = str(data.get("strokeColor", "#ffffff"))
            fill_color = str(data.get("fillColor", "#ffffff"))

        if not isinstance(points_raw, list):
            raise ItemSchemaError("Path points must be a list")
        if len(points_raw) < 2:
            raise ItemSchemaError("Path requires at least two points")
        points = []
        for p in points_raw:
            points.append({"x": float(p.get("x", 0)), "y": float(p.get("y", 0))})
    except (TypeError, ValueError, AttributeError) as exc:
        raise ItemSchemaError(f"Invalid path field: {exc}") from exc

    name = str(data.get("name", ""))
    parent_id = data.get("parentId") or None
    visible = bool(data.get("visible", True))
    locked = bool(data.get("locked", False))

    return {
        "type": ItemType.PATH.value,
        "name": name,
        "parentId": parent_id,
        "visible": visible,
        "locked": locked,
        "points": points,
        "strokeWidth": stroke_width,
        "strokeColor": stroke_color,
        "strokeOpacity": stroke_opacity,
        "fillColor": fill_color,
        "fillOpacity": fill_opacity,
        "closed": closed,
    }


def validate_layer(data: Dict[str, Any]) -> Dict[str, Any]:
    name = str(data.get("name", ""))
    layer_id = data.get("id") or None
    visible = bool(data.get("visible", True))
    locked = bool(data.get("locked", False))
    return {
        "type": ItemType.LAYER.value,
        "id": layer_id,
        "name": name,
        "visible": visible,
        "locked": locked,
    }


def validate_group(data: Dict[str, Any]) -> Dict[str, Any]:
    name = str(data.get("name", ""))
    group_id = data.get("id") or None
    parent_id = data.get("parentId") or None
    visible = bool(data.get("visible", True))
    locked = bool(data.get("locked", False))
    return {
        "type": ItemType.GROUP.value,
        "id": group_id,
        "name": name,
        "parentId": parent_id,
        "visible": visible,
        "locked": locked,
    }


def validate_text(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize text item data."""
    try:
        x = float(data.get("x", 0))
        y = float(data.get("y", 0))
        font_size = _clamp_range(float(data.get("fontSize", 16)), 8.0, 200.0)
        text_opacity = _clamp_range(float(data.get("textOpacity", 1.0)), 0.0, 1.0)
        # Text box dimensions (width >= 1, height >= 0 where 0 means auto)
        width = _clamp_min(float(data.get("width", 100)), 1.0)
        height = _clamp_min(float(data.get("height", 0)), 0.0)
    except (TypeError, ValueError) as exc:
        raise ItemSchemaError(f"Invalid text numeric field: {exc}") from exc

    text = str(data.get("text", ""))
    font_family = str(data.get("fontFamily", "Sans Serif"))
    text_color = str(data.get("textColor", "#ffffff"))
    name = str(data.get("name", ""))
    parent_id = data.get("parentId") or None
    visible = bool(data.get("visible", True))
    locked = bool(data.get("locked", False))

    return {
        "type": ItemType.TEXT.value,
        "name": name,
        "parentId": parent_id,
        "visible": visible,
        "locked": locked,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "text": text,
        "fontFamily": font_family,
        "fontSize": font_size,
        "textColor": text_color,
        "textOpacity": text_opacity,
    }


def parse_item_data(data: Dict[str, Any]) -> ParsedItem:
    item_type = _parse_type(data.get("type"))
    if item_type is ItemType.RECTANGLE:
        validated = validate_rectangle(data)
    elif item_type is ItemType.ELLIPSE:
        validated = validate_ellipse(data)
    elif item_type is ItemType.LAYER:
        validated = validate_layer(data)
    elif item_type is ItemType.GROUP:
        validated = validate_group(data)
    elif item_type is ItemType.PATH:
        validated = validate_path(data)
    elif item_type is ItemType.TEXT:
        validated = validate_text(data)
    else:  # pragma: no cover - exhaustive Enum
        raise ItemSchemaError(f"Unsupported item type: {item_type}")

    return ParsedItem(type=item_type, name=validated.get("name", ""), data=validated)


def parse_item(data: Dict[str, Any]) -> CanvasItem:
    parsed = parse_item_data(data)
    t = parsed.type
    d = parsed.data
    if t is ItemType.RECTANGLE:
        return RectangleItem(
            x=d["x"],
            y=d["y"],
            width=d["width"],
            height=d["height"],
            stroke_width=d["strokeWidth"],
            stroke_color=d["strokeColor"],
            fill_color=d["fillColor"],
            fill_opacity=d["fillOpacity"],
            stroke_opacity=d["strokeOpacity"],
            name=d["name"],
            parent_id=d["parentId"],
            visible=d.get("visible", True),
            locked=d.get("locked", False),
        )
    if t is ItemType.ELLIPSE:
        return EllipseItem(
            center_x=d["centerX"],
            center_y=d["centerY"],
            radius_x=d["radiusX"],
            radius_y=d["radiusY"],
            stroke_width=d["strokeWidth"],
            stroke_color=d["strokeColor"],
            fill_color=d["fillColor"],
            fill_opacity=d["fillOpacity"],
            stroke_opacity=d["strokeOpacity"],
            name=d["name"],
            parent_id=d["parentId"],
            visible=d.get("visible", True),
            locked=d.get("locked", False),
        )
    if t is ItemType.PATH:
        return PathItem(
            points=d["points"],
            stroke_width=d["strokeWidth"],
            stroke_color=d["strokeColor"],
            stroke_opacity=d["strokeOpacity"],
            fill_color=d["fillColor"],
            fill_opacity=d["fillOpacity"],
            closed=d.get("closed", False),
            name=d.get("name", ""),
            parent_id=d.get("parentId"),
            visible=d.get("visible", True),
            locked=d.get("locked", False),
        )
    if t is ItemType.LAYER:
        return LayerItem(
            name=d["name"],
            layer_id=d.get("id"),
            visible=d.get("visible", True),
            locked=d.get("locked", False),
        )
    if t is ItemType.GROUP:
        return GroupItem(
            name=d["name"],
            group_id=d.get("id"),
            parent_id=d.get("parentId"),
            visible=d.get("visible", True),
            locked=d.get("locked", False),
        )
    if t is ItemType.TEXT:
        return TextItem(
            x=d["x"],
            y=d["y"],
            text=d["text"],
            font_family=d["fontFamily"],
            font_size=d["fontSize"],
            text_color=d["textColor"],
            text_opacity=d["textOpacity"],
            width=d["width"],
            height=d["height"],
            name=d["name"],
            parent_id=d["parentId"],
            visible=d.get("visible", True),
            locked=d.get("locked", False),
        )
    raise ItemSchemaError(f"Unsupported item type: {parsed.type}")


def item_to_dict(item: CanvasItem) -> Dict[str, Any]:
    if isinstance(item, RectangleItem):
        return {
            "type": ItemType.RECTANGLE.value,
            "name": item.name,
            "parentId": item.parent_id,
            "visible": getattr(item, "visible", True),
            "locked": getattr(item, "locked", False),
            "x": item.x,
            "y": item.y,
            "width": item.width,
            "height": item.height,
            "strokeWidth": item.stroke_width,
            "strokeColor": item.stroke_color,
            "strokeOpacity": item.stroke_opacity,
            "fillColor": item.fill_color,
            "fillOpacity": item.fill_opacity,
        }
    if isinstance(item, EllipseItem):
        return {
            "type": ItemType.ELLIPSE.value,
            "name": item.name,
            "parentId": item.parent_id,
            "visible": getattr(item, "visible", True),
            "locked": getattr(item, "locked", False),
            "centerX": item.center_x,
            "centerY": item.center_y,
            "radiusX": item.radius_x,
            "radiusY": item.radius_y,
            "strokeWidth": item.stroke_width,
            "strokeColor": item.stroke_color,
            "strokeOpacity": item.stroke_opacity,
            "fillColor": item.fill_color,
            "fillOpacity": item.fill_opacity,
        }
    if isinstance(item, LayerItem):
        return {
            "type": ItemType.LAYER.value,
            "id": item.id,
            "name": item.name,
            "visible": getattr(item, "visible", True),
            "locked": getattr(item, "locked", False),
        }
    if isinstance(item, GroupItem):
        return {
            "type": ItemType.GROUP.value,
            "id": item.id,
            "name": item.name,
            "parentId": item.parent_id,
            "visible": getattr(item, "visible", True),
            "locked": getattr(item, "locked", False),
        }
    if isinstance(item, PathItem):
        return {
            "type": ItemType.PATH.value,
            "name": item.name,
            "parentId": item.parent_id,
            "visible": getattr(item, "visible", True),
            "locked": getattr(item, "locked", False),
            "points": item.points,
            "strokeWidth": item.stroke_width,
            "strokeColor": item.stroke_color,
            "strokeOpacity": item.stroke_opacity,
            "fillColor": item.fill_color,
            "fillOpacity": item.fill_opacity,
            "closed": item.closed,
        }
    if isinstance(item, TextItem):
        return {
            "type": ItemType.TEXT.value,
            "name": item.name,
            "parentId": item.parent_id,
            "visible": getattr(item, "visible", True),
            "locked": getattr(item, "locked", False),
            "x": item.x,
            "y": item.y,
            "width": item.width,
            "height": item.height,
            "text": item.text,
            "fontFamily": item.font_family,
            "fontSize": item.font_size,
            "textColor": item.text_color,
            "textOpacity": item.text_opacity,
        }
    raise ItemSchemaError(f"Cannot serialize unknown item type: {type(item).__name__}")
