import QtQuick
import QtQuick.Controls
import "." as DV

// Select tool component - handles panning and object selection
Item {
    id: tool

    property bool active: false
    property var hitTestCallback: null
    property var viewportToCanvasCallback: null

    property bool isPanning: false
    property bool isSelecting: false
    property bool isDraggingObject: false
    property bool clickedOnSelectedObject: false
    property real lastX: 0
    property real lastY: 0
    property real selectPressX: 0
    property real selectPressY: 0
    property int lastModifiers: Qt.NoModifier

    property var deltaBufferX: []
    property var deltaBufferY: []
    property int bufferSize: 3
    property real clickThreshold: 5

    signal panDelta(real dx, real dy)
    signal cursorShapeChanged(int shape)
    signal objectClicked(real viewportX, real viewportY, int modifiers)
    signal objectDragged(real canvasDx, real canvasDy)

    function handlePress(screenX, screenY, button, modifiers) {
        if (!tool.active)
            return false;

        if (button === Qt.MiddleButton) {
            isPanning = true;
            lastX = screenX;
            lastY = screenY;
            deltaBufferX = [];
            deltaBufferY = [];
            cursorShapeChanged(Qt.ClosedHandCursor);
            return true;
        }

        if (button === Qt.LeftButton) {
            isSelecting = true;
            selectPressX = screenX;
            selectPressY = screenY;
            lastX = screenX;
            lastY = screenY;
            clickedOnSelectedObject = false;
            lastModifiers = modifiers;
            lastModifiers = modifiers;

            if (hitTestCallback && viewportToCanvasCallback && DV.SelectionManager.selectedItemIndex >= 0) {
                var canvasCoords = viewportToCanvasCallback(screenX, screenY);
                var hitIndex = hitTestCallback(canvasCoords.x, canvasCoords.y);
                if (hitIndex === DV.SelectionManager.selectedItemIndex) {
                    clickedOnSelectedObject = true;
                }
            }

            return true;
        }

        return false;
    }

    function handleRelease(screenX, screenY, button, modifiers) {
        if (!tool.active)
            return false;

        if (isPanning && button === Qt.MiddleButton) {
            isPanning = false;
            cursorShapeChanged(Qt.OpenHandCursor);
            return true;
        }

        if (isSelecting && button === Qt.LeftButton) {
            if (isDraggingObject) {
                canvasModel.endTransaction();
                isDraggingObject = false;
                isSelecting = false;
                cursorShapeChanged(Qt.OpenHandCursor);
                return true;
            }

            isSelecting = false;
            var dx = Math.abs(screenX - selectPressX);
            var dy = Math.abs(screenY - selectPressY);

            if (dx < clickThreshold && dy < clickThreshold) {
                objectClicked(screenX, screenY, modifiers);
            }

            return true;
        }

        return false;
    }

    function handleMouseMove(screenX, screenY) {
        if (!tool.active)
            return false;

        if (isPanning) {
            var dx = screenX - lastX;
            var dy = screenY - lastY;

            var maxDelta = 200;
            if (Math.abs(dx) > maxDelta || Math.abs(dy) > maxDelta) {
                dx = Math.max(-maxDelta, Math.min(maxDelta, dx));
                dy = Math.max(-maxDelta, Math.min(maxDelta, dy));
            }

            deltaBufferX.push(dx);
            deltaBufferY.push(dy);

            if (deltaBufferX.length > bufferSize) {
                deltaBufferX.shift();
                deltaBufferY.shift();
            }

            var sumX = 0, sumY = 0;
            for (var i = 0; i < deltaBufferX.length; i++) {
                sumX += deltaBufferX[i];
                sumY += deltaBufferY[i];
            }
            var avgDx = sumX / deltaBufferX.length;
            var avgDy = sumY / deltaBufferY.length;

            panDelta(avgDx, avgDy);

            lastX = screenX;
            lastY = screenY;
            return true;
        }

        if (isSelecting && clickedOnSelectedObject && DV.SelectionManager.selectedItemIndex >= 0) {
            var dx = Math.abs(screenX - selectPressX);
            var dy = Math.abs(screenY - selectPressY);

            if (!isDraggingObject && (dx >= clickThreshold || dy >= clickThreshold)) {
                isDraggingObject = true;
                canvasModel.beginTransaction();
                cursorShapeChanged(Qt.ClosedHandCursor);
            }

            if (isDraggingObject) {
                objectDragged(screenX - lastX, screenY - lastY);
                lastX = screenX;
                lastY = screenY;
                return true;
            }
        }

        return false;
    }

    function reset() {
        isPanning = false;
        isSelecting = false;
        isDraggingObject = false;
        clickedOnSelectedObject = false;
    }
}
