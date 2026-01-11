// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

Pane {
    id: root
    width: 36
    padding: Lucent.Styles.pad.sm

    signal toolSelected(string toolName)
    property string activeTool: ""
    readonly property SystemPalette themePalette: Lucent.Themed.palette

    background: Rectangle {
        color: themePalette.window
        Rectangle {
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            width: 1
            color: themePalette.mid
        }
    }

    ButtonGroup {
        id: toolButtonGroup
        exclusive: true
    }

    contentItem: ColumnLayout {
        Lucent.ToolIconButton {
            id: selButton
            toolName: "select"
            iconName: "cursor-fill"
            tooltipText: ""
            activeTool: root.activeTool
            buttonGroup: toolButtonGroup
            isDefaultSelect: true
            deselectValue: ""
            onToolClicked: function (nextTool) {
                root.toolSelected(nextTool);
            }
        }

        Lucent.ToolIconButton {
            id: rectButton
            toolName: "rectangle"
            iconName: "rectangle"
            iconWeight: "regular"
            tooltipText: "Rectangle Tool\n\nShift: Constrain to square\nAlt: Draw from center"
            activeTool: root.activeTool
            buttonGroup: toolButtonGroup
            onToolClicked: function (nextTool) {
                root.toolSelected(nextTool);
            }
        }

        Lucent.ToolIconButton {
            id: ellipseButton
            toolName: "ellipse"
            iconName: "circle"
            iconWeight: "regular"
            tooltipText: "Ellipse Tool\n\nShift: Constrain to circle\nAlt: Draw from center"
            activeTool: root.activeTool
            buttonGroup: toolButtonGroup
            onToolClicked: function (nextTool) {
                root.toolSelected(nextTool);
            }
        }

        Lucent.ToolIconButton {
            id: penButton
            toolName: "pen"
            iconName: "pen-nib"
            iconWeight: "regular"
            tooltipText: "Pen Tool\n\nClick to add points, click first point to close"
            activeTool: root.activeTool
            buttonGroup: toolButtonGroup
            onToolClicked: function (nextTool) {
                root.toolSelected(nextTool);
            }
        }

        Lucent.ToolIconButton {
            id: textButton
            toolName: "text"
            iconName: "text-t"
            iconWeight: "regular"
            tooltipText: "Text Tool\n\nClick to place text, type, then press Enter to confirm"
            activeTool: root.activeTool
            buttonGroup: toolButtonGroup
            onToolClicked: function (nextTool) {
                root.toolSelected(nextTool);
            }
        }

        Item {
            Layout.fillHeight: true
        }
    }
}
