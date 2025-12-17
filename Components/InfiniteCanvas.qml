import QtQuick
import QtQuick.Controls

// Infinite Canvas component with pan and zoom capabilities
Item {
    id: root
    
    // Public properties
    property real zoomLevel: 0.5  // Start zoomed out
    readonly property real minZoom: 0.1
    readonly property real maxZoom: 10.0
    readonly property real zoomStep: 1.2
    
    // Canvas offset for panning (represents camera position)
    property real offsetX: 0
    property real offsetY: 0
    
    // Background color
    Rectangle {
        anchors.fill: parent
        color: "#2b2b2b"
    }
    
    // The main canvas surface that can be panned and zoomed
    Item {
        id: canvasContent
        anchors.centerIn: parent
        width: parent.width
        height: parent.height
        
        // Apply transformations for zoom and pan
        transform: [
            Scale {
                origin.x: canvasContent.width / 2
                origin.y: canvasContent.height / 2
                xScale: root.zoomLevel
                yScale: root.zoomLevel
            },
            Translate {
                x: root.offsetX / root.zoomLevel
                y: root.offsetY / root.zoomLevel
            }
        ]
        
        // Grid background for visual reference
        Canvas {
            id: gridCanvas
            anchors.centerIn: parent
            width: 36000   // Large size for "infinite" feel
            height: 36000
            
            property real gridSize: 32  // Grid cell size in pixels
            property color gridColor: "#3a3a3a"
            property color majorGridColor: "#4a4a4a"
            
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height);
                
                // Calculate visible grid bounds
                var startX = 0;
                var startY = 0;
                var endX = width;
                var endY = height;
                
                // Draw minor grid lines
                ctx.strokeStyle = gridColor;
                ctx.lineWidth = 1;
                ctx.beginPath();
                
                // Vertical lines
                for (var x = startX; x <= endX; x += gridSize) {
                    ctx.moveTo(x, startY);
                    ctx.lineTo(x, endY);
                }
                
                // Horizontal lines
                for (var y = startY; y <= endY; y += gridSize) {
                    ctx.moveTo(startX, y);
                    ctx.lineTo(endX, y);
                }
                
                ctx.stroke();
                
                // Draw major grid lines (every 5 cells)
                ctx.strokeStyle = majorGridColor;
                ctx.lineWidth = 2;
                ctx.beginPath();
                
                var majorGridSize = gridSize * 5;
                
                // Vertical major lines
                for (x = startX; x <= endX; x += majorGridSize) {
                    ctx.moveTo(x, startY);
                    ctx.lineTo(x, endY);
                }
                
                // Horizontal major lines
                for (y = startY; y <= endY; y += majorGridSize) {
                    ctx.moveTo(startX, y);
                    ctx.lineTo(endX, y);
                }
                
                ctx.stroke();
            }
            
            Component.onCompleted: requestPaint()
        }
    }
    
    // Mouse area for panning
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.MiddleButton
        
        property real lastX: 0
        property real lastY: 0
        property bool isPanning: false
        
        onPressed: (mouse) => {
            // Pan with left or middle button
            if (mouse.button === Qt.LeftButton || mouse.button === Qt.MiddleButton) {
                isPanning = true;
                lastX = mouse.x;
                lastY = mouse.y;
                cursorShape = Qt.ClosedHandCursor;
            }
        }
        
        onReleased: {
            isPanning = false;
            cursorShape = Qt.ArrowCursor;
        }
        
        onPositionChanged: (mouse) => {
            if (isPanning) {
                var dx = mouse.x - lastX;
                var dy = mouse.y - lastY;
                
                root.offsetX += dx;
                root.offsetY += dy;
                
                lastX = mouse.x;
                lastY = mouse.y;
            }
        }
        
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
}

