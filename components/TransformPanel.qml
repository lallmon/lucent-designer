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

    // Computed canvas position: geometry origin point + translation
    readonly property real displayedX: {
        if (!currentBounds)
            return 0;
        var t = currentTransform;
        var originX = t ? (t.originX || 0) : 0;
        var translateX = t ? (t.translateX || 0) : 0;
        return currentBounds.x + currentBounds.width * originX + translateX;
    }

    readonly property real displayedY: {
        if (!currentBounds)
            return 0;
        var t = currentTransform;
        var originY = t ? (t.originY || 0) : 0;
        var translateY = t ? (t.translateY || 0) : 0;
        return currentBounds.y + currentBounds.height * originY + translateY;
    }

    // Update translation to achieve a desired canvas position for the origin point
    function updatePosition(axis, newValue) {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx < 0 || !canvasModel || !currentBounds)
            return;

        var t = currentTransform || {};
        var originX = t.originX || 0;
        var originY = t.originY || 0;

        var newTransform = {
            translateX: t.translateX || 0,
            translateY: t.translateY || 0,
            rotate: t.rotate || 0,
            scaleX: t.scaleX || 1,
            scaleY: t.scaleY || 1,
            originX: originX,
            originY: originY
        };

        if (axis === "x") {
            // newValue = geometry.x + geometry.width * originX + translateX
            // So: translateX = newValue - geometry.x - geometry.width * originX
            newTransform.translateX = newValue - currentBounds.x - currentBounds.width * originX;
        } else if (axis === "y") {
            newTransform.translateY = newValue - currentBounds.y - currentBounds.height * originY;
        }

        canvasModel.setItemTransform(idx, newTransform);
    }

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
            scaleY: currentTransform.scaleY || 1,
            originX: currentTransform.originX || 0,
            originY: currentTransform.originY || 0
        } : {
            translateX: 0,
            translateY: 0,
            rotate: 0,
            scaleX: 1,
            scaleY: 1,
            originX: 0,
            originY: 0
        };
        newTransform[property] = value;
        canvasModel.setItemTransform(idx, newTransform);
    }

    function setOrigin(newOx, newOy) {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx < 0 || !canvasModel)
            return;

        var bounds = canvasModel.getGeometryBounds(idx);
        if (!bounds)
            return;

        var oldOx = currentTransform ? (currentTransform.originX || 0) : 0;
        var oldOy = currentTransform ? (currentTransform.originY || 0) : 0;
        var rotation = currentTransform ? (currentTransform.rotate || 0) : 0;
        var oldTx = currentTransform ? (currentTransform.translateX || 0) : 0;
        var oldTy = currentTransform ? (currentTransform.translateY || 0) : 0;

        // Adjust translation to keep shape visually in place when origin changes
        var dx = (oldOx - newOx) * bounds.width;
        var dy = (oldOy - newOy) * bounds.height;
        var radians = rotation * Math.PI / 180;
        var cos = Math.cos(radians);
        var sin = Math.sin(radians);
        var adjustX = dx - (dx * cos - dy * sin);
        var adjustY = dy - (dx * sin + dy * cos);

        var newTransform = {
            translateX: oldTx + adjustX,
            translateY: oldTy + adjustY,
            rotate: rotation,
            scaleX: currentTransform ? (currentTransform.scaleX || 1) : 1,
            scaleY: currentTransform ? (currentTransform.scaleY || 1) : 1,
            originX: newOx,
            originY: newOy
        };

        canvasModel.setItemTransform(idx, newTransform);
        refreshTransform();
    }

    implicitHeight: contentLayout.implicitHeight

    ColumnLayout {
        id: contentLayout
        anchors.left: parent.left
        anchors.right: parent.right

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

        // Transform properties: Origin, X/W, Y/H
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 4
            spacing: 8
            enabled: root.controlsEnabled
            opacity: root.controlsEnabled ? 1.0 : 0.5

            // Column 1: Origin grid
            ButtonGroup {
                id: originGroup
                exclusive: true
            }

            Grid {
                columns: 3
                spacing: 2

                Repeater {
                    model: [
                        {
                            ox: 0,
                            oy: 0
                        },
                        {
                            ox: 0.5,
                            oy: 0
                        },
                        {
                            ox: 1,
                            oy: 0
                        },
                        {
                            ox: 0,
                            oy: 0.5
                        },
                        {
                            ox: 0.5,
                            oy: 0.5
                        },
                        {
                            ox: 1,
                            oy: 0.5
                        },
                        {
                            ox: 0,
                            oy: 1
                        },
                        {
                            ox: 0.5,
                            oy: 1
                        },
                        {
                            ox: 1,
                            oy: 1
                        }
                    ]

                    delegate: Button {
                        required property var modelData
                        required property int index

                        width: 16
                        height: 16
                        checkable: true
                        checked: {
                            var t = root.currentTransform;
                            var curX = t ? (t.originX !== undefined ? t.originX : 0) : 0;
                            var curY = t ? (t.originY !== undefined ? t.originY : 0) : 0;
                            return curX === modelData.ox && curY === modelData.oy;
                        }
                        ButtonGroup.group: originGroup

                        onClicked: root.setOrigin(modelData.ox, modelData.oy)

                        background: Rectangle {
                            color: parent.checked ? root.themePalette.highlight : root.themePalette.button
                            border.color: root.themePalette.mid
                            border.width: 1
                            radius: 2
                        }
                    }
                }
            }

            // Column 2: X and W
            GridLayout {
                columns: 2
                rowSpacing: 4
                columnSpacing: 4
                Layout.fillWidth: true

                Label {
                    text: qsTr("X:")
                    font.pixelSize: root.labelSize
                    color: root.labelColor
                }
                SpinBox {
                    from: -100000
                    to: 100000
                    value: Math.round(root.displayedX)
                    editable: true
                    Layout.fillWidth: true
                    onValueModified: root.updatePosition("x", value)
                }

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
            }

            // Column 3: Y and H
            GridLayout {
                columns: 2
                rowSpacing: 4
                columnSpacing: 4
                Layout.fillWidth: true

                Label {
                    text: qsTr("Y:")
                    font.pixelSize: root.labelSize
                    color: root.labelColor
                }
                SpinBox {
                    from: -100000
                    to: 100000
                    value: Math.round(root.displayedY)
                    editable: true
                    Layout.fillWidth: true
                    onValueModified: root.updatePosition("y", value)
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
            }
        }

        // Rotation row
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 4
            Layout.bottomMargin: 8
            spacing: 8
            enabled: root.controlsEnabled
            opacity: root.controlsEnabled ? 1.0 : 0.5

            Label {
                text: qsTr("R:")
                font.pixelSize: root.labelSize
                color: root.labelColor
            }
            TextField {
                id: rotationField
                text: root.currentTransform ? Math.round(root.currentTransform.rotate).toString() : "0"
                horizontalAlignment: TextInput.AlignHCenter
                Layout.preferredWidth: 50
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
            Label {
                text: "°"
                font.pixelSize: root.labelSize
                color: root.labelColor
            }
            Slider {
                id: rotationSlider
                from: -180
                to: 180
                value: root.currentTransform ? root.currentTransform.rotate : 0
                Layout.fillWidth: true

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
    }
}
