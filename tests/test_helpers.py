"""Test helpers for creating item data in the new format."""


def make_rectangle(
    x=0,
    y=0,
    width=10,
    height=10,
    fill_color="#ffffff",
    fill_opacity=0.0,
    stroke_color="#ffffff",
    stroke_width=1.0,
    stroke_opacity=1.0,
    name="",
    parent_id=None,
    visible=True,
    locked=False,
):
    """Create rectangle data in new format."""
    data = {
        "type": "rectangle",
        "geometry": {"x": x, "y": y, "width": width, "height": height},
        "appearances": [
            {
                "type": "fill",
                "color": fill_color,
                "opacity": fill_opacity,
                "visible": True,
            },
            {
                "type": "stroke",
                "color": stroke_color,
                "width": stroke_width,
                "opacity": stroke_opacity,
                "visible": True,
            },
        ],
        "name": name,
        "visible": visible,
        "locked": locked,
    }
    if parent_id:
        data["parentId"] = parent_id
    return data


def make_ellipse(
    center_x=0,
    center_y=0,
    radius_x=10,
    radius_y=10,
    fill_color="#ffffff",
    fill_opacity=0.0,
    stroke_color="#ffffff",
    stroke_width=1.0,
    stroke_opacity=1.0,
    name="",
    parent_id=None,
    visible=True,
    locked=False,
):
    """Create ellipse data in new format."""
    data = {
        "type": "ellipse",
        "geometry": {
            "centerX": center_x,
            "centerY": center_y,
            "radiusX": radius_x,
            "radiusY": radius_y,
        },
        "appearances": [
            {
                "type": "fill",
                "color": fill_color,
                "opacity": fill_opacity,
                "visible": True,
            },
            {
                "type": "stroke",
                "color": stroke_color,
                "width": stroke_width,
                "opacity": stroke_opacity,
                "visible": True,
            },
        ],
        "name": name,
        "visible": visible,
        "locked": locked,
    }
    if parent_id:
        data["parentId"] = parent_id
    return data


def make_path(
    points,
    closed=False,
    fill_color="#ffffff",
    fill_opacity=0.0,
    stroke_color="#ffffff",
    stroke_width=1.0,
    stroke_opacity=1.0,
    name="",
    parent_id=None,
    visible=True,
    locked=False,
):
    """Create path data in new format."""
    data = {
        "type": "path",
        "geometry": {"points": points, "closed": closed},
        "appearances": [
            {
                "type": "fill",
                "color": fill_color,
                "opacity": fill_opacity,
                "visible": True,
            },
            {
                "type": "stroke",
                "color": stroke_color,
                "width": stroke_width,
                "opacity": stroke_opacity,
                "visible": True,
            },
        ],
        "name": name,
        "visible": visible,
        "locked": locked,
    }
    if parent_id:
        data["parentId"] = parent_id
    return data


def make_layer(name="", layer_id=None, visible=True, locked=False):
    """Create layer data."""
    data = {
        "type": "layer",
        "name": name,
        "visible": visible,
        "locked": locked,
    }
    if layer_id:
        data["id"] = layer_id
    return data


def make_group(name="", group_id=None, parent_id=None, visible=True, locked=False):
    """Create group data."""
    data = {
        "type": "group",
        "name": name,
        "visible": visible,
        "locked": locked,
    }
    if group_id:
        data["id"] = group_id
    if parent_id:
        data["parentId"] = parent_id
    return data


def make_text(
    x=0,
    y=0,
    text="",
    font_family="Sans Serif",
    font_size=16,
    text_color="#ffffff",
    text_opacity=1.0,
    width=100,
    height=0,
    name="",
    parent_id=None,
    visible=True,
    locked=False,
):
    """Create text data."""
    data = {
        "type": "text",
        "x": x,
        "y": y,
        "text": text,
        "fontFamily": font_family,
        "fontSize": font_size,
        "textColor": text_color,
        "textOpacity": text_opacity,
        "width": width,
        "height": height,
        "name": name,
        "visible": visible,
        "locked": locked,
    }
    if parent_id:
        data["parentId"] = parent_id
    return data


def make_layer_with_children(
    child_items: list[dict], name: str = "Layer", layer_id: str | None = None
) -> list[dict]:
    """Create a layer plus provided child item dicts with parentId wired."""
    layer = make_layer(name=name)
    layer_id = layer_id or name.lower().replace(" ", "-")
    layer["id"] = layer_id
    wired_children = []
    for child in child_items:
        child_copy = dict(child)
        child_copy["parentId"] = layer_id
        wired_children.append(child_copy)
    return [layer, *wired_children]


def assert_bounds(
    actual: dict, x: float, y: float, width: float, height: float
) -> None:
    """Assert a bounds dict matches expected values."""
    assert actual["x"] == x
    assert actual["y"] == y
    assert actual["width"] == width
    assert actual["height"] == height
