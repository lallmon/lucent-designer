// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

ColumnLayout {
    id: root

    property real strokeWidth: 1.0
    property string strokeStyle: "none"  // "none" or "solid"
    property string strokeAlign: "center"  // "center", "inner", "outer"

    signal widthEdited(real newWidth)
    signal widthCommitted(real newWidth)
    signal styleChanged(string newStyle)
    signal alignChanged(string newAlign)

    readonly property SystemPalette themePalette: Lucent.Themed.palette

    spacing: Lucent.Styles.pad.md

    RowLayout {
        spacing: Lucent.Styles.pad.md

        Label {
            text: qsTr("Style:")
            font.pixelSize: 12
            color: root.themePalette.text
        }

        ButtonGroup {
            id: styleGroup
            exclusive: true
        }

        Button {
            id: noneButton
            checkable: true
            checked: root.strokeStyle === "none"
            ButtonGroup.group: styleGroup
            Layout.preferredWidth: Lucent.Styles.height.lg
            Layout.preferredHeight: Lucent.Styles.height.lg

            onClicked: {
                if (root.strokeStyle !== "none") {
                    root.styleChanged("none");
                }
            }

            background: Rectangle {
                color: noneButton.checked ? root.themePalette.highlight : root.themePalette.button
                border.color: root.themePalette.mid
                border.width: 1
                radius: Lucent.Styles.rad.sm
            }

            contentItem: Lucent.PhIcon {
                name: "x-circle"
                weight: "regular"
                size: 22
                color: noneButton.checked ? root.themePalette.highlightedText : root.themePalette.buttonText
            }

            Lucent.ToolTipStyled {
                visible: noneButton.hovered
                text: qsTr("None")
            }
        }

        Button {
            id: solidButton
            checkable: true
            checked: root.strokeStyle === "solid"
            ButtonGroup.group: styleGroup
            Layout.preferredWidth: Lucent.Styles.height.lg
            Layout.preferredHeight: Lucent.Styles.height.lg

            onClicked: {
                if (root.strokeStyle !== "solid") {
                    root.styleChanged("solid");
                    if (root.strokeWidth <= 0) {
                        root.widthEdited(1.0);
                        root.widthCommitted(1.0);
                    }
                }
            }

            background: Rectangle {
                color: solidButton.checked ? root.themePalette.highlight : root.themePalette.button
                border.color: root.themePalette.mid
                border.width: 1
                radius: Lucent.Styles.rad.sm
            }

            contentItem: Lucent.PhIcon {
                name: "minus"
                weight: "regular"
                size: 22
                color: solidButton.checked ? root.themePalette.highlightedText : root.themePalette.buttonText
            }

            Lucent.ToolTipStyled {
                visible: solidButton.hovered
                text: qsTr("Solid")
            }
        }
    }

    RowLayout {
        spacing: Lucent.Styles.pad.md
        opacity: root.strokeStyle === "none" ? 0.5 : 1.0
        enabled: root.strokeStyle !== "none"

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

    RowLayout {
        spacing: Lucent.Styles.pad.md
        opacity: root.strokeStyle === "none" ? 0.5 : 1.0
        enabled: root.strokeStyle !== "none"

        Label {
            text: qsTr("Align:")
            font.pixelSize: 12
            color: root.themePalette.text
        }

        ButtonGroup {
            id: alignGroup
            exclusive: true
        }

        Button {
            id: centerButton
            checkable: true
            checked: root.strokeAlign === "center"
            ButtonGroup.group: alignGroup
            Layout.preferredWidth: Lucent.Styles.height.lg
            Layout.preferredHeight: Lucent.Styles.height.lg

            onClicked: {
                if (root.strokeAlign !== "center") {
                    root.alignChanged("center");
                }
            }

            background: Rectangle {
                color: centerButton.checked ? root.themePalette.highlight : root.themePalette.button
                border.color: root.themePalette.mid
                border.width: 1
                radius: Lucent.Styles.rad.sm
            }

            contentItem: Item {}

            Lucent.ToolTipStyled {
                visible: centerButton.hovered
                text: qsTr("Center")
            }
        }

        Button {
            id: innerButton
            checkable: true
            checked: root.strokeAlign === "inner"
            ButtonGroup.group: alignGroup
            Layout.preferredWidth: Lucent.Styles.height.lg
            Layout.preferredHeight: Lucent.Styles.height.lg

            onClicked: {
                if (root.strokeAlign !== "inner") {
                    root.alignChanged("inner");
                }
            }

            background: Rectangle {
                color: innerButton.checked ? root.themePalette.highlight : root.themePalette.button
                border.color: root.themePalette.mid
                border.width: 1
                radius: Lucent.Styles.rad.sm
            }

            contentItem: Item {}

            Lucent.ToolTipStyled {
                visible: innerButton.hovered
                text: qsTr("Inner")
            }
        }

        Button {
            id: outerButton
            checkable: true
            checked: root.strokeAlign === "outer"
            ButtonGroup.group: alignGroup
            Layout.preferredWidth: Lucent.Styles.height.lg
            Layout.preferredHeight: Lucent.Styles.height.lg

            onClicked: {
                if (root.strokeAlign !== "outer") {
                    root.alignChanged("outer");
                }
            }

            background: Rectangle {
                color: outerButton.checked ? root.themePalette.highlight : root.themePalette.button
                border.color: root.themePalette.mid
                border.width: 1
                radius: Lucent.Styles.rad.sm
            }

            contentItem: Item {}

            Lucent.ToolTipStyled {
                visible: outerButton.hovered
                text: qsTr("Outer")
            }
        }
    }
}
