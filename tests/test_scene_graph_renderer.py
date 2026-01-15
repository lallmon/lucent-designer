# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for SceneGraphRenderer Phase 5 - incremental updates and caching."""


class TestCanvasModelGetItem:
    """Tests for getItem and getItemIndex methods added for SceneGraphRenderer."""

    def test_get_item_valid_index(self, canvas_model, history_manager):
        """getItem returns the CanvasItem at a valid index."""
        from test_helpers import make_rectangle

        canvas_model.addItem(make_rectangle())
        item = canvas_model.getItem(0)
        assert item is not None
        assert hasattr(item, "geometry")

    def test_get_item_invalid_index_negative(self, canvas_model):
        """getItem returns None for negative index."""
        assert canvas_model.getItem(-1) is None

    def test_get_item_invalid_index_out_of_bounds(self, canvas_model):
        """getItem returns None for out-of-bounds index."""
        from test_helpers import make_rectangle

        canvas_model.addItem(make_rectangle())
        assert canvas_model.getItem(5) is None

    def test_get_item_empty_model(self, canvas_model):
        """getItem returns None on empty model."""
        assert canvas_model.getItem(0) is None

    def test_get_item_index_valid(self, canvas_model):
        """getItemIndex returns correct index for item in model."""
        from test_helpers import make_rectangle

        canvas_model.addItem(make_rectangle(x=10))
        canvas_model.addItem(make_rectangle(x=20))
        canvas_model.addItem(make_rectangle(x=30))

        item = canvas_model.getItem(1)
        assert canvas_model.getItemIndex(item) == 1

    def test_get_item_index_not_found(self, canvas_model):
        """getItemIndex returns -1 for item not in model."""
        from test_helpers import make_rectangle
        from lucent.canvas_items import RectangleItem
        from lucent.geometry import RectGeometry
        from lucent.transforms import Transform
        from lucent.appearances import Fill

        canvas_model.addItem(make_rectangle())

        # Create an item that's not in the model
        orphan_item = RectangleItem(
            name="Orphan",
            geometry=RectGeometry(0, 0, 100, 100),
            appearances=[Fill(color="#000000")],
            transform=Transform(),
            visible=True,
            locked=False,
        )
        assert canvas_model.getItemIndex(orphan_item) == -1


class TestSceneGraphRendererImport:
    """Basic import/instantiation tests for SceneGraphRenderer."""

    def test_import(self):
        """SceneGraphRenderer can be imported."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        assert SceneGraphRenderer is not None

    def test_has_texture_cache(self, qapp):
        """SceneGraphRenderer has texture cache for rasterized shapes."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()
        # Texture-based approach uses a texture cache
        assert hasattr(renderer, "_texture_cache")
        assert hasattr(renderer, "_textures")
        assert hasattr(renderer, "_texture_nodes")
        assert hasattr(renderer, "_transform_nodes")

    def test_initial_state_needs_rebuild(self, qapp):
        """SceneGraphRenderer starts with needs_full_rebuild True."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()
        assert renderer._needs_full_rebuild is True


class TestSceneGraphRendererSignalHandling:
    """Tests for how SceneGraphRenderer responds to model signals."""

    def test_item_modified_triggers_rebuild(self, qapp, canvas_model):
        """itemModified signal triggers full rebuild (Option C behavior)."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()
        renderer.setModel(canvas_model)

        # Reset state after setModel
        renderer._needs_full_rebuild = False

        # Simulate item modification (signal takes index and changed properties)
        canvas_model.itemModified.emit(0, {"visible": True})

        # Option C simplifies by doing full rebuild on any change
        assert renderer._needs_full_rebuild is True

    def test_item_added_triggers_rebuild(self, qapp, canvas_model):
        """itemAdded signal triggers full rebuild."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()
        renderer.setModel(canvas_model)

        renderer._needs_full_rebuild = False

        canvas_model.itemAdded.emit(0)

        assert renderer._needs_full_rebuild is True

    def test_item_removed_triggers_rebuild(self, qapp, canvas_model):
        """itemRemoved signal triggers full rebuild."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()
        renderer.setModel(canvas_model)

        renderer._needs_full_rebuild = False

        canvas_model.itemRemoved.emit(0)

        assert renderer._needs_full_rebuild is True

    def test_items_cleared_triggers_rebuild(self, qapp, canvas_model):
        """itemsCleared signal triggers full rebuild and clears texture cache."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()
        renderer.setModel(canvas_model)

        # Reset rebuild flag
        renderer._needs_full_rebuild = False

        canvas_model.itemsCleared.emit()

        # Should trigger rebuild
        assert renderer._needs_full_rebuild is True


class TestSceneGraphRendererZoomPanning:
    """Tests for zoom and pan property handling."""

    def test_zoom_change_triggers_rebuild(self, qapp):
        """Changing zoomLevel triggers full rebuild for stroke widths."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()
        renderer._needs_full_rebuild = False

        renderer.zoomLevel = 2.0

        assert renderer._needs_full_rebuild is True
        assert renderer.zoomLevel == 2.0

    def test_tile_origin_change_triggers_rebuild(self, qapp):
        """Changing tile origin triggers rebuild for coordinate offsets."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()
        renderer._needs_full_rebuild = False

        renderer.tileOriginX = 100.0
        renderer._needs_full_rebuild = False  # Reset after first change

        renderer.tileOriginY = 200.0

        assert renderer._needs_full_rebuild is True
        assert renderer.tileOriginX == 100.0
        assert renderer.tileOriginY == 200.0

    def test_zoom_no_change_no_rebuild(self, qapp):
        """Setting same zoomLevel doesn't trigger rebuild."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()
        renderer.zoomLevel = 2.0
        renderer._needs_full_rebuild = False

        renderer.zoomLevel = 2.0  # Same value

        assert renderer._needs_full_rebuild is False

    def test_tile_origin_x_no_change_no_rebuild(self, qapp):
        """Setting same tileOriginX doesn't trigger rebuild."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()
        renderer.tileOriginX = 100.0
        renderer._needs_full_rebuild = False

        renderer.tileOriginX = 100.0  # Same value

        assert renderer._needs_full_rebuild is False

    def test_tile_origin_y_no_change_no_rebuild(self, qapp):
        """Setting same tileOriginY doesn't trigger rebuild."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()
        renderer.tileOriginY = 200.0
        renderer._needs_full_rebuild = False

        renderer.tileOriginY = 200.0  # Same value

        assert renderer._needs_full_rebuild is False


class TestSceneGraphRendererUpdatePaintNode:
    """Tests for updatePaintNode scene graph building."""

    def test_returns_old_node_when_no_model(self, qapp):
        """updatePaintNode returns old_node unchanged if no model set."""
        from lucent.scene_graph_renderer import SceneGraphRenderer
        from PySide6.QtQuick import QSGNode

        renderer = SceneGraphRenderer()
        old_node = QSGNode()

        result = renderer.updatePaintNode(old_node, None)

        assert result is old_node

    def test_creates_new_node_when_old_is_none(self, qapp, canvas_model):
        """updatePaintNode creates new QSGNode if old_node is None."""
        from lucent.scene_graph_renderer import SceneGraphRenderer
        from PySide6.QtQuick import QSGNode

        renderer = SceneGraphRenderer()
        renderer.setModel(canvas_model)

        result = renderer.updatePaintNode(None, None)

        assert result is not None
        assert isinstance(result, QSGNode)

    def test_reuses_existing_node(self, qapp, canvas_model):
        """updatePaintNode reuses old_node if provided."""
        from lucent.scene_graph_renderer import SceneGraphRenderer
        from PySide6.QtQuick import QSGNode

        renderer = SceneGraphRenderer()
        renderer.setModel(canvas_model)
        old_node = QSGNode()

        result = renderer.updatePaintNode(old_node, None)

        assert result is old_node

    def test_clears_rebuild_flag_after_rebuild(self, qapp, canvas_model):
        """updatePaintNode clears _needs_full_rebuild after rebuilding."""
        from lucent.scene_graph_renderer import SceneGraphRenderer
        from PySide6.QtQuick import QSGNode

        renderer = SceneGraphRenderer()
        renderer.setModel(canvas_model)
        renderer._needs_full_rebuild = True

        renderer.updatePaintNode(QSGNode(), None)

        assert renderer._needs_full_rebuild is False


class TestSceneGraphRendererRebuildNodes:
    """Tests for _rebuild_nodes method."""

    def test_clears_node_lists_on_rebuild(self, qapp, canvas_model):
        """_rebuild_nodes clears texture/transform node lists."""
        from lucent.scene_graph_renderer import SceneGraphRenderer
        from PySide6.QtQuick import QSGNode

        renderer = SceneGraphRenderer()
        renderer.setModel(canvas_model)
        renderer._textures = ["fake1", "fake2"]
        renderer._texture_nodes = ["node1"]
        renderer._transform_nodes = ["trans1"]

        root = QSGNode()
        renderer._rebuild_nodes(root)

        assert len(renderer._textures) == 0
        assert len(renderer._texture_nodes) == 0
        assert len(renderer._transform_nodes) == 0

    def test_early_return_when_no_model(self, qapp):
        """_rebuild_nodes returns early if no model."""
        from lucent.scene_graph_renderer import SceneGraphRenderer
        from PySide6.QtQuick import QSGNode

        renderer = SceneGraphRenderer()
        root = QSGNode()

        # Should not raise
        renderer._rebuild_nodes(root)

        assert root.childCount() == 0

    def test_removes_existing_children(self, qapp, canvas_model):
        """_rebuild_nodes removes existing child nodes."""
        from lucent.scene_graph_renderer import SceneGraphRenderer
        from PySide6.QtQuick import QSGNode

        renderer = SceneGraphRenderer()
        renderer.setModel(canvas_model)

        root = QSGNode()
        child1 = QSGNode()
        child2 = QSGNode()
        root.appendChildNode(child1)
        root.appendChildNode(child2)
        assert root.childCount() == 2

        renderer._rebuild_nodes(root)

        # Children should be removed (no window = no new nodes added)
        assert root.childCount() == 0


class TestSceneGraphRendererItemModified:
    """Tests for _on_item_modified cache invalidation."""

    def test_invalidates_layer_cache_by_id(self, qapp, canvas_model, history_manager):
        """_on_item_modified invalidates texture cache for items with id attribute."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        # Add a layer (which has an id attribute)
        canvas_model.addItem({"type": "layer", "name": "Test Layer"})
        layer = canvas_model.getItem(0)
        layer_id = layer.id

        renderer = SceneGraphRenderer()
        renderer.setModel(canvas_model)

        # Manually add to cache to test invalidation logic
        renderer._texture_cache._cache[layer_id] = "dummy_entry"
        assert layer_id in renderer._texture_cache._cache

        # Simulate item modification
        renderer._on_item_modified(0, {"visible": False})

        # Cache should be invalidated
        assert layer_id not in renderer._texture_cache._cache

    def test_skips_invalidation_for_items_without_id(
        self, qapp, canvas_model, history_manager
    ):
        """_on_item_modified skips cache invalidation for items without id."""
        from lucent.scene_graph_renderer import SceneGraphRenderer
        from test_helpers import make_rectangle

        # Add a shape (which doesn't have an id attribute)
        canvas_model.addItem(make_rectangle())
        item = canvas_model.getItem(0)
        assert not hasattr(item, "id")

        renderer = SceneGraphRenderer()
        renderer.setModel(canvas_model)

        # Simulate modification - should not raise
        renderer._on_item_modified(0, {"fill": "#ff0000"})

        # Rebuild should still be triggered
        assert renderer._needs_full_rebuild is True


class TestSceneGraphRendererSetModel:
    """Tests for setModel method."""

    def test_ignores_non_canvas_model(self, qapp):
        """setModel ignores objects that aren't CanvasModel."""
        from lucent.scene_graph_renderer import SceneGraphRenderer
        from PySide6.QtCore import QObject

        renderer = SceneGraphRenderer()
        not_a_model = QObject()

        renderer.setModel(not_a_model)

        assert renderer._model is None

    def test_connects_all_signals(self, qapp, canvas_model):
        """setModel connects to all required model signals."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()
        renderer.setModel(canvas_model)

        # Verify signals trigger rebuild
        renderer._needs_full_rebuild = False
        canvas_model.itemsReordered.emit()
        assert renderer._needs_full_rebuild is True


class TestSceneGraphRendererCreateNodeForItem:
    """Tests for _create_node_for_item method."""

    def test_returns_none_for_invisible_item(self, qapp):
        """Invisible items return None."""
        from lucent.scene_graph_renderer import SceneGraphRenderer
        from lucent.canvas_items import RectangleItem
        from lucent.geometry import RectGeometry
        from lucent.transforms import Transform
        from lucent.appearances import Fill
        from lucent.texture_cache import TextureCache

        renderer = SceneGraphRenderer()

        item = RectangleItem(
            name="Hidden",
            geometry=RectGeometry(0, 0, 100, 100),
            appearances=[Fill(color="#ff0000")],
            transform=Transform(),
            visible=False,
            locked=False,
        )

        result = renderer._create_node_for_item(item, 0, 0, None, TextureCache())

        assert result is None

    def test_returns_none_for_layer_item(self, qapp):
        """LayerItem returns None (containers aren't rendered directly)."""
        from lucent.scene_graph_renderer import SceneGraphRenderer
        from lucent.canvas_items import LayerItem
        from lucent.texture_cache import TextureCache

        renderer = SceneGraphRenderer()
        layer = LayerItem(name="Layer 1", visible=True, locked=False)

        result = renderer._create_node_for_item(layer, 0, 0, None, TextureCache())

        assert result is None

    def test_returns_none_for_group_item(self, qapp):
        """GroupItem returns None (containers aren't rendered directly)."""
        from lucent.scene_graph_renderer import SceneGraphRenderer
        from lucent.canvas_items import GroupItem
        from lucent.texture_cache import TextureCache

        renderer = SceneGraphRenderer()
        group = GroupItem(name="Group 1", visible=True, locked=False, parent_id="")

        result = renderer._create_node_for_item(group, 0, 0, None, TextureCache())

        assert result is None

    def test_returns_none_when_no_cache_entry(self, qapp):
        """Returns None if texture cache returns None."""
        from lucent.scene_graph_renderer import SceneGraphRenderer
        from lucent.canvas_items import RectangleItem
        from lucent.geometry import RectGeometry
        from lucent.transforms import Transform
        from lucent.appearances import Fill
        from lucent.texture_cache import TextureCache

        renderer = SceneGraphRenderer()

        # Create item with empty bounds (will return None from cache)
        item = RectangleItem(
            name="Empty",
            geometry=RectGeometry(0, 0, 0, 0),
            appearances=[Fill(color="#ff0000")],
            transform=Transform(),
            visible=True,
            locked=False,
        )

        result = renderer._create_node_for_item(item, 0, 0, None, TextureCache())

        assert result is None


class TestSceneGraphRendererCreateTransformWrapper:
    """Tests for _create_transform_wrapper method."""

    def test_creates_transform_node_with_rotation(self, qapp):
        """Creates QSGTransformNode for rotated items."""
        from lucent.scene_graph_renderer import SceneGraphRenderer
        from lucent.canvas_items import RectangleItem
        from lucent.geometry import RectGeometry
        from lucent.transforms import Transform
        from lucent.appearances import Fill
        from PySide6.QtQuick import QSGNode, QSGTransformNode
        from PySide6.QtCore import QRectF

        renderer = SceneGraphRenderer()

        item = RectangleItem(
            name="Rotated",
            geometry=RectGeometry(0, 0, 100, 100),
            appearances=[Fill(color="#ff0000")],
            transform=Transform(rotate=45.0),
            visible=True,
            locked=False,
        )

        child_node = QSGNode()
        bounds = QRectF(0, 0, 100, 100)

        result = renderer._create_transform_wrapper(item, child_node, 0, 0, bounds)

        assert result is not None
        assert isinstance(result, QSGTransformNode)
        assert result.childCount() == 1
        assert len(renderer._transform_nodes) == 1

    def test_creates_transform_node_with_scale(self, qapp):
        """Creates QSGTransformNode for scaled items."""
        from lucent.scene_graph_renderer import SceneGraphRenderer
        from lucent.canvas_items import RectangleItem
        from lucent.geometry import RectGeometry
        from lucent.transforms import Transform
        from lucent.appearances import Fill
        from PySide6.QtQuick import QSGNode, QSGTransformNode
        from PySide6.QtCore import QRectF

        renderer = SceneGraphRenderer()

        item = RectangleItem(
            name="Scaled",
            geometry=RectGeometry(50, 50, 100, 100),
            appearances=[Fill(color="#00ff00")],
            transform=Transform(scale_x=2.0, scale_y=1.5),
            visible=True,
            locked=False,
        )

        child_node = QSGNode()
        bounds = QRectF(50, 50, 100, 100)

        result = renderer._create_transform_wrapper(item, child_node, 100, 100, bounds)

        assert result is not None
        assert isinstance(result, QSGTransformNode)

    def test_applies_offset_to_origin(self, qapp):
        """Transform origin accounts for offset."""
        from lucent.scene_graph_renderer import SceneGraphRenderer
        from lucent.canvas_items import RectangleItem
        from lucent.geometry import RectGeometry
        from lucent.transforms import Transform
        from lucent.appearances import Fill
        from PySide6.QtQuick import QSGNode
        from PySide6.QtCore import QRectF

        renderer = SceneGraphRenderer()

        # Item with custom origin (center)
        item = RectangleItem(
            name="Centered",
            geometry=RectGeometry(0, 0, 100, 100),
            appearances=[Fill(color="#0000ff")],
            transform=Transform(rotate=90.0, origin_x=0.5, origin_y=0.5),
            visible=True,
            locked=False,
        )

        child_node = QSGNode()
        bounds = QRectF(0, 0, 100, 100)

        # Apply with offset
        result = renderer._create_transform_wrapper(item, child_node, 500, 500, bounds)

        assert result is not None
        # Matrix should be set
        matrix = result.matrix()
        assert not matrix.isIdentity()


class TestSceneGraphRendererPreviewItem:
    """Tests for preview item functionality (setPreviewItem, clearPreview)."""

    def test_set_preview_item_with_valid_data(self, qapp):
        """setPreviewItem parses valid item data and sets preview."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()

        item_data = {
            "type": "rectangle",
            "name": "Preview Rect",
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 50,
            "fill": {"color": "#ff0000", "opacity": 1.0},
        }

        renderer.setPreviewItem(item_data)

        assert renderer._preview_item is not None
        assert renderer._needs_full_rebuild is True

    def test_set_preview_item_with_none_clears_preview(self, qapp):
        """setPreviewItem with None/empty data clears preview."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()

        # First set a preview
        item_data = {
            "type": "rectangle",
            "name": "Preview Rect",
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 50,
            "fill": {"color": "#ff0000", "opacity": 1.0},
        }
        renderer.setPreviewItem(item_data)
        assert renderer._preview_item is not None

        # Then clear it
        renderer.setPreviewItem(None)

        assert renderer._preview_item is None

    def test_set_preview_item_with_invalid_data_clears_preview(self, qapp):
        """setPreviewItem with invalid data sets preview to None."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()

        # Invalid data (missing required fields)
        invalid_data = {"type": "unknown_type", "invalid": True}

        renderer.setPreviewItem(invalid_data)

        assert renderer._preview_item is None

    def test_clear_preview(self, qapp):
        """clearPreview removes preview item and triggers rebuild."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()

        # Set a preview first
        item_data = {
            "type": "ellipse",
            "name": "Preview Ellipse",
            "x": 10,
            "y": 10,
            "width": 80,
            "height": 80,
            "fill": {"color": "#00ff00", "opacity": 0.5},
        }
        renderer.setPreviewItem(item_data)
        assert renderer._preview_item is not None

        renderer._needs_full_rebuild = False

        renderer.clearPreview()

        assert renderer._preview_item is None
        assert renderer._needs_full_rebuild is True

    def test_clear_preview_when_no_preview_set(self, qapp):
        """clearPreview does nothing if no preview is set."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()
        renderer._needs_full_rebuild = False

        renderer.clearPreview()

        # Should not trigger rebuild if nothing was set
        assert renderer._preview_item is None
        assert renderer._needs_full_rebuild is False

    def test_preview_item_clears_preview_cache_on_set(self, qapp):
        """Setting preview item clears the preview cache."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()

        # Add something to preview cache
        renderer._preview_cache._cache["fake_id"] = "fake_entry"
        assert "fake_id" in renderer._preview_cache._cache

        item_data = {
            "type": "rectangle",
            "name": "Preview",
            "x": 0,
            "y": 0,
            "width": 50,
            "height": 50,
            "fill": {"color": "#0000ff", "opacity": 1.0},
        }
        renderer.setPreviewItem(item_data)

        # Preview cache should be cleared
        assert "fake_id" not in renderer._preview_cache._cache

    def test_preview_item_with_stroke(self, qapp):
        """setPreviewItem handles items with stroke appearance."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()

        item_data = {
            "type": "rectangle",
            "name": "Stroked Rect",
            "geometry": {"x": 0, "y": 0, "width": 100, "height": 100},
            "appearances": [
                {"type": "fill", "color": "#ffffff", "opacity": 1.0},
                {
                    "type": "stroke",
                    "color": "#000000",
                    "opacity": 1.0,
                    "width": 5,
                    "align": "center",
                    "cap": "round",
                    "order": "top",
                },
            ],
        }

        renderer.setPreviewItem(item_data)

        assert renderer._preview_item is not None
        # Verify stroke was parsed
        from lucent.appearances import Stroke

        stroke = next(
            (a for a in renderer._preview_item.appearances if isinstance(a, Stroke)),
            None,
        )
        assert stroke is not None
        assert stroke.align == "center"
        assert stroke.cap == "round"
        assert stroke.order == "top"

    def test_preview_item_emits_signal(self, qapp):
        """setPreviewItem emits previewItemChanged signal."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()
        signal_received = []

        renderer.previewItemChanged.connect(lambda: signal_received.append(True))

        item_data = {
            "type": "rectangle",
            "name": "Signal Test",
            "x": 0,
            "y": 0,
            "width": 50,
            "height": 50,
            "fill": {"color": "#ff0000", "opacity": 1.0},
        }
        renderer.setPreviewItem(item_data)

        assert len(signal_received) == 1

    def test_clear_preview_emits_signal(self, qapp):
        """clearPreview emits previewItemChanged signal when preview exists."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()

        # Set preview first
        item_data = {
            "type": "rectangle",
            "name": "Signal Test",
            "x": 0,
            "y": 0,
            "width": 50,
            "height": 50,
            "fill": {"color": "#ff0000", "opacity": 1.0},
        }
        renderer.setPreviewItem(item_data)

        signal_received = []
        renderer.previewItemChanged.connect(lambda: signal_received.append(True))

        renderer.clearPreview()

        assert len(signal_received) == 1

    def test_clear_preview_no_signal_when_no_preview(self, qapp):
        """clearPreview doesn't emit signal if no preview was set."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()
        signal_received = []

        renderer.previewItemChanged.connect(lambda: signal_received.append(True))

        renderer.clearPreview()

        assert len(signal_received) == 0


class TestSceneGraphRendererPreviewPath:
    """Tests for preview path items specifically."""

    def test_preview_path_item(self, qapp):
        """setPreviewItem handles path items."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()

        item_data = {
            "type": "path",
            "name": "Preview Path",
            "geometry": {
                "points": [
                    {"x": 0, "y": 0},
                    {"x": 100, "y": 100},
                    {"x": 200, "y": 50},
                ],
                "closed": False,
            },
            "appearances": [
                {"type": "fill", "color": "#00ff00", "opacity": 0.5},
                {
                    "type": "stroke",
                    "color": "#000000",
                    "opacity": 1.0,
                    "width": 2,
                    "align": "center",
                    "cap": "butt",
                    "order": "top",
                },
            ],
        }

        renderer.setPreviewItem(item_data)

        assert renderer._preview_item is not None

    def test_preview_with_inner_stroke_align(self, qapp):
        """Preview handles inner stroke alignment."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()

        item_data = {
            "type": "ellipse",
            "name": "Inner Stroke",
            "geometry": {"centerX": 50, "centerY": 50, "radiusX": 50, "radiusY": 50},
            "appearances": [
                {"type": "fill", "color": "#ffffff", "opacity": 1.0},
                {
                    "type": "stroke",
                    "color": "#ff0000",
                    "opacity": 1.0,
                    "width": 10,
                    "align": "inner",
                    "cap": "butt",
                    "order": "top",
                },
            ],
        }

        renderer.setPreviewItem(item_data)

        assert renderer._preview_item is not None
        from lucent.appearances import Stroke

        stroke = next(
            (a for a in renderer._preview_item.appearances if isinstance(a, Stroke)),
            None,
        )
        assert stroke.align == "inner"

    def test_preview_with_outer_stroke_align(self, qapp):
        """Preview handles outer stroke alignment."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()

        item_data = {
            "type": "rectangle",
            "name": "Outer Stroke",
            "geometry": {"x": 50, "y": 50, "width": 150, "height": 100},
            "appearances": [
                {"type": "fill", "color": "#0000ff", "opacity": 0.8},
                {
                    "type": "stroke",
                    "color": "#ffff00",
                    "opacity": 1.0,
                    "width": 8,
                    "align": "outer",
                    "cap": "square",
                    "order": "bottom",
                },
            ],
        }

        renderer.setPreviewItem(item_data)

        assert renderer._preview_item is not None
        from lucent.appearances import Stroke

        stroke = next(
            (a for a in renderer._preview_item.appearances if isinstance(a, Stroke)),
            None,
        )
        assert stroke.align == "outer"
        assert stroke.cap == "square"
        assert stroke.order == "bottom"

    def test_has_preview_cache(self, qapp):
        """SceneGraphRenderer has separate preview cache."""
        from lucent.scene_graph_renderer import SceneGraphRenderer

        renderer = SceneGraphRenderer()

        assert hasattr(renderer, "_preview_cache")
        assert renderer._preview_cache is not renderer._texture_cache
