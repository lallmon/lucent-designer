// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import ".." as Lucent

// Artboard drawing tool - creates artboards by drawing a rectangle
Item {
    id: tool

    property real zoomLevel: 1.0
    property bool active: false
    property var settings: null

    property var setPreviewCallback: null
    property var clearPreviewCallback: null

    TwoPointToolHelper {
        id: helper
    }
    property var currentRect: null
    property real mouseX: 0
    property real mouseY: 0
    readonly property bool hasUnitSettings: typeof unitSettings !== "undefined" && unitSettings !== null

    signal itemCompleted(var itemData)

    onCurrentRectChanged: updatePreview()

    function updatePreview() {
        if (!currentRect || currentRect.width <= 0 || currentRect.height <= 0) {
            if (clearPreviewCallback)
                clearPreviewCallback();
            return;
        }
        if (!setPreviewCallback)
            return;

        // Preview artboard with border
        var backgroundColor = settings && settings.backgroundColor ? settings.backgroundColor.toString() : "#ffffff";
        setPreviewCallback({
            type: "artboard",
            x: currentRect.x,
            y: currentRect.y,
            width: currentRect.width,
            height: currentRect.height,
            backgroundColor: backgroundColor
        });
    }

    Lucent.ToolTipCanvas {
        visible: helper.isDrawing && tool.currentRect !== null
        zoomLevel: tool.zoomLevel
        cursorX: tool.mouseX
        cursorY: tool.mouseY
        text: {
            if (!tool.currentRect)
                return "";
            var w = tool.currentRect.width;
            var h = tool.currentRect.height;
            if (tool.hasUnitSettings) {
                w = unitSettings.canvasToDisplay(w);
                h = unitSettings.canvasToDisplay(h);
            }
            var unitLabel = tool.hasUnitSettings ? unitSettings.displayUnit : "px";
            var places = 1;
            if (tool.hasUnitSettings) {
                if (unitSettings.displayUnit === "in")
                    places = 3;
                else if (unitSettings.displayUnit === "mm")
                    places = 2;
                else if (unitSettings.displayUnit === "pt")
                    places = 2;
            }
            return w.toFixed(places) + " × " + h.toFixed(places) + " " + unitLabel;
        }
    }

    function handleMousePress(canvasX, canvasY, button, modifiers) {
        if (!tool.active || button !== Qt.LeftButton)
            return;

        helper.begin(canvasX, canvasY);
        currentRect = {
            x: helper.startX,
            y: helper.startY,
            width: 1,
            height: 1
        };
    }

    function handleMouseRelease(canvasX, canvasY) {
        if (!tool.active || !helper.isDrawing)
            return;

        if (helper.hasSize(currentRect)) {
            var backgroundColor = settings && settings.backgroundColor ? settings.backgroundColor.toString() : "#ffffff";
            itemCompleted({
                type: "artboard",
                x: currentRect.x,
                y: currentRect.y,
                width: currentRect.width,
                height: currentRect.height,
                backgroundColor: backgroundColor
            });
        }

        if (clearPreviewCallback)
            clearPreviewCallback();
        currentRect = null;
        helper.reset();
    }

    function handleMouseMove(canvasX, canvasY, modifiers) {
        mouseX = canvasX;
        mouseY = canvasY;

        if (!tool.active || !helper.isDrawing)
            return;

        var deltaX = canvasX - helper.startX;
        var deltaY = canvasY - helper.startY;
        var rectWidth = Math.abs(deltaX);
        var rectHeight = Math.abs(deltaY);

        // Constrain to square when Shift is held
        if (modifiers & Qt.ShiftModifier) {
            var size = Math.max(rectWidth, rectHeight);
            rectWidth = size;
            rectHeight = size;
        }

        // Calculate position based on Ctrl (center mode) or corner mode
        var rectX, rectY;
        if (modifiers & Qt.ControlModifier) {
            rectWidth *= 2;
            rectHeight *= 2;
            rectX = helper.startX - rectWidth / 2;
            rectY = helper.startY - rectHeight / 2;
        } else {
            rectX = deltaX >= 0 ? helper.startX : helper.startX - rectWidth;
            rectY = deltaY >= 0 ? helper.startY : helper.startY - rectHeight;
        }

        currentRect = {
            x: rectX,
            y: rectY,
            width: rectWidth,
            height: rectHeight
        };
    }

    function reset() {
        helper.reset();
        if (clearPreviewCallback)
            clearPreviewCallback();
        currentRect = null;
    }
}
