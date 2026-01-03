import QtQuick
import QtQuick.Controls
import "." as DV

// Viewport component responsible for zoom, pan, and camera controls
Item {
    id: root
    clip: true  // Constrain rendering to viewport boundaries

    // Zoom/pan state (camera controls)
    property real zoomLevel: 0.7  // Start at 70%
    readonly property real minZoom: 0.1
    readonly property real maxZoom: 10.0
    readonly property real zoomStep: 1.05  // 5% zoom increments

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
        color: DV.Theme.colors.canvasBackground
    }

    // GPU grid overlay: crisp, infinite-feel, tied to current viewport
    ShaderEffect {
        id: gridShader
        anchors.fill: parent
        visible: status === ShaderEffect.Ready

        property real baseGridSize: 32.0
        property real majorMultiplier: 5.0
        // Keep lines consistent across zoom by tying thickness to projected spacing.
        // Matches shader gridSize logic (base, zoomed-out major-only, zoomed-in half).
        // Keep lines very thin across zoom: small clamps plus modest scaling.
        property real _gridSizePx: {
            var g = baseGridSize;
            if (root.zoomLevel < 0.5) {
                g = baseGridSize * majorMultiplier;
            } else if (root.zoomLevel > 2.0) {
                g = baseGridSize * 0.5;
            }
            return g * root.zoomLevel;
        }
        property real minorThicknessPx: Math.min(0.6, Math.max(0.15, _gridSizePx * 0.08))
        property real majorThicknessPx: Math.min(0.9, Math.max(0.2, _gridSizePx * 0.12))
        property real featherPx: Math.min(0.8, Math.max(0.25, minorThicknessPx * 0.7))
        property real zoomLevel: root.zoomLevel
        property real offsetX: root.offsetX
        property real offsetY: root.offsetY
        property color minorColor: DV.Theme.colors.gridMinor
        property color majorColor: DV.Theme.colors.gridMajor
        property var viewportSize: Qt.vector2d(width, height)

        vertexShader: Qt.resolvedUrl("shaders/grid.vert.qsb")
        fragmentShader: Qt.resolvedUrl("shaders/grid.frag.qsb")

        onStatusChanged: {
            if (status === ShaderEffect.Error) {
                console.error("[gridShader] status=Error; grid fallback will activate");
            } else if (status !== ShaderEffect.Ready) {
                console.warn("[gridShader] status:", status, "grid fallback will activate if not Ready");
            }
        }
    }

    // Fallback grid when shader fails or is unavailable (e.g., missing GL backend)
    Canvas {
        id: gridFallback
        anchors.fill: parent
        visible: gridShader.status !== ShaderEffect.Ready
        antialiasing: false
        z: gridShader.z

        // Mirror shader params to keep spacing/colors consistent
        property real baseGridSize: gridShader.baseGridSize
        property real majorMultiplier: gridShader.majorMultiplier

        function gridParams() {
            var gridSize = baseGridSize;
            var showMinor = true;
            if (root.zoomLevel < 0.5) {
                gridSize = baseGridSize * majorMultiplier;
                showMinor = false;
            } else if (root.zoomLevel > 2.0) {
                gridSize = baseGridSize * 0.5;
            }
            return {
                gridSize: gridSize,
                majorStep: baseGridSize * majorMultiplier,
                showMinor: showMinor
            };
        }

        function drawLines(stepPx, color, lineWidth) {
            if (!isFinite(stepPx) || stepPx < 1) {
                return;
            }
            var ctx = getContext("2d");
            ctx.save();
            ctx.strokeStyle = color;
            ctx.lineWidth = lineWidth;

            var originX = (width * 0.5) + root.offsetX;
            var originY = (height * 0.5) + root.offsetY;

            var startX = originX % stepPx;
            if (startX < 0)
                startX += stepPx;
            for (var x = startX; x <= width; x += stepPx) {
                ctx.beginPath();
                ctx.moveTo(x + 0.5, 0);
                ctx.lineTo(x + 0.5, height);
                ctx.stroke();
            }

            var startY = originY % stepPx;
            if (startY < 0)
                startY += stepPx;
            for (var y = startY; y <= height; y += stepPx) {
                ctx.beginPath();
                ctx.moveTo(0, y + 0.5);
                ctx.lineTo(width, y + 0.5);
                ctx.stroke();
            }
            ctx.restore();
        }

        onPaint: {
            var ctx = getContext("2d");
            ctx.resetTransform();
            ctx.clearRect(0, 0, width, height);

            var params = gridParams();
            var zoom = root.zoomLevel;
            if (!isFinite(zoom) || zoom <= 0)
                return;

            var minorStepPx = params.gridSize * zoom;
            var majorStepPx = params.majorStep * zoom;

            // Minor grid
            if (params.showMinor) {
                drawLines(minorStepPx, DV.Theme.colors.gridMinor, gridShader.minorThicknessPx);
            }
            // Major grid overlays minor
            drawLines(majorStepPx, DV.Theme.colors.gridMajor, gridShader.majorThicknessPx);
        }

        onVisibleChanged: {
            if (visible) {
                requestPaint();
            }
        }
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()

        Connections {
            target: root
            function onZoomLevelChanged() {
                if (gridFallback.visible) {
                    gridFallback.requestPaint();
                }
            }
            function onOffsetXChanged() {
                if (gridFallback.visible) {
                    gridFallback.requestPaint();
                }
            }
            function onOffsetYChanged() {
                if (gridFallback.visible) {
                    gridFallback.requestPaint();
                }
            }
        }
    }

    // Origin marker at canvas (0,0)
    Rectangle {
        id: originDot
        width: 8
        height: 8
        radius: 4
        color: "#ff0000"
        x: (parent.width / 2) + root.offsetX - 4
        y: (parent.height / 2) + root.offsetY - 4
        z: 1
    }

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

        // Zoom with mouse wheel
        onWheel: wheel => {
            var factor = wheel.angleDelta.y > 0 ? root.zoomStep : 1.0 / root.zoomStep;
            var newZoom = root.zoomLevel * factor;

            // Clamp zoom level
            if (newZoom >= root.minZoom && newZoom <= root.maxZoom) {
                root.zoomLevel = newZoom;
            }
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
