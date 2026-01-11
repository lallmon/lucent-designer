// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

// Panel displaying unified transform properties (X, Y, Width, Height) for selected items
Item {
    id: root
    readonly property SystemPalette themePalette: Lucent.Themed.palette

    readonly property var selectedItem: Lucent.SelectionManager.selectedItem
    readonly property int selectedIndex: Lucent.SelectionManager.selectedItemIndex
    readonly property bool hasValidSelection: selectedIndex >= 0 && canvasModel

    readonly property bool hasEditableBounds: selectedItem && ["rectangle", "ellipse", "path", "text"].includes(selectedItem.type)

    readonly property bool isLocked: hasValidSelection && canvasModel.isEffectivelyLocked(selectedIndex)

    property var currentTransform: null

    function refreshTransform() {
        currentTransform = hasValidSelection ? canvasModel.getItemTransform(selectedIndex) : null;
    }

    Connections {
        target: canvasModel
        function onItemTransformChanged(index) {
            if (index === root.selectedIndex)
                root.refreshTransform();
        }
        function onItemModified(index) {
            if (index === root.selectedIndex)
                root.refreshTransform();
        }
    }

    Connections {
        target: Lucent.SelectionManager
        function onSelectedItemIndexChanged() {
            root.refreshTransform();
        }
    }

    Component.onCompleted: refreshTransform()

    readonly property bool controlsEnabled: hasEditableBounds && !isLocked

    readonly property int labelSize: 10
    readonly property color labelColor: themePalette.text

    property bool proportionalScale: false

    // Displayed position and size from model
    readonly property var displayedPosition: hasValidSelection ? canvasModel.getDisplayedPosition(selectedIndex) : null
    readonly property real displayedX: displayedPosition ? displayedPosition.x : 0
    readonly property real displayedY: displayedPosition ? displayedPosition.y : 0

    readonly property var displayedSize: hasValidSelection ? canvasModel.getDisplayedSize(selectedIndex) : null
    readonly property real displayedWidth: displayedSize ? displayedSize.width : 0
    readonly property real displayedHeight: displayedSize ? displayedSize.height : 0

    // Transform state for rotation display and origin buttons
    readonly property real currentRotation: currentTransform ? (currentTransform.rotate ?? 0) : 0
    readonly property real currentOriginX: currentTransform ? (currentTransform.originX ?? 0) : 0
    readonly property real currentOriginY: currentTransform ? (currentTransform.originY ?? 0) : 0

    implicitHeight: contentLayout.implicitHeight

    ColumnLayout {
        id: contentLayout
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: Lucent.Styles.pad.sm
            Layout.rightMargin: Lucent.Styles.pad.sm

            Label {
                text: qsTr("Transform")
                font.pixelSize: 12
                color: themePalette.text
                Layout.fillWidth: true
            }
        }

        ToolSeparator {
            Layout.fillWidth: true
            orientation: Qt.Horizontal
            contentItem: Rectangle {
                implicitHeight: 1
                color: themePalette.mid
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 4
            Layout.bottomMargin: 8
            Layout.leftMargin: Lucent.Styles.pad.sm
            Layout.rightMargin: Lucent.Styles.pad.sm
            spacing: 8
            enabled: root.controlsEnabled
            opacity: root.controlsEnabled ? 1.0 : 0.5

            ButtonGroup {
                id: originGroup
                exclusive: true
            }

            Grid {
                columns: 3
                spacing: 2

                Repeater {
                    // Generate 3x3 origin grid: (0, 0.5, 1) × (0, 0.5, 1)
                    model: {
                        var points = [];
                        for (var row = 0; row <= 1; row += 0.5)
                            for (var col = 0; col <= 1; col += 0.5)
                                points.push({
                                    ox: col,
                                    oy: row
                                });
                        return points;
                    }

                    delegate: Button {
                        required property var modelData
                        required property int index

                        width: 16
                        height: 16
                        checkable: true
                        checked: root.currentOriginX === modelData.ox && root.currentOriginY === modelData.oy
                        ButtonGroup.group: originGroup

                        onClicked: canvasModel.setItemOrigin(root.selectedIndex, modelData.ox, modelData.oy)

                        background: Rectangle {
                            color: parent.checked ? root.themePalette.highlight : root.themePalette.button
                            border.color: root.themePalette.mid
                            border.width: 1
                            radius: 2
                        }
                    }
                }
            }

            Lucent.VerticalDivider {}

            ColumnLayout {
                spacing: 4
                Layout.fillWidth: true

                Lucent.SpinBoxLabeled {
                    label: qsTr("X:")
                    labelSize: root.labelSize
                    labelColor: root.labelColor
                    from: -100000
                    to: 100000
                    value: Math.round(root.displayedX)
                    Layout.fillWidth: true
                    onValueModified: newValue => {
                        canvasModel.setItemPosition(root.selectedIndex, "x", newValue);
                        appController.focusCanvas();
                    }
                }

                Lucent.SpinBoxLabeled {
                    label: qsTr("Y:")
                    labelSize: root.labelSize
                    labelColor: root.labelColor
                    from: -100000
                    to: 100000
                    value: Math.round(root.displayedY)
                    Layout.fillWidth: true
                    onValueModified: newValue => {
                        canvasModel.setItemPosition(root.selectedIndex, "y", newValue);
                        appController.focusCanvas();
                    }
                }
            }

            Lucent.VerticalDivider {}

            ColumnLayout {
                spacing: 4
                Layout.fillWidth: true

                Lucent.SpinBoxLabeled {
                    label: qsTr("W:")
                    labelSize: root.labelSize
                    labelColor: root.labelColor
                    from: 0
                    to: 100000
                    value: Math.round(root.displayedWidth)
                    Layout.fillWidth: true
                    onValueModified: newValue => {
                        canvasModel.setDisplayedSize(root.selectedIndex, "width", newValue, root.proportionalScale);
                        appController.focusCanvas();
                    }
                }

                Lucent.SpinBoxLabeled {
                    label: qsTr("H:")
                    labelSize: root.labelSize
                    labelColor: root.labelColor
                    from: 0
                    to: 100000
                    value: Math.round(root.displayedHeight)
                    Layout.fillWidth: true
                    onValueModified: newValue => {
                        canvasModel.setDisplayedSize(root.selectedIndex, "height", newValue, root.proportionalScale);
                        appController.focusCanvas();
                    }
                }
            }

            ColumnLayout {
                spacing: 0
                Layout.alignment: Qt.AlignVCenter

                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 8
                    Layout.alignment: Qt.AlignHCenter
                    color: proportionalToggle.checked ? root.themePalette.highlight : root.themePalette.mid
                }

                Button {
                    id: proportionalToggle
                    Layout.preferredWidth: 24
                    Layout.preferredHeight: 24
                    checkable: true
                    checked: root.proportionalScale
                    onCheckedChanged: root.proportionalScale = checked

                    background: Rectangle {
                        color: proportionalToggle.checked ? root.themePalette.highlight : root.themePalette.button
                        border.color: root.themePalette.mid
                        border.width: 1
                        radius: 2
                    }

                    contentItem: Lucent.PhIcon {
                        name: proportionalToggle.checked ? "lock" : "lock-open"
                        size: 14
                        color: proportionalToggle.checked ? root.themePalette.highlightedText : root.themePalette.buttonText
                        anchors.centerIn: parent
                    }

                    Lucent.ToolTipStyled {
                        visible: proportionalToggle.hovered
                        text: proportionalToggle.checked ? qsTr("Constrain proportions") : qsTr("Free resize")
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 8
                    Layout.alignment: Qt.AlignHCenter
                    color: proportionalToggle.checked ? root.themePalette.highlight : root.themePalette.mid
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 4
            Layout.bottomMargin: 8
            Layout.leftMargin: Lucent.Styles.pad.xsm
            Layout.rightMargin: Lucent.Styles.pad.xsm
            spacing: 8
            enabled: root.controlsEnabled
            opacity: root.controlsEnabled ? 1.0 : 0.5

            Label {
                text: qsTr("Rotate:")
                font.pixelSize: root.labelSize
                color: root.labelColor
            }
            TextField {
                id: rotationField
                horizontalAlignment: TextInput.AlignHCenter
                Layout.preferredWidth: 50
                validator: IntValidator {
                    bottom: -9999
                    top: 9999
                }

                readonly property string expectedText: Math.round(root.currentRotation).toString()
                property bool isCommitting: false

                Component.onCompleted: text = expectedText

                // Sync with undo/redo; skip during commit to prevent double-fire
                onExpectedTextChanged: {
                    if (!isCommitting)
                        text = expectedText;
                }

                onEditingFinished: {
                    if (isCommitting)
                        return;
                    isCommitting = true;

                    // Model normalizes to 0-360° automatically
                    var val = parseInt(text) || 0;
                    canvasModel.updateTransformProperty(root.selectedIndex, "rotate", val);
                    appController.focusCanvas();

                    isCommitting = false;
                }
            }
            Label {
                text: "°"
                font.pixelSize: root.labelSize
                color: root.labelColor
            }
            Slider {
                id: rotationSlider
                from: 0
                to: 360
                value: root.currentRotation
                Layout.fillWidth: true

                onPressedChanged: {
                    if (pressed)
                        canvasModel.beginTransaction();
                    else
                        canvasModel.endTransaction();
                }

                onMoved: canvasModel.updateTransformProperty(root.selectedIndex, "rotate", value)

                handle: Rectangle {
                    x: rotationSlider.leftPadding + rotationSlider.visualPosition * (rotationSlider.availableWidth - width)
                    y: rotationSlider.topPadding + rotationSlider.availableHeight / 2 - height / 2
                    width: Lucent.Styles.height.xs
                    height: Lucent.Styles.height.xs
                    radius: Lucent.Styles.rad.lg
                    color: rotationSlider.pressed ? root.themePalette.highlight : root.themePalette.button
                    border.color: root.themePalette.mid
                    border.width: 1
                }
            }

            Lucent.IconButton {
                iconName: "stack-simple-fill"
                iconWeight: "fill"
                iconSize: 14
                tooltipText: qsTr("Flatten Transform")
                enabled: root.controlsEnabled && canvasModel.hasNonIdentityTransform(root.selectedIndex)
                onClicked: {
                    if (root.hasValidSelection) {
                        canvasModel.bakeTransform(root.selectedIndex);
                        appController.focusCanvas();
                    }
                }
            }
        }
    }
}
