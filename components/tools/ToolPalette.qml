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
        Repeater {
            model: Lucent.ToolRegistry.toolOrder

            Lucent.ToolIconButton {
                required property int index
                required property string modelData

                readonly property var toolInfo: Lucent.ToolRegistry.getTool(modelData)

                toolName: modelData
                iconName: toolInfo ? toolInfo.icon : ""
                iconWeight: toolInfo ? toolInfo.iconWeight : "regular"
                tooltipText: Lucent.ToolRegistry.getTooltip(modelData)
                activeTool: root.activeTool
                buttonGroup: toolButtonGroup
                isDefaultSelect: modelData === "select"
                deselectValue: ""

                onToolClicked: function (nextTool) {
                    root.toolSelected(nextTool);
                }
            }
        }

        Item {
            Layout.fillHeight: true
        }
    }
}
