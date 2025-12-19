import QtQuick
import QtQuick.Controls

// Rectangle drawing tool component
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
    property var currentRect: null
    
    // Signal emitted when an item is completed
    signal itemCompleted(var itemData)
    
    // Starting point indicator (black dot shown during rectangle drawing)
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
    
    // Preview rectangle with dashed border (shown while drawing)
    Item {
        id: previewRect
        visible: tool.currentRect !== null && 
                 tool.currentRect !== undefined &&
                 tool.currentRect.width > 0 &&
                 tool.currentRect.height > 0
        x: tool.currentRect ? tool.currentRect.x : 0
        y: tool.currentRect ? tool.currentRect.y : 0
        width: tool.currentRect ? tool.currentRect.width : 0
        height: tool.currentRect ? tool.currentRect.height : 0
        
        Rectangle {
            property real halfStroke: settings ? (settings.strokeWidth / tool.zoomLevel / 2) : 0
            x: -halfStroke
            y: -halfStroke
            width: parent.width + settings.strokeWidth / tool.zoomLevel
            height: parent.height + settings.strokeWidth / tool.zoomLevel
            color: {
                if (!settings) return "transparent";
                var c = Qt.color(settings.fillColor);
                c.a = settings.fillOpacity;
                return c;
            }
            border.color: settings ? settings.strokeColor : "#ffffff"
            border.width: (settings ? settings.strokeWidth : 1) / tool.zoomLevel
        }
    }
    
    // Handle clicks for rectangle drawing
    function handleClick(canvasX, canvasY) {
        if (!tool.active) return;
        
        if (!isDrawing) {
            // First click: Start drawing a rectangle
            isDrawing = true;
            drawStartX = canvasX;
            drawStartY = canvasY;
            
            console.log("Draw start:", drawStartX, drawStartY);
            
            // Initialize rectangle at start point with minimal size
            currentRect = {
                x: drawStartX,
                y: drawStartY,
                width: 1,
                height: 1
            };
        } else {
            // Second click: Finalize the rectangle
            if (currentRect && 
                currentRect.width > 1 && 
                currentRect.height > 1) {
                
                console.log("Finalizing rect:", currentRect.x, currentRect.y, 
                           currentRect.width, currentRect.height);
                
                // Create complete item data object
                var itemData = {
                    type: "rectangle",
                    x: currentRect.x,
                    y: currentRect.y,
                    width: currentRect.width,
                    height: currentRect.height,
                    strokeWidth: settings ? settings.strokeWidth : 1,
                    strokeColor: settings ? settings.strokeColor : "#ffffff",
                    fillColor: settings ? settings.fillColor : "#ffffff",
                    fillOpacity: settings ? settings.fillOpacity : 0.0
                };
                
                // Emit signal with complete item data
                itemCompleted(itemData);
            }
            
            // Clear current rectangle and reset drawing state
            currentRect = null;
            isDrawing = false;
        }
    }
    
    // Update preview during mouse movement
    function handleMouseMove(canvasX, canvasY) {
        if (!tool.active || !isDrawing) return;
        
        // Calculate width and height from start point to current point
        var width = canvasX - drawStartX;
        var height = canvasY - drawStartY;
        
        // Handle dragging in any direction (normalize rectangle)
        var rectX = width >= 0 ? drawStartX : canvasX;
        var rectY = height >= 0 ? drawStartY : canvasY;
        var rectWidth = Math.abs(width);
        var rectHeight = Math.abs(height);
        
        // Update current rectangle (create new object to trigger binding)
        currentRect = {
            x: rectX,
            y: rectY,
            width: rectWidth,
            height: rectHeight
        };
    }
    
    // Reset tool state (called when switching tools)
    function reset() {
        isDrawing = false;
        currentRect = null;
    }
}

