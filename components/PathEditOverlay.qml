// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Shapes
import "." as Lucent

Item {
    id: overlay

    property var pathGeometry: null
    property var transformedPoints: null
    property real zoomLevel: 1.0
    property var selectedPointIndices: []
    property color accentColor: Lucent.Themed.editSelector

    property real cursorX: 0
    property real cursorY: 0
    property int currentModifiers: 0

    signal pointClicked(int index, int modifiers)
    signal pointMoved(int index, real screenX, real screenY)
    signal handleMoved(int index, string handleType, real screenX, real screenY, int modifiers)
    signal backgroundClicked
    signal dragStarted
    signal dragEnded

    readonly property var points: transformedPoints || []
    readonly property bool isClosed: pathGeometry ? pathGeometry.closed : false

    readonly property real handleSize: 10 / zoomLevel
    readonly property real handleLineWidth: 1 / zoomLevel

    visible: points.length > 0

    function isPointSelected(index) {
        return selectedPointIndices.indexOf(index) >= 0;
    }

    Shape {
        id: pathShape

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

    Repeater {
        id: handleRepeater
        model: overlay.points.length

        Item {
            id: pointItem
            required property int index

            readonly property var pointData: overlay.points[index] || {}
            readonly property bool isSelected: overlay.isPointSelected(index)
            readonly property bool hasHandleIn: pointData.handleIn !== undefined && pointData.handleIn !== null
            readonly property bool hasHandleOut: pointData.handleOut !== undefined && pointData.handleOut !== null

            Shape {
                visible: pointItem.hasHandleIn || pointItem.hasHandleOut

                ShapePath {
                    strokeColor: overlay.accentColor
                    strokeWidth: overlay.handleLineWidth
                    fillColor: "transparent"

                    startX: pointItem.hasHandleIn ? pointItem.pointData.handleIn.x : pointItem.pointData.x
                    startY: pointItem.hasHandleIn ? pointItem.pointData.handleIn.y : pointItem.pointData.y

                    PathLine {
                        x: pointItem.pointData.x
                        y: pointItem.pointData.y
                    }
                    PathLine {
                        x: pointItem.hasHandleOut ? pointItem.pointData.handleOut.x : pointItem.pointData.x
                        y: pointItem.hasHandleOut ? pointItem.pointData.handleOut.y : pointItem.pointData.y
                    }
                }
            }

            Rectangle {
                id: handleIn
                visible: pointItem.hasHandleIn

                x: pointItem.pointData.handleIn ? pointItem.pointData.handleIn.x - overlay.handleSize / 2 : 0
                y: pointItem.pointData.handleIn ? pointItem.pointData.handleIn.y - overlay.handleSize / 2 : 0
                width: overlay.handleSize
                height: overlay.handleSize
                radius: width / 2
                color: overlay.accentColor
                border.width: 0

                DragHandler {
                    target: null
                    onActiveChanged: {
                        if (active) {
                            overlay.dragStarted();
                        } else {
                            overlay.dragEnded();
                        }
                    }
                    onTranslationChanged: {
                        if (!active)
                            return;
                        overlay.handleMoved(pointItem.index, "handleIn", overlay.cursorX, overlay.cursorY, overlay.currentModifiers);
                    }
                }
            }

            Rectangle {
                id: handleOut
                visible: pointItem.hasHandleOut

                x: pointItem.pointData.handleOut ? pointItem.pointData.handleOut.x - overlay.handleSize / 2 : 0
                y: pointItem.pointData.handleOut ? pointItem.pointData.handleOut.y - overlay.handleSize / 2 : 0
                width: overlay.handleSize
                height: overlay.handleSize
                radius: width / 2
                color: overlay.accentColor
                border.width: 0

                DragHandler {
                    target: null
                    onActiveChanged: {
                        if (active) {
                            overlay.dragStarted();
                        } else {
                            overlay.dragEnded();
                        }
                    }
                    onTranslationChanged: {
                        if (!active)
                            return;
                        overlay.handleMoved(pointItem.index, "handleOut", overlay.cursorX, overlay.cursorY, overlay.currentModifiers);
                    }
                }
            }

            Rectangle {
                id: anchorPoint
                x: pointItem.pointData.x - overlay.handleSize / 2
                y: pointItem.pointData.y - overlay.handleSize / 2
                width: overlay.handleSize
                height: overlay.handleSize
                color: pointItem.isSelected ? overlay.accentColor : "transparent"
                border.color: overlay.accentColor
                border.width: overlay.handleLineWidth

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
                            overlay.dragStarted();
                        } else {
                            overlay.dragEnded();
                        }
                    }
                    onTranslationChanged: {
                        if (!active)
                            return;
                        overlay.pointMoved(pointItem.index, overlay.cursorX, overlay.cursorY);
                    }
                }
            }
        }
    }

    function _buildSvgPath() {
        if (!points || points.length === 0)
            return "";

        var svg = "";
        svg += "M " + points[0].x + " " + points[0].y + " ";

        for (var i = 1; i < points.length; i++) {
            var prev = points[i - 1];
            var curr = points[i];

            var hasHandles = prev.handleOut || curr.handleIn;

            if (hasHandles) {
                var cp1x = prev.handleOut ? prev.handleOut.x : prev.x;
                var cp1y = prev.handleOut ? prev.handleOut.y : prev.y;
                var cp2x = curr.handleIn ? curr.handleIn.x : curr.x;
                var cp2y = curr.handleIn ? curr.handleIn.y : curr.y;
                svg += "C " + cp1x + " " + cp1y + " " + cp2x + " " + cp2y + " " + curr.x + " " + curr.y + " ";
            } else {
                svg += "L " + curr.x + " " + curr.y + " ";
            }
        }

        if (isClosed && points.length >= 2) {
            var last = points[points.length - 1];
            var firstPt = points[0];
            var hasClosingHandles = last.handleOut || firstPt.handleIn;

            if (hasClosingHandles) {
                var cp1CloseX = last.handleOut ? last.handleOut.x : last.x;
                var cp1CloseY = last.handleOut ? last.handleOut.y : last.y;
                var cp2CloseX = firstPt.handleIn ? firstPt.handleIn.x : firstPt.x;
                var cp2CloseY = firstPt.handleIn ? firstPt.handleIn.y : firstPt.y;
                svg += "C " + cp1CloseX + " " + cp1CloseY + " " + cp2CloseX + " " + cp2CloseY + " " + firstPt.x + " " + firstPt.y + " ";
            }
            svg += "Z";
        }

        return svg;
    }
}
