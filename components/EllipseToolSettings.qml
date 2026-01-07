import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as Lucent

RowLayout {
    id: root

    // Edit mode: when true, we're editing a selected item instead of setting defaults
    property bool editMode: false
    property var selectedItem: null

    // Internal defaults for creation mode
    property real _defaultStrokeWidth: 0
    property color _defaultStrokeColor: Lucent.Themed.defaultStroke
    property real _defaultStrokeOpacity: 1.0
    property color _defaultFillColor: Lucent.Themed.defaultFill
    property real _defaultFillOpacity: 1.0

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

    Lucent.LabeledNumericField {
        labelText: qsTr("Stroke Width:")
        value: root.strokeWidth
        minimum: 0
        maximum: 100.0
        decimals: 1
        suffix: qsTr("pt")
        onCommitted: newValue => root.updateProperty("strokeWidth", newValue)
    }

    ToolSeparator {}

    Label {
        text: qsTr("Stroke Color:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    Lucent.ColorPickerButton {
        color: root.strokeColor
        colorOpacity: root.strokeOpacity
        dialogTitle: qsTr("Choose Stroke Color")
        onColorPreview: previewColor => root.updateProperty("strokeColor", previewColor.toString())
        onColorPicked: newColor => root.updateProperty("strokeColor", newColor.toString())
    }

    Label {
        text: qsTr("Opacity:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    Lucent.OpacitySlider {
        opacityValue: root.strokeOpacity
        onValueUpdated: newOpacity => root.updateProperty("strokeOpacity", newOpacity)
    }

    Lucent.LabeledNumericField {
        labelText: ""
        value: Math.round(root.strokeOpacity * 100)
        minimum: 0
        maximum: 100
        decimals: 0
        fieldWidth: 35
        suffix: qsTr("%")
        onCommitted: newValue => root.updateProperty("strokeOpacity", newValue / 100.0)
    }

    ToolSeparator {}

    Label {
        text: qsTr("Fill Color:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    Lucent.ColorPickerButton {
        color: root.fillColor
        colorOpacity: root.fillOpacity
        dialogTitle: qsTr("Choose Fill Color")
        onColorPreview: previewColor => root.updateProperty("fillColor", previewColor.toString())
        onColorPicked: newColor => root.updateProperty("fillColor", newColor.toString())
    }

    Label {
        text: qsTr("Opacity:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    Lucent.OpacitySlider {
        opacityValue: root.fillOpacity
        onValueUpdated: newOpacity => root.updateProperty("fillOpacity", newOpacity)
    }

    Lucent.LabeledNumericField {
        labelText: ""
        value: Math.round(root.fillOpacity * 100)
        minimum: 0
        maximum: 100
        decimals: 0
        fieldWidth: 35
        suffix: qsTr("%")
        onCommitted: newValue => root.updateProperty("fillOpacity", newValue / 100.0)
    }
}
