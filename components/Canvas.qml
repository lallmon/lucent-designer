// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import "." as Lucent
import "tools" as Tools

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

    // Current keyboard modifiers (updated during mouse move)
    property int currentModifiers: 0

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

    // Exposed properties for SelectionOverlay (bound from SelectionManager)
    readonly property var selectionGeometryBounds: Lucent.SelectionManager.geometryBounds
    readonly property var selectionTransform: Lucent.SelectionManager.selectionTransform

    // Overlay state tracking (set by Viewport's SelectionOverlay)
    property bool overlayIsResizing: false
    property bool overlayIsRotating: false

    // Path edit mode - delegate to PathEditController
    readonly property bool pathEditModeActive: pathEditController.editModeActive
    readonly property var pathEditGeometry: pathEditController.geometry
    readonly property var pathEditTransformedPoints: pathEditController.transformedPoints
    readonly property var pathSelectedPointIndices: pathEditController.selectedPointIndices

    // Path edit controller handles all path point/handle operations
    PathEditController {
        id: pathEditController
    }

    // Signals emitted by SelectionOverlay in Viewport, handled here
    signal overlayResizeRequested(var newBounds)
    signal overlayRotateRequested(real angle)
    signal overlayScaleResizeRequested(real scaleX, real scaleY, real anchorX, real anchorY)
    signal overlayResizingChanged(bool isResizing)
    signal overlayRotatingChanged(bool isRotating)

    // Handle overlay signals from Viewport's SelectionOverlay
    onOverlayResizingChanged: function (isResizing) {
        if (isResizing) {
            canvasModel.beginTransaction();
        } else {
            canvasModel.endTransaction();
        }
    }

    onOverlayRotatingChanged: function (isRotating) {
        if (isRotating) {
            canvasModel.beginTransaction();
        } else {
            canvasModel.endTransaction();
        }
    }

    onOverlayResizeRequested: function (newBounds) {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx >= 0 && canvasModel) {
            canvasModel.setBoundingBox(idx, newBounds);
        }
    }

    onOverlayRotateRequested: function (angle) {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx >= 0 && canvasModel) {
            canvasModel.updateTransformProperty(idx, "rotate", angle);
        }
    }

    onOverlayScaleResizeRequested: function (scaleX, scaleY, anchorX, anchorY) {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx >= 0 && canvasModel) {
            canvasModel.applyScaleResize(idx, scaleX, scaleY, anchorX, anchorY);
        }
    }

    // Path edit delegations to controller
    function handlePathPointClicked(index, modifiers) {
        pathEditController.handlePointClicked(index, modifiers);
    }

    function handlePathPointMoved(index, x, y) {
        pathEditController.handlePointMoved(index, x, y);
    }

    function handlePathHandleMoved(index, handleType, x, y, modifiers) {
        pathEditController.handleHandleMoved(index, handleType, x, y, modifiers);
    }

    function deleteSelectedPoints() {
        pathEditController.deleteSelectedPoints();
    }

    function lockPathEditTransform() {
        pathEditController.lockTransformForDrag();
    }

    function unlockPathEditTransform() {
        pathEditController.unlockTransformAfterDrag();
    }

    // Tiled rendering layer
    TiledShapesLayer {
        id: shapesLayer
        zoomLevel: root.zoomLevel
        offsetX: root.offsetX
        offsetY: root.offsetY
        viewportWidth: root.width
        viewportHeight: root.height
    }

    function setPreviewItem(itemData) {
        shapesLayer.setPreviewItem(itemData);
    }

    function clearPreview() {
        shapesLayer.clearPreview();
    }

    // Select tool for object selection (panning handled by Viewport)
    SelectTool {
        id: selectTool
        active: root.drawingMode === ""
        hitTestCallback: root.hitTest
        viewportToCanvasCallback: root.viewportToCanvas
        canvasToViewportCallback: root.canvasToViewport
        getBoundsCallback: function (idx) {
            return canvasModel.getBoundingBox(idx);
        }
        // Overlay geometry for manual handle hit testing
        overlayGeometry: root.selectionGeometryBounds ? {
            bounds: root.selectionGeometryBounds,
            transform: root.selectionTransform || {},
            armLength: 30 / root.zoomLevel,
            handleSize: 8 / root.zoomLevel,
            zoomLevel: root.zoomLevel
        } : null
        // Don't drag object when overlay resize/rotate handles are being used
        overlayActive: root.overlayIsResizing || root.overlayIsRotating

        onCursorShapeChanged: shape => {
            root.currentCursorShape = shape;
        }

        onObjectClicked: (viewportX, viewportY, modifiers) => {
            if (Lucent.SelectionManager.shouldSkipClick())
                return;

            if (Lucent.SelectionManager.editModeActive) {
                Lucent.SelectionManager.exitEditMode();
                return;
            }

            var canvasCoords = root.viewportToCanvas(viewportX, viewportY);
            root.selectItemAt(canvasCoords.x, canvasCoords.y, !!(modifiers & Qt.ControlModifier));
        }

        onObjectDragged: (viewportDx, viewportDy) => {
            root.updateSelectedItemPosition(viewportDx / root.zoomLevel, viewportDy / root.zoomLevel);
        }
    }

    // Dynamic tool loader for drawing tools
    // Centered at (0,0) to match TiledShapesLayer coordinate system
    Tools.ToolLoader {
        id: toolLoader
        anchors.centerIn: parent
        width: 0
        height: 0

        drawingMode: root.drawingMode
        zoomLevel: root.zoomLevel
        toolSettings: root.toolSettings
        viewportWidth: root.width
        viewportHeight: root.height
        setPreviewCallback: function (data) {
            root.setPreviewItem(data);
        }
        clearPreviewCallback: function () {
            root.clearPreview();
        }

        onItemCompleted: function (itemData) {
            root.handleItemCompleted(itemData);
        }
    }

    // Convert viewport coordinates to canvas coordinates
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

    // Convert canvas coordinates to viewport coordinates
    function canvasToViewport(canvasX, canvasY) {
        var centerX = root.width / 2;
        var centerY = root.height / 2;

        var viewportX = canvasX * root.zoomLevel + centerX + root.offsetX;
        var viewportY = canvasY * root.zoomLevel + centerY + root.offsetY;

        return {
            x: viewportX,
            y: viewportY
        };
    }

    // Public event handlers called from Viewport MouseArea
    function handleMousePress(viewportX, viewportY, button, modifiers) {
        // Delegate to active tool (SelectTool uses viewport coords)
        if (root.drawingMode === "") {
            selectTool.handlePress(viewportX, viewportY, button, modifiers);
        } else if (toolLoader.currentTool && toolLoader.currentTool.handleMousePress) {
            // When using a drawing tool, don't start drawing if clicking on selection handles
            if (Lucent.SelectionManager.selectedItemIndex >= 0) {
                var nearHandle = selectTool.isNearRotationHandle(viewportX, viewportY) || selectTool.isNearResizeHandle(viewportX, viewportY);
                if (nearHandle) {
                    return;  // Let SelectionOverlay handle it
                }
            }
            var canvasCoords = viewportToCanvas(viewportX, viewportY);
            toolLoader.currentTool.handleMousePress(canvasCoords.x, canvasCoords.y, button, modifiers);
        }
    }

    function handleMouseRelease(viewportX, viewportY, button, modifiers) {
        if (root.drawingMode === "") {
            selectTool.handleRelease(viewportX, viewportY, button, modifiers);
        } else if (toolLoader.currentTool && toolLoader.currentTool.handleMouseRelease) {
            var canvasCoords = viewportToCanvas(viewportX, viewportY);
            toolLoader.currentTool.handleMouseRelease(canvasCoords.x, canvasCoords.y);
        }
    }

    function handleMouseClick(viewportX, viewportY, button) {
        if (toolLoader.currentTool && toolLoader.currentTool.handleClick && button === Qt.LeftButton) {
            var canvasCoords = viewportToCanvas(viewportX, viewportY);
            toolLoader.currentTool.handleClick(canvasCoords.x, canvasCoords.y);
        }
    }

    function handleMouseDoubleClick(viewportX, viewportY, button) {
        if (button !== Qt.LeftButton)
            return;

        // In selection mode, check if double-clicking on a path to enter edit mode
        if (root.drawingMode === "") {
            var canvasCoords = viewportToCanvas(viewportX, viewportY);
            var hitIndex = hitTest(canvasCoords.x, canvasCoords.y);

            if (hitIndex >= 0) {
                var itemData = canvasModel.getItemData(hitIndex);
                if (itemData && itemData.type === "path") {
                    Lucent.SelectionManager.setSelection([hitIndex]);
                    Lucent.SelectionManager.enterEditMode();
                    return;
                }
            }
        }

        // Otherwise, delegate to the current tool
        if (toolLoader.currentTool && toolLoader.currentTool.handleDoubleClick) {
            var coords = viewportToCanvas(viewportX, viewportY);
            toolLoader.currentTool.handleDoubleClick(coords.x, coords.y);
        }
    }

    function handleMouseMove(viewportX, viewportY, modifiers) {
        // Update cursor position and modifiers
        var canvasCoords = viewportToCanvas(viewportX, viewportY);
        root.cursorX = canvasCoords.x;
        root.cursorY = canvasCoords.y;
        root.currentModifiers = modifiers;

        // Only log if coordinates are invalid
        if (!isFinite(root.cursorX) || !isFinite(root.cursorY)) {
            console.error("[handleMouseMove] CRITICAL: Invalid canvas coords!", "cursorX:", root.cursorX, "cursorY:", root.cursorY);
        }

        // Delegate to active tool
        if (root.drawingMode === "") {
            selectTool.handleMouseMove(viewportX, viewportY);
        } else if (toolLoader.currentTool) {
            toolLoader.currentTool.handleMouseMove(canvasCoords.x, canvasCoords.y, modifiers);
        }
    }

    // Generic item completion handler
    function handleItemCompleted(itemData) {
        canvasModel.addItem(itemData);
        var newIndex = canvasModel.count() - 1;
        Lucent.SelectionManager.setSelection([newIndex]);
    }

    // Set the drawing mode
    function setDrawingMode(mode) {
        // Reset any active tool
        if (drawingMode === "") {
            selectTool.reset();
        } else {
            toolLoader.reset();
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
            Lucent.SelectionManager.setSelection([]);
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
        Lucent.SelectionManager.toggleSelection(hitIndex, multiSelect === true);
    }

    function updateSelectedItemPosition(canvasDx, canvasDy) {
        var indices = Lucent.SelectionManager.selectedIndices || [];
        if (indices.length === 0)
            return;
        canvasModel.moveItems(indices, canvasDx, canvasDy);
    }

    function deleteSelectedItem() {
        var indices = Lucent.SelectionManager.currentSelectionIndices();
        if (indices.length === 0)
            return;
        canvasModel.deleteItems(indices);
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
    }

    // Undo last action in current drawing tool (Escape key)
    function cancelCurrentTool() {
        if (toolLoader.currentTool) {
            if (toolLoader.currentTool.undoLastAction) {
                toolLoader.currentTool.undoLastAction();
            } else {
                toolLoader.reset();
            }
        }
    }

    // Finish the current drawing tool operation (for open paths)
    function finishCurrentTool() {
        if (toolLoader.currentTool && toolLoader.currentTool._finalize) {
            toolLoader.currentTool._finalize();
        }
    }
}
