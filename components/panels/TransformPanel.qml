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

    readonly property bool hasEditableBounds: selectedItem && ["rectangle", "ellipse", "path", "text", "artboard"].includes(selectedItem.type)
    readonly property bool isArtboard: selectedItem && selectedItem.type === "artboard"

    readonly property bool isLocked: hasValidSelection && canvasModel.isEffectivelyLocked(selectedIndex)

    property var currentTransform: null
    readonly property bool hasUnitSettings: typeof unitSettings !== "undefined" && unitSettings !== null
    property bool hasFlattenableTransform: false
    readonly property bool hasTransformControls: !isArtboard && currentTransform !== null

    function refreshTransform() {
        if (hasValidSelection) {
            if (isArtboard) {
                currentTransform = null;
                var bounds = canvasModel.getBoundingBox(selectedIndex);
                displayedX = bounds ? bounds.x : 0;
                displayedY = bounds ? bounds.y : 0;
                displayedWidth = bounds ? bounds.width : 0;
                displayedHeight = bounds ? bounds.height : 0;
            } else {
                currentTransform = canvasModel.getItemTransform(selectedIndex);
                var pos = canvasModel.getDisplayedPosition(selectedIndex);
                displayedX = pos ? pos.x : 0;
                displayedY = pos ? pos.y : 0;
                var size = canvasModel.getDisplayedSize(selectedIndex);
                displayedWidth = size ? size.width : 0;
                displayedHeight = size ? size.height : 0;
            }
        } else {
            currentTransform = null;
            displayedX = 0;
            displayedY = 0;
            displayedWidth = 0;
            displayedHeight = 0;
        }
        hasFlattenableTransform = root.controlsEnabled && root.hasTransformControls && canvasModel && canvasModel.hasNonIdentityTransform(root.selectedIndex);
        if (widthField && !widthField.activeFocus) {
            widthField.text = (hasUnitSettings ? unitSettings.canvasToDisplay(displayedWidth) : displayedWidth).toFixed(unitPrecision);
        }
        if (heightField && !heightField.activeFocus) {
            heightField.text = (hasUnitSettings ? unitSettings.canvasToDisplay(displayedHeight) : displayedHeight).toFixed(unitPrecision);
        }
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
        target: historyManager
        function onUndoStackChanged() {
            root.refreshTransform();
        }
        function onRedoStackChanged() {
            root.refreshTransform();
        }
    }

    Connections {
        target: Lucent.SelectionManager
        function onSelectedItemIndexChanged() {
            root.refreshTransform();
        }
        function onSelectedItemChanged() {
            root.refreshTransform();
        }
    }

    Connections {
        target: unitSettings
        ignoreUnknownSignals: true
        function onDisplayUnitChanged() {
            root.refreshTransform();
        }
        function onPreviewDPIChanged() {
            root.refreshTransform();
        }
    }

    Component.onCompleted: refreshTransform()

    readonly property bool controlsEnabled: hasEditableBounds && !isLocked

    readonly property int labelSize: 10
    readonly property color labelColor: themePalette.text

    property bool proportionalScale: false

    // Displayed position and size from model (updated in refreshTransform)
    property real displayedX: 0
    property real displayedY: 0
    property real displayedWidth: 0
    property real displayedHeight: 0

    readonly property int unitPrecision: {
        if (!hasUnitSettings)
            return 1;
        switch (unitSettings.displayUnit) {
        case "in":
            return 3;
        case "mm":
            return 2;
        case "pt":
            return 2;
        default:
            return 1;
        }
    }

    // Include displayUnit/previewDPI to ensure bindings update when units change.
    readonly property real unitX: hasUnitSettings ? unitSettings.canvasToDisplay(displayedX) : displayedX
    readonly property real unitY: hasUnitSettings ? unitSettings.canvasToDisplay(displayedY) : displayedY
    readonly property real unitWidth: hasUnitSettings ? unitSettings.canvasToDisplay(displayedWidth) : displayedWidth
    readonly property real unitHeight: hasUnitSettings ? unitSettings.canvasToDisplay(displayedHeight) : displayedHeight

    // Transform state for rotation display and origin buttons
    readonly property real currentRotation: currentTransform ? (currentTransform.rotate ?? 0) : 0
    readonly property real currentOriginX: currentTransform ? (currentTransform.originX ?? 0) : 0
    readonly property real currentOriginY: currentTransform ? (currentTransform.originY ?? 0) : 0
    readonly property real originSnapTolerance: 0.02
    readonly property bool hasPresetOrigin: _isPresetOrigin(currentOriginX, currentOriginY)

    function _snapOrigin(value) {
        var targets = [0, 0.5, 1];
        for (var i = 0; i < targets.length; i++) {
            if (Math.abs(value - targets[i]) <= originSnapTolerance)
                return targets[i];
        }
        return value;
    }

    function _isPresetOrigin(x, y) {
        var targets = [0, 0.5, 1];
        for (var row = 0; row < targets.length; row++) {
            for (var col = 0; col < targets.length; col++) {
                if (Math.abs(x - targets[col]) <= originSnapTolerance && Math.abs(y - targets[row]) <= originSnapTolerance) {
                    return true;
                }
            }
        }
        return false;
    }

    implicitHeight: contentLayout.implicitHeight

    ColumnLayout {
        id: contentLayout
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 16
            Layout.bottomMargin: 16
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
                enabled: root.hasTransformControls
                opacity: root.hasTransformControls ? 1.0 : 0.4

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
                        checked: root._snapOrigin(root.currentOriginX) === modelData.ox && root._snapOrigin(root.currentOriginY) === modelData.oy
                        ButtonGroup.group: originGroup

                        onClicked: canvasModel.setItemOrigin(root.selectedIndex, modelData.ox, modelData.oy)

                        background: Rectangle {
                            color: parent.checked ? root.themePalette.highlight : root.themePalette.button
                            border.color: root.hasPresetOrigin ? root.themePalette.mid : "#ffffff"
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

                RowLayout {
                    spacing: 4
                    Layout.fillWidth: true
                    Label {
                        text: qsTr("X:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    TextField {
                        id: xField
                        Layout.fillWidth: true
                        implicitHeight: 24
                        inputMethodHints: Qt.ImhFormattedNumbersOnly
                        text: (root.hasUnitSettings ? unitSettings.canvasToDisplay(root.displayedX) : root.displayedX).toFixed(root.unitPrecision)

                        onActiveFocusChanged: if (activeFocus)
                            selectAll()
                        KeyNavigation.tab: yField
                        KeyNavigation.backtab: rotationField

                        onEditingFinished: {
                            var val = parseFloat(text);
                            if (isFinite(val)) {
                                var target = root.hasUnitSettings ? unitSettings.displayToCanvas(val) : val;
                                if (root.isArtboard) {
                                    var bounds = canvasModel.getBoundingBox(root.selectedIndex);
                                    if (bounds) {
                                        canvasModel.setBoundingBox(root.selectedIndex, {
                                            x: target,
                                            y: bounds.y,
                                            width: bounds.width,
                                            height: bounds.height
                                        });
                                    }
                                } else {
                                    canvasModel.setItemPosition(root.selectedIndex, "x", target);
                                }
                                appController.focusCanvas();
                            }
                            text = (root.hasUnitSettings ? unitSettings.canvasToDisplay(root.displayedX) : root.displayedX).toFixed(root.unitPrecision);
                        }
                    }
                }

                RowLayout {
                    spacing: 4
                    Layout.fillWidth: true
                    Label {
                        text: qsTr("Y:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    TextField {
                        id: yField
                        Layout.fillWidth: true
                        implicitHeight: 24
                        inputMethodHints: Qt.ImhFormattedNumbersOnly
                        text: (root.hasUnitSettings ? unitSettings.canvasToDisplay(root.displayedY) : root.displayedY).toFixed(root.unitPrecision)

                        onActiveFocusChanged: if (activeFocus)
                            selectAll()
                        KeyNavigation.tab: widthField
                        KeyNavigation.backtab: xField

                        onEditingFinished: {
                            var val = parseFloat(text);
                            if (isFinite(val)) {
                                var target = root.hasUnitSettings ? unitSettings.displayToCanvas(val) : val;
                                if (root.isArtboard) {
                                    var bounds = canvasModel.getBoundingBox(root.selectedIndex);
                                    if (bounds) {
                                        canvasModel.setBoundingBox(root.selectedIndex, {
                                            x: bounds.x,
                                            y: target,
                                            width: bounds.width,
                                            height: bounds.height
                                        });
                                    }
                                } else {
                                    canvasModel.setItemPosition(root.selectedIndex, "y", target);
                                }
                                appController.focusCanvas();
                            }
                            text = (root.hasUnitSettings ? unitSettings.canvasToDisplay(root.displayedY) : root.displayedY).toFixed(root.unitPrecision);
                        }
                    }
                }
            }

            Lucent.VerticalDivider {}

            ColumnLayout {
                spacing: 2
                Layout.fillWidth: true

                RowLayout {
                    spacing: 4
                    Layout.fillWidth: true
                    Label {
                        text: qsTr("W:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    TextField {
                        id: widthField
                        Layout.fillWidth: true
                        implicitHeight: 24
                        inputMethodHints: Qt.ImhFormattedNumbersOnly
                        text: (root.hasUnitSettings ? unitSettings.canvasToDisplay(root.displayedWidth) : root.displayedWidth).toFixed(root.unitPrecision)

                        onActiveFocusChanged: if (activeFocus)
                            selectAll()
                        KeyNavigation.tab: heightField
                        KeyNavigation.backtab: yField

                        onEditingFinished: {
                            var val = parseFloat(text);
                            if (isFinite(val)) {
                                var target = root.hasUnitSettings ? unitSettings.displayToCanvas(val) : val;
                                if (root.isArtboard) {
                                    var bounds = canvasModel.getBoundingBox(root.selectedIndex);
                                    if (bounds) {
                                        var newWidth = Math.max(1, target);
                                        var newHeight = bounds.height;
                                        if (root.proportionalScale && bounds.width > 0) {
                                            newHeight = bounds.height * (newWidth / bounds.width);
                                        }
                                        canvasModel.setBoundingBox(root.selectedIndex, {
                                            x: bounds.x,
                                            y: bounds.y,
                                            width: newWidth,
                                            height: newHeight
                                        });
                                    }
                                } else {
                                    canvasModel.setDisplayedSize(root.selectedIndex, "width", target, root.proportionalScale);
                                }
                                appController.focusCanvas();
                            }
                            text = root.unitWidth.toFixed(root.unitPrecision);
                        }
                    }
                }

                RowLayout {
                    spacing: 4
                    Layout.fillWidth: true
                    Label {
                        text: qsTr("H:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    TextField {
                        id: heightField
                        Layout.fillWidth: true
                        implicitHeight: 24
                        inputMethodHints: Qt.ImhFormattedNumbersOnly
                        text: (root.hasUnitSettings ? unitSettings.canvasToDisplay(root.displayedHeight) : root.displayedHeight).toFixed(root.unitPrecision)

                        onActiveFocusChanged: if (activeFocus)
                            selectAll()
                        KeyNavigation.tab: rotationField
                        KeyNavigation.backtab: widthField

                        onEditingFinished: {
                            var val = parseFloat(text);
                            if (isFinite(val)) {
                                var target = root.hasUnitSettings ? unitSettings.displayToCanvas(val) : val;
                                if (root.isArtboard) {
                                    var bounds = canvasModel.getBoundingBox(root.selectedIndex);
                                    if (bounds) {
                                        var newHeight = Math.max(1, target);
                                        var newWidth = bounds.width;
                                        if (root.proportionalScale && bounds.height > 0) {
                                            newWidth = bounds.width * (newHeight / bounds.height);
                                        }
                                        canvasModel.setBoundingBox(root.selectedIndex, {
                                            x: bounds.x,
                                            y: bounds.y,
                                            width: newWidth,
                                            height: newHeight
                                        });
                                    }
                                } else {
                                    canvasModel.setDisplayedSize(root.selectedIndex, "height", target, root.proportionalScale);
                                }
                                appController.focusCanvas();
                            }
                            text = root.unitHeight.toFixed(root.unitPrecision);
                        }
                    }
                }
            }

            // Unit label column for both W/H
            ColumnLayout {
                spacing: 0
                Layout.alignment: Qt.AlignVCenter
                Label {
                    text: root.hasUnitSettings ? unitSettings.displayUnit : "px"
                    font.pixelSize: 12
                    color: root.labelColor
                    Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
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
                        text: proportionalToggle.checked ? qsTr("Free resize") : qsTr("Constrain proportions")
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
            enabled: root.controlsEnabled && root.hasTransformControls
            opacity: (root.controlsEnabled && root.hasTransformControls) ? 1.0 : 0.5

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

                onActiveFocusChanged: if (activeFocus)
                    selectAll()
                KeyNavigation.tab: xField
                KeyNavigation.backtab: heightField

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
                    canvasModel.rotateItem(root.selectedIndex, val);
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

                onMoved: canvasModel.rotateItem(root.selectedIndex, value)

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
                enabled: hasFlattenableTransform
                onClicked: {
                    if (hasFlattenableTransform && canvasModel) {
                        canvasModel.bakeTransform(root.selectedIndex);
                        appController.focusCanvas();
                    }
                }
            }
        }
    }
}
