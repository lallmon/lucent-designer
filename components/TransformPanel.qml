import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as Lucent

// Panel displaying unified transform properties (X, Y, Width, Height) for selected items
Item {
    id: root
    readonly property SystemPalette themePalette: Lucent.Themed.palette

    // Signal to request focus return to canvas after editing
    signal focusCanvasRequested

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

    // Current bounding box from the model (transformed) - updated reactively via signal
    property var currentBounds: null

    // Current geometry bounds (untransformed) - for position calculations
    property var geometryBounds: null

    // Current transform - updated reactively via signal
    property var currentTransform: null

    function refreshBounds() {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx >= 0 && canvasModel) {
            currentBounds = canvasModel.getBoundingBox(idx);
            geometryBounds = canvasModel.getGeometryBounds(idx);
        } else {
            currentBounds = null;
            geometryBounds = null;
        }
    }

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
                root.refreshBounds();
            }
        }
        function onItemModified(index) {
            if (index === Lucent.SelectionManager.selectedItemIndex) {
                root.refreshTransform();
                root.refreshBounds();
            }
        }
    }

    Connections {
        target: Lucent.SelectionManager
        function onSelectedItemIndexChanged() {
            root.refreshTransform();
            root.refreshBounds();
        }
    }

    Component.onCompleted: {
        refreshTransform();
        refreshBounds();
    }

    // Controls are enabled only when an editable item is selected and not locked
    readonly property bool controlsEnabled: hasEditableBounds && !isLocked

    readonly property int labelSize: 10
    readonly property color labelColor: themePalette.text

    // Proportional scaling toggle
    property bool proportionalScale: true

    // Computed canvas position: geometry origin point + translation (using untransformed geometry)
    readonly property real displayedX: {
        if (!geometryBounds)
            return 0;
        var t = currentTransform;
        var originX = t ? (t.originX || 0) : 0;
        var translateX = t ? (t.translateX || 0) : 0;
        return geometryBounds.x + geometryBounds.width * originX + translateX;
    }

    readonly property real displayedY: {
        if (!geometryBounds)
            return 0;
        var t = currentTransform;
        var originY = t ? (t.originY || 0) : 0;
        var translateY = t ? (t.translateY || 0) : 0;
        return geometryBounds.y + geometryBounds.height * originY + translateY;
    }

    // Update translation to achieve a desired canvas position for the origin point
    function updatePosition(axis, newValue) {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx < 0 || !canvasModel || !geometryBounds)
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
            newTransform.translateX = newValue - geometryBounds.x - geometryBounds.width * originX;
        } else if (axis === "y") {
            newTransform.translateY = newValue - geometryBounds.y - geometryBounds.height * originY;
        }

        canvasModel.setItemTransform(idx, newTransform);
    }

    function updateBounds(property, value) {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx < 0 || !canvasModel || !geometryBounds)
            return;

        var t = currentTransform || {};
        var scaleX = t.scaleX || 1;
        var scaleY = t.scaleY || 1;

        // User enters displayed size (geometry × scale), so divide by scale to get geometry
        var newBounds = {
            x: geometryBounds.x,
            y: geometryBounds.y,
            width: geometryBounds.width,
            height: geometryBounds.height
        };

        if (property === "width") {
            newBounds.width = value / scaleX;
        } else if (property === "height") {
            newBounds.height = value / scaleY;
        }

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
        var scaleX = currentTransform ? (currentTransform.scaleX || 1) : 1;
        var scaleY = currentTransform ? (currentTransform.scaleY || 1) : 1;
        var oldTx = currentTransform ? (currentTransform.translateX || 0) : 0;
        var oldTy = currentTransform ? (currentTransform.translateY || 0) : 0;

        // Adjust translation to keep shape visually in place when origin changes
        // Formula: adjustment = delta - R(S(delta))
        // Where delta is unscaled displacement, R is rotation, S is scale
        var dx = (oldOx - newOx) * bounds.width;
        var dy = (oldOy - newOy) * bounds.height;

        // Scale the displacement
        var scaledDx = dx * scaleX;
        var scaledDy = dy * scaleY;

        // Rotate the scaled displacement
        var radians = rotation * Math.PI / 180;
        var cos = Math.cos(radians);
        var sin = Math.sin(radians);
        var rotatedScaledDx = scaledDx * cos - scaledDy * sin;
        var rotatedScaledDy = scaledDx * sin + scaledDy * cos;

        // Adjustment = unscaled delta - rotated scaled delta
        var adjustX = dx - rotatedScaledDx;
        var adjustY = dy - rotatedScaledDy;

        var newTransform = {
            translateX: oldTx + adjustX,
            translateY: oldTy + adjustY,
            rotate: rotation,
            scaleX: scaleX,
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
                    onValueModified: {
                        root.updatePosition("x", value);
                        root.focusCanvasRequested();
                    }
                }

                Label {
                    text: qsTr("W:")
                    font.pixelSize: root.labelSize
                    color: root.labelColor
                }
                SpinBox {
                    from: 0
                    to: 100000
                    value: {
                        if (!root.geometryBounds)
                            return 0;
                        var scaleX = root.currentTransform ? (root.currentTransform.scaleX || 1) : 1;
                        return Math.round(root.geometryBounds.width * scaleX);
                    }
                    editable: true
                    Layout.fillWidth: true
                    onValueModified: {
                        root.updateBounds("width", value);
                        root.focusCanvasRequested();
                    }
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
                    onValueModified: {
                        root.updatePosition("y", value);
                        root.focusCanvasRequested();
                    }
                }

                Label {
                    text: qsTr("H:")
                    font.pixelSize: root.labelSize
                    color: root.labelColor
                }
                SpinBox {
                    from: 0
                    to: 100000
                    value: {
                        if (!root.geometryBounds)
                            return 0;
                        var scaleY = root.currentTransform ? (root.currentTransform.scaleY || 1) : 1;
                        return Math.round(root.geometryBounds.height * scaleY);
                    }
                    editable: true
                    Layout.fillWidth: true
                    onValueModified: {
                        root.updateBounds("height", value);
                        root.focusCanvasRequested();
                    }
                }
            }
        }

        // Scale row
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 4
            spacing: 8
            enabled: root.controlsEnabled
            opacity: root.controlsEnabled ? 1.0 : 0.5

            Label {
                text: qsTr("Scale X:")
                font.pixelSize: root.labelSize
                color: root.labelColor
            }
            SpinBox {
                id: scaleXSpinBox
                from: 1
                to: 1000
                value: root.currentTransform ? Math.round((root.currentTransform.scaleX || 1) * 100) : 100
                editable: true
                Layout.fillWidth: true

                property int decimals: 0
                textFromValue: function (value, locale) {
                    return value + "%";
                }
                valueFromText: function (text, locale) {
                    return parseInt(text.replace("%", "")) || 100;
                }

                onValueModified: {
                    var newScaleX = value / 100.0;
                    if (root.proportionalScale) {
                        canvasModel.beginTransaction();
                        root.updateTransform("scaleX", newScaleX);
                        root.updateTransform("scaleY", newScaleX);
                        canvasModel.endTransaction();
                    } else {
                        root.updateTransform("scaleX", newScaleX);
                    }
                    root.focusCanvasRequested();
                }
            }

            Label {
                text: qsTr("Y:")
                font.pixelSize: root.labelSize
                color: root.labelColor
            }
            SpinBox {
                id: scaleYSpinBox
                from: 1
                to: 1000
                value: root.currentTransform ? Math.round((root.currentTransform.scaleY || 1) * 100) : 100
                editable: true
                Layout.fillWidth: true

                property int decimals: 0
                textFromValue: function (value, locale) {
                    return value + "%";
                }
                valueFromText: function (text, locale) {
                    return parseInt(text.replace("%", "")) || 100;
                }

                onValueModified: {
                    var newScaleY = value / 100.0;
                    if (root.proportionalScale) {
                        canvasModel.beginTransaction();
                        root.updateTransform("scaleX", newScaleY);
                        root.updateTransform("scaleY", newScaleY);
                        canvasModel.endTransaction();
                    } else {
                        root.updateTransform("scaleY", newScaleY);
                    }
                    root.focusCanvasRequested();
                }
            }

            // Proportional scale toggle
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

                ToolTip.visible: hovered
                ToolTip.text: proportionalToggle.checked ? qsTr("Proportional scaling on") : qsTr("Proportional scaling off")
                ToolTip.delay: 500
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
                text: qsTr("Rotate:")
                font.pixelSize: root.labelSize
                color: root.labelColor
            }
            TextField {
                id: rotationField
                horizontalAlignment: TextInput.AlignHCenter
                Layout.preferredWidth: 50
                validator: IntValidator {
                    bottom: -360
                    top: 360
                }

                // Compute the expected text value from current transform
                readonly property string expectedText: root.currentTransform ? Math.round(root.currentTransform.rotate).toString() : "0"

                // Flag to prevent double-firing of editingFinished
                property bool isCommitting: false

                // Initialize text
                Component.onCompleted: text = expectedText

                // Update text when expectedText changes (handles undo/redo)
                // Skip if we're in the middle of committing to prevent double onEditingFinished
                onExpectedTextChanged: {
                    if (!isCommitting) {
                        text = expectedText;
                    }
                }

                onEditingFinished: {
                    if (isCommitting)
                        return;
                    isCommitting = true;

                    var val = parseInt(text) || 0;
                    val = Math.max(-360, Math.min(360, val));
                    root.updateTransform("rotate", val);
                    root.focusCanvasRequested();

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
                from: -180
                to: 180
                value: root.currentTransform ? root.currentTransform.rotate : 0
                Layout.fillWidth: true

                onPressedChanged: {
                    if (pressed) {
                        canvasModel.beginTransaction();
                    } else {
                        canvasModel.endTransaction();
                    }
                }

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
