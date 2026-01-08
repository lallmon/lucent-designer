"""Tests for tree-based layout/flattening of canvas items."""

from test_helpers import make_layer_with_children, make_rectangle, make_ellipse


def names(items):
    return [item.name for item in items]


def test_flatten_orders_layers_and_children(canvas_model):
    layer1_items = make_layer_with_children(
        [
            make_rectangle(x=0, y=0, width=10, height=10, name="A"),
            make_ellipse(center_x=0, center_y=0, radius_x=5, radius_y=5, name="B"),
        ],
        name="Layer1",
    )
    for item in layer1_items:
        canvas_model.addItem(item)

    layer2_items = make_layer_with_children(
        [make_rectangle(x=10, y=0, width=10, height=10, name="C")], name="Layer2"
    )
    for item in layer2_items:
        canvas_model.addItem(item)

    ordered = canvas_model.getRenderItems()
    assert names(ordered) == ["A", "B", "C"]


def test_move_layer_keeps_children_grouped(canvas_model):
    layer1_items = make_layer_with_children(
        [make_rectangle(x=0, y=0, width=10, height=10, name="A")], name="Layer1"
    )
    for item in layer1_items:
        canvas_model.addItem(item)

    layer2_items = make_layer_with_children(
        [make_rectangle(x=10, y=0, width=10, height=10, name="B")], name="Layer2"
    )
    for item in layer2_items:
        canvas_model.addItem(item)

    canvas_model.moveItem(2, 0)

    ordered = canvas_model.getRenderItems()
    assert names(ordered) == ["B", "A"]


def test_reparent_moves_node_and_render_order_updates(canvas_model):
    layer1_items = make_layer_with_children([], name="Layer1")
    for item in layer1_items:
        canvas_model.addItem(item)
    layer2_items = make_layer_with_children([], name="Layer2")
    for item in layer2_items:
        canvas_model.addItem(item)

    canvas_model.addItem(make_rectangle(x=0, y=0, width=10, height=10, name="Rect"))

    assert names(canvas_model.getRenderItems()) == ["Rect"]

    canvas_model.reparentItem(2, canvas_model.getItems()[0].id)
    assert names(canvas_model.getRenderItems()) == ["Rect"]

    canvas_model.moveItem(0, 1)
    assert names(canvas_model.getRenderItems()) == ["Rect"]

    canvas_model.reparentItem(2, canvas_model.getItems()[0].id)
    assert names(canvas_model.getRenderItems()) == ["Rect"]
