// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Shapes
import "." as Lucent

Shape {
    id: selectionOverlay

    property var geometryBounds
    property var itemTransform
    property real zoomLevel: 1.0
    property real selectionPadding: 0
    property color accentColor: Lucent.Themed.selector

    // Cursor position in canvas coordinates (passed from Canvas)
    property real cursorX: 0
    property real cursorY: 0

    signal resizeRequested(var newBounds)
    signal rotateRequested(real angle)
    signal scaleResizeRequested(real scaleX, real scaleY, real anchorX, real anchorY)

    property bool shiftPressed: false
    property bool isRotating: false

    readonly property real _geomX: geometryBounds ? geometryBounds.x : 0
    readonly property real _geomY: geometryBounds ? geometryBounds.y : 0
    readonly property real _geomWidth: geometryBounds ? geometryBounds.width : 0
    readonly property real _geomHeight: geometryBounds ? geometryBounds.height : 0

    readonly property real _rotation: itemTransform ? (itemTransform.rotate || 0) : 0
    readonly property real _translateX: itemTransform ? (itemTransform.translateX || 0) : 0
    readonly property real _translateY: itemTransform ? (itemTransform.translateY || 0) : 0
    readonly property real _scaleX: itemTransform ? (itemTransform.scaleX || 1) : 1
    readonly property real _scaleY: itemTransform ? (itemTransform.scaleY || 1) : 1
    readonly property real _originX: itemTransform ? (itemTransform.originX || 0) : 0
    readonly property real _originY: itemTransform ? (itemTransform.originY || 0) : 0

    readonly property bool _hasTransform: itemTransform !== null && itemTransform !== undefined

    // Displayed size (geometry × scale) - what the user sees
    readonly property real _displayedWidth: _geomWidth * _scaleX
    readonly property real _displayedHeight: _geomHeight * _scaleY

    visible: geometryBounds !== null && geometryBounds !== undefined

    // Position accounts for scale's effect on origin offset
    x: _geomX + _translateX + (_geomWidth * _originX) - (_displayedWidth * _originX) - selectionPadding
    y: _geomY + _translateY + (_geomHeight * _originY) - (_displayedHeight * _originY) - selectionPadding
    width: _displayedWidth + selectionPadding * 2
    height: _displayedHeight + selectionPadding * 2

    // Only rotation - no scale (size already accounts for scale)
    transform: Rotation {
        origin.x: selectionOverlay.width * selectionOverlay._originX
        origin.y: selectionOverlay.height * selectionOverlay._originY
        angle: selectionOverlay._rotation
    }

    readonly property real handleSize: 10 / zoomLevel
    readonly property real rotationArmLength: 30 / zoomLevel
    property bool isResizing: false

    ShapePath {
        strokeColor: selectionOverlay.accentColor
        strokeWidth: selectionOverlay.zoomLevel > 0 ? 1 / selectionOverlay.zoomLevel : 0
        fillColor: "transparent"
        joinStyle: ShapePath.MiterJoin
        capStyle: ShapePath.FlatCap

        startX: 0
        startY: 0
        PathLine {
            x: selectionOverlay.width
            y: 0
        }
        PathLine {
            x: selectionOverlay.width
            y: selectionOverlay.height
        }
        PathLine {
            x: 0
            y: selectionOverlay.height
        }
        PathLine {
            x: 0
            y: 0
        }
    }

    // Rotation arm line from center-top upward
    ShapePath {
        strokeColor: selectionOverlay._hasTransform ? selectionOverlay.accentColor : "transparent"
        strokeWidth: selectionOverlay._hasTransform && selectionOverlay.zoomLevel > 0 ? 1 / selectionOverlay.zoomLevel : 0
        fillColor: "transparent"

        startX: selectionOverlay.width / 2
        startY: 0
        PathLine {
            x: selectionOverlay.width / 2
            y: -selectionOverlay.rotationArmLength
        }
    }

    // Rotation handle: stem + grip as a single interactive area
    Item {
        id: rotationHandle
        visible: selectionOverlay._hasTransform
        x: selectionOverlay.width / 2 - selectionOverlay.handleSize / 2
        y: -selectionOverlay.rotationArmLength - selectionOverlay.handleSize / 2
        width: selectionOverlay.handleSize
        height: selectionOverlay.rotationArmLength + selectionOverlay.handleSize / 2

        property real startAngle: 0
        property real initialCursorAngle: 0
        property bool initialAngleCaptured: false

        function calculateCursorAngle() {
            var centerX = selectionOverlay._geomX + selectionOverlay._geomWidth / 2 + selectionOverlay._translateX;
            var centerY = selectionOverlay._geomY + selectionOverlay._geomHeight / 2 + selectionOverlay._translateY;
            var dx = selectionOverlay.cursorX - centerX;
            var dy = selectionOverlay.cursorY - centerY;
            return Math.atan2(dx, -dy) * 180 / Math.PI;
        }

        // Visible grip circle at the top
        Rectangle {
            id: rotationGrip
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            width: selectionOverlay.handleSize
            height: selectionOverlay.handleSize
            radius: selectionOverlay.handleSize / 2
            color: selectionOverlay.accentColor
        }

        DragHandler {
            id: rotationDragHandler
            target: null

            onActiveChanged: {
                selectionOverlay.isRotating = active;
                if (active) {
                    rotationHandle.startAngle = selectionOverlay._rotation;
                    rotationHandle.initialAngleCaptured = false;
                }
            }

            onTranslationChanged: {
                if (!active)
                    return;

                if (!rotationHandle.initialAngleCaptured) {
                    rotationHandle.initialCursorAngle = rotationHandle.calculateCursorAngle();
                    rotationHandle.initialAngleCaptured = true;
                    return;
                }

                var currentCursorAngle = rotationHandle.calculateCursorAngle();
                var deltaAngle = currentCursorAngle - rotationHandle.initialCursorAngle;
                var newAngle = rotationHandle.startAngle + deltaAngle;

                if (selectionOverlay.shiftPressed) {
                    newAngle = Math.round(newAngle / 15) * 15;
                }

                selectionOverlay.rotateRequested(newAngle);
            }
        }
    }

    Repeater {
        model: [
            {
                x: 0,
                y: 0,
                type: "tl"
            },
            {
                x: 0.5,
                y: 0,
                type: "t"
            },
            {
                x: 1,
                y: 0,
                type: "tr"
            },
            {
                x: 1,
                y: 0.5,
                type: "r"
            },
            {
                x: 1,
                y: 1,
                type: "br"
            },
            {
                x: 0.5,
                y: 1,
                type: "b"
            },
            {
                x: 0,
                y: 1,
                type: "bl"
            },
            {
                x: 0,
                y: 0.5,
                type: "l"
            }
        ]

        Rectangle {
            id: handle
            required property var modelData
            required property int index

            x: selectionOverlay.width * modelData.x - selectionOverlay.handleSize / 2
            y: selectionOverlay.height * modelData.y - selectionOverlay.handleSize / 2
            width: selectionOverlay.handleSize
            height: selectionOverlay.handleSize
            radius: selectionOverlay.handleSize / 2
            color: selectionOverlay.accentColor

            property var startBounds: null
            property var startTransform: null
            property real startCursorX: 0
            property real startCursorY: 0

            // Anchor point is the opposite corner/edge (stays fixed during resize)
            readonly property real anchorX: {
                var t = modelData.type;
                if (t.indexOf("l") >= 0)
                    return 1.0;  // left edge → anchor right
                if (t.indexOf("r") >= 0)
                    return 0.0;  // right edge → anchor left
                return 0.5;  // center (edge handles)
            }
            readonly property real anchorY: {
                var t = modelData.type;
                if (t.indexOf("t") >= 0)
                    return 1.0;  // top edge → anchor bottom
                if (t.indexOf("b") >= 0)
                    return 0.0;  // bottom edge → anchor top
                return 0.5;  // center (edge handles)
            }

            DragHandler {
                id: dragHandler
                target: null

                onActiveChanged: {
                    selectionOverlay.isResizing = active;
                    if (active) {
                        handle.startBounds = {
                            x: selectionOverlay._geomX,
                            y: selectionOverlay._geomY,
                            width: selectionOverlay._geomWidth,
                            height: selectionOverlay._geomHeight
                        };
                        handle.startTransform = {
                            scaleX: selectionOverlay._scaleX,
                            scaleY: selectionOverlay._scaleY,
                            rotate: selectionOverlay._rotation
                        };
                        handle.startCursorX = selectionOverlay.cursorX;
                        handle.startCursorY = selectionOverlay.cursorY;
                    }
                }

                onTranslationChanged: {
                    if (!active || !handle.startBounds || !handle.startTransform)
                        return;

                    // Get cursor delta in canvas coordinates
                    var dx = selectionOverlay.cursorX - handle.startCursorX;
                    var dy = selectionOverlay.cursorY - handle.startCursorY;

                    // Transform delta to local (unrotated) space
                    var angleRad = -handle.startTransform.rotate * Math.PI / 180;
                    var localDx = dx * Math.cos(angleRad) - dy * Math.sin(angleRad);
                    var localDy = dx * Math.sin(angleRad) + dy * Math.cos(angleRad);

                    var t = handle.modelData.type;
                    var b = handle.startBounds;
                    var st = handle.startTransform;

                    // Calculate displayed size (geometry × scale)
                    var displayedWidth = b.width * st.scaleX;
                    var displayedHeight = b.height * st.scaleY;

                    var newScaleX = st.scaleX;
                    var newScaleY = st.scaleY;

                    // Horizontal scaling
                    if (t.indexOf("l") >= 0) {
                        // Left edge: negative delta grows
                        var newDisplayedWidth = Math.max(1, displayedWidth - localDx);
                        newScaleX = b.width > 0 ? newDisplayedWidth / b.width : st.scaleX;
                    } else if (t.indexOf("r") >= 0) {
                        // Right edge: positive delta grows
                        var newDisplayedWidth = Math.max(1, displayedWidth + localDx);
                        newScaleX = b.width > 0 ? newDisplayedWidth / b.width : st.scaleX;
                    }

                    // Vertical scaling
                    if (t.indexOf("t") >= 0) {
                        // Top edge: negative delta grows
                        var newDisplayedHeight = Math.max(1, displayedHeight - localDy);
                        newScaleY = b.height > 0 ? newDisplayedHeight / b.height : st.scaleY;
                    } else if (t.indexOf("b") >= 0) {
                        // Bottom edge: positive delta grows
                        var newDisplayedHeight = Math.max(1, displayedHeight + localDy);
                        newScaleY = b.height > 0 ? newDisplayedHeight / b.height : st.scaleY;
                    }

                    // Proportional scaling with Shift for corner handles
                    if (selectionOverlay.shiftPressed && (t === "tl" || t === "tr" || t === "bl" || t === "br")) {
                        // Use the larger scale change for proportional scaling
                        var scaleRatioX = newScaleX / st.scaleX;
                        var scaleRatioY = newScaleY / st.scaleY;
                        var avgRatio = (Math.abs(scaleRatioX - 1) > Math.abs(scaleRatioY - 1)) ? scaleRatioX : scaleRatioY;
                        newScaleX = st.scaleX * avgRatio;
                        newScaleY = st.scaleY * avgRatio;
                    }

                    // Artboards resize via absolute bounds (no transform system)
                    var selectedItem = Lucent.SelectionManager.selectedItem;
                    if (selectedItem && selectedItem.type === "artboard") {
                        var newWidth = b.width * newScaleX;
                        var newHeight = b.height * newScaleY;
                        var newX = b.x + b.width * handle.anchorX - newWidth * handle.anchorX;
                        var newY = b.y + b.height * handle.anchorY - newHeight * handle.anchorY;
                        selectionOverlay.resizeRequested({
                            x: newX,
                            y: newY,
                            width: newWidth,
                            height: newHeight
                        });
                        return;
                    }

                    selectionOverlay.scaleResizeRequested(newScaleX, newScaleY, handle.anchorX, handle.anchorY);
                }
            }
        }
    }
}
