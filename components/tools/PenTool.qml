// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import ".." as Lucent

// Bezier pen tool - click to place corners, drag to create smooth curves
Item {
    id: tool

    property real zoomLevel: 1.0
    property bool active: false
    property var settings: null
    property real viewportWidth: 0
    property real viewportHeight: 0
    readonly property real previewPad: 256

    // Preview callbacks from ToolLoader
    property var setPreviewCallback: null
    property var clearPreviewCallback: null

    property var points: []
    property var pendingAnchor: null
    property var pendingHandle: null
    property var previewPoint: null
    property bool isDragging: false
    property bool isClosed: false

    readonly property real dragThreshold: 6 / Math.max(zoomLevel, 0.0001)
    readonly property real closeThreshold: 10 / Math.max(zoomLevel, 0.0001)

    signal itemCompleted(var itemData)

    onPointsChanged: updatePreview()
    onPendingAnchorChanged: updatePreview()
    onPendingHandleChanged: updatePreview()
    onPreviewPointChanged: updatePreview()
    onIsClosedChanged: updatePreview()

    function updatePreview() {
        if (points.length === 0 && !pendingAnchor) {
            if (clearPreviewCallback)
                clearPreviewCallback();
            return;
        }
        if (!setPreviewCallback)
            return;

        var previewPoints = points.slice();

        if (!isClosed && pendingAnchor) {
            var newPoint = {
                x: pendingAnchor.x,
                y: pendingAnchor.y
            };
            if (pendingHandle) {
                var dx = pendingHandle.x - pendingAnchor.x;
                var dy = pendingHandle.y - pendingAnchor.y;
                newPoint.handleOut = {
                    x: pendingHandle.x,
                    y: pendingHandle.y
                };
                if (previewPoints.length > 0) {
                    newPoint.handleIn = {
                        x: pendingAnchor.x - dx,
                        y: pendingAnchor.y - dy
                    };
                }
            }
            previewPoints.push(newPoint);
        } else if (!isClosed && previewPoint && points.length > 0) {
            previewPoints.push({
                x: previewPoint.x,
                y: previewPoint.y
            });
        }

        if (previewPoints.length < 1) {
            if (clearPreviewCallback)
                clearPreviewCallback();
            return;
        }

        var s = settings || {};
        var strokeWidth = s.strokeWidth !== undefined ? s.strokeWidth : 1;
        var strokeColor = _colorString(s.strokeColor);
        var strokeOpacity = s.strokeOpacity !== undefined ? s.strokeOpacity : 1.0;
        var strokeVisible = s.strokeVisible !== undefined ? s.strokeVisible : false;
        var strokeCap = s.strokeCap !== undefined ? s.strokeCap : "butt";
        var strokeAlign = s.strokeAlign !== undefined ? s.strokeAlign : "center";
        var strokeOrder = s.strokeOrder !== undefined ? s.strokeOrder : "top";
        var strokeScaleWithObject = s.strokeScaleWithObject === true;
        var fillColor = _colorString(s.fillColor);
        var fillOpacity = s.fillOpacity !== undefined ? s.fillOpacity : 1.0;

        setPreviewCallback({
            type: "path",
            geometry: {
                points: previewPoints,
                closed: isClosed
            },
            appearances: [
                {
                    type: "fill",
                    color: fillColor,
                    opacity: fillOpacity,
                    visible: true
                },
                {
                    type: "stroke",
                    color: strokeColor,
                    width: strokeWidth,
                    opacity: strokeOpacity,
                    visible: strokeVisible,
                    cap: strokeCap,
                    align: strokeAlign,
                    order: strokeOrder,
                    scaleWithObject: strokeScaleWithObject
                }
            ]
        });
    }

    // Handle lines and grips rendered as QML overlay
    Canvas {
        id: handlesCanvas
        width: Math.max(0, tool.viewportWidth + tool.previewPad * 2)
        height: Math.max(0, tool.viewportHeight + tool.previewPad * 2)
        x: -width / 2
        y: -height / 2
        antialiasing: true
        renderTarget: Canvas.FramebufferObject

        onPaint: {
            var ctx = getContext("2d");
            ctx.resetTransform();
            ctx.clearRect(0, 0, width, height);

            var originX = width / 2;
            var originY = height / 2;
            var handleLineColor = Lucent.Themed.selector.toString();
            var handleGripColor = Lucent.Themed.selector.toString();

            ctx.save();
            ctx.lineWidth = 1;
            ctx.strokeStyle = handleLineColor;
            ctx.fillStyle = handleGripColor;

            for (var j = 0; j < tool.points.length; j++) {
                var p = tool.points[j];
                tool._drawHandles(ctx, originX, originY, p);
            }

            if (tool.isDragging && tool.pendingAnchor && tool.pendingHandle) {
                var ax = originX + tool.pendingAnchor.x;
                var ay = originY + tool.pendingAnchor.y;
                var hx = originX + tool.pendingHandle.x;
                var hy = originY + tool.pendingHandle.y;

                ctx.beginPath();
                ctx.moveTo(ax, ay);
                ctx.lineTo(hx, hy);
                ctx.stroke();

                var mx = ax - (hx - ax);
                var my = ay - (hy - ay);
                ctx.beginPath();
                ctx.moveTo(ax, ay);
                ctx.lineTo(mx, my);
                ctx.stroke();

                var gripSize = 10 / Math.max(tool.zoomLevel, 0.0001);
                ctx.beginPath();
                ctx.arc(hx, hy, gripSize / 2, 0, Math.PI * 2);
                ctx.fill();
                ctx.beginPath();
                ctx.arc(mx, my, gripSize / 2, 0, Math.PI * 2);
                ctx.fill();
            }
            ctx.restore();
        }
    }

    Repeater {
        model: tool.points.length
        delegate: Rectangle {
            property var point: tool.points[index]
            width: 10 / Math.max(tool.zoomLevel, 0.0001)
            height: width
            radius: width / 2
            x: point.x - width / 2
            y: point.y - height / 2
            color: Lucent.Themed.palette.mid
            border.color: Lucent.Themed.palette.text
            border.width: 1 / Math.max(tool.zoomLevel, 0.0001)
        }
    }

    Rectangle {
        visible: tool.isDragging && tool.pendingAnchor !== null
        width: 10 / Math.max(tool.zoomLevel, 0.0001)
        height: width
        radius: width / 2
        x: tool.pendingAnchor ? tool.pendingAnchor.x - width / 2 : 0
        y: tool.pendingAnchor ? tool.pendingAnchor.y - height / 2 : 0
        color: Lucent.Themed.palette.mid
        border.color: Lucent.Themed.palette.text
        border.width: 1 / Math.max(tool.zoomLevel, 0.0001)
    }

    function handleMousePress(canvasX, canvasY, button, modifiers) {
        if (!tool.active || button !== Qt.LeftButton)
            return;

        if (tool.isClosed)
            return;

        if (tool.points.length >= 2 && tool._isNearFirst(canvasX, canvasY)) {
            tool.isClosed = true;

            // Add symmetric handleIn to first point for proper closing curve
            var first = tool.points[0];
            if (first.handleOut && !first.handleIn) {
                var dx = first.handleOut.x - first.x;
                var dy = first.handleOut.y - first.y;
                var nextPoints = tool.points.slice();
                nextPoints[0] = Object.assign({}, first, {
                    handleIn: {
                        x: first.x - dx,
                        y: first.y - dy
                    }
                });
                tool.points = nextPoints;
            }

            tool._finalize();
            return;
        }

        tool.isDragging = true;
        tool.pendingAnchor = {
            x: canvasX,
            y: canvasY
        };
        tool.pendingHandle = null;
        tool.previewPoint = null;
        handlesCanvas.requestPaint();
    }

    function handleMouseMove(canvasX, canvasY, modifiers) {
        if (!tool.active || tool.isClosed)
            return;

        if (tool.isDragging && tool.pendingAnchor) {
            tool.pendingHandle = {
                x: canvasX,
                y: canvasY
            };
        } else if (tool.points.length > 0) {
            tool.previewPoint = {
                x: canvasX,
                y: canvasY
            };
        }
        handlesCanvas.requestPaint();
    }

    function handleMouseRelease(canvasX, canvasY) {
        if (!tool.isDragging || !tool.pendingAnchor)
            return;

        var anchor = tool.pendingAnchor;
        var dx = canvasX - anchor.x;
        var dy = canvasY - anchor.y;
        var dist = Math.sqrt(dx * dx + dy * dy);

        var newPoint;
        var isFirstPoint = tool.points.length === 0;

        if (dist < tool.dragThreshold) {
            newPoint = {
                x: anchor.x,
                y: anchor.y
            };
        } else {
            newPoint = {
                x: anchor.x,
                y: anchor.y,
                handleOut: {
                    x: canvasX,
                    y: canvasY
                }
            };

            if (!isFirstPoint) {
                newPoint.handleIn = {
                    x: anchor.x - dx,
                    y: anchor.y - dy
                };
            }
        }

        var nextPoints = tool.points.slice();
        nextPoints.push(newPoint);
        tool.points = nextPoints;

        tool.isDragging = false;
        tool.pendingAnchor = null;
        tool.pendingHandle = null;
        handlesCanvas.requestPaint();
    }

    // Double-click finishes open path
    function handleDoubleClick(canvasX, canvasY) {
        if (!tool.active)
            return;

        if (tool.points.length >= 2) {
            tool._finalize();
        }
    }

    function undoLastAction() {
        if (tool.isDragging) {
            tool.isDragging = false;
            tool.pendingAnchor = null;
            tool.pendingHandle = null;
            tool.previewPoint = null;
            handlesCanvas.requestPaint();
            return true;
        }

        if (tool.points.length > 0) {
            if (tool.points.length === 1) {
                reset();
            } else {
                var nextPoints = tool.points.slice(0, -1);
                tool.points = nextPoints;
                tool.previewPoint = null;
                handlesCanvas.requestPaint();
            }
            return true;
        }

        return false;
    }

    function reset() {
        tool.points = [];
        tool.pendingAnchor = null;
        tool.pendingHandle = null;
        tool.previewPoint = null;
        tool.isDragging = false;
        tool.isClosed = false;
        if (clearPreviewCallback)
            clearPreviewCallback();
        handlesCanvas.requestPaint();
    }

    function _finalize() {
        if (tool.points.length < 2) {
            reset();
            return;
        }

        var s = settings || {};
        var strokeWidth = s.strokeWidth !== undefined ? s.strokeWidth : 1;
        var strokeColor = tool._colorString(s.strokeColor);
        var strokeOpacity = s.strokeOpacity !== undefined ? s.strokeOpacity : 1.0;
        var strokeVisible = s.strokeVisible !== undefined ? s.strokeVisible : false;
        var strokeCap = s.strokeCap !== undefined ? s.strokeCap : "butt";
        var strokeAlign = s.strokeAlign !== undefined ? s.strokeAlign : "center";
        var strokeOrder = s.strokeOrder !== undefined ? s.strokeOrder : "top";
        var strokeScaleWithObject = s.strokeScaleWithObject === true;
        var fillColor = tool._colorString(s.fillColor);
        var fillOpacity = s.fillOpacity !== undefined ? s.fillOpacity : 1.0;

        if (clearPreviewCallback)
            clearPreviewCallback();
        itemCompleted({
            type: "path",
            geometry: {
                points: tool.points,
                closed: tool.isClosed
            },
            appearances: [
                {
                    type: "fill",
                    color: fillColor,
                    opacity: fillOpacity,
                    visible: true
                },
                {
                    type: "stroke",
                    color: strokeColor,
                    width: strokeWidth,
                    opacity: strokeOpacity,
                    visible: strokeVisible,
                    cap: strokeCap,
                    align: strokeAlign,
                    order: strokeOrder,
                    scaleWithObject: strokeScaleWithObject
                }
            ]
        });
        reset();
    }

    function _drawHandles(ctx, originX, originY, p) {
        var ax = originX + p.x;
        var ay = originY + p.y;
        var gripSize = 10 / Math.max(tool.zoomLevel, 0.0001);

        if (p.handleIn) {
            var hix = originX + p.handleIn.x;
            var hiy = originY + p.handleIn.y;
            ctx.beginPath();
            ctx.moveTo(ax, ay);
            ctx.lineTo(hix, hiy);
            ctx.stroke();
            ctx.beginPath();
            ctx.arc(hix, hiy, gripSize / 2, 0, Math.PI * 2);
            ctx.fill();
        }

        if (p.handleOut) {
            var hox = originX + p.handleOut.x;
            var hoy = originY + p.handleOut.y;
            ctx.beginPath();
            ctx.moveTo(ax, ay);
            ctx.lineTo(hox, hoy);
            ctx.stroke();
            ctx.beginPath();
            ctx.arc(hox, hoy, gripSize / 2, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    function _colorString(value) {
        if (value === null || value === undefined)
            return "";
        if (typeof value === "string")
            return value;
        if (value.toString)
            return value.toString();
        return "";
    }

    function _isNearFirst(x, y) {
        if (tool.points.length === 0)
            return false;
        var first = tool.points[0];
        return Math.abs(first.x - x) <= tool.closeThreshold && Math.abs(first.y - y) <= tool.closeThreshold;
    }
}
