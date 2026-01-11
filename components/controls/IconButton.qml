// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import ".." as Lucent

// Simple icon button for action triggers (non-checkable)
Rectangle {
    id: root

    property string iconName: ""
    property string iconWeight: "fill"
    property string tooltipText: ""
    property int size: 24
    property int iconSize: 20
    // Base icon color when not hovered (e.g. based on selection state)
    property color iconBaseColor: themePalette.text
    // Final icon color: highlight on hover, otherwise use base
    readonly property color iconColor: hovered ? themePalette.highlight : iconBaseColor

    signal clicked

    readonly property SystemPalette themePalette: Lucent.Themed.palette
    readonly property bool hovered: hoverHandler.hovered

    width: size
    height: size
    radius: Lucent.Styles.rad.sm
    color: hovered ? themePalette.midlight : "transparent"

    Lucent.PhIcon {
        anchors.centerIn: parent
        name: root.iconName
        weight: root.iconWeight
        size: root.iconSize
        color: root.iconColor
    }

    HoverHandler {
        id: hoverHandler
        cursorShape: Qt.PointingHandCursor
    }

    TapHandler {
        onTapped: root.clicked()
    }

    Lucent.ToolTipStyled {
        visible: root.hovered && root.tooltipText !== ""
        text: root.tooltipText
    }
}
