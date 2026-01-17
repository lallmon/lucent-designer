// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

RowLayout {
    id: root

    // Edit mode: when true, we're editing a selected path instead of setting defaults
    property bool editMode: false
    property var selectedItem: null

    // Internal defaults for creation mode
    property real _defaultStrokeWidth: 2
    property color _defaultStrokeColor: Lucent.Themed.defaultStroke
    property real _defaultStrokeOpacity: 1.0
    property bool _defaultStrokeVisible: true
    property string _defaultStrokeCap: "butt"
    property string _defaultStrokeAlign: "center"
    property string _defaultStrokeOrder: "top"
    property bool _defaultStrokeScaleWithObject: false
    property color _defaultFillColor: Lucent.Themed.defaultFill
    property real _defaultFillOpacity: 0.0

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
    readonly property bool strokeScaleWithObject: {
        if (editMode) {
            var stroke = _getStroke();
            return stroke ? (stroke.scaleWithObject === true) : _defaultStrokeScaleWithObject;
        }
        return _defaultStrokeScaleWithObject;
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
        else if (propName === "strokeScaleWithObject")
            _defaultStrokeScaleWithObject = value;
        else if (propName === "fillColor")
            _defaultFillColor = value;
        else if (propName === "fillOpacity")
            _defaultFillOpacity = value;

        // Also update selected item if in edit mode
        if (editMode && Lucent.SelectionManager.selectedItemIndex >= 0) {
            // Build updated appearances array
            var currentItem = selectedItem;
            if (!currentItem)
                return;

            var newAppearances = [];
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
                    else if (propName === "strokeScaleWithObject")
                        updated.scaleWithObject = value;
                }
                newAppearances.push(updated);
            }

            canvasModel.updateItem(Lucent.SelectionManager.selectedItemIndex, {
                type: currentItem.type,
                geometry: currentItem.geometry,
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
        strokeScaleWithObject: root.strokeScaleWithObject
        onWidthEdited: newWidth => root.updateProperty("strokeWidth", newWidth)
        onWidthCommitted: newWidth => root.updateProperty("strokeWidth", newWidth)
        onStyleChanged: newStyle => root.updateProperty("strokeVisible", newStyle === "solid")
        onCapChanged: newCap => root.updateProperty("strokeCap", newCap)
        onAlignChanged: newAlign => root.updateProperty("strokeAlign", newAlign)
        onOrderChanged: newOrder => root.updateProperty("strokeOrder", newOrder)
        onScaleWithObjectChanged: newValue => root.updateProperty("strokeScaleWithObject", newValue)
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
}
