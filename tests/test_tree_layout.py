"""Tests for tree-based layout/flattening of canvas items."""

import pytest

from lucent.canvas_model import CanvasModel


def names(items):
    return [item.name for item in items]


def test_flatten_orders_layers_and_children(canvas_model):
    # Layer1, childA, childB; then Layer2, childC
    canvas_model.addLayer()  # Layer 1
    layer1 = canvas_model.getItems()[0]
    canvas_model.addItem(
        {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10, "name": "A"}
    )
    canvas_model.setParent(1, layer1.id)
    canvas_model.addItem(
        {
            "type": "ellipse",
            "centerX": 0,
            "centerY": 0,
            "radiusX": 5,
            "radiusY": 5,
            "name": "B",
        }
    )
    canvas_model.setParent(2, layer1.id)

    canvas_model.addLayer()  # Layer 2
    layer2 = canvas_model.getItems()[3]
    canvas_model.addItem(
        {"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10, "name": "C"}
    )
    canvas_model.setParent(4, layer2.id)

    ordered = canvas_model.getRenderItems()
    # Render order is bottom-to-top based on model order (index 0 is top), children follow their layer in reverse paint order
    assert names(ordered) == ["B", "A", "C"]  # Layer nodes are skipped


def test_move_layer_keeps_children_grouped(canvas_model):
    canvas_model.addLayer()  # Layer 1
    layer1 = canvas_model.getItems()[0]
    canvas_model.addItem(
        {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10, "name": "A"}
    )
    canvas_model.setParent(1, layer1.id)

    canvas_model.addLayer()  # Layer 2
    layer2 = canvas_model.getItems()[2]
    canvas_model.addItem(
        {"type": "rectangle", "x": 10, "y": 0, "width": 10, "height": 10, "name": "B"}
    )
    canvas_model.setParent(3, layer2.id)

    # Move Layer2 above Layer1 (index 2 -> 0). Render order should put B above A.
    canvas_model.moveItem(2, 0)

    ordered = canvas_model.getRenderItems()
    assert names(ordered) == ["B", "A"]


def test_reparent_moves_node_and_render_order_updates(canvas_model):
    canvas_model.addLayer()  # Layer 1
    layer1 = canvas_model.getItems()[0]
    canvas_model.addLayer()  # Layer 2
    layer2 = canvas_model.getItems()[1]

    canvas_model.addItem(
        {"type": "rectangle", "x": 0, "y": 0, "width": 10, "height": 10, "name": "Rect"}
    )

    # Initially top-level
    assert names(canvas_model.getRenderItems()) == ["Rect"]

    # Reparent into Layer1
    canvas_model.reparentItem(2, layer1.id)
    assert names(canvas_model.getRenderItems()) == ["Rect"]

    # Move Layer1 below Layer2
    canvas_model.moveItem(0, 1)
    # Rect should move with Layer1 group behind Layer2 (no children)
    assert names(canvas_model.getRenderItems()) == ["Rect"]

    # Reparent into Layer2 and ensure render order reflects new parent group
    canvas_model.reparentItem(2, layer2.id)
    assert names(canvas_model.getRenderItems()) == ["Rect"]
