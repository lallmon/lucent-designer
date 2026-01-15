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

    // Fires during drag for live preview
    signal widthEdited(real newWidth)
    // Fires on release for undo/redo history
    signal widthCommitted(real newWidth)
    signal panelOpened
    signal panelClosed

    readonly property SystemPalette themePalette: Lucent.Themed.palette
    readonly property bool panelVisible: strokePanel.visible

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
                visible: root.strokeWidth > 0
                anchors.centerIn: parent
                width: parent.width - 8
                height: Math.max(Math.min(root.strokeWidth, 6), 1)
                color: root.strokeColor
                radius: height / 2
            }

            Rectangle {
                visible: root.strokeWidth <= 0
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

        contentItem: RowLayout {
            spacing: Lucent.Styles.pad.md

            Label {
                text: qsTr("Width:")
                font.pixelSize: 12
                color: root.themePalette.text
            }

            Slider {
                id: widthSlider
                Layout.fillWidth: true
                Layout.preferredHeight: Lucent.Styles.height.sm
                from: 0
                to: 100
                stepSize: 0.1
                snapMode: Slider.SnapAlways
                value: root.strokeWidth

                onMoved: root.widthEdited(value)

                onPressedChanged: {
                    if (!pressed) {
                        root.widthCommitted(value);
                    }
                }

                background: Rectangle {
                    x: widthSlider.leftPadding
                    y: widthSlider.topPadding + widthSlider.availableHeight / 2 - height / 2
                    width: widthSlider.availableWidth
                    height: Lucent.Styles.height.xxxsm
                    radius: Lucent.Styles.rad.sm
                    color: root.themePalette.base

                    Rectangle {
                        width: widthSlider.visualPosition * parent.width
                        height: parent.height
                        color: root.themePalette.highlight
                        radius: Lucent.Styles.rad.sm
                    }
                }

                handle: Rectangle {
                    x: widthSlider.leftPadding + widthSlider.visualPosition * (widthSlider.availableWidth - width)
                    y: widthSlider.topPadding + widthSlider.availableHeight / 2 - height / 2
                    width: Lucent.Styles.height.xs
                    height: Lucent.Styles.height.xs
                    radius: Lucent.Styles.rad.lg
                    color: widthSlider.pressed ? root.themePalette.highlight : root.themePalette.button
                    border.color: root.themePalette.mid
                    border.width: 1
                }
            }

            TextField {
                id: widthField
                Layout.preferredWidth: 40
                Layout.preferredHeight: Lucent.Styles.height.md
                text: root.strokeWidth.toFixed(1)
                font.pixelSize: 11
                horizontalAlignment: TextInput.AlignHCenter
                selectByMouse: true

                validator: DoubleValidator {
                    bottom: 0
                    top: 100
                    decimals: 1
                }

                onEditingFinished: {
                    var val = parseFloat(text);
                    if (!isNaN(val)) {
                        val = Math.max(0, Math.min(100, val));
                        root.widthEdited(val);
                        root.widthCommitted(val);
                    }
                }

                background: Rectangle {
                    color: root.themePalette.base
                    border.color: widthField.activeFocus ? root.themePalette.highlight : root.themePalette.mid
                    border.width: 1
                    radius: Lucent.Styles.rad.sm
                }
            }
        }
    }
}
