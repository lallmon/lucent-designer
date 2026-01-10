import QtQuick
import QtQuick.Controls
import ".." as Lucent

// Select tool component - handles panning and object selection
Item {
    id: tool

    property bool active: false
    property var hitTestCallback: null
    property var viewportToCanvasCallback: null
    property var getBoundsCallback: null  // For checking if click is inside selected group
    property var canvasToViewportCallback: null  // For converting canvas coords to viewport

    // Overlay geometry for manual hit testing of rotation handle
    property var overlayGeometry: null  // {centerX, centerY, rotation, armLength, handleSize}

    // When true, overlay handles are being used - don't interfere with dragging
    property bool overlayActive: false

    // When true, cursor is hovering over an overlay handle - don't initiate object drag on press
    property bool isHoveringHandle: false

    // Check if viewport coordinates are near the rotation handle
    function isNearRotationHandle(viewportX, viewportY) {
        if (!overlayGeometry || !canvasToViewportCallback) {
            // #region agent log
            var xhrNoGeom = new XMLHttpRequest();
            xhrNoGeom.open("POST", "http://127.0.0.1:7243/ingest/72fbc74d-dfe2-4303-96ca-b309ef45018d", true);
            xhrNoGeom.setRequestHeader("Content-Type", "application/json");
            xhrNoGeom.send(JSON.stringify({
                location: "SelectTool.qml:isNearRotationHandle",
                message: "Early return - no geometry",
                data: {
                    hasOverlayGeometry: !!overlayGeometry,
                    hasCallback: !!canvasToViewportCallback
                },
                timestamp: Date.now(),
                sessionId: "debug-session",
                hypothesisId: "D"
            }));
            // #endregion
            return false;
        }

        var geom = overlayGeometry;
        var angleRad = geom.rotation * Math.PI / 180;

        // Rotation handle is at top center of overlay, which is at (centerX, centerY - halfHeight - armLength - handleSize/2)
        // The grip's offset from the shape's center (rotation origin) is:
        var offsetX = 0;
        var offsetY = -(geom.halfHeight + geom.armLength + geom.handleSize / 2);

        // Apply rotation
        var rotatedOffsetX = offsetX * Math.cos(angleRad) - offsetY * Math.sin(angleRad);
        var rotatedOffsetY = offsetX * Math.sin(angleRad) + offsetY * Math.cos(angleRad);

        // Handle position in canvas coords
        var handleCanvasX = geom.centerX + rotatedOffsetX;
        var handleCanvasY = geom.centerY + rotatedOffsetY;

        // Convert to viewport coords
        var handleViewport = canvasToViewportCallback(handleCanvasX, handleCanvasY);

        // Check distance (use a generous hit radius)
        var dx = viewportX - handleViewport.x;
        var dy = viewportY - handleViewport.y;
        var dist = Math.sqrt(dx * dx + dy * dy);

        // Hit radius: handleSize + some padding (in viewport space, scale by zoom)
        var hitRadius = (geom.handleSize + geom.armLength) * geom.zoomLevel;

        // #region agent log
        var xhrGeo = new XMLHttpRequest();
        xhrGeo.open("POST", "http://127.0.0.1:7243/ingest/72fbc74d-dfe2-4303-96ca-b309ef45018d", true);
        xhrGeo.setRequestHeader("Content-Type", "application/json");
        xhrGeo.send(JSON.stringify({
            location: "SelectTool.qml:isNearRotationHandle",
            message: "Geometry check",
            data: {
                viewportX: viewportX,
                viewportY: viewportY,
                handleViewportX: handleViewport.x,
                handleViewportY: handleViewport.y,
                dist: dist,
                hitRadius: hitRadius,
                rotation: geom.rotation,
                centerX: geom.centerX,
                centerY: geom.centerY,
                halfHeight: geom.halfHeight,
                offsetY: offsetY,
                result: dist < hitRadius
            },
            timestamp: Date.now(),
            sessionId: "debug-session",
            hypothesisId: "D"
        }));
        // #endregion

        return dist < hitRadius;
    }

    // Reset drag state when overlay becomes active to prevent drag after overlay release
    onOverlayActiveChanged: {
        if (overlayActive) {
            clickedOnSelectedObject = false;
            isDraggingObject = false;
        }
    }

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

            // Check if press is near rotation handle (manual hit test since HoverHandler doesn't work on rotated items)
            var nearRotationHandle = isNearRotationHandle(screenX, screenY);

            // #region agent log
            var xhr1 = new XMLHttpRequest();
            xhr1.open("POST", "http://127.0.0.1:7243/ingest/72fbc74d-dfe2-4303-96ca-b309ef45018d", true);
            xhr1.setRequestHeader("Content-Type", "application/json");
            xhr1.send(JSON.stringify({
                location: "SelectTool.qml:handlePress",
                message: "Press event",
                data: {
                    isHoveringHandle: isHoveringHandle,
                    nearRotationHandle: nearRotationHandle,
                    overlayActive: overlayActive,
                    selectedIdx: Lucent.SelectionManager.selectedItemIndex
                },
                timestamp: Date.now(),
                sessionId: "debug-session",
                hypothesisId: "A,C"
            }));
            // #endregion
            // Don't initiate object drag if cursor is over an overlay handle
            if (!nearRotationHandle && !isHoveringHandle && hitTestCallback && viewportToCanvasCallback && Lucent.SelectionManager.selectedItemIndex >= 0) {
                var canvasCoords = viewportToCanvasCallback(screenX, screenY);
                var hitIndex = hitTestCallback(canvasCoords.x, canvasCoords.y);
                if (hitIndex === Lucent.SelectionManager.selectedItemIndex) {
                    // #region agent log
                    var xhr2 = new XMLHttpRequest();
                    xhr2.open("POST", "http://127.0.0.1:7243/ingest/72fbc74d-dfe2-4303-96ca-b309ef45018d", true);
                    xhr2.setRequestHeader("Content-Type", "application/json");
                    xhr2.send(JSON.stringify({
                        location: "SelectTool.qml:handlePress",
                        message: "clickedOnSelectedObject set TRUE via hitTest",
                        data: {
                            hitIndex: hitIndex
                        },
                        timestamp: Date.now(),
                        sessionId: "debug-session",
                        hypothesisId: "C"
                    }));
                    // #endregion
                    clickedOnSelectedObject = true;
                }
                // Check if click is inside the selected item's bounding box
                if (!clickedOnSelectedObject && getBoundsCallback) {
                    var selectedItem = Lucent.SelectionManager.selectedItem;
                    if (selectedItem) {
                        var bounds = getBoundsCallback(Lucent.SelectionManager.selectedItemIndex);
                        if (bounds && bounds.width >= 0 && bounds.height >= 0) {
                            if (canvasCoords.x >= bounds.x && canvasCoords.x <= bounds.x + bounds.width && canvasCoords.y >= bounds.y && canvasCoords.y <= bounds.y + bounds.height) {
                                clickedOnSelectedObject = true;
                            }
                        }
                    }
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

        // Don't drag object if overlay handles (resize/rotate) are being used
        if (isSelecting && clickedOnSelectedObject && !overlayActive && Lucent.SelectionManager.selectedItemIndex >= 0) {
            var dx = Math.abs(screenX - selectPressX);
            var dy = Math.abs(screenY - selectPressY);

            if (!isDraggingObject && (dx >= clickThreshold || dy >= clickThreshold)) {
                // #region agent log
                var xhr3 = new XMLHttpRequest();
                xhr3.open("POST", "http://127.0.0.1:7243/ingest/72fbc74d-dfe2-4303-96ca-b309ef45018d", true);
                xhr3.setRequestHeader("Content-Type", "application/json");
                xhr3.send(JSON.stringify({
                    location: "SelectTool.qml:handleMouseMove",
                    message: "STARTING OBJECT DRAG",
                    data: {
                        dx: dx,
                        dy: dy,
                        clickThreshold: clickThreshold,
                        clickedOnSelectedObject: clickedOnSelectedObject,
                        overlayActive: overlayActive,
                        isHoveringHandle: isHoveringHandle
                    },
                    timestamp: Date.now(),
                    sessionId: "debug-session",
                    hypothesisId: "C"
                }));
                // #endregion
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
