import QtQuick
import QtQuick.Controls
import "." as DV

// Viewport component responsible for zoom, pan, and camera controls
Item {
    id: root
    clip: true  // Constrain rendering to viewport boundaries
    
    // Zoom/pan state (camera controls)
    property real zoomLevel: 1.0  // Start at 100%
    readonly property real minZoom: 0.1
    readonly property real maxZoom: 10.0
    readonly property real zoomStep: 1.05  // 5% zoom increments
    
    // Camera offset for panning
    property real offsetX: 0
    property real offsetY: 0
    
    // Canvas bounds (matches CanvasRenderer dimensions)
    readonly property real canvasWidth: 10000
    readonly property real canvasHeight: 10000
    readonly property real canvasMinX: -5000
    readonly property real canvasMaxX: 5000
    readonly property real canvasMinY: -5000
    readonly property real canvasMaxY: 5000
    
    // Minimum visible canvas area (percentage)
    readonly property real minVisibleRatio: 0.2  // Keep 20% of canvas visible
    
    // Content to be displayed (Canvas should be placed as a child)
    default property alias content: contentContainer.data
    
    // Background color
    Rectangle {
        anchors.fill: parent
        color: DV.Theme.colors.canvasBackground
    }
    
    // Enhanced Canvas grid with crisp rendering and adaptive spacing
    // Placed outside viewportContent so it always fills the viewport
    Canvas {
        id: gridCanvas
        anchors.fill: parent
        renderTarget: Canvas.FramebufferObject
        renderStrategy: Canvas.Immediate
        
        property real baseGridSize: 32.0
        property int majorMultiplier: 5
        
        // Trigger repaint on zoom/pan changes immediately (no debouncing)
        onAvailableChanged: requestPaint()
        
        Connections {
            target: root
            function onZoomLevelChanged() { gridCanvas.requestPaint() }
            function onOffsetXChanged() { gridCanvas.requestPaint() }
            function onOffsetYChanged() { gridCanvas.requestPaint() }
        }
        
        onPaint: {
            var ctx = getContext("2d");
            
            // Enable crisp rendering for high-DPI displays
            var dpr = 1.0;  // Qt handles DPI scaling automatically
            
            ctx.clearRect(0, 0, width, height);
            
            // Disable image smoothing for crisp lines
            ctx.imageSmoothingEnabled = false;
            
            // Translate by 0.5px for crisp 1px lines on pixel boundaries
            ctx.save();
            ctx.translate(0.5, 0.5);
            
            // Calculate visible canvas area
            var centerX = width / 2;
            var centerY = height / 2;
            
            // Adaptive grid spacing based on zoom level
            var gridSize = baseGridSize;
            var showMinorLines = true;
            
            if (root.zoomLevel < 0.5) {
                // Zoomed way out: show only major lines with larger spacing
                gridSize = baseGridSize * majorMultiplier;
                showMinorLines = false;
            } else if (root.zoomLevel > 2.0) {
                // Zoomed in: show subdivided grid
                gridSize = baseGridSize / 2;
            }
            
            // Calculate the canvas coordinates of the viewport corners
            var topLeftCanvasX = (-centerX - root.offsetX) / root.zoomLevel;
            var topLeftCanvasY = (-centerY - root.offsetY) / root.zoomLevel;
            var bottomRightCanvasX = (width - centerX - root.offsetX) / root.zoomLevel;
            var bottomRightCanvasY = (height - centerY - root.offsetY) / root.zoomLevel;
            
            // Calculate which grid lines are visible, clamped to canvas bounds
            var startX = Math.max(root.canvasMinX, Math.floor(topLeftCanvasX / gridSize) * gridSize);
            var endX = Math.min(root.canvasMaxX, Math.ceil(bottomRightCanvasX / gridSize) * gridSize);
            var startY = Math.max(root.canvasMinY, Math.floor(topLeftCanvasY / gridSize) * gridSize);
            var endY = Math.min(root.canvasMaxY, Math.ceil(bottomRightCanvasY / gridSize) * gridSize);
            
            // Limit number of lines to prevent performance issues
            var maxLines = 200;
            var xStep = Math.max(gridSize, (endX - startX) / maxLines);
            var yStep = Math.max(gridSize, (endY - startY) / maxLines);
            
            // Round steps to nearest grid multiple
            xStep = Math.ceil(xStep / gridSize) * gridSize;
            yStep = Math.ceil(yStep / gridSize) * gridSize;
            
            // Calculate canvas bounds in screen coordinates for clipping lines
            var canvasTopScreen = root.canvasMinY * root.zoomLevel + centerY + root.offsetY;
            var canvasBottomScreen = root.canvasMaxY * root.zoomLevel + centerY + root.offsetY;
            var canvasLeftScreen = root.canvasMinX * root.zoomLevel + centerX + root.offsetX;
            var canvasRightScreen = root.canvasMaxX * root.zoomLevel + centerX + root.offsetX;
            
            ctx.lineWidth = 1;
            
            // Draw vertical lines (clipped to canvas height)
            for (var x = startX; x <= endX; x += xStep) {
                var screenX = x * root.zoomLevel + centerX + root.offsetX;  // Sub-pixel positioning
                var gridIndex = Math.round(x / baseGridSize);
                var isMajor = (gridIndex % majorMultiplier === 0);
                
                // Skip minor lines if zoomed out
                if (!showMinorLines && !isMajor) continue;
                
                ctx.strokeStyle = isMajor ? DV.Theme.colors.gridMajor : DV.Theme.colors.gridMinor;
                
                ctx.beginPath();
                // Clip line to canvas bounds vertically
                var lineTop = Math.max(0, canvasTopScreen);
                var lineBottom = Math.min(height, canvasBottomScreen);
                ctx.moveTo(screenX, lineTop);
                ctx.lineTo(screenX, lineBottom);
                ctx.stroke();
            }
            
            // Draw horizontal lines (clipped to canvas width)
            for (var y = startY; y <= endY; y += yStep) {
                var screenY = y * root.zoomLevel + centerY + root.offsetY;  // Sub-pixel positioning
                var gridIndex = Math.round(y / baseGridSize);
                var isMajor = (gridIndex % majorMultiplier === 0);
                
                // Skip minor lines if zoomed out
                if (!showMinorLines && !isMajor) continue;
                
                ctx.strokeStyle = isMajor ? DV.Theme.colors.gridMajor : DV.Theme.colors.gridMinor;
                
                ctx.beginPath();
                // Clip line to canvas bounds horizontally
                var lineLeft = Math.max(0, canvasLeftScreen);
                var lineRight = Math.min(width, canvasRightScreen);
                ctx.moveTo(lineLeft, screenY);
                ctx.lineTo(lineRight, screenY);
                ctx.stroke();
            }
            
            // Draw canvas boundary rectangle
            ctx.strokeStyle = DV.Theme.colors.gridMajor;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.rect(
                Math.max(0, canvasLeftScreen),
                Math.max(0, canvasTopScreen),
                Math.min(width, canvasRightScreen) - Math.max(0, canvasLeftScreen),
                Math.min(height, canvasBottomScreen) - Math.max(0, canvasTopScreen)
            );
            ctx.stroke();
            
            ctx.restore();
        }
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
        
        onPressed: (mouse) => {
            forceActiveFocus();
            if (canvasComponent) {
                canvasComponent.handleMousePress(mouse.x, mouse.y, mouse.button);
            }
        }
        
        onReleased: (mouse) => {
            if (canvasComponent) {
                canvasComponent.handleMouseRelease(mouse.x, mouse.y, mouse.button);
            }
        }
        
        onClicked: (mouse) => {
            if (canvasComponent) {
                canvasComponent.handleMouseClick(mouse.x, mouse.y, mouse.button);
            }
        }
        
        onPositionChanged: (mouse) => {
            if (canvasComponent) {
                canvasComponent.handleMouseMove(mouse.x, mouse.y);
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
        onWheel: (wheel) => {
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
            console.error("[clampOffset] CRITICAL: Invalid input! offset:", offset, 
                         "viewportSize:", viewportSize, "canvasSize:", canvasSize);
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
            console.error("[clampOffset] CRITICAL: Invalid clamp range! minOffset:", 
                         minOffset, ">=", "maxOffset:", maxOffset,
                         "zoom:", zoomLevel, "viewportSize:", viewportSize,
                         "Falling back to no clamping");
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

