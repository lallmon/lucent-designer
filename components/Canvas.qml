import QtQuick
import QtQuick.Controls
import CanvasRendering 1.0
import "." as Lucent

// Canvas component focused on data management and tool coordination
Item {
    id: root

    // Viewport properties (provided by parent Viewport component)
    property real zoomLevel: 1.0
    property real offsetX: 0
    property real offsetY: 0

    // Cursor position in canvas coordinates
    property real cursorX: 0
    property real cursorY: 0

    // Signal for pan requests (handled by Viewport)
    signal panRequested(real dx, real dy)

    // Drawing mode
    property string drawingMode: ""  // "" for pan, "rectangle" for drawing rectangles, "ellipse" for drawing ellipses

    HitTestHelper {
        id: hitTestHelper
    }

    // Tool settings - bound from parent (App.qml)
    property var toolSettings: null

    // Current cursor shape (for dynamic cursor changes)
    property int currentCursorShape: Qt.OpenHandCursor

    // Selection transform (updated reactively via signal)
    property var _selectionTransform: null

    // Selection geometry bounds (untransformed, from model)
    property var _selectionGeometryBounds: null

    // Canvas content (no transforms - handled by parent Viewport)
    Item {
        id: shapesLayer
        anchors.centerIn: parent
        width: 0
        height: 0

        // Renderer sized to the current viewport; we only render what is visible.
        CanvasRenderer {
            id: canvasRenderer
            // Expand with zoom and modest padding; cap under GPU limits to reduce overdraw.
            readonly property real _pad: 1000
            width: Math.min(14000, (root.width / Math.max(root.zoomLevel, 0.001)) + _pad * 2)
            height: Math.min(14000, (root.height / Math.max(root.zoomLevel, 0.001)) + _pad * 2)
            x: -width / 2
            y: -height / 2
            zoomLevel: root.zoomLevel

            Component.onCompleted: {
                setModel(canvasModel);
            }
        }

        // Selection indicator overlay
        SelectionOverlay {
            id: selectionOverlay
            geometryBounds: root._selectionGeometryBounds
            itemTransform: root._selectionTransform
            zoomLevel: root.zoomLevel
        }

        // Select tool for object selection (panning handled by Viewport)
        SelectTool {
            id: selectTool
            active: root.drawingMode === ""
            hitTestCallback: root.hitTest
            viewportToCanvasCallback: root.viewportToCanvas
            getBoundsCallback: function (idx) {
                return canvasModel.getBoundingBox(idx);
            }

            onPanDelta: (dx, dy) => {
                root.panRequested(dx, dy);
            }

            onCursorShapeChanged: shape => {
                root.currentCursorShape = shape;
            }

            onObjectClicked: (viewportX, viewportY, modifiers) => {
                var canvasCoords = root.viewportToCanvas(viewportX, viewportY);
                root.selectItemAt(canvasCoords.x, canvasCoords.y, !!(modifiers & Qt.ControlModifier));
            }

            onObjectDragged: (viewportDx, viewportDy) => {
                root.updateSelectedItemPosition(viewportDx / root.zoomLevel, viewportDy / root.zoomLevel);
            }
        }

        // Dynamic tool loader - loads the appropriate tool based on drawingMode
        Loader {
            id: currentToolLoader
            active: root.drawingMode !== "" && root.drawingMode !== "select"

            source: {
                var toolMap = {
                    "rectangle": "tools/RectangleTool.qml",
                    "ellipse": "tools/EllipseTool.qml",
                    "pen": "tools/PenTool.qml",
                    "text": "tools/TextTool.qml"
                };
                return toolMap[root.drawingMode] || "";
            }

            onLoaded: {
                if (item) {
                    // Bind properties to the loaded tool
                    item.zoomLevel = Qt.binding(function () {
                        return root.zoomLevel;
                    });
                    item.active = Qt.binding(function () {
                        return root.drawingMode !== "" && root.drawingMode !== "select";
                    });
                    item.settings = Qt.binding(function () {
                        return root.toolSettings[root.drawingMode];
                    });
                    if (item.hasOwnProperty("viewportWidth")) {
                        item.viewportWidth = Qt.binding(function () {
                            return root.width;
                        });
                    }
                    if (item.hasOwnProperty("viewportHeight")) {
                        item.viewportHeight = Qt.binding(function () {
                            return root.height;
                        });
                    }

                    // Connect the itemCompleted signal
                    item.itemCompleted.connect(root.handleItemCompleted);
                }
            }
        }
    }

    // Convert viewport coordinates to canvas coordinates
    // Called from Viewport MouseArea (outside transforms)
    function viewportToCanvas(viewportX, viewportY) {
        var centerX = root.width / 2;
        var centerY = root.height / 2;

        // Inverse transform: undo pan, then undo zoom
        var canvasX = (viewportX - centerX - root.offsetX) / root.zoomLevel;
        var canvasY = (viewportY - centerY - root.offsetY) / root.zoomLevel;

        return {
            x: canvasX,
            y: canvasY
        };
    }

    // Public event handlers called from Viewport MouseArea
    function handleMousePress(viewportX, viewportY, button, modifiers) {
        // Delegate to active tool (SelectTool uses viewport coords)
        if (root.drawingMode === "") {
            selectTool.handlePress(viewportX, viewportY, button, modifiers);
        } else if (currentToolLoader.item && currentToolLoader.item.handleMousePress) {
            var canvasCoords = viewportToCanvas(viewportX, viewportY);
            currentToolLoader.item.handleMousePress(canvasCoords.x, canvasCoords.y, button, modifiers);
        }
    }

    function handleMouseRelease(viewportX, viewportY, button, modifiers) {
        if (root.drawingMode === "") {
            selectTool.handleRelease(viewportX, viewportY, button, modifiers);
        } else if (currentToolLoader.item && currentToolLoader.item.handleMouseRelease) {
            var canvasCoords = viewportToCanvas(viewportX, viewportY);
            currentToolLoader.item.handleMouseRelease(canvasCoords.x, canvasCoords.y);
        }
    }

    function handleMouseClick(viewportX, viewportY, button) {
        if (currentToolLoader.item && button === Qt.LeftButton) {
            var canvasCoords = viewportToCanvas(viewportX, viewportY);
            currentToolLoader.item.handleClick(canvasCoords.x, canvasCoords.y);
        }
    }

    function handleMouseMove(viewportX, viewportY, modifiers) {
        // Update cursor position in canvas coordinates
        var canvasCoords = viewportToCanvas(viewportX, viewportY);
        root.cursorX = canvasCoords.x;
        root.cursorY = canvasCoords.y;

        // Only log if coordinates are invalid
        if (!isFinite(root.cursorX) || !isFinite(root.cursorY)) {
            console.error("[handleMouseMove] CRITICAL: Invalid canvas coords!", "cursorX:", root.cursorX, "cursorY:", root.cursorY);
        }

        // Delegate to active tool
        if (root.drawingMode === "") {
            selectTool.handleMouseMove(viewportX, viewportY);
        } else if (currentToolLoader.item) {
            currentToolLoader.item.handleMouseMove(canvasCoords.x, canvasCoords.y, modifiers);
        }
    }

    // Generic item completion handler
    function handleItemCompleted(itemData) {
        // Add item to the model
        canvasModel.addItem(itemData);

        // Select the newly created item (it's at the end of the list)
        var newIndex = canvasModel.count() - 1;
        Lucent.SelectionManager.selectedIndices = [newIndex];
        Lucent.SelectionManager.selectedItemIndex = newIndex;
        Lucent.SelectionManager.selectedItem = canvasModel.getItemData(newIndex);
        refreshSelectionTransform();
        refreshSelectionGeometryBounds();
    }

    // Set the drawing mode
    function setDrawingMode(mode) {
        // Reset any active tool
        if (drawingMode === "") {
            selectTool.reset();
        } else if (currentToolLoader.item) {
            currentToolLoader.item.reset();
        }

        // "select" mode is the same as no mode (pan/zoom)
        if (mode === "select") {
            drawingMode = "";
        } else {
            drawingMode = mode;
        }

        // Set cursor based on mode type
        root.currentCursorShape = (drawingMode !== "") ? Qt.CrossCursor : Qt.OpenHandCursor;

        // Clear selection when switching to drawing tools
        if (drawingMode !== "") {
            Lucent.SelectionManager.selectedItemIndex = -1;
            Lucent.SelectionManager.selectedItem = null;
        }
    }

    // Hit test to find item at canvas coordinates
    function hitTest(canvasX, canvasY) {
        return hitTestHelper.hitTest(canvasModel.getItemsForHitTest(), canvasX, canvasY, function (idx) {
            return canvasModel.getBoundingBox(idx);
        });
    }

    // Select item at canvas coordinates
    function selectItemAt(canvasX, canvasY, multiSelect) {
        var hitIndex = hitTest(canvasX, canvasY);
        updateSelection(hitIndex, multiSelect === true);
    }

    function selectionTransform() {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx < 0 || !canvasModel)
            return null;
        return canvasModel.getItemTransform(idx);
    }

    function refreshSelectionTransform() {
        _selectionTransform = selectionTransform();
    }

    function refreshSelectionGeometryBounds() {
        var indices = Lucent.SelectionManager.currentSelectionIndices();
        if (indices.length === 0 || !canvasModel) {
            _selectionGeometryBounds = null;
            return;
        }

        if (indices.length === 1) {
            // Single selection: try geometry bounds first, fall back to bounding box
            var bounds = canvasModel.getGeometryBounds(indices[0]);
            if (!bounds) {
                bounds = canvasModel.getBoundingBox(indices[0]);
            }
            _selectionGeometryBounds = bounds;
        } else {
            // Multi-selection: compute union of all bounding boxes
            _selectionGeometryBounds = canvasModel.getUnionBoundingBox(indices);
        }
    }

    function updateSelection(hitIndex, multiSelect) {
        Lucent.SelectionManager.toggleSelection(hitIndex, multiSelect);
    }

    function updateSelectedItemPosition(canvasDx, canvasDy) {
        var indices = Lucent.SelectionManager.selectedIndices || [];
        if (indices.length === 0)
            return;

        var containerIds = {};
        for (var i = 0; i < indices.length; i++) {
            var d = canvasModel.getItemData(indices[i]);
            if (d && (d.type === "group" || d.type === "layer") && d.id) {
                containerIds[d.id] = true;
            }
        }

        var movedContainers = {};
        for (var j = 0; j < indices.length; j++) {
            var idx = indices[j];
            var data = canvasModel.getItemData(idx);
            if (!data)
                continue;
            if (canvasModel.isEffectivelyLocked(idx))
                continue;

            if (data.type === "group" || data.type === "layer") {
                if (movedContainers[data.id])
                    continue;
                movedContainers[data.id] = true;
                canvasModel.moveGroup(idx, canvasDx, canvasDy);
            } else if (data.type === "rectangle") {
                if (data.parentId && containerIds[data.parentId])
                    continue;
                // Update geometry with new position
                var rectGeom = Object.assign({}, data.geometry);
                rectGeom.x = rectGeom.x + canvasDx;
                rectGeom.y = rectGeom.y + canvasDy;
                canvasModel.updateItem(idx, {
                    type: data.type,
                    geometry: rectGeom,
                    appearances: data.appearances,
                    name: data.name,
                    parentId: data.parentId,
                    visible: data.visible,
                    locked: data.locked
                });
            } else if (data.type === "ellipse") {
                if (data.parentId && containerIds[data.parentId])
                    continue;
                var ellipseGeom = Object.assign({}, data.geometry);
                ellipseGeom.centerX = ellipseGeom.centerX + canvasDx;
                ellipseGeom.centerY = ellipseGeom.centerY + canvasDy;
                canvasModel.updateItem(idx, {
                    type: data.type,
                    geometry: ellipseGeom,
                    appearances: data.appearances,
                    name: data.name,
                    parentId: data.parentId,
                    visible: data.visible,
                    locked: data.locked
                });
            } else if (data.type === "text") {
                if (data.parentId && containerIds[data.parentId])
                    continue;
                var textGeom = Object.assign({}, data.geometry);
                textGeom.x = textGeom.x + canvasDx;
                textGeom.y = textGeom.y + canvasDy;
                canvasModel.updateItem(idx, {
                    type: data.type,
                    geometry: textGeom,
                    text: data.text,
                    fontFamily: data.fontFamily,
                    fontSize: data.fontSize,
                    textColor: data.textColor,
                    textOpacity: data.textOpacity,
                    name: data.name,
                    parentId: data.parentId,
                    visible: data.visible,
                    locked: data.locked
                });
            } else if (data.type === "path") {
                if (data.parentId && containerIds[data.parentId])
                    continue;
                // Move path by translating all points in geometry
                var pathGeom = data.geometry;
                var newPoints = [];
                for (var p = 0; p < pathGeom.points.length; p++) {
                    newPoints.push({
                        x: pathGeom.points[p].x + canvasDx,
                        y: pathGeom.points[p].y + canvasDy
                    });
                }
                canvasModel.updateItem(idx, {
                    type: data.type,
                    geometry: {
                        points: newPoints,
                        closed: pathGeom.closed
                    },
                    appearances: data.appearances,
                    name: data.name,
                    parentId: data.parentId,
                    visible: data.visible,
                    locked: data.locked
                });
            }
        }
        refreshSelectionGeometryBounds();
    }

    Connections {
        target: Lucent.SelectionManager
        function onSelectedItemChanged() {
            refreshSelectionTransform();
            refreshSelectionGeometryBounds();
        }
        function onSelectedItemIndexChanged() {
            refreshSelectionTransform();
            refreshSelectionGeometryBounds();
        }
        function onSelectedIndicesChanged() {
            refreshSelectionTransform();
            refreshSelectionGeometryBounds();
        }
    }

    Connections {
        target: canvasModel
        function onItemTransformChanged(index) {
            if (index === Lucent.SelectionManager.selectedItemIndex) {
                refreshSelectionTransform();
                refreshSelectionGeometryBounds();
            }
        }
        function onItemModified(index) {
            if (index === Lucent.SelectionManager.selectedItemIndex) {
                refreshSelectionTransform();
                refreshSelectionGeometryBounds();
            }
        }
    }

    function deleteSelectedItem() {
        var indices = Lucent.SelectionManager.currentSelectionIndices();
        if (indices.length === 0)
            return;
        indices.sort(function (a, b) {
            return b - a;
        });
        for (var i = 0; i < indices.length; i++) {
            var idx = indices[i];
            if (canvasModel.isEffectivelyLocked(idx))
                continue;
            canvasModel.removeItem(idx);
        }
        Lucent.SelectionManager.setSelection([]);
    }

    function duplicateSelectedItem() {
        var indices = Lucent.SelectionManager.currentSelectionIndices();
        if (indices.length === 0)
            return;
        var newIndices = canvasModel.duplicateItems(indices);
        if (!newIndices || newIndices.length === 0)
            return;
        Lucent.SelectionManager.setSelection(newIndices);
        refreshSelectionGeometryBounds();
    }

    // Cancel the current drawing tool operation
    function cancelCurrentTool() {
        if (currentToolLoader.item) {
            currentToolLoader.item.reset();
        }
    }
}
