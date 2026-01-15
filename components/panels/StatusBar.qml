// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

ToolBar {
    id: root
    implicitHeight: 32
    property real cursorX: 0
    property real cursorY: 0
    property string activeTool: "select"

    readonly property bool hasUnitSettings: typeof unitSettings !== "undefined" && unitSettings !== null
    readonly property string displayUnitLabel: hasUnitSettings ? unitSettings.displayUnit : "px"

    // Cache instruction text - prioritize edit mode, then active tool
    readonly property string toolInstruction: {
        if (Lucent.SelectionManager.editModeActive) {
            return Lucent.ToolRegistry.getInstruction("pathEdit");
        }
        return Lucent.ToolRegistry.getInstruction(activeTool);
    }

    RowLayout {
        anchors.fill: parent
        spacing: 12
        Layout.alignment: Qt.AlignVCenter

        // Tool instructions (left side) - bound to cached property
        Label {
            Layout.leftMargin: 10
            Layout.fillWidth: true
            text: root.toolInstruction
            color: palette.text
            font.pixelSize: 11
            elide: Text.ElideRight
        }

        // Cursor readout (right side) - separate labels for efficient updates
        RowLayout {
            Layout.alignment: Qt.AlignVCenter
            Layout.rightMargin: 10
            spacing: 2

            Lucent.PhIcon {
                name: "crosshair-simple"
                size: 16
                color: "white"
            }

            Label {
                text: "X:"
            }
            Label {
                id: xLabel
                text: root.hasUnitSettings ? unitSettings.canvasToDisplay(root.cursorX).toFixed(1) : root.cursorX.toFixed(1)
                horizontalAlignment: Text.AlignRight
                Layout.minimumWidth: 50
            }
            Label {
                text: "Y:"
            }
            Label {
                id: yLabel
                text: root.hasUnitSettings ? unitSettings.canvasToDisplay(root.cursorY).toFixed(1) : root.cursorY.toFixed(1)
                horizontalAlignment: Text.AlignRight
                Layout.minimumWidth: 50
            }
            Label {
                text: root.displayUnitLabel
            }
        }
    }
}
