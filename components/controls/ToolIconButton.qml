// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

ToolButton {
    id: root
    property string toolName: ""
    property string iconName: ""
    property string iconWeight: "fill"
    property string tooltipText: ""
    property string activeTool: ""
    property ButtonGroup buttonGroup: null
    // For select tool: treat empty activeTool as selected.
    property bool isDefaultSelect: false
    property string deselectValue: ""
    readonly property SystemPalette themePalette: Lucent.Themed.palette

    signal toolClicked(string nextTool)

    Layout.preferredWidth: Lucent.Styles.height.xlg
    Layout.preferredHeight: Lucent.Styles.height.xlg
    Layout.alignment: Qt.AlignHCenter
    checkable: true
    checked: isDefaultSelect ? (activeTool === toolName || activeTool === "") : activeTool === toolName
    ButtonGroup.group: buttonGroup

    Lucent.ToolTipStyled {
        visible: root.hovered && root.tooltipText !== ""
        text: root.tooltipText
    }

    contentItem: Item {
        anchors.fill: parent
        Lucent.PhIcon {
            anchors.centerIn: parent
            name: iconName
            weight: iconWeight
            color: root.checked ? themePalette.highlight : themePalette.buttonText
        }
    }

    onClicked: {
        toolClicked(checked ? toolName : deselectValue);
    }
}
