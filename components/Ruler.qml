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
    property real baseGridSize: viewState ? viewState.gridSpacing : 32
    property real majorMultiplier: viewState ? viewState.majorMultiplier : 5

    // Internal
    property real _targetPx: viewState && typeof viewState.targetMajorPx !== "undefined" ? viewState.targetMajorPx : 60
    property var _ticks: []      // {posPx, label, isMajor}
    property real _lastZoom: NaN
    property real _lastOffsetX: NaN
    property real _lastOffsetY: NaN
    property real _lastW: NaN
    property real _lastH: NaN
    property real _lastGrid: NaN
    property real _lastMajorMult: NaN

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
        if (!viewState)
            return;
        // Guard: only regenerate if relevant inputs changed (rounded to reduce churn)
        var z = Math.round(viewState.zoom * 1000) / 1000;
        var ox = Math.round(viewState.offsetX);
        var oy = Math.round(viewState.offsetY);
        var vw = Math.round(viewState.viewportWidth);
        var vh = Math.round(viewState.viewportHeight);
        var gs = Math.round(baseGridSizeVal() * 1000) / 1000;
        var mm = Math.round(majorMultiplier * 1000) / 1000;
        if (_lastZoom === z && _lastOffsetX === ox && _lastOffsetY === oy && _lastW === vw && _lastH === vh && _lastGrid === gs && _lastMajorMult === mm) {
            return;
        }
        _lastZoom = z;
        _lastOffsetX = ox;
        _lastOffsetY = oy;
        _lastW = vw;
        _lastH = vh;
        _lastGrid = gs;
        _lastMajorMult = mm;

        _ticks = generateTicks();
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

    Rectangle {
        anchors.fill: parent
        color: backgroundColor
    }

    // Axis marker (short, not full height/width)
    Rectangle {
        color: tickColor
        visible: viewState !== null
        width: orientation === "horizontal" ? 1 : 8
        height: orientation === "horizontal" ? 8 : 1
        x: orientation === "horizontal" ? (viewState ? viewState.viewportWidth * 0.5 + viewState.offsetX : 0) : parent.width - width
        y: orientation === "horizontal" ? parent.height - height : (viewState ? viewState.viewportHeight * 0.5 + viewState.offsetY : 0)
    }

    // Cursor marker (full length)
    Rectangle {
        color: axisColor
        visible: viewState && ((orientation === "horizontal" && isFinite(viewState.cursorViewportX)) || (orientation === "vertical" && isFinite(viewState.cursorViewportY)))
        width: orientation === "horizontal" ? 1 : parent.width
        height: orientation === "horizontal" ? parent.height : 1
        x: orientation === "horizontal" ? viewState.cursorViewportX : 0
        y: orientation === "horizontal" ? 0 : viewState.cursorViewportY
    }

    // Tick marks
    Repeater {
        model: _ticks
        delegate: Rectangle {
            property var t: modelData
            color: tickColor
            width: orientation === "horizontal" ? 1 : (isOrigin ? 8 : 4)
            height: orientation === "horizontal" ? (isOrigin ? 8 : 4) : 1
            x: orientation === "horizontal" ? t.posPx : parent.width - width
            y: orientation === "horizontal" ? parent.height - height : t.posPx
            readonly property bool isOrigin: Math.abs(t.posPx - (orientation === "horizontal" ? parent.width * 0.5 + viewState.offsetX : parent.height * 0.5 + viewState.offsetY)) < 0.5
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
