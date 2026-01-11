# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Integration tests for LayerPanel-related model behaviors.

These tests verify the Python-QML contract that LayerPanel.qml depends on.
By testing the model methods LayerPanel calls, we ensure refactoring
the QML won't break functionality as long as these contracts hold.
"""

from pathlib import Path

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent

from lucent.canvas_model import CanvasModel


class TestLayerPanelModelBehaviors:
    """Tests for model behaviors that LayerPanel.qml relies on."""

    @pytest.fixture
    def model(self, qapp):
        return CanvasModel()

    def test_add_layer_creates_layer_item(self, model):
        """LayerPanel calls canvasModel.addLayer() on button tap."""
        model.addLayer()

        assert model.count() == 1
        data = model.getItemData(0)
        assert data is not None
        assert data["type"] == "layer"
        assert "Layer" in data["name"]

    def test_add_group_creates_group_item(self, model):
        """LayerPanel calls canvasModel.addItem({type: 'group'})."""
        model.addItem({"type": "group"})

        assert model.count() == 1
        data = model.getItemData(0)
        assert data is not None
        assert data["type"] == "group"

    def test_toggle_visibility_flips_state(self, model):
        """LayerPanel calls canvasModel.toggleVisibility(index)."""
        model.addLayer()
        data = model.getItemData(0)
        assert data is not None
        assert data["visible"] is True

        model.toggleVisibility(0)
        data = model.getItemData(0)
        assert data is not None
        assert data["visible"] is False

        model.toggleVisibility(0)
        data = model.getItemData(0)
        assert data is not None
        assert data["visible"] is True

    def test_toggle_locked_flips_state(self, model):
        """LayerPanel calls canvasModel.toggleLocked(index)."""
        model.addLayer()
        data = model.getItemData(0)
        assert data is not None
        assert data["locked"] is False

        model.toggleLocked(0)
        data = model.getItemData(0)
        assert data is not None
        assert data["locked"] is True

    def test_rename_item_updates_name(self, model):
        """LayerPanel calls canvasModel.renameItem(index, name)."""
        model.addLayer()
        model.renameItem(0, "My Custom Layer")

        data = model.getItemData(0)
        assert data is not None
        assert data["name"] == "My Custom Layer"

    def test_move_item_up_in_model(self, model):
        """Moving item to higher index (drag up in display, down in model)."""
        # Model order: [A@0, B@1, C@2, D@3]
        # Display order (reversed): [D, C, B, A] from top to bottom
        model.addItem({"type": "rectangle", "name": "A"})
        model.addItem({"type": "rectangle", "name": "B"})
        model.addItem({"type": "rectangle", "name": "C"})
        model.addItem({"type": "rectangle", "name": "D"})

        # Move A from index 0 to index 2 (dragging A up in display)
        model.moveItem(0, 2)

        # Expected model: [B@0, C@1, A@2, D@3]
        assert model.getItemData(0)["name"] == "B"
        assert model.getItemData(1)["name"] == "C"
        assert model.getItemData(2)["name"] == "A"
        assert model.getItemData(3)["name"] == "D"

    def test_move_item_down_in_model(self, model):
        """Moving item to lower index (drag down in display, up in model).

        This tests the off-by-one fix: when dragging from higher model index
        to lower, the target must be adjusted for removal-insertion semantics.
        """
        # Model order: [A@0, B@1, C@2, D@3]
        # Display order (reversed): [D, C, B, A] from top to bottom
        model.addItem({"type": "rectangle", "name": "A"})
        model.addItem({"type": "rectangle", "name": "B"})
        model.addItem({"type": "rectangle", "name": "C"})
        model.addItem({"type": "rectangle", "name": "D"})

        # Move D from index 3 to index 1 (dragging D down in display)
        model.moveItem(3, 1)

        # Expected model: [A@0, D@1, B@2, C@3]
        assert model.getItemData(0)["name"] == "A"
        assert model.getItemData(1)["name"] == "D"
        assert model.getItemData(2)["name"] == "B"
        assert model.getItemData(3)["name"] == "C"

    def test_move_item_to_bottom_edge(self, model):
        """Moving item to very bottom of list (model index 0).

        This tests the edge case fix: dropping at the bottom of the display
        should move the item to model index 0 without the off-by-one adjustment.
        """
        # Model order: [A@0, B@1, C@2, D@3]
        # Display order (reversed): [D, C, B, A] from top to bottom
        model.addItem({"type": "rectangle", "name": "A"})
        model.addItem({"type": "rectangle", "name": "B"})
        model.addItem({"type": "rectangle", "name": "C"})
        model.addItem({"type": "rectangle", "name": "D"})

        # Move D from index 3 to index 0 (dragging D to very bottom of display)
        model.moveItem(3, 0)

        # Expected model: [D@0, A@1, B@2, C@3]
        # Display: [C, B, A, D] - D is now at the bottom
        assert model.getItemData(0)["name"] == "D"
        assert model.getItemData(1)["name"] == "A"
        assert model.getItemData(2)["name"] == "B"
        assert model.getItemData(3)["name"] == "C"

    def test_group_items_creates_group(self, model):
        """LayerPanel group button calls canvasModel.groupItems(indices)."""
        model.addItem({"type": "rectangle"})
        model.addItem({"type": "ellipse"})

        group_idx = model.groupItems([0, 1])

        assert group_idx >= 0
        group_data = model.getItemData(group_idx)
        assert group_data is not None
        assert group_data["type"] == "group"

    def test_reparent_item_changes_parent(self, model):
        """LayerPanel drag-into-group calls canvasModel.reparentItem()."""
        model.addLayer()
        layer_data = model.getItemData(0)
        assert layer_data is not None
        layer_id = layer_data["id"]

        model.addItem({"type": "rectangle"})

        # reparentItem sets parent and moves item; find rectangle after reparent
        model.reparentItem(1, layer_id)

        # Find the rectangle after reparenting (indices may have shifted)
        rect_data = None
        for i in range(model.count()):
            data = model.getItemData(i)
            if data and data["type"] == "rectangle":
                rect_data = data
                break

        assert rect_data is not None, "Rectangle not found after reparent"
        assert rect_data["parentId"] == layer_id

    def test_reparent_item_default_position_below_container(self, model):
        """Reparenting without explicit position places item below container.

        When dropping onto a container center (not between children), the
        item should appear as the first child below the container in display.
        """
        # Setup: Items added before layer, so layer is at top of display
        model.addItem({"type": "rectangle", "name": "Square1"})
        model.addItem({"type": "rectangle", "name": "Square2"})
        model.addLayer()

        layer_data = model.getItemData(2)
        layer_id = layer_data["id"]

        # Reparent without explicit position (simulates dropping onto container center)
        model.reparentItem(0, layer_id)  # No insert_index

        # Square1 should now be a child of Layer, positioned right below it
        # Model order should be: [Square2@0, Square1@1, Layer@2]
        # Display (reversed): Layer, Square1, Square2
        sq1_data = model.getItemData(1)
        assert sq1_data["name"] == "Square1"
        assert sq1_data["parentId"] == layer_id

    def test_reparent_item_with_position_inserts_correctly(self, model):
        """Reparenting with explicit position places item at correct index.

        This tests the fix for dropping items between existing children:
        when dropping between Square1 and Square2, the item should end up
        between them, not at the bottom of the container.
        """
        # Setup: Square3 (top-level), Square1, Square2 (children of Layer)
        model.addItem({"type": "rectangle", "name": "Square3"})
        model.addItem({"type": "rectangle", "name": "Square1"})
        model.addItem({"type": "rectangle", "name": "Square2"})
        model.addLayer()

        layer_data = model.getItemData(3)
        layer_id = layer_data["id"]

        # Reparent Square1 and Square2 to Layer
        model.reparentItem(1, layer_id)
        model.reparentItem(1, layer_id)

        # Model: [Square3@0, Square1@1, Square2@2, Layer@3]
        assert model.getItemData(0)["name"] == "Square3"
        assert model.getItemData(1)["name"] == "Square1"
        assert model.getItemData(2)["name"] == "Square2"

        # Reparent Square3 to position 1 (between Square1 and Square2)
        model.reparentItem(0, layer_id, 1)

        # Expected: [Square1@0, Square3@1, Square2@2, Layer@3]
        assert model.getItemData(0)["name"] == "Square1"
        assert model.getItemData(1)["name"] == "Square3"
        assert model.getItemData(2)["name"] == "Square2"
        assert model.getItemData(1)["parentId"] == layer_id

    def test_remove_item_decreases_count(self, model):
        """LayerPanel delete calls canvasModel.removeItem(index)."""
        model.addLayer()
        model.addItem({"type": "rectangle"})
        assert model.count() == 2

        model.removeItem(1)
        assert model.count() == 1

    def test_container_bounds_fallback_for_selection_overlay(self, model):
        """Layers/groups need getBoundingBox for selection overlay.

        getGeometryBounds returns None for containers (no geometry attribute),
        but getBoundingBox computes union of children's bounds. The selection
        overlay in Canvas.qml relies on this fallback behavior.
        """
        model.addLayer()
        layer_data = model.getItemData(0)
        layer_id = layer_data["id"]

        # Add a child rectangle
        model.addItem(
            {
                "type": "rectangle",
                "name": "Child",
                "geometry": {"x": 100, "y": 100, "width": 50, "height": 50},
            }
        )
        model.reparentItem(1, layer_id)

        # Find the layer's new index after reparent
        layer_idx = None
        for i in range(model.count()):
            if model.getItemData(i)["type"] == "layer":
                layer_idx = i
                break

        # getGeometryBounds returns None for layers (no geometry attribute)
        assert model.getGeometryBounds(layer_idx) is None

        # getBoundingBox returns union of children's bounds
        bounds = model.getBoundingBox(layer_idx)
        assert bounds is not None
        assert bounds["x"] == 100
        assert bounds["y"] == 100
        assert bounds["width"] == 50
        assert bounds["height"] == 50

    def test_union_bounding_box_for_multiselection(self, model):
        """Multi-selection needs getUnionBoundingBox for selection overlay."""
        model.addItem(
            {
                "type": "rectangle",
                "name": "Rect1",
                "geometry": {"x": 0, "y": 0, "width": 50, "height": 50},
            }
        )
        model.addItem(
            {
                "type": "rectangle",
                "name": "Rect2",
                "geometry": {"x": 100, "y": 100, "width": 50, "height": 50},
            }
        )

        # Get union bounds for both items
        union = model.getUnionBoundingBox([0, 1])
        assert union is not None
        assert union["x"] == 0
        assert union["y"] == 0
        assert union["width"] == 150
        assert union["height"] == 150

    def test_model_roles_match_qml_expectations(self, model):
        """Verify model exposes roles that LayerPanel.qml binds to."""
        model.addLayer()
        model.addItem({"type": "rectangle", "parent_id": ""})

        # Check role names exist (LayerPanel binds to these)
        role_names = model.roleNames()
        expected_roles = [
            b"name",
            b"itemType",
            b"itemIndex",
            b"itemId",
            b"parentId",
            b"modelVisible",
            b"modelLocked",
        ]
        for role in expected_roles:
            assert role in role_names.values(), f"Missing role: {role}"


class TestLayerPanelQmlLoads:
    """Smoke test: verify LayerPanel.qml compiles without errors."""

    def test_layer_panel_loads(self, qml_engine, canvas_model):
        """Verify LayerPanel.qml compiles and instantiates."""
        # Register model as context property (same as main.py)
        qml_engine.rootContext().setContextProperty("canvasModel", canvas_model)

        # Add components import path
        components_dir = Path(__file__).parent.parent / "components"
        qml_engine.addImportPath(str(components_dir))

        # Load LayerPanel
        qml_file = components_dir / "panels" / "LayerPanel.qml"
        component = QQmlComponent(qml_engine, QUrl.fromLocalFile(str(qml_file)))

        if component.isError():
            errors = "\n".join(e.toString() for e in component.errors())
            pytest.fail(f"LayerPanel.qml failed to load:\n{errors}")

        obj = component.create()
        assert obj is not None, "Failed to instantiate LayerPanel"

        obj.deleteLater()
