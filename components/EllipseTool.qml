import QtQuick
import QtQuick.Controls

// Ellipse drawing tool component
Item {
    id: tool
    
    // Properties passed from Canvas
    property real zoomLevel: 1.0
    property bool active: false
    property var settings: null  // Tool settings object
    
    // Internal state
    property bool isDrawing: false
    property real drawStartX: 0
    property real drawStartY: 0
    property var currentEllipse: null
    
    // Signal emitted when an item is completed
    signal itemCompleted(var itemData)
    
    // Starting point indicator (black dot shown during ellipse drawing)
    Rectangle {
        id: startPointIndicator
        visible: tool.isDrawing
        x: tool.drawStartX - (6 / tool.zoomLevel)
        y: tool.drawStartY - (6 / tool.zoomLevel)
        width: 12 / tool.zoomLevel
        height: 12 / tool.zoomLevel
        radius: 6 / tool.zoomLevel
        color: "black"
        border.color: "white"
        border.width: 1 / tool.zoomLevel
    }
    
    // Preview ellipse with dashed border (shown while drawing)
    Item {
        id: previewEllipse
        visible: tool.currentEllipse !== null && 
                 tool.currentEllipse !== undefined &&
                 tool.currentEllipse.width > 0 &&
                 tool.currentEllipse.height > 0
        x: tool.currentEllipse ? tool.currentEllipse.x : 0
        y: tool.currentEllipse ? tool.currentEllipse.y : 0
        width: tool.currentEllipse ? tool.currentEllipse.width : 0
        height: tool.currentEllipse ? tool.currentEllipse.height : 0
        
        // Dashed border drawn with Canvas
        Canvas {
            id: dashedCanvas
            property real padding: settings ? (settings.strokeWidth / tool.zoomLevel / 2) : 0
            x: -padding
            y: -padding
            width: parent.width + padding * 2
            height: parent.height + padding * 2
            
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height);
                
                if (width > 0 && height > 0 && settings) {
                    var pad = padding;
                    var centerX = width / 2;
                    var centerY = height / 2;
                    var radiusX = (parent.width / 2);
                    var radiusY = (parent.height / 2);
                    
                    ctx.save();
                    ctx.translate(centerX, centerY);
                    ctx.scale(radiusX, radiusY);
                    ctx.beginPath();
                    ctx.arc(0, 0, 1, 0, 2 * Math.PI, false);
                    ctx.restore();
                    
                    var fillColor = Qt.color(settings.fillColor);
                    fillColor.a = settings.fillOpacity;
                    ctx.fillStyle = fillColor;
                    ctx.fill();
                    
                    ctx.strokeStyle = settings.strokeColor;
                    ctx.lineWidth = settings.strokeWidth / tool.zoomLevel;
                    ctx.stroke();
                }
            }
            
            Component.onCompleted: requestPaint()
            
            Connections {
                target: previewEllipse
                function onWidthChanged() { dashedCanvas.requestPaint() }
                function onHeightChanged() { dashedCanvas.requestPaint() }
                function onVisibleChanged() { if (previewEllipse.visible) dashedCanvas.requestPaint() }
            }
            
            Connections {
                target: tool
                function onZoomLevelChanged() { dashedCanvas.requestPaint() }
                function onSettingsChanged() { dashedCanvas.requestPaint() }
            }
        }
    }
    
    // Handle clicks for ellipse drawing (two-click pattern like rectangle tool)
    function handleClick(canvasX, canvasY) {
        if (!tool.active) return;
        
        if (!isDrawing) {
            // First click: Start drawing an ellipse
            isDrawing = true;
            drawStartX = canvasX;
            drawStartY = canvasY;
            
            console.log("Ellipse draw start:", drawStartX, drawStartY);
            
            // Initialize ellipse at start point with minimal size
            currentEllipse = {
                x: drawStartX,
                y: drawStartY,
                width: 1,
                height: 1
            };
        } else {
            // Second click: Finalize the ellipse
            if (currentEllipse && 
                currentEllipse.width > 1 && 
                currentEllipse.height > 1) {
                
                console.log("Finalizing ellipse:", currentEllipse.x, currentEllipse.y, 
                           currentEllipse.width, currentEllipse.height);
                
                // Convert bounding box to center and radii
                var centerX = currentEllipse.x + currentEllipse.width / 2;
                var centerY = currentEllipse.y + currentEllipse.height / 2;
                var radiusX = currentEllipse.width / 2;
                var radiusY = currentEllipse.height / 2;
                
                // Create complete item data object
                var itemData = {
                    type: "ellipse",
                    centerX: centerX,
                    centerY: centerY,
                    radiusX: radiusX,
                    radiusY: radiusY,
                    strokeWidth: settings ? settings.strokeWidth : 1,
                    strokeColor: settings ? settings.strokeColor : "#ffffff",
                    fillColor: settings ? settings.fillColor : "#ffffff",
                    fillOpacity: settings ? settings.fillOpacity : 0.0
                };
                
                // Emit signal with complete item data
                itemCompleted(itemData);
            }
            
            // Clear current ellipse and reset drawing state
            currentEllipse = null;
            isDrawing = false;
        }
    }
    
    // Update preview during mouse movement
    function handleMouseMove(canvasX, canvasY) {
        if (!tool.active || !isDrawing) return;
        
        // Calculate width and height from start point to current point
        var width = canvasX - drawStartX;
        var height = canvasY - drawStartY;
        
        // Handle dragging in any direction (normalize bounding box)
        var ellipseX = width >= 0 ? drawStartX : canvasX;
        var ellipseY = height >= 0 ? drawStartY : canvasY;
        var ellipseWidth = Math.abs(width);
        var ellipseHeight = Math.abs(height);
        
        // Update current ellipse (create new object to trigger binding)
        currentEllipse = {
            x: ellipseX,
            y: ellipseY,
            width: ellipseWidth,
            height: ellipseHeight
        };
    }
    
    // Reset tool state (called when switching tools)
    function reset() {
        isDrawing = false;
        currentEllipse = null;
    }
}

