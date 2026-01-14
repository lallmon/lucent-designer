// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

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

    // Selection transform (updated reactively via signal)
    property var _selectionTransform: null

    // Selection geometry bounds (untransformed, from model)
    property var _selectionGeometryBounds: null

    // Exposed properties for SelectionOverlay (used by Viewport)
    readonly property var selectionGeometryBounds: _selectionGeometryBounds
    readonly property var selectionTransform: _selectionTransform

    // Overlay state tracking (set by Viewport's SelectionOverlay)
    property bool overlayIsResizing: false
    property bool overlayIsRotating: false

    // Path edit mode
    readonly property bool pathEditModeActive: Lucent.SelectionManager.editModeActive
    readonly property var pathEditGeometry: {
        if (!pathEditModeActive)
            return null;
        var item = Lucent.SelectionManager.selectedItem;
        if (item && item.type === "path" && item.geometry)
            return item.geometry;
        return null;
    }
    readonly property var pathEditTransform: {
        if (!pathEditModeActive)
            return null;
        var item = Lucent.SelectionManager.selectedItem;
        if (item && item.transform)
            return item.transform;
        return {};
    }
    readonly property var pathSelectedPointIndices: Lucent.SelectionManager.selectedPointIndices

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
            // Move origin to center BEFORE rotation starts to prevent visual jump
            var idx = Lucent.SelectionManager.selectedItemIndex;
            if (idx >= 0) {
                canvasModel.ensureOriginCentered(idx);
            }
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

    function handlePathPointClicked(index, modifiers) {
        var multi = modifiers & Qt.ShiftModifier;
        Lucent.SelectionManager.selectPoint(index, multi);
    }

    function handlePathPointMoved(index, x, y) {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx < 0)
            return;

        var item = Lucent.SelectionManager.selectedItem;
        if (!item || item.type !== "path")
            return;

        var draggedPt = item.geometry.points[index];
        var dx = x - draggedPt.x;
        var dy = y - draggedPt.y;

        var selectedIndices = Lucent.SelectionManager.selectedPointIndices || [];
        var isDraggedSelected = selectedIndices.indexOf(index) >= 0;

        var newPoints = [];
        for (var i = 0; i < item.geometry.points.length; i++) {
            var pt = item.geometry.points[i];
            var shouldMove = (i === index) || (isDraggedSelected && selectedIndices.indexOf(i) >= 0);

            if (shouldMove) {
                var newPt = {
                    x: pt.x + dx,
                    y: pt.y + dy
                };
                if (pt.handleIn)
                    newPt.handleIn = {
                        x: pt.handleIn.x + dx,
                        y: pt.handleIn.y + dy
                    };
                if (pt.handleOut)
                    newPt.handleOut = {
                        x: pt.handleOut.x + dx,
                        y: pt.handleOut.y + dy
                    };
                newPoints.push(newPt);
            } else {
                newPoints.push(pt);
            }
        }

        canvasModel.updateItem(idx, {
            geometry: {
                points: newPoints,
                closed: item.geometry.closed
            }
        });
    }

    function handlePathHandleMoved(index, handleType, x, y, modifiers) {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx < 0)
            return;

        var item = Lucent.SelectionManager.selectedItem;
        if (!item || item.type !== "path")
            return;

        var breakSymmetry = !!(modifiers & Qt.AltModifier);

        var newPoints = [];
        for (var i = 0; i < item.geometry.points.length; i++) {
            var pt = item.geometry.points[i];
            if (i === index) {
                var newPt = {
                    x: pt.x,
                    y: pt.y
                };

                if (handleType === "handleIn") {
                    newPt.handleIn = {
                        x: x,
                        y: y
                    };
                    if (pt.handleOut) {
                        if (breakSymmetry) {
                            newPt.handleOut = {
                                x: pt.handleOut.x,
                                y: pt.handleOut.y
                            };
                        } else {
                            // Mirror angle, preserve opposite handle length
                            var dx = x - pt.x;
                            var dy = y - pt.y;
                            var outDx = pt.handleOut.x - pt.x;
                            var outDy = pt.handleOut.y - pt.y;
                            var outLen = Math.sqrt(outDx * outDx + outDy * outDy);
                            var inLen = Math.sqrt(dx * dx + dy * dy);
                            if (inLen > 0.001) {
                                newPt.handleOut = {
                                    x: pt.x - (dx / inLen) * outLen,
                                    y: pt.y - (dy / inLen) * outLen
                                };
                            } else {
                                newPt.handleOut = {
                                    x: pt.handleOut.x,
                                    y: pt.handleOut.y
                                };
                            }
                        }
                    }
                } else if (handleType === "handleOut") {
                    newPt.handleOut = {
                        x: x,
                        y: y
                    };
                    if (pt.handleIn) {
                        if (breakSymmetry) {
                            newPt.handleIn = {
                                x: pt.handleIn.x,
                                y: pt.handleIn.y
                            };
                        } else {
                            // Mirror angle, preserve opposite handle length
                            var dx = x - pt.x;
                            var dy = y - pt.y;
                            var inDx = pt.handleIn.x - pt.x;
                            var inDy = pt.handleIn.y - pt.y;
                            var inLen = Math.sqrt(inDx * inDx + inDy * inDy);
                            var outLen = Math.sqrt(dx * dx + dy * dy);
                            if (outLen > 0.001) {
                                newPt.handleIn = {
                                    x: pt.x - (dx / outLen) * inLen,
                                    y: pt.y - (dy / outLen) * inLen
                                };
                            } else {
                                newPt.handleIn = {
                                    x: pt.handleIn.x,
                                    y: pt.handleIn.y
                                };
                            }
                        }
                    }
                }

                newPoints.push(newPt);
            } else {
                newPoints.push(pt);
            }
        }

        canvasModel.updateItem(idx, {
            geometry: {
                points: newPoints,
                closed: item.geometry.closed
            }
        });
    }

    function deleteSelectedPoints() {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx < 0)
            return;

        var item = Lucent.SelectionManager.selectedItem;
        if (!item || item.type !== "path")
            return;

        var selectedIndices = Lucent.SelectionManager.selectedPointIndices;
        if (!selectedIndices || selectedIndices.length === 0)
            return;

        var newPoints = [];
        for (var i = 0; i < item.geometry.points.length; i++) {
            if (selectedIndices.indexOf(i) < 0) {
                newPoints.push(item.geometry.points[i]);
            }
        }

        if (newPoints.length < 2) {
            canvasModel.removeItem(idx);
            Lucent.SelectionManager.exitEditMode();
        } else {
            canvasModel.updateItem(idx, {
                geometry: {
                    points: newPoints,
                    closed: item.geometry.closed && newPoints.length >= 3
                }
            });
            Lucent.SelectionManager.clearPointSelection();
        }
    }

    // Canvas content (no transforms - handled by parent Viewport)
    Item {
        id: shapesLayer
        anchors.centerIn: parent
        width: 0
        height: 0

        // Adaptive tile size based on zoom level to limit tile count
        // At low zoom, use larger tiles to reduce overhead
        readonly property int baseTileSize: 1024
        readonly property int maxTileCount: 16  // Target max tiles for smooth panning

        // Cached tile size to enable hysteresis (avoid binding loop)
        property int _lastTileSize: baseTileSize

        function getAdaptiveTileSize() {
            var zs = Math.max(root.zoomLevel, 0.0001);
            var viewCanvasW = root.width / zs;
            var viewCanvasH = root.height / zs;

            // Calculate how many base tiles would cover the viewport
            var tilesX = Math.ceil(viewCanvasW / baseTileSize);
            var tilesY = Math.ceil(viewCanvasH / baseTileSize);
            var tileCount = tilesX * tilesY;

            // If too many tiles, double tile size until acceptable
            var ts = baseTileSize;
            while (tileCount > maxTileCount && ts < 16384) {
                ts *= 2;
                tilesX = Math.ceil(viewCanvasW / ts);
                tilesY = Math.ceil(viewCanvasH / ts);
                tileCount = tilesX * tilesY;
            }

            // Hysteresis: prefer keeping current size unless forced to change
            if (_lastTileSize > ts) {
                var currentTilesX = Math.ceil(viewCanvasW / _lastTileSize);
                var currentTilesY = Math.ceil(viewCanvasH / _lastTileSize);
                var currentCount = currentTilesX * currentTilesY;
                // Keep current larger size unless it would exceed max
                if (currentCount <= maxTileCount) {
                    return _lastTileSize;
                }
            }

            _lastTileSize = ts;
            return ts;
        }

        property int tileSize: baseTileSize
        property var _tiles: []

        function updateTiles() {
            if (!isFinite(root.width) || !isFinite(root.height) || root.width <= 0 || root.height <= 0) {
                _tiles = [];
                return;
            }

            // Recalculate adaptive tile size
            tileSize = getAdaptiveTileSize();

            var zs = Math.max(root.zoomLevel, 0.0001);
            var halfW = root.width / zs / 2;
            var halfH = root.height / zs / 2;
            var minX = (-root.offsetX - halfW);
            var maxX = (-root.offsetX + halfW);
            var minY = (-root.offsetY - halfH);
            var maxY = (-root.offsetY + halfH);

            var ts = tileSize;
            var startX = Math.floor(minX / ts);
            var endX = Math.floor(maxX / ts);
            var startY = Math.floor(minY / ts);
            var endY = Math.floor(maxY / ts);

            var list = [];
            for (var ix = startX; ix <= endX; ix++) {
                for (var iy = startY; iy <= endY; iy++) {
                    list.push({
                        cx: (ix + 0.5) * ts,
                        cy: (iy + 0.5) * ts
                    });
                }
            }
            _tiles = list;
        }

        // Debounce timer for tile updates during zoom to prevent churn
        Timer {
            id: tileUpdateDebounce
            interval: 50  // Wait 50ms after last zoom change
            repeat: false
            onTriggered: shapesLayer.updateTiles()
        }

        Connections {
            target: root
            function onZoomLevelChanged() {
                // Debounce zoom changes to prevent tile churn during animation
                tileUpdateDebounce.restart();
            }
            function onOffsetXChanged() {
                shapesLayer.updateTiles();
            }
            function onOffsetYChanged() {
                shapesLayer.updateTiles();
            }
            function onWidthChanged() {
                shapesLayer.updateTiles();
            }
            function onHeightChanged() {
                shapesLayer.updateTiles();
            }
        }

        Component.onCompleted: updateTiles()

        Repeater {
            model: shapesLayer._tiles
            delegate: CanvasRenderer {
                required property var modelData
                readonly property real _dpiScale: 1.0
                readonly property real _maxPxBase: shapesLayer.tileSize
                readonly property real _padBase: 0

                width: shapesLayer.tileSize
                height: shapesLayer.tileSize
                x: modelData.cx - width / 2
                y: modelData.cy - height / 2
                zoomLevel: root.zoomLevel
                tileOriginX: modelData.cx
                tileOriginY: modelData.cy

                Component.onCompleted: setModel(canvasModel)
            }
        }

        // SelectionOverlay and ToolTipCanvas have been moved to Viewport.qml overlayContainer

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
            overlayGeometry: root._selectionGeometryBounds ? {
                bounds: root._selectionGeometryBounds,
                transform: root._selectionTransform || {},
                armLength: 30 / root.zoomLevel,
                handleSize: 8 / root.zoomLevel,
                zoomLevel: root.zoomLevel
            } : null
            // Don't drag object when overlay resize/rotate handles are being used
            overlayActive: root.overlayIsResizing || root.overlayIsRotating

            onPanDelta: (dx, dy) => {
                root.panRequested(dx, dy);
            }

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
        } else if (currentToolLoader.item && currentToolLoader.item.handleMousePress) {
            // When using a drawing tool, don't start drawing if clicking on selection handles
            // This allows manipulating selected shapes without switching to select tool
            if (Lucent.SelectionManager.selectedItemIndex >= 0) {
                var nearHandle = selectTool.isNearRotationHandle(viewportX, viewportY) || selectTool.isNearResizeHandle(viewportX, viewportY);
                if (nearHandle) {
                    return;  // Let SelectionOverlay handle it
                }
            }
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
        if (currentToolLoader.item && currentToolLoader.item.handleClick && button === Qt.LeftButton) {
            var canvasCoords = viewportToCanvas(viewportX, viewportY);
            currentToolLoader.item.handleClick(canvasCoords.x, canvasCoords.y);
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
        if (currentToolLoader.item && currentToolLoader.item.handleDoubleClick) {
            var coords = viewportToCanvas(viewportX, viewportY);
            currentToolLoader.item.handleDoubleClick(coords.x, coords.y);
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
        updateSelection(hitIndex, multiSelect === true);
    }

    function getSelectionTransform() {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx < 0 || !canvasModel)
            return null;
        return canvasModel.getItemTransform(idx);
    }

    function refreshSelectionTransform() {
        _selectionTransform = getSelectionTransform();
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
        function onEditModeExited() {
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

        // Wrap in transaction so deleting multiple items is one undo step
        canvasModel.beginTransaction();
        for (var i = 0; i < indices.length; i++) {
            var idx = indices[i];
            if (canvasModel.isEffectivelyLocked(idx))
                continue;
            canvasModel.removeItem(idx);
        }
        canvasModel.endTransaction();

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

    // Undo last action in current drawing tool (Escape key)
    function cancelCurrentTool() {
        if (currentToolLoader.item) {
            // Use undoLastAction if available (progressive undo), otherwise reset
            if (currentToolLoader.item.undoLastAction) {
                currentToolLoader.item.undoLastAction();
            } else if (currentToolLoader.item.reset) {
                currentToolLoader.item.reset();
            }
        }
    }

    // Finish the current drawing tool operation (for open paths)
    function finishCurrentTool() {
        if (currentToolLoader.item && currentToolLoader.item._finalize) {
            currentToolLoader.item._finalize();
        }
    }
}
