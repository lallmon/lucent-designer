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
    property bool gridVisible: true

    function refreshGrid() {
        if (!gridVisible)
            return;
        gridShader.baseGridSize = gridSpacingCanvas;
        gridShader.majorMultiplier = gridConfig.majorMultiplier;
        if (gridFallback.visible) {
            gridFallback.requestPaint();
        }
    }

    Component.onCompleted: {
        console.log("[viewport] completed size:", width, height);
    }
    onWidthChanged: {
        console.log("[viewport] width changed:", width, "height:", height);
    }
    onHeightChanged: {
        console.log("[viewport] height changed:", height, "width:", width);
    }

    // Zoom/pan state (camera controls)
    property real zoomLevel: 0.7  // Start at 70%
    readonly property real minZoom: 0.05
    readonly property real maxZoom: 10.0
    readonly property real zoomStep: 1.08  // ~8% base zoom increments for faster wheel zoom

    // Camera offset for panning
    property real offsetX: 0
    property real offsetY: 0

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
        z: 1000  // Render above content as an overlay

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
        property color minorColor: Lucent.Themed.gridMinor
        property color majorColor: Lucent.Themed.gridMajor
        // Precomputed spacing/visibility (matches fallback)
        property real minorStepCanvas: {
            var gridSize = root.gridSpacingCanvas;
            var msPx = gridSize * root.zoomLevel;
            if (msPx < 6) {
                return gridSize; // hidden via showMinorFlag
            } else if (msPx > 24) {
                gridSize = root.gridSpacingCanvas * 0.5;
            }
            return gridSize;
        }
        property real majorStepCanvas: {
            var major = root.gridSpacingCanvas * root.gridConfig.majorMultiplier;
            var msPx = major * root.zoomLevel;
            if (msPx < 12) {
                major = root.gridSpacingCanvas * root.gridConfig.majorMultiplier * 2.0;
            }
            return major;
        }
        property real showMinorFlag: {
            var gridSize = root.gridSpacingCanvas;
            var msPx = gridSize * root.zoomLevel;
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

        onStatusChanged: {
            console.log("[gridShader] status:", status, "baseGridSize:", baseGridSize, "majorMultiplier:", majorMultiplier, "zoomLevel:", root.zoomLevel, "offsetX:", root.offsetX, "offsetY:", root.offsetY, "viewport:", width, height);
        }

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

    // Fallback grid removed (shader-only rendering)

    // The viewport surface that applies zoom and pan transforms
    Item {
        id: viewportContent
        anchors.centerIn: parent
        width: parent.width
        height: parent.height

        // Apply transformations for zoom and pan
        transform: [
            Scale {
                origin.x: viewportContent.width / 2
                origin.y: viewportContent.height / 2
                xScale: root.zoomLevel
                yScale: root.zoomLevel
            },
            Translate {
                x: root.offsetX
                y: root.offsetY
            }
        ]

        // Container for content (Canvas will be placed here)
        // Fill the entire transformed viewport area so Canvas MouseArea receives events
        Item {
            id: contentContainer
            anchors.fill: parent
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

        // Bind cursor shape to Canvas's currentCursorShape
        cursorShape: canvasComponent ? canvasComponent.currentCursorShape : Qt.ArrowCursor

        Keys.onDeletePressed: {
            if (canvasComponent) {
                canvasComponent.deleteSelectedItem();
            }
        }

        Keys.onEscapePressed: {
            if (canvasComponent) {
                canvasComponent.cancelCurrentTool();
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
            if (canvasComponent) {
                canvasComponent.handleMousePress(mouse.x, mouse.y, mouse.button, mouse.modifiers);
            }
        }

        onReleased: mouse => {
            if (canvasComponent) {
                canvasComponent.handleMouseRelease(mouse.x, mouse.y, mouse.button, mouse.modifiers);
            }
        }

        onClicked: mouse => {
            if (canvasComponent) {
                canvasComponent.handleMouseClick(mouse.x, mouse.y, mouse.button);
            }
        }

        onPositionChanged: mouse => {
            lastMouseX = mouse.x;
            lastMouseY = mouse.y;
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

        // Zoom with mouse wheel: proportional, cursor-centered (no zoom animation)
        onWheel: wheel => {
            var step = root.zoomStep;
            var deltaSteps = (wheel.angleDelta.y / 120.0) * 2.0; // 120 per wheel notch
            var factor = Math.pow(step, deltaSteps);
            var newZoom = root.zoomLevel * factor;
            if (newZoom < root.minZoom || newZoom > root.maxZoom)
                return;

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
        }
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
}
