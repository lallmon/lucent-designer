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

    ToolDefaults {
        id: toolDefaults
    }
    HitTestHelper {
        id: hitTestHelper
    }

    // Tool settings model - organized by tool type
    property var toolSettings: toolDefaults.values

    // Current cursor shape (for dynamic cursor changes)
    property int currentCursorShape: Qt.OpenHandCursor

    // Canvas content (no transforms - handled by parent Viewport)
    Item {
        id: shapesLayer
        anchors.centerIn: parent
        width: 0
        height: 0

        // Renderer sized to the current viewport; we only render what is visible.
        CanvasRenderer {
            id: canvasRenderer
            // Expand with zoom and modest padding; cap under GPU limits to reduce overdraw.
            readonly property real _pad: 1000
            width: Math.min(14000, (root.width / Math.max(root.zoomLevel, 0.001)) + _pad * 2)
            height: Math.min(14000, (root.height / Math.max(root.zoomLevel, 0.001)) + _pad * 2)
            x: -width / 2
            y: -height / 2
            zoomLevel: root.zoomLevel

            Component.onCompleted: {
                setModel(canvasModel);
            }
        }

        // Selection indicator overlay
        SelectionOverlay {
            id: selectionOverlay
            selectionPadding: 8  // Padding around selected object in canvas units
            selectedItem: DV.SelectionManager.selectedItem
            zoomLevel: root.zoomLevel
            accentColor: DV.Theme.colors.accent
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

            onCursorShapeChanged: shape => {
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
                    item.zoomLevel = Qt.binding(function () {
                        return root.zoomLevel;
                    });
                    item.active = Qt.binding(function () {
                        return root.drawingMode !== "" && root.drawingMode !== "select";
                    });
                    item.settings = Qt.binding(function () {
                        return root.toolSettings[root.drawingMode];
                    });

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

    function handleMouseMove(viewportX, viewportY, modifiers) {
        // Update cursor position in canvas coordinates
        var canvasCoords = viewportToCanvas(viewportX, viewportY);
        root.cursorX = canvasCoords.x;
        root.cursorY = canvasCoords.y;

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
        hitTestHelper.applySelection(DV.SelectionManager, canvasModel, newIndex);
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
        return hitTestHelper.hitTest(canvasModel.getItemsForHitTest(), canvasX, canvasY);
    }

    // Select item at canvas coordinates
    function selectItemAt(canvasX, canvasY) {
        var hitIndex = hitTest(canvasX, canvasY);
        hitTestHelper.applySelection(DV.SelectionManager, canvasModel, hitIndex);
    }

    function updateSelectedItemPosition(canvasDx, canvasDy) {
        var index = DV.SelectionManager.selectedItemIndex;
        if (index < 0)
            return;

        var item = DV.SelectionManager.selectedItem;
        if (!item)
            return;
        if (canvasModel.isEffectivelyLocked(index))
            return;

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
            if (canvasModel.isEffectivelyLocked(index))
                return;
            DV.SelectionManager.selectedItemIndex = -1;
            DV.SelectionManager.selectedItem = null;
            canvasModel.removeItem(index);
        }
    }

    // Cancel the current drawing tool operation
    function cancelCurrentTool() {
        if (currentToolLoader.item) {
            currentToolLoader.item.reset();
        }
    }
}
