// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

RowLayout {
    id: root

    // Edit mode: when true, we're editing a selected item instead of setting defaults
    property bool editMode: false
    property var selectedItem: null

    // Internal defaults for creation mode
    property real _defaultStrokeWidth: 0
    property color _defaultStrokeColor: Lucent.Themed.defaultStroke
    property real _defaultStrokeOpacity: 1.0
    property bool _defaultStrokeVisible: false
    property string _defaultStrokeCap: "butt"
    property string _defaultStrokeAlign: "center"
    property string _defaultStrokeOrder: "top"
    property color _defaultFillColor: Lucent.Themed.defaultFill
    property real _defaultFillOpacity: 1.0
    property real _defaultCornerRadius: 0
    property real _defaultCornerRadiusTL: 0
    property real _defaultCornerRadiusTR: 0
    property real _defaultCornerRadiusBR: 0
    property real _defaultCornerRadiusBL: 0
    property bool _singleRadiusMode: true

    // Helper to get fill appearance from selectedItem
    function _getFill() {
        if (!selectedItem || !selectedItem.appearances)
            return null;
        for (var i = 0; i < selectedItem.appearances.length; i++) {
            if (selectedItem.appearances[i].type === "fill")
                return selectedItem.appearances[i];
        }
        return null;
    }

    // Helper to get stroke appearance from selectedItem
    function _getStroke() {
        if (!selectedItem || !selectedItem.appearances)
            return null;
        for (var i = 0; i < selectedItem.appearances.length; i++) {
            if (selectedItem.appearances[i].type === "stroke")
                return selectedItem.appearances[i];
        }
        return null;
    }

    // Exposed properties: read from selectedItem in edit mode, defaults in creation mode
    readonly property real strokeWidth: {
        if (editMode) {
            var stroke = _getStroke();
            return stroke ? stroke.width : _defaultStrokeWidth;
        }
        return _defaultStrokeWidth;
    }
    readonly property color strokeColor: {
        if (editMode) {
            var stroke = _getStroke();
            return stroke ? stroke.color : _defaultStrokeColor;
        }
        return _defaultStrokeColor;
    }
    readonly property real strokeOpacity: {
        if (editMode) {
            var stroke = _getStroke();
            return stroke ? stroke.opacity : _defaultStrokeOpacity;
        }
        return _defaultStrokeOpacity;
    }
    readonly property bool strokeVisible: {
        if (editMode) {
            var stroke = _getStroke();
            return stroke ? (stroke.visible !== false) : _defaultStrokeVisible;
        }
        return _defaultStrokeVisible;
    }
    readonly property string strokeStyle: strokeVisible ? "solid" : "none"
    readonly property string strokeCap: {
        if (editMode) {
            var stroke = _getStroke();
            return stroke && stroke.cap ? stroke.cap : _defaultStrokeCap;
        }
        return _defaultStrokeCap;
    }
    readonly property string strokeAlign: {
        if (editMode) {
            var stroke = _getStroke();
            return stroke && stroke.align ? stroke.align : _defaultStrokeAlign;
        }
        return _defaultStrokeAlign;
    }
    readonly property string strokeOrder: {
        if (editMode) {
            var stroke = _getStroke();
            return stroke && stroke.order ? stroke.order : _defaultStrokeOrder;
        }
        return _defaultStrokeOrder;
    }

    readonly property color fillColor: {
        if (editMode) {
            var fill = _getFill();
            return fill ? fill.color : _defaultFillColor;
        }
        return _defaultFillColor;
    }
    readonly property real fillOpacity: {
        if (editMode) {
            var fill = _getFill();
            return fill ? fill.opacity : _defaultFillOpacity;
        }
        return _defaultFillOpacity;
    }
    readonly property real cornerRadius: {
        if (editMode && selectedItem && selectedItem.geometry) {
            return selectedItem.geometry.cornerRadius || 0;
        }
        return _defaultCornerRadius;
    }
    readonly property real cornerRadiusTL: {
        if (editMode && selectedItem && selectedItem.geometry) {
            return selectedItem.geometry.cornerRadiusTL || 0;
        }
        return _defaultCornerRadiusTL;
    }
    readonly property real cornerRadiusTR: {
        if (editMode && selectedItem && selectedItem.geometry) {
            return selectedItem.geometry.cornerRadiusTR || 0;
        }
        return _defaultCornerRadiusTR;
    }
    readonly property real cornerRadiusBR: {
        if (editMode && selectedItem && selectedItem.geometry) {
            return selectedItem.geometry.cornerRadiusBR || 0;
        }
        return _defaultCornerRadiusBR;
    }
    readonly property real cornerRadiusBL: {
        if (editMode && selectedItem && selectedItem.geometry) {
            return selectedItem.geometry.cornerRadiusBL || 0;
        }
        return _defaultCornerRadiusBL;
    }
    readonly property bool hasPerCornerRadius: {
        if (editMode && selectedItem && selectedItem.geometry) {
            var g = selectedItem.geometry;
            return g.cornerRadiusTL !== undefined || g.cornerRadiusTR !== undefined || g.cornerRadiusBR !== undefined || g.cornerRadiusBL !== undefined;
        }
        return !_singleRadiusMode;
    }
    readonly property bool singleRadiusMode: {
        if (editMode) {
            return !hasPerCornerRadius;
        }
        return _singleRadiusMode;
    }

    // Update helper: always updates defaults, and also updates selected item in edit mode
    function updateProperty(propName, value) {
        // Always update defaults so new shapes use the last-used settings
        if (propName === "strokeWidth")
            _defaultStrokeWidth = value;
        else if (propName === "strokeColor")
            _defaultStrokeColor = value;
        else if (propName === "strokeOpacity")
            _defaultStrokeOpacity = value;
        else if (propName === "strokeVisible")
            _defaultStrokeVisible = value;
        else if (propName === "strokeCap")
            _defaultStrokeCap = value;
        else if (propName === "strokeAlign")
            _defaultStrokeAlign = value;
        else if (propName === "strokeOrder")
            _defaultStrokeOrder = value;
        else if (propName === "fillColor")
            _defaultFillColor = value;
        else if (propName === "fillOpacity")
            _defaultFillOpacity = value;
        else if (propName === "cornerRadius")
            _defaultCornerRadius = value;
        else if (propName === "cornerRadiusTL")
            _defaultCornerRadiusTL = value;
        else if (propName === "cornerRadiusTR")
            _defaultCornerRadiusTR = value;
        else if (propName === "cornerRadiusBR")
            _defaultCornerRadiusBR = value;
        else if (propName === "cornerRadiusBL")
            _defaultCornerRadiusBL = value;

        // Also update selected item if in edit mode
        if (editMode && Lucent.SelectionManager.selectedItemIndex >= 0) {
            // Build updated appearances array
            var currentItem = selectedItem;
            if (!currentItem)
                return;

            var updatesAppearance = propName === "fillColor" || propName === "fillOpacity" || propName === "strokeWidth" || propName === "strokeColor" || propName === "strokeOpacity" || propName === "strokeVisible" || propName === "strokeCap" || propName === "strokeAlign" || propName === "strokeOrder";
            var updatesGeometry = propName === "cornerRadius" || propName === "cornerRadiusTL" || propName === "cornerRadiusTR" || propName === "cornerRadiusBR" || propName === "cornerRadiusBL";

            var newAppearances = currentItem.appearances;
            if (updatesAppearance) {
                newAppearances = [];
                for (var i = 0; i < currentItem.appearances.length; i++) {
                    var app = currentItem.appearances[i];
                    var updated = Object.assign({}, app);
                    if (app.type === "fill") {
                        if (propName === "fillColor")
                            updated.color = value;
                        else if (propName === "fillOpacity")
                            updated.opacity = value;
                    } else if (app.type === "stroke") {
                        if (propName === "strokeWidth")
                            updated.width = value;
                        else if (propName === "strokeColor")
                            updated.color = value;
                        else if (propName === "strokeOpacity")
                            updated.opacity = value;
                        else if (propName === "strokeVisible")
                            updated.visible = value;
                        else if (propName === "strokeCap")
                            updated.cap = value;
                        else if (propName === "strokeAlign")
                            updated.align = value;
                        else if (propName === "strokeOrder")
                            updated.order = value;
                    }
                    newAppearances.push(updated);
                }
            }

            var newGeometry = currentItem.geometry;
            if (updatesGeometry) {
                newGeometry = Object.assign({}, currentItem.geometry);
                if (propName === "cornerRadius")
                    newGeometry.cornerRadius = value;
                else if (propName === "cornerRadiusTL")
                    newGeometry.cornerRadiusTL = value > 0 ? value : undefined;
                else if (propName === "cornerRadiusTR")
                    newGeometry.cornerRadiusTR = value > 0 ? value : undefined;
                else if (propName === "cornerRadiusBR")
                    newGeometry.cornerRadiusBR = value > 0 ? value : undefined;
                else if (propName === "cornerRadiusBL")
                    newGeometry.cornerRadiusBL = value > 0 ? value : undefined;
            }

            canvasModel.updateItem(Lucent.SelectionManager.selectedItemIndex, {
                type: currentItem.type,
                geometry: newGeometry,
                appearances: newAppearances,
                name: currentItem.name,
                parentId: currentItem.parentId,
                visible: currentItem.visible,
                locked: currentItem.locked
            });
        }
    }

    Layout.fillHeight: true
    Layout.alignment: Qt.AlignVCenter
    spacing: 6

    Label {
        text: qsTr("Fill:")
        font.pixelSize: 12
        Layout.alignment: Qt.AlignVCenter
    }

    Lucent.ColorPickerButton {
        color: root.fillColor
        colorOpacity: root.fillOpacity
        dialogTitle: qsTr("Choose Fill Color")
        onDialogOpened: canvasModel.beginTransaction()
        onDialogClosed: canvasModel.endTransaction()
        onColorPreview: previewColor => root.updateProperty("fillColor", previewColor.toString())
        onOpacityPreview: previewOpacity => root.updateProperty("fillOpacity", previewOpacity)
        onColorPicked: newColor => root.updateProperty("fillColor", newColor.toString())
        onOpacityPicked: newOpacity => root.updateProperty("fillOpacity", newOpacity)
    }

    ToolSeparator {
        contentItem: Rectangle {
            implicitWidth: 1
            implicitHeight: 16
            color: Lucent.Themed.palette.mid
        }
    }

    Lucent.StrokeEditorButton {
        strokeWidth: root.strokeWidth
        strokeColor: root.strokeColor
        strokeStyle: root.strokeStyle
        strokeCap: root.strokeCap
        strokeAlign: root.strokeAlign
        strokeOrder: root.strokeOrder
        onWidthEdited: newWidth => root.updateProperty("strokeWidth", newWidth)
        onWidthCommitted: newWidth => root.updateProperty("strokeWidth", newWidth)
        onStyleChanged: newStyle => root.updateProperty("strokeVisible", newStyle === "solid")
        onCapChanged: newCap => root.updateProperty("strokeCap", newCap)
        onAlignChanged: newAlign => root.updateProperty("strokeAlign", newAlign)
        onOrderChanged: newOrder => root.updateProperty("strokeOrder", newOrder)
        onPanelOpened: canvasModel.beginTransaction()
        onPanelClosed: canvasModel.endTransaction()
    }

    Lucent.ColorPickerButton {
        color: root.strokeColor
        colorOpacity: root.strokeOpacity
        dialogTitle: qsTr("Choose Stroke Color")
        onDialogOpened: canvasModel.beginTransaction()
        onDialogClosed: canvasModel.endTransaction()
        onColorPreview: previewColor => root.updateProperty("strokeColor", previewColor.toString())
        onOpacityPreview: previewOpacity => root.updateProperty("strokeOpacity", previewOpacity)
        onColorPicked: newColor => root.updateProperty("strokeColor", newColor.toString())
        onOpacityPicked: newOpacity => root.updateProperty("strokeOpacity", newOpacity)
    }

    ToolSeparator {
        contentItem: Rectangle {
            implicitWidth: 1
            implicitHeight: 16
            color: Lucent.Themed.palette.mid
        }
    }

    Label {
        text: qsTr("Corner:")
        font.pixelSize: 12
        Layout.alignment: Qt.AlignVCenter
    }

    CheckBox {
        id: singleRadiusCheckbox
        text: qsTr("Single Radius")
        font.pixelSize: 12
        checked: root.singleRadiusMode
        Layout.alignment: Qt.AlignVCenter

        onToggled: {
            root._singleRadiusMode = checked;
            if (checked && editMode) {
                // Switching to single mode: use TL value as uniform, clear per-corner
                var tlVal = root.cornerRadiusTL || root.cornerRadius || 0;
                root.updateProperty("cornerRadius", tlVal);
                root.updateProperty("cornerRadiusTL", 0);
                root.updateProperty("cornerRadiusTR", 0);
                root.updateProperty("cornerRadiusBR", 0);
                root.updateProperty("cornerRadiusBL", 0);
            } else if (!checked && editMode) {
                // Switching to per-corner mode: initialize all corners with current uniform value
                var uniformVal = root.cornerRadius || 25;
                root.updateProperty("cornerRadiusTL", uniformVal);
                root.updateProperty("cornerRadiusTR", uniformVal);
                root.updateProperty("cornerRadiusBR", uniformVal);
                root.updateProperty("cornerRadiusBL", uniformVal);
                root.updateProperty("cornerRadius", 0);
            } else if (!checked) {
                // Creation mode: initialize defaults
                root._defaultCornerRadiusTL = root._defaultCornerRadius || 25;
                root._defaultCornerRadiusTR = root._defaultCornerRadius || 25;
                root._defaultCornerRadiusBR = root._defaultCornerRadius || 25;
                root._defaultCornerRadiusBL = root._defaultCornerRadius || 25;
            }
        }
    }

    // Single radius controls (visible when singleRadiusMode is true)
    ComboBox {
        id: cornerTypeCombo
        visible: root.singleRadiusMode
        Layout.preferredWidth: 90
        Layout.preferredHeight: Lucent.Styles.height.md
        Layout.alignment: Qt.AlignVCenter
        model: ["None", "Rounded"]
        currentIndex: root.cornerRadius > 0 ? 1 : 0

        onActivated: index => {
            if (index === 0) {
                root.updateProperty("cornerRadius", 0);
            } else {
                root.updateProperty("cornerRadius", 25);
            }
        }

        background: Rectangle {
            color: palette.base
            border.color: cornerTypeCombo.activeFocus ? palette.highlight : palette.mid
            border.width: 1
            radius: Lucent.Styles.rad.sm
        }

        contentItem: Text {
            text: cornerTypeCombo.displayText
            color: palette.text
            font.pixelSize: 12
            verticalAlignment: Text.AlignVCenter
            leftPadding: 6
            elide: Text.ElideRight
        }
    }

    Item {
        id: cornerRadiusContainer
        visible: root.singleRadiusMode && root.cornerRadius > 0
        Layout.preferredWidth: 50
        Layout.preferredHeight: Lucent.Styles.height.md
        Layout.alignment: Qt.AlignVCenter

        TextField {
            id: cornerRadiusField
            anchors.fill: parent
            horizontalAlignment: Text.AlignHCenter
            text: Math.round(root.cornerRadius).toString()
            validator: IntValidator {
                bottom: 1
                top: 50
            }

            onActiveFocusChanged: {
                if (activeFocus) {
                    selectAll();
                    cornerSliderPopup.open();
                }
            }

            onEditingFinished: {
                var val = parseInt(text);
                if (!isNaN(val) && val >= 1 && val <= 50) {
                    root.updateProperty("cornerRadius", val);
                } else {
                    text = Math.round(root.cornerRadius).toString();
                }
            }

            background: Rectangle {
                color: palette.base
                border.color: cornerRadiusField.activeFocus ? palette.highlight : palette.mid
                border.width: 1
                radius: Lucent.Styles.rad.sm
            }
        }

        Popup {
            id: cornerSliderPopup
            x: -75
            y: cornerRadiusContainer.height + 4
            width: 200
            padding: 12
            closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

            onOpened: cornerSlider.value = root.cornerRadius

            background: Rectangle {
                color: Lucent.Themed.palette.window
                border.color: Lucent.Themed.palette.mid
                border.width: 1
                radius: Lucent.Styles.rad.md
            }

            contentItem: Slider {
                id: cornerSlider
                from: 1
                to: 50
                stepSize: 1

                onPressedChanged: {
                    if (pressed)
                        canvasModel.beginTransaction();
                    else
                        canvasModel.endTransaction();
                }

                onMoved: {
                    cornerRadiusField.text = Math.round(value).toString();
                    root.updateProperty("cornerRadius", Math.round(value));
                }

                handle: Rectangle {
                    x: cornerSlider.leftPadding + cornerSlider.visualPosition * (cornerSlider.availableWidth - width)
                    y: cornerSlider.topPadding + cornerSlider.availableHeight / 2 - height / 2
                    width: 16
                    height: 16
                    radius: 8
                    color: cornerSlider.pressed ? Lucent.Themed.palette.highlight : Lucent.Themed.palette.button
                    border.color: Lucent.Themed.palette.mid
                    border.width: 1
                }
            }
        }
    }

    Label {
        visible: root.singleRadiusMode && root.cornerRadius > 0
        text: "%"
        font.pixelSize: 12
        Layout.alignment: Qt.AlignVCenter
    }

    // Per-corner controls (visible when singleRadiusMode is false)
    ListModel {
        id: cornerRadiusModel
        ListElement {
            label: "TL:"
            prop: "cornerRadiusTL"
        }
        ListElement {
            label: "TR:"
            prop: "cornerRadiusTR"
        }
        ListElement {
            label: "BR:"
            prop: "cornerRadiusBR"
        }
        ListElement {
            label: "BL:"
            prop: "cornerRadiusBL"
        }
    }

    Repeater {
        model: root.singleRadiusMode ? null : cornerRadiusModel

        delegate: RowLayout {
            spacing: 4
            Layout.leftMargin: index > 0 ? 8 : 0

            property string cornerProp: prop
            property real cornerValue: root[cornerProp] || 0

            Label {
                text: label
                font.pixelSize: 12
                Layout.alignment: Qt.AlignVCenter
            }

            ComboBox {
                id: cornerCombo
                Layout.preferredWidth: 80
                Layout.preferredHeight: Lucent.Styles.height.md
                Layout.alignment: Qt.AlignVCenter
                model: ["None", "Rounded"]
                currentIndex: cornerValue > 0 ? 1 : 0

                onActivated: index => {
                    if (index === 0) {
                        root.updateProperty(cornerProp, 0);
                    } else {
                        root.updateProperty(cornerProp, 25);
                    }
                }

                background: Rectangle {
                    color: palette.base
                    border.color: cornerCombo.activeFocus ? palette.highlight : palette.mid
                    border.width: 1
                    radius: Lucent.Styles.rad.sm
                }

                contentItem: Text {
                    text: cornerCombo.displayText
                    color: palette.text
                    font.pixelSize: 12
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: 6
                    elide: Text.ElideRight
                }
            }

            Item {
                visible: cornerValue > 0
                Layout.preferredWidth: 40
                Layout.preferredHeight: Lucent.Styles.height.md
                Layout.alignment: Qt.AlignVCenter

                TextField {
                    id: cornerField
                    anchors.fill: parent
                    horizontalAlignment: Text.AlignHCenter
                    text: Math.round(cornerValue).toString()
                    font.pixelSize: 12
                    validator: IntValidator {
                        bottom: 1
                        top: 50
                    }

                    onActiveFocusChanged: {
                        if (activeFocus) {
                            selectAll();
                            cornerPopup.open();
                        }
                    }

                    onEditingFinished: {
                        var val = parseInt(text);
                        if (!isNaN(val) && val >= 1 && val <= 50) {
                            root.updateProperty(cornerProp, val);
                        } else {
                            text = Math.round(cornerValue).toString();
                        }
                    }

                    background: Rectangle {
                        color: palette.base
                        border.color: cornerField.activeFocus ? palette.highlight : palette.mid
                        border.width: 1
                        radius: Lucent.Styles.rad.sm
                    }
                }

                Popup {
                    id: cornerPopup
                    x: -75
                    y: parent.height + 4
                    width: 200
                    padding: 12
                    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

                    onOpened: perCornerSlider.value = cornerValue

                    background: Rectangle {
                        color: Lucent.Themed.palette.window
                        border.color: Lucent.Themed.palette.mid
                        border.width: 1
                        radius: Lucent.Styles.rad.md
                    }

                    contentItem: Slider {
                        id: perCornerSlider
                        from: 1
                        to: 50
                        stepSize: 1

                        onPressedChanged: {
                            if (pressed)
                                canvasModel.beginTransaction();
                            else
                                canvasModel.endTransaction();
                        }

                        onMoved: {
                            cornerField.text = Math.round(value).toString();
                            root.updateProperty(cornerProp, Math.round(value));
                        }

                        handle: Rectangle {
                            x: perCornerSlider.leftPadding + perCornerSlider.visualPosition * (perCornerSlider.availableWidth - width)
                            y: perCornerSlider.topPadding + perCornerSlider.availableHeight / 2 - height / 2
                            width: 16
                            height: 16
                            radius: 8
                            color: perCornerSlider.pressed ? Lucent.Themed.palette.highlight : Lucent.Themed.palette.button
                            border.color: Lucent.Themed.palette.mid
                            border.width: 1
                        }
                    }
                }
            }
        }
    }

    Label {
        visible: !root.singleRadiusMode
        text: "%"
        font.pixelSize: 12
        Layout.alignment: Qt.AlignVCenter
    }
}
