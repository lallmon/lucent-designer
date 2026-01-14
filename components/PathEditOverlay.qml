// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Shapes
import "." as Lucent

Item {
    id: overlay

    property var pathGeometry: null
    property var itemTransform: null
    property real zoomLevel: 1.0
    property var selectedPointIndices: []
    property color accentColor: Lucent.Themed.editSelector

    property real cursorX: 0
    property real cursorY: 0
    property int currentModifiers: 0

    signal pointClicked(int index, int modifiers)
    signal pointMoved(int index, real x, real y)
    signal handleMoved(int index, string handleType, real x, real y, int modifiers)
    signal backgroundClicked
    signal dragStarted
    signal dragEnded

    readonly property var points: pathGeometry ? pathGeometry.points : []
    readonly property bool isClosed: pathGeometry ? pathGeometry.closed : false

    readonly property real _translateX: itemTransform ? (itemTransform.translateX || 0) : 0
    readonly property real _translateY: itemTransform ? (itemTransform.translateY || 0) : 0
    readonly property real _scaleX: itemTransform ? (itemTransform.scaleX || 1) : 1
    readonly property real _scaleY: itemTransform ? (itemTransform.scaleY || 1) : 1
    readonly property real _rotation: itemTransform ? (itemTransform.rotate || 0) : 0

    readonly property real handleSize: 10 / zoomLevel
    readonly property real handleLineWidth: 1 / zoomLevel

    visible: pathGeometry !== null

    function isPointSelected(index) {
        return selectedPointIndices.indexOf(index) >= 0;
    }

    function transformPoint(px, py) {
        var x = px * _scaleX + _translateX;
        var y = py * _scaleY + _translateY;
        return {
            x: x,
            y: y
        };
    }

    function inverseTransformPoint(x, y) {
        var px = (x - _translateX) / _scaleX;
        var py = (y - _translateY) / _scaleY;
        return {
            x: px,
            y: py
        };
    }

    Shape {
        id: pathShape
        anchors.fill: parent

        ShapePath {
            id: curvePath
            strokeColor: overlay.accentColor
            strokeWidth: overlay.handleLineWidth
            fillColor: "transparent"

            PathSvg {
                path: overlay._buildSvgPath()
            }
        }
    }

    function _buildSvgPath() {
        if (!points || points.length === 0)
            return "";

        var svg = "";
        var first = transformPoint(points[0].x, points[0].y);
        svg += "M " + first.x + " " + first.y + " ";

        for (var i = 1; i < points.length; i++) {
            var prev = points[i - 1];
            var curr = points[i];

            var hasHandles = prev.handleOut || curr.handleIn;
            var currT = transformPoint(curr.x, curr.y);

            if (hasHandles) {
                var cp1 = prev.handleOut ? transformPoint(prev.handleOut.x, prev.handleOut.y) : transformPoint(prev.x, prev.y);
                var cp2 = curr.handleIn ? transformPoint(curr.handleIn.x, curr.handleIn.y) : currT;
                svg += "C " + cp1.x + " " + cp1.y + " " + cp2.x + " " + cp2.y + " " + currT.x + " " + currT.y + " ";
            } else {
                svg += "L " + currT.x + " " + currT.y + " ";
            }
        }

        if (isClosed && points.length >= 2) {
            var last = points[points.length - 1];
            var firstPt = points[0];
            var hasClosingHandles = last.handleOut || firstPt.handleIn;
            var firstT = transformPoint(firstPt.x, firstPt.y);

            if (hasClosingHandles) {
                var cp1Close = last.handleOut ? transformPoint(last.handleOut.x, last.handleOut.y) : transformPoint(last.x, last.y);
                var cp2Close = firstPt.handleIn ? transformPoint(firstPt.handleIn.x, firstPt.handleIn.y) : firstT;
                svg += "C " + cp1Close.x + " " + cp1Close.y + " " + cp2Close.x + " " + cp2Close.y + " " + firstT.x + " " + firstT.y + " ";
            }
            svg += "Z";
        }

        return svg;
    }

    Repeater {
        id: handleRepeater
        model: overlay.points.length

        Item {
            id: pointItem
            required property int index

            readonly property var pointData: overlay.points[index] || {}
            readonly property bool isSelected: overlay.isPointSelected(index)
            readonly property var anchorPos: overlay.transformPoint(pointData.x || 0, pointData.y || 0)
            readonly property bool hasHandleIn: pointData.handleIn !== undefined && pointData.handleIn !== null
            readonly property bool hasHandleOut: pointData.handleOut !== undefined && pointData.handleOut !== null

            Shape {
                visible: pointItem.isSelected && (pointItem.hasHandleIn || pointItem.hasHandleOut)

                ShapePath {
                    strokeColor: overlay.accentColor
                    strokeWidth: overlay.handleLineWidth
                    fillColor: "transparent"

                    startX: pointItem.hasHandleIn ? overlay.transformPoint(pointItem.pointData.handleIn.x, pointItem.pointData.handleIn.y).x : pointItem.anchorPos.x
                    startY: pointItem.hasHandleIn ? overlay.transformPoint(pointItem.pointData.handleIn.x, pointItem.pointData.handleIn.y).y : pointItem.anchorPos.y

                    PathLine {
                        x: pointItem.anchorPos.x
                        y: pointItem.anchorPos.y
                    }
                    PathLine {
                        x: pointItem.hasHandleOut ? overlay.transformPoint(pointItem.pointData.handleOut.x, pointItem.pointData.handleOut.y).x : pointItem.anchorPos.x
                        y: pointItem.hasHandleOut ? overlay.transformPoint(pointItem.pointData.handleOut.x, pointItem.pointData.handleOut.y).y : pointItem.anchorPos.y
                    }
                }
            }

            Rectangle {
                id: handleIn
                visible: pointItem.isSelected && pointItem.hasHandleIn

                property var handlePos: pointItem.hasHandleIn ? overlay.transformPoint(pointItem.pointData.handleIn.x, pointItem.pointData.handleIn.y) : {
                    x: 0,
                    y: 0
                }

                x: handlePos.x - overlay.handleSize / 2
                y: handlePos.y - overlay.handleSize / 2
                width: overlay.handleSize
                height: overlay.handleSize
                radius: overlay.handleSize / 2
                color: overlay.accentColor
                border.width: 0

                property real startX: 0
                property real startY: 0
                property real startHandleX: 0
                property real startHandleY: 0

                DragHandler {
                    target: null
                    onActiveChanged: {
                        if (active) {
                            handleIn.startX = overlay.cursorX;
                            handleIn.startY = overlay.cursorY;
                            handleIn.startHandleX = pointItem.pointData.handleIn.x;
                            handleIn.startHandleY = pointItem.pointData.handleIn.y;
                            overlay.dragStarted();
                        } else {
                            overlay.dragEnded();
                        }
                    }
                    onTranslationChanged: {
                        if (!active)
                            return;
                        var dx = (overlay.cursorX - handleIn.startX) / overlay._scaleX;
                        var dy = (overlay.cursorY - handleIn.startY) / overlay._scaleY;
                        var newX = handleIn.startHandleX + dx;
                        var newY = handleIn.startHandleY + dy;
                        overlay.handleMoved(pointItem.index, "handleIn", newX, newY, overlay.currentModifiers);
                    }
                }
            }

            Rectangle {
                id: handleOut
                visible: pointItem.isSelected && pointItem.hasHandleOut

                property var handlePos: pointItem.hasHandleOut ? overlay.transformPoint(pointItem.pointData.handleOut.x, pointItem.pointData.handleOut.y) : {
                    x: 0,
                    y: 0
                }

                x: handlePos.x - overlay.handleSize / 2
                y: handlePos.y - overlay.handleSize / 2
                width: overlay.handleSize
                height: overlay.handleSize
                radius: overlay.handleSize / 2
                color: overlay.accentColor
                border.width: 0

                property real startX: 0
                property real startY: 0
                property real startHandleX: 0
                property real startHandleY: 0

                DragHandler {
                    target: null
                    onActiveChanged: {
                        if (active) {
                            handleOut.startX = overlay.cursorX;
                            handleOut.startY = overlay.cursorY;
                            handleOut.startHandleX = pointItem.pointData.handleOut.x;
                            handleOut.startHandleY = pointItem.pointData.handleOut.y;
                            overlay.dragStarted();
                        } else {
                            overlay.dragEnded();
                        }
                    }
                    onTranslationChanged: {
                        if (!active)
                            return;
                        var dx = (overlay.cursorX - handleOut.startX) / overlay._scaleX;
                        var dy = (overlay.cursorY - handleOut.startY) / overlay._scaleY;
                        var newX = handleOut.startHandleX + dx;
                        var newY = handleOut.startHandleY + dy;
                        overlay.handleMoved(pointItem.index, "handleOut", newX, newY, overlay.currentModifiers);
                    }
                }
            }

            Rectangle {
                id: anchorPoint
                x: pointItem.anchorPos.x - overlay.handleSize / 2
                y: pointItem.anchorPos.y - overlay.handleSize / 2
                width: overlay.handleSize
                height: overlay.handleSize
                color: pointItem.isSelected ? overlay.accentColor : "transparent"
                border.color: overlay.accentColor
                border.width: overlay.handleLineWidth

                property real startX: 0
                property real startY: 0
                property real startPointX: 0
                property real startPointY: 0

                MouseArea {
                    anchors.fill: parent
                    onPressed: mouse => {
                        Lucent.SelectionManager._skipNextClick = true;
                        mouse.accepted = true;
                    }
                    onClicked: overlay.pointClicked(pointItem.index, overlay.currentModifiers)
                }

                DragHandler {
                    id: anchorDragHandler
                    target: null
                    onActiveChanged: {
                        if (active) {
                            anchorPoint.startX = overlay.cursorX;
                            anchorPoint.startY = overlay.cursorY;
                            anchorPoint.startPointX = pointItem.pointData.x;
                            anchorPoint.startPointY = pointItem.pointData.y;
                            overlay.dragStarted();
                        } else {
                            overlay.dragEnded();
                        }
                    }
                    onTranslationChanged: {
                        if (!active)
                            return;
                        var dx = (overlay.cursorX - anchorPoint.startX) / overlay._scaleX;
                        var dy = (overlay.cursorY - anchorPoint.startY) / overlay._scaleY;
                        var newX = anchorPoint.startPointX + dx;
                        var newY = anchorPoint.startPointY + dy;
                        overlay.pointMoved(pointItem.index, newX, newY);
                    }
                }
            }
        }
    }
}
