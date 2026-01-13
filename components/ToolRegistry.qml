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
                instruction: "Click to select • Drag to move • Shift+click for multi-select"
            },
            "rectangle": {
                name: "Rectangle Tool",
                shortcut: "R",
                icon: "rectangle",
                iconWeight: "regular",
                instruction: "Click and drag to draw • Shift: Square • Alt: From center"
            },
            "ellipse": {
                name: "Ellipse Tool",
                shortcut: "O",
                icon: "circle",
                iconWeight: "regular",
                instruction: "Click and drag to draw • Shift: Circle • Alt: From center"
            },
            "pen": {
                name: "Pen Tool",
                shortcut: "P",
                icon: "pen-nib",
                iconWeight: "regular",
                instruction: "Click to add points • Click first point to close path"
            },
            "text": {
                name: "Text Tool",
                shortcut: "T",
                icon: "text-t",
                iconWeight: "regular",
                instruction: "Click to place text • Type, then Enter to confirm"
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
