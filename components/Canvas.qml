import QtQuick
import QtQuick.Controls
import CanvasRendering 1.0
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
    property string drawingMode: ""  // "" for pan, "rectangle" for drawing rectangles, "ellipse" for drawing ellipses
    
    // Tool settings model - organized by tool type
    property var toolSettings: ({
        "rectangle": {
            strokeWidth: 1,
            strokeColor: "#ffffff",
            fillColor: "#ffffff",
            fillOpacity: 0.0
        },
        "ellipse": {
            strokeWidth: 1,
            strokeColor: "#ffffff",
            fillColor: "#ffffff",
            fillOpacity: 0.0
        }
    })
    
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
            zoomLevel: root.zoomLevel
            
            Component.onCompleted: {
                setModel(canvasModel)
            }
        }
        
        // Selection indicator overlay
        Rectangle {
            property real selectionPadding: 8  // Padding around selected object in canvas units
            visible: DV.SelectionManager.selectedItemIndex >= 0 && DV.SelectionManager.selectedItem
            
            // Calculate bounding box based on item type
            x: {
                if (!visible) return 0;
                var item = DV.SelectionManager.selectedItem;
                if (item.type === "rectangle") {
                    return item.x - selectionPadding;
                } else if (item.type === "ellipse") {
                    return item.centerX - item.radiusX - selectionPadding;
                }
                return 0;
            }
            
            y: {
                if (!visible) return 0;
                var item = DV.SelectionManager.selectedItem;
                if (item.type === "rectangle") {
                    return item.y - selectionPadding;
                } else if (item.type === "ellipse") {
                    return item.centerY - item.radiusY - selectionPadding;
                }
                return 0;
            }
            
            width: {
                if (!visible) return 0;
                var item = DV.SelectionManager.selectedItem;
                if (item.type === "rectangle") {
                    return item.width + selectionPadding * 2;
                } else if (item.type === "ellipse") {
                    return item.radiusX * 2 + selectionPadding * 2;
                }
                return 0;
            }
            
            height: {
                if (!visible) return 0;
                var item = DV.SelectionManager.selectedItem;
                if (item.type === "rectangle") {
                    return item.height + selectionPadding * 2;
                } else if (item.type === "ellipse") {
                    return item.radiusY * 2 + selectionPadding * 2;
                }
                return 0;
            }
            
            color: "transparent"
            border.color: DV.Theme.colors.accent  // Light blue
            border.width: 2 / root.zoomLevel  // Inverse scale with zoom
        }
        
        // Select tool for object selection (panning handled by Viewport)
        SelectTool {
            id: selectTool
            active: root.drawingMode === ""
            hitTestCallback: root.hitTest
            viewportToCanvasCallback: root.viewportToCanvas
            
            onPanDelta: (dx, dy) => {
                root.panRequested(dx, dy);
            }
            
            onCursorShapeChanged: (shape) => {
                root.currentCursorShape = shape;
            }
            
            onObjectClicked: (viewportX, viewportY) => {
                var canvasCoords = root.viewportToCanvas(viewportX, viewportY);
                root.selectItemAt(canvasCoords.x, canvasCoords.y);
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
                    "rectangle": "RectangleTool.qml",
                    "ellipse": "EllipseTool.qml"
                };
                return toolMap[root.drawingMode] || "";
            }
            
            onLoaded: {
                if (item) {
                    // Bind properties to the loaded tool
                    item.zoomLevel = Qt.binding(function() { return root.zoomLevel; });
                    item.active = Qt.binding(function() { return root.drawingMode !== "" && root.drawingMode !== "select"; });
                    item.settings = Qt.binding(function() { return root.toolSettings[root.drawingMode]; });
                    
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
        
        return { x: canvasX, y: canvasY };
    }
    
    // Public event handlers called from Viewport MouseArea
    function handleMousePress(viewportX, viewportY, button) {
        // Delegate to active tool (SelectTool uses viewport coords)
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
        if (currentToolLoader.item && button === Qt.LeftButton) {
            var canvasCoords = viewportToCanvas(viewportX, viewportY);
            currentToolLoader.item.handleClick(canvasCoords.x, canvasCoords.y);
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
        } else if (currentToolLoader.item) {
            currentToolLoader.item.handleMouseMove(canvasCoords.x, canvasCoords.y);
        }
    }
    
    // Generic item completion handler
    function handleItemCompleted(itemData) {
        // Add item to the model instead of local array
        canvasModel.addItem(itemData);
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
            DV.SelectionManager.selectedItemIndex = -1;
            DV.SelectionManager.selectedItem = null;
        }
    }
    
    // Hit test to find item at canvas coordinates
    function hitTest(canvasX, canvasY) {
        // Get items from model for hit testing
        var items = canvasModel.getItemsForHitTest();
        
        // Iterate backwards (topmost items first)
        for (var i = items.length - 1; i >= 0; i--) {
            var item = items[i];
            if (item.type === "rectangle") {
                // Check if point is within rectangle bounds
                if (canvasX >= item.x && canvasX <= item.x + item.width &&
                    canvasY >= item.y && canvasY <= item.y + item.height) {
                    return i;
                }
            } else if (item.type === "ellipse") {
                // Check if point is within ellipse using the ellipse equation
                var dx = (canvasX - item.centerX) / item.radiusX;
                var dy = (canvasY - item.centerY) / item.radiusY;
                if (dx * dx + dy * dy <= 1.0) {
                    return i;
                }
            }
        }
        return -1; // No hit
    }
    
    // Select item at canvas coordinates
    function selectItemAt(canvasX, canvasY) {
        var hitIndex = hitTest(canvasX, canvasY);
        DV.SelectionManager.selectedItemIndex = hitIndex;
        DV.SelectionManager.selectedItem = (hitIndex >= 0) ? canvasModel.getItemData(hitIndex) : null;
    }
    
    function updateSelectedItemPosition(canvasDx, canvasDy) {
        var index = DV.SelectionManager.selectedItemIndex;
        if (index < 0) return;
        
        var item = DV.SelectionManager.selectedItem;
        if (!item) return;
        
        var properties = {};
        if (item.type === "rectangle") {
            properties.x = item.x + canvasDx;
            properties.y = item.y + canvasDy;
        } else if (item.type === "ellipse") {
            properties.centerX = item.centerX + canvasDx;
            properties.centerY = item.centerY + canvasDy;
        }
        
        canvasModel.updateItem(index, properties);
    }
    
    function deleteSelectedItem() {
        if (DV.SelectionManager.selectedItemIndex >= 0) {
            var index = DV.SelectionManager.selectedItemIndex;
            DV.SelectionManager.selectedItemIndex = -1;
            DV.SelectionManager.selectedItem = null;
            canvasModel.removeItem(index);
        }
    }
}

