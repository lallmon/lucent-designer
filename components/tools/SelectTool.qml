// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import ".." as Lucent

// Select tool component - handles panning and object selection
Item {
    id: tool

    property bool active: false
    property var hitTestCallback: null
    property var viewportToCanvasCallback: null
    property var getBoundsCallback: null
    property var canvasToViewportCallback: null

    // Overlay geometry for manual hit testing of handles
    property var overlayGeometry: null

    // When true, overlay handles are being used - don't interfere with dragging
    property bool overlayActive: false

    // Calculate overlay position and dimensions accounting for origin and scale
    function getOverlayBounds(geom) {
        var b = geom.bounds;
        var t = geom.transform;
        var scaleX = t.scaleX || 1;
        var scaleY = t.scaleY || 1;
        var originX = t.originX || 0;
        var originY = t.originY || 0;
        var translateX = t.translateX || 0;
        var translateY = t.translateY || 0;

        var displayedWidth = b.width * scaleX;
        var displayedHeight = b.height * scaleY;

        var overlayX = b.x + translateX + (b.width * originX) - (displayedWidth * originX);
        var overlayY = b.y + translateY + (b.height * originY) - (displayedHeight * originY);

        return {
            x: overlayX,
            y: overlayY,
            width: displayedWidth,
            height: displayedHeight,
            pivotX: overlayX + displayedWidth * originX,
            pivotY: overlayY + displayedHeight * originY,
            originX: originX,
            originY: originY,
            rotation: t.rotate || 0
        };
    }

    // Transform a point from overlay-local coords to canvas coords
    function overlayToCanvas(localX, localY, bounds) {
        var dx = localX - bounds.width * bounds.originX;
        var dy = localY - bounds.height * bounds.originY;
        var angleRad = bounds.rotation * Math.PI / 180;
        var rotatedX = dx * Math.cos(angleRad) - dy * Math.sin(angleRad);
        var rotatedY = dx * Math.sin(angleRad) + dy * Math.cos(angleRad);
        return {
            x: bounds.pivotX + rotatedX,
            y: bounds.pivotY + rotatedY
        };
    }

    // Check if viewport coordinates are near the rotation handle
    function isNearRotationHandle(viewportX, viewportY) {
        if (!overlayGeometry || !canvasToViewportCallback)
            return false;

        var geom = overlayGeometry;
        var bounds = getOverlayBounds(geom);

        // Rotation grip is at top-center of overlay, extending upward
        var handleCanvas = overlayToCanvas(bounds.width / 2, -geom.armLength - geom.handleSize / 2, bounds);
        var handleViewport = canvasToViewportCallback(handleCanvas.x, handleCanvas.y);

        var dx = viewportX - handleViewport.x;
        var dy = viewportY - handleViewport.y;
        // Cap hit radius to prevent overlap with shape at low zoom
        var hitRadius = Math.min((geom.handleSize + geom.armLength) * geom.zoomLevel, 30);
        return Math.sqrt(dx * dx + dy * dy) < hitRadius;
    }

    // Resize handle positions as fractions of width/height
    readonly property var resizeHandleFactors: [
        {
            x: 0,
            y: 0
        },
        {
            x: 0.5,
            y: 0
        },
        {
            x: 1,
            y: 0
        },
        {
            x: 1,
            y: 0.5
        },
        {
            x: 1,
            y: 1
        },
        {
            x: 0.5,
            y: 1
        },
        {
            x: 0,
            y: 1
        },
        {
            x: 0,
            y: 0.5
        }
    ]

    // Check if viewport coordinates are near any resize handle
    function isNearResizeHandle(viewportX, viewportY) {
        if (!overlayGeometry || !canvasToViewportCallback)
            return false;

        var geom = overlayGeometry;
        var bounds = getOverlayBounds(geom);
        // Cap hit radius to prevent overlap with shape at low zoom
        var hitRadius = Math.min(geom.handleSize * geom.zoomLevel * 2, 20);

        for (var i = 0; i < resizeHandleFactors.length; i++) {
            var f = resizeHandleFactors[i];
            var handleCanvas = overlayToCanvas(f.x * bounds.width, f.y * bounds.height, bounds);
            var handleViewport = canvasToViewportCallback(handleCanvas.x, handleCanvas.y);

            var dx = viewportX - handleViewport.x;
            var dy = viewportY - handleViewport.y;
            if (Math.sqrt(dx * dx + dy * dy) < hitRadius)
                return true;
        }
        return false;
    }

    onOverlayActiveChanged: {
        if (overlayActive) {
            clickedOnSelectedObject = false;
            isDraggingObject = false;
        }
    }

    property bool isSelecting: false
    property bool isDraggingObject: false
    property bool clickedOnSelectedObject: false
    property real lastX: 0
    property real lastY: 0
    property real selectPressX: 0
    property real selectPressY: 0
    property int lastModifiers: Qt.NoModifier

    property real clickThreshold: 5
    signal cursorShapeChanged(int shape)
    signal objectClicked(real viewportX, real viewportY, int modifiers)
    signal objectDragged(real canvasDx, real canvasDy)

    function handlePress(screenX, screenY, button, modifiers) {
        if (!tool.active)
            return false;

        if (button === Qt.LeftButton && Lucent.SelectionManager.editModeActive)
            return false;

        if (button === Qt.LeftButton) {
            isSelecting = true;
            selectPressX = screenX;
            selectPressY = screenY;
            lastX = screenX;
            lastY = screenY;
            clickedOnSelectedObject = false;
            lastModifiers = modifiers;

            // Don't initiate object drag if cursor is over an overlay handle
            var nearAnyHandle = isNearRotationHandle(screenX, screenY) || isNearResizeHandle(screenX, screenY);

            if (!nearAnyHandle && hitTestCallback && viewportToCanvasCallback && Lucent.SelectionManager.selectedItemIndex >= 0) {
                var canvasCoords = viewportToCanvasCallback(screenX, screenY);
                var hitIndex = hitTestCallback(canvasCoords.x, canvasCoords.y);
                if (hitIndex === Lucent.SelectionManager.selectedItemIndex) {
                    clickedOnSelectedObject = true;
                }
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
                if (!Lucent.SelectionManager.editModeActive)
                    objectClicked(screenX, screenY, modifiers);
            }

            return true;
        }

        return false;
    }

    function handleMouseMove(screenX, screenY) {
        if (!tool.active)
            return false;

        if (isSelecting && clickedOnSelectedObject && !overlayActive && !Lucent.SelectionManager.editModeActive && Lucent.SelectionManager.selectedItemIndex >= 0) {
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
        isSelecting = false;
        isDraggingObject = false;
        clickedOnSelectedObject = false;
    }
}
