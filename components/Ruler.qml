// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import "." as Lucent

// Lightweight ruler overlay; non-interactive and updated on zoom/pan/unit changes.
Item {
    id: root
    property string orientation: "horizontal"  // "horizontal" | "vertical"
    property real zoomLevel: 1.0
    property real offsetX: 0
    property real offsetY: 0
    property real viewportWidth: width
    property real viewportHeight: height
    property var unitSettings: null
    property color tickColor: Lucent.Themed.palette.text
    property color textColor: Lucent.Themed.palette.text
    property color axisColor: Lucent.Themed.selector
    property color backgroundColor: Lucent.Themed.palette.mid
    property real devicePixelRatio: Screen.devicePixelRatio
    property real cursorViewportX: NaN
    property real cursorViewportY: NaN
    property real baseGridSize: 32.0
    property real majorMultiplier: 5.0

    // Internal
    property real _targetPx: 60  // desired spacing in px
    property var _ticks: []      // {posPx, label, isMajor}

    implicitHeight: orientation === "horizontal" ? 22 : parent ? parent.height : 100
    implicitWidth: orientation === "vertical" ? 22 : parent ? parent.width : 100
    clip: true
    z: 1001

    // Recompute ticks whenever view changes
    onZoomLevelChanged: requestRepaint()
    onOffsetXChanged: requestRepaint()
    onOffsetYChanged: requestRepaint()
    onViewportWidthChanged: requestRepaint()
    onViewportHeightChanged: requestRepaint()
    onUnitSettingsChanged: requestRepaint()
    onCursorViewportXChanged: requestRepaint()
    onCursorViewportYChanged: requestRepaint()

    function requestRepaint() {
        canvas.requestPaint();
    }

    function baseGridSizeVal() {
        if (unitSettings && unitSettings.gridSpacingCanvas)
            return unitSettings.gridSpacingCanvas;
        return baseGridSize;
    }

    function canvasToDisplay(val) {
        if (unitSettings && unitSettings.canvasToDisplay)
            return unitSettings.canvasToDisplay(val);
        return val;
    }

    function displayUnit() {
        if (unitSettings && unitSettings.displayUnit)
            return unitSettings.displayUnit;
        return "px";
    }

    function majorStepCanvas() {
        return baseGridSizeVal() * majorMultiplier;
    }

    // Snap step to a multiple of the major grid to hit ~target px spacing
    function computeStep() {
        var zoom = zoomLevel;
        var stepBase = majorStepCanvas();
        if (!isFinite(zoom) || zoom <= 0 || stepBase <= 0)
            return stepBase;
        var stepPx = stepBase * zoom;
        var mult = Math.max(1, Math.ceil(_targetPx / stepPx));
        return stepBase * mult;
    }

    function fmtLabel(v) {
        var dv = canvasToDisplay(v);
        // integer, strip unit per request
        return Math.round(dv).toString();
    }

    function generateTicks() {
        var ticks = [];
        var zoom = zoomLevel;
        if (!isFinite(zoom) || zoom <= 0)
            return ticks;

        // visible span in canvas coords
        var centerX = viewportWidth * 0.5;
        var centerY = viewportHeight * 0.5;
        var startCanvas, endCanvas, axisOffset, axisSize, offset;

        if (orientation === "horizontal") {
            startCanvas = (-centerX - offsetX) / zoom;
            endCanvas = (centerX - offsetX) / zoom;
            axisOffset = -offsetX;
            axisSize = viewportWidth;
            offset = offsetX;
        } else {
            startCanvas = (-centerY - offsetY) / zoom;
            endCanvas = (centerY - offsetY) / zoom;
            axisOffset = -offsetY;
            axisSize = viewportHeight;
            offset = offsetY;
        }

        var stepCanvas = computeStep();

        // snap to step
        var first = Math.floor(startCanvas / stepCanvas) * stepCanvas;

        for (var v = first; v <= endCanvas; v += stepCanvas) {
            var posPx;
            if (orientation === "horizontal") {
                posPx = (v * zoom) + centerX + offsetX;
                if (posPx < 0 || posPx > viewportWidth)
                    continue;
                ticks.push({
                    posPx: posPx,
                    label: fmtLabel(v),
                    isMajor: true
                });
            } else {
                posPx = (v * zoom) + centerY + offsetY;
                if (posPx < 0 || posPx > viewportHeight)
                    continue;
                ticks.push({
                    posPx: posPx,
                    label: fmtLabel(-v) // flip y for label sense
                    ,
                    isMajor: true
                });
            }
        }
        return ticks;
    }

    Canvas {
        id: canvas
        anchors.fill: parent
        renderTarget: Canvas.FramebufferObject
        antialiasing: false
        onPaint: {
            var ctx = getContext("2d");
            ctx.resetTransform();
            ctx.clearRect(0, 0, width, height);

            // background
            ctx.fillStyle = backgroundColor;
            ctx.fillRect(0, 0, width, height);

            var ticks = generateTicks();
            if (!ticks.length)
                return;

            ctx.save();
            ctx.strokeStyle = tickColor;
            ctx.fillStyle = textColor;
            ctx.lineWidth = 1;
            ctx.font = "10px monospace";
            ctx.textBaseline = "top";

            // Axis line at canvas origin (neutral color)
            ctx.beginPath();
            ctx.strokeStyle = tickColor;
            if (orientation === "horizontal") {
                var originX = width * 0.5 + offsetX;
                ctx.moveTo(originX + 0.5, 0);
                ctx.lineTo(originX + 0.5, height);
            } else {
                var originY = height * 0.5 + offsetY;
                ctx.moveTo(0, originY + 0.5);
                ctx.lineTo(width, originY + 0.5);
            }
            ctx.stroke();

            // Cursor marker (full length, light)
            var cx = cursorViewportX;
            var cy = cursorViewportY;
            ctx.strokeStyle = axisColor;
            if (orientation === "horizontal" && isFinite(cx)) {
                ctx.beginPath();
                ctx.moveTo(cx + 0.5, 0);
                ctx.lineTo(cx + 0.5, height);
                ctx.stroke();
            } else if (orientation === "vertical" && isFinite(cy)) {
                ctx.beginPath();
                ctx.moveTo(0, cy + 0.5);
                ctx.lineTo(width, cy + 0.5);
                ctx.stroke();
            }

            ctx.strokeStyle = tickColor;
            ticks.forEach(function (t) {
                ctx.beginPath();
                if (orientation === "horizontal") {
                    ctx.moveTo(t.posPx + 0.5, height - 4);
                    ctx.lineTo(t.posPx + 0.5, height);
                } else {
                    ctx.moveTo(width - 4, t.posPx + 0.5);
                    ctx.lineTo(width, t.posPx + 0.5);
                }
                ctx.stroke();
            });

            ctx.restore();
        }
    }

    // Label layer (Text for crisper rendering)
    Repeater {
        model: generateTicks()
        delegate: Text {
            property var t: modelData
            text: t.label
            color: textColor
            font.pixelSize: 10
            font.family: "monospace"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            x: orientation === "horizontal" ? (t.posPx - implicitWidth * 0.5) : 4
            y: orientation === "horizontal" ? 2 : (t.posPx - implicitHeight * 0.5)
            rotation: orientation === "horizontal" ? 0 : -90
            transformOrigin: Item.Center
        }
    }
}
