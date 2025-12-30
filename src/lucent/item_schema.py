"""Shared item validation and serialization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

from lucent.canvas_items import CanvasItem, RectangleItem, EllipseItem, LayerItem


class ItemSchemaError(ValueError):
    """Raised when incoming item data is invalid or unsupported."""


class ItemType(str, Enum):
    RECTANGLE = "rectangle"
    ELLIPSE = "ellipse"
    LAYER = "layer"


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
    try:
        x = float(data.get("x", 0))
        y = float(data.get("y", 0))
        width = _clamp_min(float(data.get("width", 0)), 0.0)
        height = _clamp_min(float(data.get("height", 0)), 0.0)
        stroke_width = _clamp_range(float(data.get("strokeWidth", 1)), 0.1, 100.0)
        stroke_opacity = _clamp_range(float(data.get("strokeOpacity", 1.0)), 0.0, 1.0)
        fill_opacity = _clamp_range(float(data.get("fillOpacity", 0.0)), 0.0, 1.0)
    except (TypeError, ValueError) as exc:
        raise ItemSchemaError(f"Invalid rectangle numeric field: {exc}") from exc

    stroke_color = str(data.get("strokeColor", "#ffffff"))
    fill_color = str(data.get("fillColor", "#ffffff"))
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
    try:
        center_x = float(data.get("centerX", 0))
        center_y = float(data.get("centerY", 0))
        radius_x = _clamp_min(float(data.get("radiusX", 0)), 0.0)
        radius_y = _clamp_min(float(data.get("radiusY", 0)), 0.0)
        stroke_width = _clamp_range(float(data.get("strokeWidth", 1)), 0.1, 100.0)
        stroke_opacity = _clamp_range(float(data.get("strokeOpacity", 1.0)), 0.0, 1.0)
        fill_opacity = _clamp_range(float(data.get("fillOpacity", 0.0)), 0.0, 1.0)
    except (TypeError, ValueError) as exc:
        raise ItemSchemaError(f"Invalid ellipse numeric field: {exc}") from exc

    stroke_color = str(data.get("strokeColor", "#ffffff"))
    fill_color = str(data.get("fillColor", "#ffffff"))
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


def parse_item_data(data: Dict[str, Any]) -> ParsedItem:
    item_type = _parse_type(data.get("type"))
    if item_type is ItemType.RECTANGLE:
        validated = validate_rectangle(data)
    elif item_type is ItemType.ELLIPSE:
        validated = validate_ellipse(data)
    elif item_type is ItemType.LAYER:
        validated = validate_layer(data)
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
    if t is ItemType.LAYER:
        return LayerItem(
            name=d["name"],
            layer_id=d.get("id"),
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
    raise ItemSchemaError(f"Cannot serialize unknown item type: {type(item).__name__}")
