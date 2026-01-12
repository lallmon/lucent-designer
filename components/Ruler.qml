// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import "." as Lucent

// Lightweight ruler overlay; non-interactive and updated on zoom/pan/unit changes.
Item {
    id: root
    property string orientation: "horizontal"  // "horizontal" | "vertical"
    property var viewState: null
    property color tickColor: Lucent.Themed.palette.text
    property color textColor: Lucent.Themed.palette.text
    property color axisColor: Lucent.Themed.selector
    property color backgroundColor: Lucent.Themed.palette.mid
    property real devicePixelRatio: Screen.devicePixelRatio
    property real cursorViewportX: NaN
    property real cursorViewportY: NaN
    property real baseGridSize: viewState.gridSpacing
    property real majorMultiplier: viewState.majorMultiplier

    // Internal
    property real _targetPx: viewState && typeof viewState.targetMajorPx !== "undefined" ? viewState.targetMajorPx : 60
    property var _ticks: []      // {posPx, label, isMajor}

    implicitHeight: orientation === "horizontal" ? 22 : parent ? parent.height : 100
    implicitWidth: orientation === "vertical" ? 22 : parent ? parent.width : 100
    clip: true
    z: 1001

    // Recompute ticks whenever view changes
    onViewStateChanged: updateAll()
    onWidthChanged: updateAll()
    onHeightChanged: updateAll()
    Component.onCompleted: updateAll()

    function updateAll() {
        _ticks = generateTicks();
        canvas.requestPaint();
    }

    function baseGridSizeVal() {
        if (viewState.unitSettings && viewState.unitSettings.gridSpacingCanvas)
            return viewState.unitSettings.gridSpacingCanvas;
        return baseGridSize;
    }

    function canvasToDisplay(val) {
        if (viewState.unitSettings && viewState.unitSettings.canvasToDisplay)
            return viewState.unitSettings.canvasToDisplay(val);
        return val;
    }

    function displayUnit() {
        if (viewState.unitSettings && viewState.unitSettings.displayUnit)
            return viewState.unitSettings.displayUnit;
        return "px";
    }

    function majorStepCanvas() {
        return baseGridSizeVal() * majorMultiplier;
    }

    // Snap step to a multiple of the major grid to hit ~target px spacing
    function unitStepToCanvas(uStep) {
        if (viewState.unitSettings && viewState.unitSettings.displayToCanvas) {
            return viewState.unitSettings.displayToCanvas(uStep);
        }
        return uStep * baseGridSizeVal();
    }

    function computeStep() {
        if (!viewState)
            return baseGridSizeVal();
        var zoom = viewState.zoom;
        var stepBase = majorStepCanvas();
        if (!isFinite(zoom) || zoom <= 0 || stepBase <= 0)
            return stepBase;

        var allowed = viewState.allowedMajorUnits;
        if (allowed && allowed.length) {
            var chosen = allowed[allowed.length - 1];
            for (var i = 0; i < allowed.length; i++) {
                var projPx = unitStepToCanvas(allowed[i]) * zoom;
                if (projPx >= _targetPx) {
                    chosen = allowed[i];
                    break;
                }
            }
            return unitStepToCanvas(chosen);
        }

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
        if (!viewState)
            return [];
        var ticks = [];
        var zoom = viewState.zoom;
        if (!isFinite(zoom) || zoom <= 0)
            return ticks;

        // visible span in canvas coords
        var centerX = viewState.viewportWidth * 0.5;
        var centerY = viewState.viewportHeight * 0.5;
        var startCanvas, endCanvas, axisOffset, axisSize, offset;

        if (orientation === "horizontal") {
            startCanvas = (-centerX - viewState.offsetX) / zoom;
            endCanvas = (centerX - viewState.offsetX) / zoom;
            offset = viewState.offsetX;
        } else {
            startCanvas = (-centerY - viewState.offsetY) / zoom;
            endCanvas = (centerY - viewState.offsetY) / zoom;
            offset = viewState.offsetY;
        }

        var stepCanvas = computeStep();

        // snap to step
        var first = Math.floor(startCanvas / stepCanvas) * stepCanvas;

        for (var v = first; v <= endCanvas; v += stepCanvas) {
            var posPx;
            if (orientation === "horizontal") {
                posPx = (v * zoom) + centerX + viewState.offsetX;
                if (posPx < 0 || posPx > viewState.viewportWidth)
                    continue;
                ticks.push({
                    posPx: posPx,
                    label: fmtLabel(v),
                    isMajor: true
                });
            } else {
                posPx = (v * zoom) + centerY + viewState.offsetY;
                if (posPx < 0 || posPx > viewState.viewportHeight)
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

            var ticks = _ticks;
            if (!ticks.length)
                return;

            ctx.save();
            ctx.strokeStyle = tickColor;
            ctx.fillStyle = textColor;
            ctx.lineWidth = 1;
            ctx.font = "10px monospace";
            ctx.textBaseline = "top";

            // Axis marker (short, not full height/width)
            ctx.beginPath();
            ctx.strokeStyle = tickColor;
            var axisLen = 8;
            if (orientation === "horizontal") {
                var originX = viewState.viewportWidth * 0.5 + viewState.offsetX;
                ctx.moveTo(originX + 0.5, height - axisLen);
                ctx.lineTo(originX + 0.5, height);
            } else {
                var originY = viewState.viewportHeight * 0.5 + viewState.offsetY;
                ctx.moveTo(width - axisLen, originY + 0.5);
                ctx.lineTo(width, originY + 0.5);
            }
            ctx.stroke();

            // Cursor marker (full length, light)
            var cx = viewState.cursorViewportX;
            var cy = viewState.cursorViewportY;
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
                var isOrigin = Math.abs(t.posPx - (orientation === "horizontal" ? width * 0.5 + offsetX : height * 0.5 + offsetY)) < 0.5;
                var tickLen = isOrigin ? 8 : 4;
                if (orientation === "horizontal") {
                    ctx.moveTo(t.posPx + 0.5, height - tickLen);
                    ctx.lineTo(t.posPx + 0.5, height);
                } else {
                    ctx.moveTo(width - tickLen, t.posPx + 0.5);
                    ctx.lineTo(width, t.posPx + 0.5);
                }
                ctx.stroke();
            });

            ctx.restore();
        }
    }

    // Label layer (Text for crisper rendering)
    Repeater {
        model: _ticks
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
