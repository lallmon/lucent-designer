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

    readonly property SystemPalette themePalette: Lucent.Themed.palette

    spacing: Lucent.Styles.pad.md

    RowLayout {
        spacing: Lucent.Styles.pad.md

        Label {
            text: qsTr("Style:")
            font.pixelSize: 12
            color: root.themePalette.text
            Layout.preferredWidth: 36
        }

        Lucent.SegmentedButtonGroup {
            Lucent.SegmentedButton {
                checked: root.strokeStyle === "none"
                iconName: "x-circle"
                toolTipText: qsTr("None")
                onClicked: {
                    if (root.strokeStyle !== "none") {
                        root.styleChanged("none");
                    }
                }
            }

            Lucent.SegmentedButton {
                checked: root.strokeStyle === "solid"
                iconName: "minus"
                toolTipText: qsTr("Solid")
                onClicked: {
                    if (root.strokeStyle !== "solid") {
                        root.styleChanged("solid");
                        if (root.strokeWidth <= 0) {
                            root.widthEdited(1.0);
                            root.widthCommitted(1.0);
                        }
                    }
                }
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
            Layout.preferredWidth: 36
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
            text: qsTr("Cap:")
            font.pixelSize: 12
            color: root.themePalette.text
            Layout.preferredWidth: 36
        }

        Lucent.SegmentedButtonGroup {
            Lucent.SegmentedButton {
                checked: root.strokeCap === "butt"
                toolTipText: qsTr("Butt")
                onClicked: {
                    if (root.strokeCap !== "butt") {
                        root.capChanged("butt");
                    }
                }
            }

            Lucent.SegmentedButton {
                checked: root.strokeCap === "square"
                toolTipText: qsTr("Square")
                onClicked: {
                    if (root.strokeCap !== "square") {
                        root.capChanged("square");
                    }
                }
            }

            Lucent.SegmentedButton {
                checked: root.strokeCap === "round"
                toolTipText: qsTr("Round")
                onClicked: {
                    if (root.strokeCap !== "round") {
                        root.capChanged("round");
                    }
                }
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
            Layout.preferredWidth: 36
        }

        Lucent.SegmentedButtonGroup {
            Lucent.SegmentedButton {
                checked: root.strokeAlign === "center"
                toolTipText: qsTr("Center")
                onClicked: {
                    if (root.strokeAlign !== "center") {
                        root.alignChanged("center");
                    }
                }
            }

            Lucent.SegmentedButton {
                checked: root.strokeAlign === "inner"
                toolTipText: qsTr("Inner")
                onClicked: {
                    if (root.strokeAlign !== "inner") {
                        root.alignChanged("inner");
                    }
                }
            }

            Lucent.SegmentedButton {
                checked: root.strokeAlign === "outer"
                toolTipText: qsTr("Outer")
                onClicked: {
                    if (root.strokeAlign !== "outer") {
                        root.alignChanged("outer");
                    }
                }
            }
        }
    }

    RowLayout {
        spacing: Lucent.Styles.pad.md
        opacity: root.strokeStyle === "none" ? 0.5 : 1.0
        enabled: root.strokeStyle !== "none"

        Label {
            text: qsTr("Order:")
            font.pixelSize: 12
            color: root.themePalette.text
            Layout.preferredWidth: 36
        }

        Lucent.SegmentedButtonGroup {
            Lucent.SegmentedButton {
                checked: root.strokeOrder === "top"
                toolTipText: qsTr("Top")
                onClicked: {
                    if (root.strokeOrder !== "top") {
                        root.orderChanged("top");
                    }
                }
            }

            Lucent.SegmentedButton {
                checked: root.strokeOrder === "bottom"
                toolTipText: qsTr("Bottom")
                onClicked: {
                    if (root.strokeOrder !== "bottom") {
                        root.orderChanged("bottom");
                    }
                }
            }
        }

        Item {
            Layout.fillWidth: true
        }

        CheckBox {
            text: qsTr("Scale with object")
            font.pixelSize: 12
            checked: root.strokeScaleWithObject
            onToggled: root.scaleWithObjectChanged(checked)
        }
    }
}
