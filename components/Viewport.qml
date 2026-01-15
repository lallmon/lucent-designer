// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import "." as Lucent

// Viewport component responsible for zoom, pan, and camera controls
Item {
    id: root
    clip: true  // Constrain rendering to viewport boundaries
    readonly property SystemPalette themePalette: Lucent.Themed.palette

    // Grid config derived from unitSettings (display unit + preview DPI)
    readonly property var gridConfig: {
        if (typeof unitSettings !== "undefined" && unitSettings) {
            // Touch properties so binding re-evaluates on change
            unitSettings.displayUnit;
            unitSettings.previewDPI;
            return unitSettings.gridConfig();
        }
        return {
            minorCanvas: 32.0,
            majorMultiplier: 5.0,
            labelStyle: "decimal",
            targetMajorPx: 80.0
        };
    }

    // Grid spacing in canvas units (driven by gridConfig)
    property real gridSpacingCanvas: gridConfig.minorCanvas || 32.0

    // Grid visibility (toggled from View menu)
    property bool gridVisible: false

    function refreshGrid() {
        if (!gridVisible)
            return;
        gridShader.baseGridSize = gridSpacingCanvas;
        gridShader.majorMultiplier = gridConfig.majorMultiplier;
    }

    // Zoom/pan state (camera controls)
    property real zoomLevel: 0.7  // Start at 70%
    readonly property real minZoom: 0.01
    readonly property real maxZoom: 10.0
    readonly property real zoomStep: 1.08  // ~8% base zoom increments for faster wheel zoom

    // Camera offset for panning
    property real offsetX: 0
    property real offsetY: 0

    // Animation control - disabled during wheel zoom for precise cursor tracking
    property bool animationsEnabled: true

    // Smooth zoom animation for menu-driven zoom (not wheel)
    Behavior on zoomLevel {
        enabled: root.animationsEnabled
        NumberAnimation {
            duration: 150
            easing.type: Easing.OutCubic
        }
    }

    // Inertial panning state
    property real panVelocityX: 0
    property real panVelocityY: 0
    readonly property real panFriction: 0.92  // Velocity multiplier per frame
    readonly property real panMinVelocity: 0.5  // Stop threshold

    // Inertia timer for smooth pan deceleration
    Timer {
        id: inertiaTimer
        interval: 16  // ~60fps
        repeat: true
        running: Math.abs(root.panVelocityX) > root.panMinVelocity || Math.abs(root.panVelocityY) > root.panMinVelocity
        onTriggered: {
            root.offsetX += root.panVelocityX;
            root.offsetY += root.panVelocityY;
            root.panVelocityX *= root.panFriction;
            root.panVelocityY *= root.panFriction;

            // Stop when velocity is negligible
            if (Math.abs(root.panVelocityX) <= root.panMinVelocity && Math.abs(root.panVelocityY) <= root.panMinVelocity) {
                root.panVelocityX = 0;
                root.panVelocityY = 0;
            }
        }
    }

    // Canvas bounds (matches the viewport-sized renderer surface)
    readonly property real canvasWidth: width
    readonly property real canvasHeight: height
    readonly property real canvasMinX: -width / 2
    readonly property real canvasMaxX: width / 2
    readonly property real canvasMinY: -height / 2
    readonly property real canvasMaxY: height / 2

    // Minimum visible canvas area (percentage)
    readonly property real minVisibleRatio: 0.2  // Keep 20% of canvas visible

    // Content to be displayed (Canvas should be placed as a child)
    default property alias content: contentContainer.data

    // Background color
    Rectangle {
        anchors.fill: parent
        color: Lucent.Themed.gridBackground
    }

    // Shared transforms for zoom and pan - used by viewportContent and overlayContainer
    Scale {
        id: viewportScale
        origin.x: viewportContent.width / 2
        origin.y: viewportContent.height / 2
        xScale: root.zoomLevel
        yScale: root.zoomLevel
    }
    Translate {
        id: viewportTranslate
        x: root.offsetX
        y: root.offsetY
    }

    Connections {
        target: typeof unitSettings !== "undefined" ? unitSettings : null
        function onDisplayUnitChanged() {
            refreshGrid();
        }
        function onPreviewDPIChanged() {
            refreshGrid();
        }
        function onGridSpacingCanvasChanged() {
            refreshGrid();
        }
    }

    // GPU grid overlay: crisp, infinite-feel, tied to current viewport
    ShaderEffect {
        id: gridShader
        anchors.fill: parent
        visible: gridVisible && width > 0 && height > 0
        z: 5  // Above shapes, below overlays/tooltips

        // Order matters: must match shader uniform block
        property real baseGridSize: 32.0
        property real majorMultiplier: 5.0
        property real minorThicknessPx: 0.4
        property real majorThicknessPx: 0.7
        property real featherPx: 0.4
        property real zoomLevel: root.zoomLevel
        property real offsetX: root.offsetX
        property real offsetY: root.offsetY
        property var viewportSize: Qt.vector2d(width, height)
        property color minorColor: Qt.rgba(Lucent.Themed.gridMinor.r, Lucent.Themed.gridMinor.g, Lucent.Themed.gridMinor.b, 0.25)
        property color majorColor: Qt.rgba(Lucent.Themed.gridMajor.r, Lucent.Themed.gridMajor.g, Lucent.Themed.gridMajor.b, 0.85)
        // Precomputed spacing/visibility
        property real majorStepCanvas: {
            var z = root.zoomLevel;
            var base = root.gridSpacingCanvas;
            if (!isFinite(z) || z <= 0 || !isFinite(base) || base <= 0)
                return base * root.gridConfig.majorMultiplier;

            var us = typeof unitSettings !== "undefined" ? unitSettings : null;

            // Pixel unit: target ~16px using powers of two
            if (us && us.displayUnit === "px") {
                var targetPx = 16.0;
                var targetCanvas = targetPx / z;
                var power = Math.round(Math.log(targetCanvas) / Math.LN2);
                var step = Math.pow(2, power);
                return step * root.gridConfig.majorMultiplier;
            }

            // Inches: pick nearest clean step to target pixels
            if (us && us.displayUnit === "in" && us.displayToCanvas) {
                var targetPxIn = 80.0; // aim majors near ~80px
                var candidatesIn = [0.25, 0.5, 1.0, 2.0, 4.0]; // inches
                var bestIn = candidatesIn[0];
                var bestDiffIn = 1e9;
                for (var i = 0; i < candidatesIn.length; i++) {
                    var stepIn = candidatesIn[i];
                    var stepCanvas = us.displayToCanvas(stepIn);
                    var diff = Math.abs(stepCanvas * z - targetPxIn);
                    if (diff < bestDiffIn) {
                        bestDiffIn = diff;
                        bestIn = stepIn;
                    }
                }
                return us.displayToCanvas(bestIn);
            }

            // Millimeters: pick nearest clean step to target pixels
            if (us && us.displayUnit === "mm" && us.displayToCanvas) {
                var targetPxMm = 100.0; // aim majors near ~100px
                var candidatesMm = [10.0, 20.0, 25.0, 50.0, 100.0, 200.0]; // mm
                var bestMm = candidatesMm[0];
                var bestDiffMm = 1e9;
                for (var j = 0; j < candidatesMm.length; j++) {
                    var stepMm = candidatesMm[j];
                    var stepCanvasMm = us.displayToCanvas(stepMm);
                    var diffMm = Math.abs(stepCanvasMm * z - targetPxMm);
                    if (diffMm < bestDiffMm) {
                        bestDiffMm = diffMm;
                        bestMm = stepMm;
                    }
                }
                return us.displayToCanvas(bestMm);
            }

            // Other units: 1-2-5 ladder near targetMajorPx
            var targetPx = root.gridConfig.targetMajorPx || 80;
            var targetCanvas = targetPx / z;
            var ratio = targetCanvas / base;
            var pow10 = Math.pow(10, Math.floor(Math.log(ratio) / Math.LN10));
            var best = base * pow10;
            var bestDiff = Math.abs(best - targetCanvas);
            var candidates = [1, 2, 5];
            for (var i = 0; i < candidates.length; i++) {
                var step = base * candidates[i] * pow10;
                var diff = Math.abs(step - targetCanvas);
                if (diff < bestDiff) {
                    bestDiff = diff;
                    best = step;
                }
            }
            return best;
        }
        property real minorStepCanvas: majorStepCanvas / root.gridConfig.majorMultiplier
        property real showMinorFlag: {
            var msPx = minorStepCanvas * root.zoomLevel;
            if (msPx < 6)
                return 0;
            return 1;
        }
        Binding on baseGridSize {
            value: root.gridSpacingCanvas
        }
        Binding on majorMultiplier {
            value: root.gridConfig.majorMultiplier
        }

        vertexShader: Qt.resolvedUrl("shaders/grid.vert.qsb")
        fragmentShader: Qt.resolvedUrl("shaders/grid.frag.qsb")

        onWidthChanged: {
            if (width > 0 && height > 0 && gridVisible) {
                gridShader.baseGridSize = root.gridSpacingCanvas;
                gridShader.majorMultiplier = root.gridConfig.majorMultiplier;
            }
        }

        onHeightChanged: {
            if (width > 0 && height > 0 && gridVisible) {
                gridShader.baseGridSize = root.gridSpacingCanvas;
                gridShader.majorMultiplier = root.gridConfig.majorMultiplier;
            }
        }
    }

    // The viewport surface that applies zoom and pan transforms
    Item {
        id: viewportContent
        anchors.centerIn: parent
        width: parent.width
        height: parent.height

        // Apply shared transformations for zoom and pan
        transform: [viewportScale, viewportTranslate]

        // Container for content (Canvas will be placed here)
        // Fill the entire transformed viewport area so Canvas MouseArea receives events
        Item {
            id: contentContainer
            anchors.fill: parent
        }
    }

    // Overlay container for selection UI elements that render above the grid
    Item {
        id: overlayContainer
        anchors.centerIn: parent
        width: parent.width
        height: parent.height
        z: 10  // Above grid (z: 5), below mouse areas

        // Apply same shared transformations as viewportContent
        transform: [viewportScale, viewportTranslate]

        // Reference to Canvas component for overlay bindings
        property var canvasRef: contentContainer.children.length > 0 ? contentContainer.children[0] : null

        // Anchor point at center with 0x0 size, matching shapesLayer in Canvas
        Item {
            id: overlayAnchor
            anchors.centerIn: parent
            width: 0
            height: 0

            SelectionOverlay {
                id: selectionOverlay
                z: 20
                visible: overlayContainer.canvasRef && overlayContainer.canvasRef.selectionGeometryBounds !== null && !overlayContainer.canvasRef.pathEditModeActive
                geometryBounds: overlayContainer.canvasRef ? overlayContainer.canvasRef.selectionGeometryBounds : null
                itemTransform: overlayContainer.canvasRef ? overlayContainer.canvasRef.selectionTransform : null
                zoomLevel: root.zoomLevel
                cursorX: overlayContainer.canvasRef ? overlayContainer.canvasRef.cursorX : 0
                cursorY: overlayContainer.canvasRef ? overlayContainer.canvasRef.cursorY : 0
                shiftPressed: overlayContainer.canvasRef ? !!(overlayContainer.canvasRef.currentModifiers & Qt.ShiftModifier) : false

                onIsResizingChanged: {
                    if (overlayContainer.canvasRef) {
                        overlayContainer.canvasRef.overlayIsResizing = isResizing;
                        overlayContainer.canvasRef.overlayResizingChanged(isResizing);
                    }
                }

                onIsRotatingChanged: {
                    if (overlayContainer.canvasRef) {
                        overlayContainer.canvasRef.overlayIsRotating = isRotating;
                        overlayContainer.canvasRef.overlayRotatingChanged(isRotating);
                    }
                }

                onResizeRequested: function (newBounds) {
                    if (overlayContainer.canvasRef) {
                        overlayContainer.canvasRef.overlayResizeRequested(newBounds);
                    }
                }

                onRotateRequested: function (angle) {
                    if (overlayContainer.canvasRef) {
                        overlayContainer.canvasRef.overlayRotateRequested(angle);
                    }
                }

                onScaleResizeRequested: function (scaleX, scaleY, anchorX, anchorY) {
                    if (overlayContainer.canvasRef) {
                        overlayContainer.canvasRef.overlayScaleResizeRequested(scaleX, scaleY, anchorX, anchorY);
                    }
                }
            }

            PathEditOverlay {
                id: pathEditOverlay
                z: 21
                visible: overlayContainer.canvasRef && overlayContainer.canvasRef.pathEditModeActive
                pathGeometry: overlayContainer.canvasRef ? overlayContainer.canvasRef.pathEditGeometry : null
                itemTransform: overlayContainer.canvasRef ? overlayContainer.canvasRef.pathEditTransform : null
                zoomLevel: root.zoomLevel
                cursorX: overlayContainer.canvasRef ? overlayContainer.canvasRef.cursorX : 0
                cursorY: overlayContainer.canvasRef ? overlayContainer.canvasRef.cursorY : 0
                currentModifiers: overlayContainer.canvasRef ? overlayContainer.canvasRef.currentModifiers : 0
                selectedPointIndices: overlayContainer.canvasRef ? overlayContainer.canvasRef.pathSelectedPointIndices : []

                onPointClicked: function (index, modifiers) {
                    if (overlayContainer.canvasRef) {
                        overlayContainer.canvasRef.handlePathPointClicked(index, modifiers);
                    }
                }

                onPointMoved: function (index, x, y) {
                    if (overlayContainer.canvasRef) {
                        overlayContainer.canvasRef.handlePathPointMoved(index, x, y);
                    }
                }

                onHandleMoved: function (index, handleType, x, y, modifiers) {
                    if (overlayContainer.canvasRef)
                        overlayContainer.canvasRef.handlePathHandleMoved(index, handleType, x, y, modifiers);
                }

                onDragStarted: {
                    canvasModel.beginTransaction();
                }

                onDragEnded: {
                    canvasModel.endTransaction();
                }
            }

            Lucent.ToolTipCanvas {
                z: 30
                visible: (selectionOverlay.isResizing || selectionOverlay.isRotating) && overlayContainer.canvasRef && overlayContainer.canvasRef.selectionGeometryBounds
                zoomLevel: root.zoomLevel
                cursorX: overlayContainer.canvasRef ? overlayContainer.canvasRef.cursorX : 0
                cursorY: overlayContainer.canvasRef ? overlayContainer.canvasRef.cursorY : 0
                text: {
                    if (selectionOverlay.isRotating) {
                        var transform = overlayContainer.canvasRef ? overlayContainer.canvasRef.selectionTransform : null;
                        var angle = transform ? Math.round(transform.rotate || 0) : 0;
                        return angle + "°";
                    }
                    // Show displayed size (geometry × scale) during resize
                    var bounds = overlayContainer.canvasRef ? overlayContainer.canvasRef.selectionGeometryBounds : null;
                    if (bounds) {
                        var transform = overlayContainer.canvasRef ? overlayContainer.canvasRef.selectionTransform : null;
                        var scaleX = transform ? (transform.scaleX || 1) : 1;
                        var scaleY = transform ? (transform.scaleY || 1) : 1;
                        var w = bounds.width * scaleX;
                        var h = bounds.height * scaleY;
                        var label = "px";
                        if (typeof unitSettings !== "undefined" && unitSettings) {
                            w = unitSettings.canvasToDisplay(w);
                            h = unitSettings.canvasToDisplay(h);
                            label = unitSettings.displayUnit;
                        }
                        return Math.round(w) + " × " + Math.round(h) + " " + label;
                    }
                    return "";
                }
            }
        }
    }

    // Mouse area for tool interaction (clicks, drags, hover)
    // This is at viewport level so it always covers full viewport regardless of zoom
    MouseArea {
        id: toolMouseArea
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.MiddleButton
        hoverEnabled: true
        focus: true

        // Get reference to Canvas component
        property var canvasComponent: contentContainer.children.length > 0 ? contentContainer.children[0] : null

        // Track last mouse position for modifier key updates
        property real lastMouseX: 0
        property real lastMouseY: 0

        // Middle-mouse panning state (global, works with any tool)
        property bool isPanning: false
        property real panStartX: 0
        property real panStartY: 0

        // Bind cursor shape - show hand cursor when panning
        cursorShape: isPanning ? Qt.ClosedHandCursor : (canvasComponent ? canvasComponent.currentCursorShape : Qt.ArrowCursor)

        Keys.onDeletePressed: {
            if (!canvasComponent)
                return;
            if (Lucent.SelectionManager.editModeActive)
                canvasComponent.deleteSelectedPoints();
            else
                canvasComponent.deleteSelectedItem();
        }

        Keys.onEscapePressed: {
            if (Lucent.SelectionManager.editModeActive) {
                Lucent.SelectionManager.exitEditMode();
                return;
            }
            if (canvasComponent)
                canvasComponent.cancelCurrentTool();
        }

        Keys.onReturnPressed: {
            if (canvasComponent) {
                canvasComponent.finishCurrentTool();
            }
        }

        Keys.onEnterPressed: {
            if (canvasComponent) {
                canvasComponent.finishCurrentTool();
            }
        }

        Keys.onPressed: event => {
            if ((event.key === Qt.Key_Shift || event.key === Qt.Key_Alt) && canvasComponent) {
                canvasComponent.handleMouseMove(lastMouseX, lastMouseY, event.modifiers);
            }
        }

        Keys.onReleased: event => {
            if ((event.key === Qt.Key_Shift || event.key === Qt.Key_Alt) && canvasComponent) {
                canvasComponent.handleMouseMove(lastMouseX, lastMouseY, event.modifiers);
            }
        }

        onPressed: mouse => {
            forceActiveFocus();
            root.stopInertia();

            // Middle mouse triggers panning globally (works with any tool)
            if (mouse.button === Qt.MiddleButton) {
                isPanning = true;
                panStartX = mouse.x;
                panStartY = mouse.y;
                return;
            }

            if (canvasComponent) {
                canvasComponent.handleMousePress(mouse.x, mouse.y, mouse.button, mouse.modifiers);
            }
        }

        onReleased: mouse => {
            if (mouse.button === Qt.MiddleButton && isPanning) {
                isPanning = false;
                return;
            }

            if (canvasComponent) {
                canvasComponent.handleMouseRelease(mouse.x, mouse.y, mouse.button, mouse.modifiers);
            }
        }

        onClicked: mouse => {
            if (mouse.button === Qt.MiddleButton)
                return;

            if (canvasComponent) {
                canvasComponent.handleMouseClick(mouse.x, mouse.y, mouse.button);
            }
        }

        onDoubleClicked: mouse => {
            if (mouse.button === Qt.MiddleButton)
                return;

            if (canvasComponent) {
                canvasComponent.handleMouseDoubleClick(mouse.x, mouse.y, mouse.button);
            }
        }

        onPositionChanged: mouse => {
            lastMouseX = mouse.x;
            lastMouseY = mouse.y;

            // Handle panning when middle mouse is held
            if (isPanning) {
                var dx = mouse.x - panStartX;
                var dy = mouse.y - panStartY;
                root.pan(dx, dy);
                panStartX = mouse.x;
                panStartY = mouse.y;
                return;
            }

            if (canvasComponent) {
                canvasComponent.handleMouseMove(mouse.x, mouse.y, mouse.modifiers);
            }
        }
    }

    // Mouse area for zoom control (wheel events)
    MouseArea {
        id: viewportMouseArea
        anchors.fill: parent
        acceptedButtons: Qt.NoButton  // Only handle wheel, not clicks
        propagateComposedEvents: true  // Allow toolMouseArea to receive events too

        // Zoom with mouse wheel: proportional, cursor-centered
        // Animations disabled for precise cursor tracking during wheel zoom
        onWheel: wheel => {
            var step = root.zoomStep;
            var deltaSteps = (wheel.angleDelta.y / 120.0) * 2.0; // 120 per wheel notch
            var factor = Math.pow(step, deltaSteps);
            var newZoom = root.zoomLevel * factor;
            if (newZoom < root.minZoom || newZoom > root.maxZoom)
                return;

            // Disable animations for precise cursor-centered zoom
            root.animationsEnabled = false;

            // Compute scene point under cursor before zoom
            var cx = wheel.x - root.width / 2 - root.offsetX;
            var cy = wheel.y - root.height / 2 - root.offsetY;
            var sceneX = cx / root.zoomLevel;
            var sceneY = cy / root.zoomLevel;

            root.zoomLevel = newZoom;

            // Adjust offsets so cursor stays over same scene point
            var newCx = sceneX * newZoom;
            var newCy = sceneY * newZoom;
            root.offsetX = -(newCx - (wheel.x - root.width / 2));
            root.offsetY = -(newCy - (wheel.y - root.height / 2));

            // Re-enable animations after wheel zoom completes
            wheelAnimationReenableTimer.restart();
        }
    }

    // Timer to re-enable animations after wheel zoom settles
    Timer {
        id: wheelAnimationReenableTimer
        interval: 100  // Re-enable after 100ms of no wheel events
        repeat: false
        onTriggered: root.animationsEnabled = true
    }

    // Public functions for zoom control
    function zoomIn() {
        var newZoom = zoomLevel * zoomStep;
        if (newZoom <= maxZoom) {
            zoomLevel = newZoom;
        }
    }

    function zoomOut() {
        var newZoom = zoomLevel / zoomStep;
        if (newZoom >= minZoom) {
            zoomLevel = newZoom;
        }
    }

    function resetZoom() {
        zoomLevel = 1.0;
        offsetX = 0;
        offsetY = 0;
    }

    function clampOffset(offset, minBound, maxBound, viewportSize, canvasSize) {
        // Validate inputs - return 0 if any are invalid
        if (!isFinite(offset) || !isFinite(viewportSize) || !isFinite(canvasSize)) {
            console.error("[clampOffset] CRITICAL: Invalid input! offset:", offset, "viewportSize:", viewportSize, "canvasSize:", canvasSize);
            return 0;  // Safe default
        }

        // Prevent division by zero or invalid viewport dimensions
        if (viewportSize <= 0) {
            console.error("[clampOffset] CRITICAL: Invalid viewport size:", viewportSize);
            return 0;  // Safe default
        }

        // Validate zoom level
        if (!isFinite(zoomLevel) || zoomLevel <= 0) {
            console.error("[clampOffset] CRITICAL: Invalid zoom level:", zoomLevel);
            return 0;  // Safe default
        }

        // Calculate how much canvas extends beyond viewport at current zoom
        var scaledCanvasSize = canvasSize * zoomLevel;
        var scaledMinBound = minBound * zoomLevel;
        var scaledMaxBound = maxBound * zoomLevel;

        // Allow panning until only minVisibleRatio of canvas is visible
        var maxOffset = scaledMaxBound - (viewportSize / 2) + (viewportSize * (1 - minVisibleRatio));
        var minOffset = scaledMinBound + (viewportSize / 2) - (viewportSize * (1 - minVisibleRatio));

        // Check for invalid clamp range
        if (!isFinite(minOffset) || !isFinite(maxOffset)) {
            console.error("[clampOffset] CRITICAL: NaN/Infinity in clamp range!");
            return 0;  // Safe default
        }

        // Detect if clamping range is inverted or too narrow
        if (minOffset >= maxOffset) {
            console.error("[clampOffset] CRITICAL: Invalid clamp range! minOffset:", minOffset, ">=", "maxOffset:", maxOffset, "zoom:", zoomLevel, "viewportSize:", viewportSize, "Falling back to no clamping");
            // If clamp range is invalid, just return the offset without clamping
            // This prevents getting stuck at an invalid position
            return offset;
        }

        // Clamp the offset
        var result = Math.max(minOffset, Math.min(maxOffset, offset));

        // Validate result
        if (!isFinite(result)) {
            console.error("[clampOffset] CRITICAL: Result is NaN/Infinity!");
            return 0;  // Safe default
        }

        return result;
    }

    function pan(dx, dy) {
        // Validate input deltas
        if (!isFinite(dx) || !isFinite(dy)) {
            console.error("[pan] CRITICAL: Invalid delta! dx:", dx, "dy:", dy);
            return;  // Abort pan operation
        }

        // Track velocity for inertia (smoothed with previous velocity)
        panVelocityX = dx * 0.7 + panVelocityX * 0.3;
        panVelocityY = dy * 0.7 + panVelocityY * 0.3;

        // Apply pan delta
        var newOffsetX = offsetX + dx;
        var newOffsetY = offsetY + dy;

        // Clamp to canvas bounds
        offsetX = clampOffset(newOffsetX, canvasMinX, canvasMaxX, width, canvasWidth);
        offsetY = clampOffset(newOffsetY, canvasMinY, canvasMaxY, height, canvasHeight);

        // Validate final result
        if (!isFinite(offsetX) || !isFinite(offsetY)) {
            console.error("[pan] CRITICAL: Invalid offset produced! Resetting to 0,0");
            offsetX = 0;
            offsetY = 0;
        }
    }

    // Stop inertia when user starts a new interaction
    function stopInertia() {
        panVelocityX = 0;
        panVelocityY = 0;
    }
}
