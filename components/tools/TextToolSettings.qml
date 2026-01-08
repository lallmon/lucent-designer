import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

RowLayout {
    id: root

    // Edit mode: when true, we're editing a selected text item instead of setting defaults
    property bool editMode: false
    property var selectedItem: null

    // Internal defaults for creation mode
    property string _defaultFontFamily: "Sans Serif"
    property real _defaultFontSize: 16
    property color _defaultTextColor: Lucent.Themed.palette.text
    property real _defaultTextOpacity: 1.0

    // Exposed properties: read from selectedItem in edit mode, defaults in creation mode
    readonly property string fontFamily: editMode && selectedItem ? selectedItem.fontFamily : _defaultFontFamily
    readonly property real fontSize: editMode && selectedItem ? selectedItem.fontSize : _defaultFontSize
    readonly property color textColor: editMode && selectedItem ? selectedItem.textColor : _defaultTextColor
    readonly property real textOpacity: editMode && selectedItem ? selectedItem.textOpacity : _defaultTextOpacity

    // Update helper: always updates defaults, and also updates selected item in edit mode
    function updateProperty(propName, value) {
        // Always update defaults so new shapes use the last-used settings
        if (propName === "fontFamily")
            _defaultFontFamily = value;
        else if (propName === "fontSize")
            _defaultFontSize = value;
        else if (propName === "textColor")
            _defaultTextColor = value;
        else if (propName === "textOpacity")
            _defaultTextOpacity = value;

        // Also update selected item if in edit mode
        if (editMode && Lucent.SelectionManager.selectedItemIndex >= 0) {
            var props = {};
            props[propName] = value;
            canvasModel.updateItem(Lucent.SelectionManager.selectedItemIndex, props);
        }
    }

    Layout.fillHeight: true
    Layout.alignment: Qt.AlignVCenter
    spacing: 6

    Label {
        text: qsTr("Font:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    ComboBox {
        id: fontFamilyCombo
        Layout.preferredWidth: 160
        Layout.preferredHeight: Lucent.Styles.height.md
        Layout.alignment: Qt.AlignVCenter
        model: fontProvider ? fontProvider.fonts : []
        currentIndex: fontProvider ? fontProvider.indexOf(root.fontFamily) : 0

        onActivated: index => {
            if (index >= 0 && model[index]) {
                root.updateProperty("fontFamily", model[index]);
            }
        }

        // Real-time preview while scrolling through dropdown
        onHighlightedIndexChanged: {
            if (popup.visible && highlightedIndex >= 0 && model[highlightedIndex]) {
                root._defaultFontFamily = model[highlightedIndex];
            }
        }

        Component.onCompleted: {
            if (fontProvider && (!root._defaultFontFamily || root._defaultFontFamily === "Sans Serif")) {
                root._defaultFontFamily = fontProvider.defaultFont();
            }
        }

        background: Rectangle {
            color: palette.base
            border.color: fontFamilyCombo.activeFocus ? palette.highlight : palette.mid
            border.width: 1
            radius: Lucent.Styles.rad.sm
        }

        contentItem: Text {
            text: fontFamilyCombo.displayText
            color: palette.text
            font.pixelSize: 11
            verticalAlignment: Text.AlignVCenter
            leftPadding: 6
            elide: Text.ElideRight
        }
    }

    ToolSeparator {}

    Label {
        text: qsTr("Size:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    ComboBox {
        id: fontSizeCombo
        Layout.preferredWidth: 70
        Layout.preferredHeight: Lucent.Styles.height.md
        Layout.alignment: Qt.AlignVCenter
        editable: true
        model: [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 64, 72, 96, 128]

        currentIndex: {
            var idx = model.indexOf(Math.round(root.fontSize));
            return idx >= 0 ? idx : -1;
        }

        Component.onCompleted: {
            editText = Math.round(root.fontSize).toString();
        }

        onActivated: index => {
            if (index >= 0) {
                root.updateProperty("fontSize", model[index]);
            }
        }

        // Real-time preview while scrolling through dropdown
        onHighlightedIndexChanged: {
            if (popup.visible && highlightedIndex >= 0) {
                root._defaultFontSize = model[highlightedIndex];
            }
        }

        onAccepted: {
            var value = parseFloat(editText);
            if (!isNaN(value) && value >= 8 && value <= 200) {
                root.updateProperty("fontSize", Math.round(value));
            }
            editText = Math.round(root.fontSize).toString();
        }

        Connections {
            target: root
            function onFontSizeChanged() {
                if (!fontSizeCombo.activeFocus) {
                    fontSizeCombo.editText = Math.round(root.fontSize).toString();
                }
            }
        }

        validator: IntValidator {
            bottom: 8
            top: 200
        }

        background: Rectangle {
            color: palette.base
            border.color: fontSizeCombo.activeFocus ? palette.highlight : palette.mid
            border.width: 1
            radius: Lucent.Styles.rad.sm
        }

        contentItem: TextInput {
            text: fontSizeCombo.editText
            font.pixelSize: 11
            color: palette.text
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            leftPadding: 6
            rightPadding: 6
            selectByMouse: true
            validator: fontSizeCombo.validator

            onTextChanged: fontSizeCombo.editText = text
            onAccepted: fontSizeCombo.accepted()
        }
    }

    Label {
        text: qsTr("pt")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    ToolSeparator {}

    Label {
        text: qsTr("Color:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    Lucent.ColorPickerButton {
        color: root.textColor
        colorOpacity: root.textOpacity
        dialogTitle: qsTr("Choose Text Color")
        onColorPreview: previewColor => root.updateProperty("textColor", previewColor.toString())
        onColorPicked: newColor => root.updateProperty("textColor", newColor.toString())
    }

    Label {
        text: qsTr("Opacity:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    Lucent.OpacitySlider {
        opacityValue: root.textOpacity
        onValueUpdated: newOpacity => root.updateProperty("textOpacity", newOpacity)
    }

    Lucent.LabeledNumericField {
        labelText: ""
        value: Math.round(root.textOpacity * 100)
        minimum: 0
        maximum: 100
        decimals: 0
        fieldWidth: 35
        suffix: qsTr("%")
        onCommitted: newValue => root.updateProperty("textOpacity", newValue / 100.0)
    }
}
