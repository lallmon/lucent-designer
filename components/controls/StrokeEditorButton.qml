// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

Item {
    id: root

    property real strokeWidth: 1.0
    property color strokeColor: "#808080"
    property string strokeStyle: "none"  // "none" or "solid"
    property string strokeCap: "butt"  // "butt", "square", "round"
    property string strokeAlign: "center"  // "center", "inner", "outer"
    property string strokeOrder: "top"  // "top" or "bottom"
    property bool strokeScaleWithObject: false

    signal widthEdited(real newWidth)
    signal widthCommitted(real newWidth)
    signal styleChanged(string newStyle)
    signal capChanged(string newCap)
    signal alignChanged(string newAlign)
    signal orderChanged(string newOrder)
    signal scaleWithObjectChanged(bool newValue)
    signal panelOpened
    signal panelClosed

    readonly property SystemPalette themePalette: Lucent.Themed.palette
    readonly property bool panelVisible: strokePanel.visible
    readonly property bool hasStroke: root.strokeStyle !== "none" && root.strokeWidth > 0

    implicitWidth: strokeButton.implicitWidth
    implicitHeight: strokeButton.implicitHeight

    Button {
        id: strokeButton
        implicitWidth: 96
        implicitHeight: 20

        onClicked: {
            if (strokePanel.visible) {
                strokePanel.close();
            } else {
                strokePanel.open();
            }
        }

        background: Rectangle {
            border.color: root.themePalette.mid
            border.width: 1
            radius: Lucent.Styles.rad.sm
            color: "transparent"

            Rectangle {
                visible: root.hasStroke
                anchors.centerIn: parent
                width: parent.width - 8
                height: Math.max(Math.min(root.strokeWidth, 6), 1)
                color: root.strokeColor
                radius: height / 2
            }

            Rectangle {
                visible: !root.hasStroke
                anchors.centerIn: parent
                width: Math.sqrt(Math.pow(parent.width - 6, 2) + Math.pow(parent.height - 6, 2))
                height: 1
                color: "#e53935"
                rotation: -Math.atan2(parent.height - 6, parent.width - 6) * 180 / Math.PI
                antialiasing: true
            }
        }

        Lucent.ToolTipStyled {
            visible: strokeButton.hovered && !strokePanel.visible
            text: qsTr("Edit Stroke")
        }
    }

    Popup {
        id: strokePanel
        x: 0
        y: strokeButton.height + 4
        width: 350
        padding: 16

        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        onOpened: root.panelOpened()
        onClosed: root.panelClosed()

        background: Rectangle {
            color: root.themePalette.window
            border.color: root.themePalette.mid
            border.width: 1
            radius: Lucent.Styles.rad.md
        }

        contentItem: Lucent.StrokeControls {
            strokeWidth: root.strokeWidth
            strokeStyle: root.strokeStyle
            strokeCap: root.strokeCap
            strokeAlign: root.strokeAlign
            strokeOrder: root.strokeOrder
            strokeScaleWithObject: root.strokeScaleWithObject
            onWidthEdited: newWidth => root.widthEdited(newWidth)
            onWidthCommitted: newWidth => root.widthCommitted(newWidth)
            onStyleChanged: newStyle => root.styleChanged(newStyle)
            onCapChanged: newCap => root.capChanged(newCap)
            onAlignChanged: newAlign => root.alignChanged(newAlign)
            onOrderChanged: newOrder => root.orderChanged(newOrder)
            onScaleWithObjectChanged: newValue => root.scaleWithObjectChanged(newValue)
        }
    }
}
