// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

pragma Singleton
import QtQuick

QtObject {
    readonly property var tools: ({
            "select": {
                name: "Move Tool",
                shortcut: "V",
                icon: "cursor-fill",
                iconWeight: "fill",
                instruction: "<b>Click</b> to select • <b>Drag</b> to move • <b>Shift + click</b> to multi-select • <b>Double-click</b> to edit shapes"
            },
            "rectangle": {
                name: "Rectangle Tool",
                shortcut: "R",
                icon: "rectangle",
                iconWeight: "regular",
                instruction: "<b>Click</b> and <b>Drag</b> to draw • <b>Shift</b>: Draw evenly sized • <b>Ctrl</b>: Draw from center"
            },
            "ellipse": {
                name: "Ellipse Tool",
                shortcut: "O",
                icon: "circle",
                iconWeight: "regular",
                instruction: "<b>Click</b> and <b>Drag</b> to draw • <b>Shift</b>: Draw evenly sized • <b>Ctrl</b>: Draw from center"
            },
            "pen": {
                name: "Pen Tool",
                shortcut: "P",
                icon: "pen-nib",
                iconWeight: "regular",
                instruction: "<b>Click</b> to add points • <b>Drag</b>: bezier curve • <b>Click</b> start to close • <b>Double-click</b> for line"
            },
            "text": {
                name: "Text Tool",
                shortcut: "T",
                icon: "text-t",
                iconWeight: "regular",
                instruction: "<b>Click</b> to place text box • <b>Type</b> to enter, then <b>Enter</b> to commit text"
            },
            "pathEdit": {
                name: "Path Edit Mode",
                instruction: "<b>Click</b> to select points • <b>Drag</b> handles to adjust curves • <b>Alt + Drag</b> to break handlesymmetry • <b>Click</b> outside or <b>Esc</b> to finish"
            }
        })

    readonly property var toolOrder: ["select", "rectangle", "ellipse", "pen", "text"]

    function getTooltip(toolName) {
        var t = tools[toolName];
        return t ? (t.name + " (" + t.shortcut + ")") : "";
    }

    function getInstruction(toolName) {
        var t = tools[toolName];
        return t ? t.instruction : "";
    }

    function getTool(toolName) {
        return tools[toolName] || null;
    }
}
