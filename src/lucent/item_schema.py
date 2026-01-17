# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Shared item validation and serialization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from lucent.canvas_items import (
    CanvasItem,
    RectangleItem,
    EllipseItem,
    LayerItem,
    GroupItem,
    PathItem,
    TextItem,
)
from lucent.geometry import (
    RectGeometry,
    EllipseGeometry,
    PathGeometry,
    TextGeometry,
)
from lucent.appearances import Fill, Stroke
from lucent.transforms import Transform


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


def _parse_appearances(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse appearances from data, with defaults."""
    appearances = data.get("appearances", [])
    if not appearances:
        # Default appearances
        return [
            {"type": "fill", "color": "#ffffff", "opacity": 0.0, "visible": True},
            {
                "type": "stroke",
                "color": "#ffffff",
                "width": 1.0,
                "opacity": 1.0,
                "visible": True,
                "cap": "butt",
                "align": "center",
                "order": "top",
            },
        ]

    result = []
    for a in appearances:
        app_type = a.get("type")
        if app_type == "fill":
            result.append(
                {
                    "type": "fill",
                    "color": str(a.get("color", "#ffffff")),
                    "opacity": _clamp_range(float(a.get("opacity", 0.0)), 0.0, 1.0),
                    "visible": bool(a.get("visible", True)),
                }
            )
        elif app_type == "stroke":
            cap = a.get("cap", "butt")
            if cap not in ("butt", "square", "round"):
                cap = "butt"
            align = a.get("align", "center")
            if align not in ("center", "inner", "outer"):
                align = "center"
            order = a.get("order", "top")
            if order not in ("top", "bottom"):
                order = "top"
            result.append(
                {
                    "type": "stroke",
                    "color": str(a.get("color", "#ffffff")),
                    "width": _clamp_range(float(a.get("width", 1.0)), 0.0, 100.0),
                    "opacity": _clamp_range(float(a.get("opacity", 1.0)), 0.0, 1.0),
                    "visible": bool(a.get("visible", True)),
                    "cap": cap,
                    "align": align,
                    "order": order,
                }
            )
    return result


def _parse_transform(data: Dict[str, Any]) -> Dict[str, Any] | None:
    """Parse transform from data, returning None for identity or missing."""
    t = data.get("transform")
    if not t:
        return None

    translate_x = float(t.get("translateX", 0))
    translate_y = float(t.get("translateY", 0))
    rotate = float(t.get("rotate", 0))
    scale_x = float(t.get("scaleX", 1))
    scale_y = float(t.get("scaleY", 1))
    pivot_x = t.get("pivotX")
    pivot_y = t.get("pivotY")
    has_pivot = pivot_x is not None or pivot_y is not None
    pivot_x = float(pivot_x) if pivot_x is not None else None
    pivot_y = float(pivot_y) if pivot_y is not None else None

    # Return None for identity transforms to keep serialized data clean
    if (
        translate_x == 0
        and translate_y == 0
        and rotate == 0
        and scale_x == 1
        and scale_y == 1
        and not has_pivot
    ):
        return None

    result = {
        "translateX": translate_x,
        "translateY": translate_y,
        "rotate": rotate,
        "scaleX": scale_x,
        "scaleY": scale_y,
    }
    if has_pivot:
        result["pivotX"] = pivot_x if pivot_x is not None else 0.0
        result["pivotY"] = pivot_y if pivot_y is not None else 0.0
    return result


def _parse_optional_corner_radius(geom: Dict[str, Any], key: str) -> Optional[float]:
    """Parse an optional per-corner radius value."""
    if key not in geom or geom[key] is None:
        return None
    val = geom[key]
    if val == 0:
        return None
    return max(0.0, min(50.0, float(val)))


def validate_rectangle(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate rectangle data."""
    try:
        geom = data.get("geometry", {})
        x = float(geom.get("x", 0))
        y = float(geom.get("y", 0))
        width = _clamp_min(float(geom.get("width", 0)), 0.0)
        height = _clamp_min(float(geom.get("height", 0)), 0.0)
        corner_radius = max(0.0, min(50.0, float(geom.get("cornerRadius", 0))))
        corner_radius_tl = _parse_optional_corner_radius(geom, "cornerRadiusTL")
        corner_radius_tr = _parse_optional_corner_radius(geom, "cornerRadiusTR")
        corner_radius_br = _parse_optional_corner_radius(geom, "cornerRadiusBR")
        corner_radius_bl = _parse_optional_corner_radius(geom, "cornerRadiusBL")
    except (TypeError, ValueError) as exc:
        raise ItemSchemaError(f"Invalid rectangle numeric field: {exc}") from exc

    appearances = _parse_appearances(data)
    transform = _parse_transform(data)
    name = str(data.get("name", ""))
    parent_id = data.get("parentId") or None
    visible = bool(data.get("visible", True))
    locked = bool(data.get("locked", False))

    geometry: Dict[str, Any] = {
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "cornerRadius": corner_radius,
    }
    if corner_radius_tl is not None:
        geometry["cornerRadiusTL"] = corner_radius_tl
    if corner_radius_tr is not None:
        geometry["cornerRadiusTR"] = corner_radius_tr
    if corner_radius_br is not None:
        geometry["cornerRadiusBR"] = corner_radius_br
    if corner_radius_bl is not None:
        geometry["cornerRadiusBL"] = corner_radius_bl

    result: Dict[str, Any] = {
        "type": ItemType.RECTANGLE.value,
        "name": name,
        "parentId": parent_id,
        "visible": visible,
        "locked": locked,
        "geometry": geometry,
        "appearances": appearances,
    }
    if transform is not None:
        result["transform"] = transform
    return result


def validate_ellipse(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate ellipse data."""
    try:
        geom = data.get("geometry", {})
        center_x = float(geom.get("centerX", 0))
        center_y = float(geom.get("centerY", 0))
        radius_x = _clamp_min(float(geom.get("radiusX", 0)), 0.0)
        radius_y = _clamp_min(float(geom.get("radiusY", 0)), 0.0)
    except (TypeError, ValueError) as exc:
        raise ItemSchemaError(f"Invalid ellipse numeric field: {exc}") from exc

    appearances = _parse_appearances(data)
    transform = _parse_transform(data)
    name = str(data.get("name", ""))
    parent_id = data.get("parentId") or None
    visible = bool(data.get("visible", True))
    locked = bool(data.get("locked", False))

    result: Dict[str, Any] = {
        "type": ItemType.ELLIPSE.value,
        "name": name,
        "parentId": parent_id,
        "visible": visible,
        "locked": locked,
        "geometry": {
            "centerX": center_x,
            "centerY": center_y,
            "radiusX": radius_x,
            "radiusY": radius_y,
        },
        "appearances": appearances,
    }
    if transform is not None:
        result["transform"] = transform
    return result


def _parse_handle(handle_data: Any) -> Dict[str, float] | None:
    """Parse a bezier handle from point data."""
    if handle_data is None:
        return None
    if not isinstance(handle_data, dict):
        return None
    return {"x": float(handle_data.get("x", 0)), "y": float(handle_data.get("y", 0))}


def validate_path(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate path data, preserving bezier handles."""
    try:
        geom = data.get("geometry", {})
        points_raw = geom.get("points") or []
        closed = bool(geom.get("closed", False))

        if not isinstance(points_raw, list):
            raise ItemSchemaError("Path points must be a list")
        if len(points_raw) < 2:
            raise ItemSchemaError("Path requires at least two points")

        points: List[Dict[str, Any]] = []
        for p in points_raw:
            point: Dict[str, Any] = {
                "x": float(p.get("x", 0)),
                "y": float(p.get("y", 0)),
            }
            # Preserve bezier handles if present
            handle_in = _parse_handle(p.get("handleIn"))
            if handle_in is not None:
                point["handleIn"] = handle_in
            handle_out = _parse_handle(p.get("handleOut"))
            if handle_out is not None:
                point["handleOut"] = handle_out
            points.append(point)
    except (TypeError, ValueError, AttributeError) as exc:
        raise ItemSchemaError(f"Invalid path field: {exc}") from exc

    appearances = _parse_appearances(data)
    transform = _parse_transform(data)
    name = str(data.get("name", ""))
    parent_id = data.get("parentId") or None
    visible = bool(data.get("visible", True))
    locked = bool(data.get("locked", False))

    result: Dict[str, Any] = {
        "type": ItemType.PATH.value,
        "name": name,
        "parentId": parent_id,
        "visible": visible,
        "locked": locked,
        "geometry": {"points": points, "closed": closed},
        "appearances": appearances,
    }
    if transform is not None:
        result["transform"] = transform
    return result


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
    """Validate text item data."""
    try:
        # Support both new geometry format and legacy x/y format
        geom = data.get("geometry", {})
        x = float(geom.get("x", data.get("x", 0)))
        y = float(geom.get("y", data.get("y", 0)))
        width = _clamp_min(float(geom.get("width", data.get("width", 100))), 1.0)
        height = _clamp_min(float(geom.get("height", data.get("height", 0))), 0.0)
        font_size = _clamp_range(float(data.get("fontSize", 16)), 8.0, 200.0)
        text_opacity = _clamp_range(float(data.get("textOpacity", 1.0)), 0.0, 1.0)
    except (TypeError, ValueError) as exc:
        raise ItemSchemaError(f"Invalid text numeric field: {exc}") from exc

    transform = _parse_transform(data)
    text = str(data.get("text", ""))
    font_family = str(data.get("fontFamily", "Sans Serif"))
    text_color = str(data.get("textColor", "#ffffff"))
    name = str(data.get("name", ""))
    parent_id = data.get("parentId") or None
    visible = bool(data.get("visible", True))
    locked = bool(data.get("locked", False))

    result: Dict[str, Any] = {
        "type": ItemType.TEXT.value,
        "name": name,
        "parentId": parent_id,
        "visible": visible,
        "locked": locked,
        "geometry": {"x": x, "y": y, "width": width, "height": height},
        "text": text,
        "fontFamily": font_family,
        "fontSize": font_size,
        "textColor": text_color,
        "textOpacity": text_opacity,
    }
    if transform is not None:
        result["transform"] = transform
    return result


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


def _create_transform(data: Dict[str, Any], geometry: Any) -> Transform | None:
    """Create a Transform object from validated data, or None for identity."""
    t = data.get("transform")
    if not t:
        return None
    pivot_x = t.get("pivotX")
    pivot_y = t.get("pivotY")
    if pivot_x is None or pivot_y is None:
        bounds = geometry.get_bounds()
        pivot_x = bounds.x() + bounds.width() * 0.5
        pivot_y = bounds.y() + bounds.height() * 0.5
    else:
        pivot_x = float(pivot_x)
        pivot_y = float(pivot_y)
    return Transform(
        translate_x=t["translateX"],
        translate_y=t["translateY"],
        rotate=t["rotate"],
        scale_x=t["scaleX"],
        scale_y=t["scaleY"],
        pivot_x=pivot_x,
        pivot_y=pivot_y,
    )


def parse_item(data: Dict[str, Any]) -> CanvasItem:
    parsed = parse_item_data(data)
    t = parsed.type
    d = parsed.data
    if t is ItemType.RECTANGLE:
        geom = d["geometry"]
        geometry = RectGeometry(
            x=geom["x"],
            y=geom["y"],
            width=geom["width"],
            height=geom["height"],
            corner_radius=geom.get("cornerRadius", 0),
            corner_radius_tl=geom.get("cornerRadiusTL"),
            corner_radius_tr=geom.get("cornerRadiusTR"),
            corner_radius_br=geom.get("cornerRadiusBR"),
            corner_radius_bl=geom.get("cornerRadiusBL"),
        )
        return RectangleItem(
            geometry=geometry,
            appearances=[
                Fill(a["color"], a["opacity"], a["visible"])
                if a["type"] == "fill"
                else Stroke(
                    a["color"],
                    a["width"],
                    a["opacity"],
                    a["visible"],
                    a.get("cap", "butt"),
                    a.get("align", "center"),
                    a.get("order", "top"),
                )
                for a in d["appearances"]
            ],
            transform=_create_transform(d, geometry),
            name=d["name"],
            parent_id=d["parentId"],
            visible=d.get("visible", True),
            locked=d.get("locked", False),
        )
    if t is ItemType.ELLIPSE:
        geom = d["geometry"]
        geometry = EllipseGeometry(
            center_x=geom["centerX"],
            center_y=geom["centerY"],
            radius_x=geom["radiusX"],
            radius_y=geom["radiusY"],
        )
        return EllipseItem(
            geometry=geometry,
            appearances=[
                Fill(a["color"], a["opacity"], a["visible"])
                if a["type"] == "fill"
                else Stroke(
                    a["color"],
                    a["width"],
                    a["opacity"],
                    a["visible"],
                    a.get("cap", "butt"),
                    a.get("align", "center"),
                    a.get("order", "top"),
                )
                for a in d["appearances"]
            ],
            transform=_create_transform(d, geometry),
            name=d["name"],
            parent_id=d["parentId"],
            visible=d.get("visible", True),
            locked=d.get("locked", False),
        )
    if t is ItemType.PATH:
        geom = d["geometry"]
        geometry = PathGeometry(points=geom["points"], closed=geom["closed"])
        return PathItem(
            geometry=geometry,
            appearances=[
                Fill(a["color"], a["opacity"], a["visible"])
                if a["type"] == "fill"
                else Stroke(
                    a["color"],
                    a["width"],
                    a["opacity"],
                    a["visible"],
                    a.get("cap", "butt"),
                    a.get("align", "center"),
                    a.get("order", "top"),
                )
                for a in d["appearances"]
            ],
            transform=_create_transform(d, geometry),
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
        geom = d["geometry"]
        geometry = TextGeometry(
            x=geom["x"], y=geom["y"], width=geom["width"], height=geom["height"]
        )
        return TextItem(
            geometry=geometry,
            text=d["text"],
            font_family=d["fontFamily"],
            font_size=d["fontSize"],
            text_color=d["textColor"],
            text_opacity=d["textOpacity"],
            transform=_create_transform(d, geometry),
            name=d["name"],
            parent_id=d["parentId"],
            visible=d.get("visible", True),
            locked=d.get("locked", False),
        )
    raise ItemSchemaError(f"Unsupported item type: {parsed.type}")


def _geometry_bounds_dict(geom: Any) -> Dict[str, float]:
    """Get bounds dict from geometry without triggering Qt dependencies."""
    bounds = geom.get_bounds()
    return {
        "x": bounds.x(),
        "y": bounds.y(),
        "width": bounds.width(),
        "height": bounds.height(),
    }


def _should_serialize_transform(item: Any) -> bool:
    """Return True when transform should be included in serialization."""
    if not hasattr(item, "transform") or item.transform is None:
        return False

    if not item.transform.is_identity():
        return True

    # Persist pivot changes even if rotation/scale/translate are identity.
    bounds = item.geometry.get_bounds()
    default_pivot_x = bounds.x() + bounds.width() * 0.5
    default_pivot_y = bounds.y() + bounds.height() * 0.5
    return (
        abs(item.transform.pivot_x - default_pivot_x) > 0.001
        or abs(item.transform.pivot_y - default_pivot_y) > 0.001
    )


def item_to_dict(item: CanvasItem) -> Dict[str, Any]:
    """Serialize a CanvasItem to dictionary."""
    if isinstance(item, RectangleItem):
        result: Dict[str, Any] = {
            "type": ItemType.RECTANGLE.value,
            "name": item.name,
            "parentId": item.parent_id,
            "visible": item.visible,
            "locked": item.locked,
            "geometry": item.geometry.to_dict(),
            "bounds": _geometry_bounds_dict(item.geometry),
            "appearances": [a.to_dict() for a in item.appearances],
        }
        if _should_serialize_transform(item):
            result["transform"] = item.transform.to_dict()
        return result
    if isinstance(item, EllipseItem):
        result = {
            "type": ItemType.ELLIPSE.value,
            "name": item.name,
            "parentId": item.parent_id,
            "visible": item.visible,
            "locked": item.locked,
            "geometry": item.geometry.to_dict(),
            "bounds": _geometry_bounds_dict(item.geometry),
            "appearances": [a.to_dict() for a in item.appearances],
        }
        if _should_serialize_transform(item):
            result["transform"] = item.transform.to_dict()
        return result
    if isinstance(item, PathItem):
        result = {
            "type": ItemType.PATH.value,
            "name": item.name,
            "parentId": item.parent_id,
            "visible": item.visible,
            "locked": item.locked,
            "geometry": item.geometry.to_dict(),
            "bounds": _geometry_bounds_dict(item.geometry),
            "appearances": [a.to_dict() for a in item.appearances],
        }
        if _should_serialize_transform(item):
            result["transform"] = item.transform.to_dict()
        return result
    if isinstance(item, LayerItem):
        return {
            "type": ItemType.LAYER.value,
            "id": item.id,
            "name": item.name,
            "visible": item.visible,
            "locked": item.locked,
        }
    if isinstance(item, GroupItem):
        return {
            "type": ItemType.GROUP.value,
            "id": item.id,
            "name": item.name,
            "parentId": item.parent_id,
            "visible": item.visible,
            "locked": item.locked,
        }
    if isinstance(item, TextItem):
        result = {
            "type": ItemType.TEXT.value,
            "name": item.name,
            "parentId": item.parent_id,
            "visible": item.visible,
            "locked": item.locked,
            "geometry": item.geometry.to_dict(),
            "bounds": _geometry_bounds_dict(item.geometry),
            "text": item.text,
            "fontFamily": item.font_family,
            "fontSize": item.font_size,
            "textColor": item.text_color,
            "textOpacity": item.text_opacity,
        }
        if _should_serialize_transform(item):
            result["transform"] = item.transform.to_dict()
        return result
    raise ItemSchemaError(f"Cannot serialize unknown item type: {type(item).__name__}")
