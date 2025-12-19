import QtQuick
import QtQuick.Controls
import DesignVibe 1.0
import "." as DV

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
    property string drawingMode: ""  // "" for pan, "rectangle" for drawing rectangles
    
    // Tool settings
    property real rectangleStrokeWidth: 1
    property color rectangleStrokeColor: "#ffffff"  // White by default
    property color rectangleFillColor: "#ffffff"  // White by default
    property real rectangleFillOpacity: 0.0  // Transparent by default
    
    // List to store drawn items
    property var items: []
    
    // Current cursor shape (for dynamic cursor changes)
    property int currentCursorShape: Qt.OpenHandCursor
    
    // Canvas content (no transforms - handled by parent Viewport)
    Item {
        id: shapesLayer
        anchors.centerIn: parent
        width: 0
        height: 0
        
        CanvasRenderer {
            x: -5000
            y: -5000
            width: 10000
            height: 10000
            items: root.items
            zoomLevel: root.zoomLevel
        }
        
        // Select tool for object selection (panning handled by Viewport)
        SelectTool {
            id: selectTool
            active: root.drawingMode === ""
            
            onPanDelta: (dx, dy) => {
                root.panRequested(dx, dy);
            }
            
            onCursorShapeChanged: (shape) => {
                root.currentCursorShape = shape;
            }
        }
        
        // Rectangle drawing tool
        RectangleTool {
            id: rectangleTool
            zoomLevel: root.zoomLevel
            active: root.drawingMode === "rectangle"
            
            onRectangleCompleted: (x, y, width, height) => {
                // Copy values (not bindings) to ensure each rectangle has independent properties
                var strokeWidth = Number(root.rectangleStrokeWidth);
                var strokeColorString = root.rectangleStrokeColor.toString();
                var fillColorString = root.rectangleFillColor.toString();
                var fillOpacity = Number(root.rectangleFillOpacity);
                var newItems = root.items.slice();
                newItems.push({
                    type: "rectangle",
                    x: x,
                    y: y,
                    width: width,
                    height: height,
                    strokeWidth: strokeWidth,
                    strokeColor: strokeColorString,
                    fillColor: fillColorString,
                    fillOpacity: fillOpacity
                });
                root.items = newItems;
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
        
        return { x: canvasX, y: canvasY };
    }
    
    // Public event handlers called from Viewport MouseArea
    function handleMousePress(viewportX, viewportY, button) {
        // Delegate to active tool (SelectTool uses viewport coords, RectangleTool needs canvas coords)
        if (root.drawingMode === "") {
            selectTool.handlePress(viewportX, viewportY, button);
        }
    }
    
    function handleMouseRelease(viewportX, viewportY, button) {
        if (root.drawingMode === "") {
            selectTool.handleRelease(viewportX, viewportY, button);
        }
    }
    
    function handleMouseClick(viewportX, viewportY, button) {
        if (root.drawingMode === "rectangle" && button === Qt.LeftButton) {
            var canvasCoords = viewportToCanvas(viewportX, viewportY);
            rectangleTool.handleClick(canvasCoords.x, canvasCoords.y);
        }
    }
    
    function handleMouseMove(viewportX, viewportY) {
        // Update cursor position in canvas coordinates
        var canvasCoords = viewportToCanvas(viewportX, viewportY);
        root.cursorX = canvasCoords.x;
        root.cursorY = canvasCoords.y;
        
        // Only log if coordinates are invalid
        if (!isFinite(root.cursorX) || !isFinite(root.cursorY)) {
            console.error("[handleMouseMove] CRITICAL: Invalid canvas coords!",
                        "cursorX:", root.cursorX, "cursorY:", root.cursorY);
        }
        
        // Delegate to active tool
        if (root.drawingMode === "") {
            selectTool.handleMouseMove(viewportX, viewportY);
        } else if (root.drawingMode === "rectangle") {
            rectangleTool.handleMouseMove(canvasCoords.x, canvasCoords.y);
        }
    }
    
    // Set the drawing mode
    function setDrawingMode(mode) {
        // Reset any active tool
        if (drawingMode === "") {
            selectTool.reset();
        } else if (drawingMode === "rectangle") {
            rectangleTool.reset();
        }
        
        // "select" mode is the same as no mode (pan/zoom)
        if (mode === "select") {
            drawingMode = "";
        } else {
            drawingMode = mode;
        }
        
        if (mode === "rectangle") {
            root.currentCursorShape = Qt.CrossCursor;
        } else {
            root.currentCursorShape = Qt.OpenHandCursor;
        }
    }
}

