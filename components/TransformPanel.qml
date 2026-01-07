import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as Lucent

// Panel displaying unified transform properties (X, Y, Width, Height) for selected items
Item {
    id: root
    readonly property SystemPalette themePalette: Lucent.Themed.palette

    property var selectedItem: null

    // Check if the selected item supports bounding box editing
    readonly property bool hasEditableBounds: {
        if (!selectedItem)
            return false;
        var t = selectedItem.type;
        return t === "rectangle" || t === "ellipse" || t === "path" || t === "text";
    }

    // Check if selected item is effectively locked
    readonly property bool isLocked: (Lucent.SelectionManager.selectedItemIndex >= 0) && canvasModel && canvasModel.isEffectivelyLocked(Lucent.SelectionManager.selectedItemIndex)

    // Current bounding box from the model
    readonly property var currentBounds: {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx < 0 || !canvasModel)
            return null;
        return canvasModel.getBoundingBox(idx);
    }

    // Current transform - updated reactively via signal
    property var currentTransform: null

    function refreshTransform() {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx >= 0 && canvasModel) {
            currentTransform = canvasModel.getItemTransform(idx);
        } else {
            currentTransform = null;
        }
    }

    Connections {
        target: canvasModel
        function onItemTransformChanged(index) {
            if (index === Lucent.SelectionManager.selectedItemIndex) {
                root.refreshTransform();
            }
        }
    }

    Connections {
        target: Lucent.SelectionManager
        function onSelectedItemIndexChanged() {
            root.refreshTransform();
        }
    }

    Component.onCompleted: refreshTransform()

    // Controls are enabled only when an editable item is selected and not locked
    readonly property bool controlsEnabled: hasEditableBounds && !isLocked

    readonly property int labelSize: 10
    readonly property color labelColor: themePalette.text

    function updateBounds(property, value) {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx < 0 || !canvasModel || !currentBounds)
            return;

        var newBounds = {
            x: currentBounds.x,
            y: currentBounds.y,
            width: currentBounds.width,
            height: currentBounds.height
        };
        newBounds[property] = value;
        canvasModel.setBoundingBox(idx, newBounds);
    }

    function updateTransform(property, value) {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx < 0 || !canvasModel)
            return;

        var newTransform = currentTransform ? {
            translateX: currentTransform.translateX || 0,
            translateY: currentTransform.translateY || 0,
            rotate: currentTransform.rotate || 0,
            scaleX: currentTransform.scaleX || 1,
            scaleY: currentTransform.scaleY || 1
        } : {
            translateX: 0,
            translateY: 0,
            rotate: 0,
            scaleX: 1,
            scaleY: 1
        };
        newTransform[property] = value;
        canvasModel.setItemTransform(idx, newTransform);
    }

    ColumnLayout {
        anchors.fill: parent

        Label {
            text: qsTr("Transform")
            font.pixelSize: 12
            color: themePalette.text
            Layout.fillWidth: true
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: themePalette.mid
        }

        // Transform properties grid - always visible for consistent height
        // Row 1: X and Y, Row 2: Width and Height
        GridLayout {
            columns: 4
            rowSpacing: 4
            columnSpacing: 8
            Layout.fillWidth: true
            Layout.topMargin: 4
            enabled: root.controlsEnabled
            opacity: root.controlsEnabled ? 1.0 : 0.5

            // Row 1: X and Y
            Label {
                text: qsTr("X:")
                font.pixelSize: root.labelSize
                color: root.labelColor
            }
            SpinBox {
                from: -100000
                to: 100000
                value: root.currentBounds ? Math.round(root.currentBounds.x) : 0
                editable: true
                Layout.fillWidth: true
                onValueModified: root.updateBounds("x", value)
            }

            Label {
                text: qsTr("Y:")
                font.pixelSize: root.labelSize
                color: root.labelColor
            }
            SpinBox {
                from: -100000
                to: 100000
                value: root.currentBounds ? Math.round(root.currentBounds.y) : 0
                editable: true
                Layout.fillWidth: true
                onValueModified: root.updateBounds("y", value)
            }

            // Row 2: Width and Height
            Label {
                text: qsTr("W:")
                font.pixelSize: root.labelSize
                color: root.labelColor
            }
            SpinBox {
                from: 0
                to: 100000
                value: root.currentBounds ? Math.round(root.currentBounds.width) : 0
                editable: true
                Layout.fillWidth: true
                onValueModified: root.updateBounds("width", value)
            }

            Label {
                text: qsTr("H:")
                font.pixelSize: root.labelSize
                color: root.labelColor
            }
            SpinBox {
                from: 0
                to: 100000
                value: root.currentBounds ? Math.round(root.currentBounds.height) : 0
                editable: true
                Layout.fillWidth: true
                onValueModified: root.updateBounds("height", value)
            }

            // Row 3: Rotation with text input and slider
            Label {
                text: qsTr("R:")
                font.pixelSize: root.labelSize
                color: root.labelColor
            }
            TextField {
                id: rotationField
                text: root.currentTransform ? Math.round(root.currentTransform.rotate).toString() : "0"
                horizontalAlignment: TextInput.AlignHCenter
                Layout.preferredWidth: 45
                validator: IntValidator {
                    bottom: -360
                    top: 360
                }

                onEditingFinished: {
                    var val = parseInt(text) || 0;
                    val = Math.max(-360, Math.min(360, val));
                    root.updateTransform("rotate", val);
                }
            }
            Slider {
                id: rotationSlider
                from: -180
                to: 180
                value: root.currentTransform ? root.currentTransform.rotate : 0
                Layout.fillWidth: true
                Layout.columnSpan: 2

                onMoved: root.updateTransform("rotate", value)

                // Circular handle to match other sliders
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
        }

        Item {
            Layout.fillHeight: true
        }
    }
}
