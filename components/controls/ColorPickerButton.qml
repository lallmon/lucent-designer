import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import ".." as Lucent

Button {
    id: root

    property color color: "black"
    property real colorOpacity: 1.0
    property string dialogTitle: qsTr("Choose Color")

    signal colorPicked(color newColor)
    signal colorPreview(color previewColor)

    readonly property SystemPalette themePalette: Lucent.Themed.palette

    Layout.preferredWidth: 16
    Layout.preferredHeight: 16
    Layout.alignment: Qt.AlignVCenter

    onClicked: colorDialog.open()

    background: Rectangle {
        border.color: root.themePalette.mid
        border.width: 1
        radius: Lucent.Styles.rad.sm
        color: "transparent"
        clip: true

        // Checkerboard pattern to show transparency
        Canvas {
            anchors.fill: parent
            z: 0
            property color checkerLight: root.themePalette.midlight
            property color checkerDark: root.themePalette.mid
            onCheckerLightChanged: requestPaint()
            onCheckerDarkChanged: requestPaint()
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height);
                var size = 4;
                for (var y = 0; y < height; y += size) {
                    for (var x = 0; x < width; x += size) {
                        if ((Math.floor(x / size) + Math.floor(y / size)) % 2 === 0) {
                            ctx.fillStyle = checkerLight;
                        } else {
                            ctx.fillStyle = checkerDark;
                        }
                        ctx.fillRect(x, y, size, size);
                    }
                }
            }
            Component.onCompleted: requestPaint()
        }

        // Color overlay with opacity applied
        Rectangle {
            anchors.fill: parent
            z: 1
            color: root.color
            opacity: root.colorOpacity
        }
    }

    ColorDialog {
        id: colorDialog
        title: root.dialogTitle
        selectedColor: root.color
        modality: Qt.NonModal

        // Live preview while picking
        onSelectedColorChanged: {
            if (visible) {
                root.colorPreview(selectedColor);
            }
        }

        onAccepted: {
            root.colorPicked(selectedColor);
        }

        onRejected: {
            // Restore original color on cancel
            root.colorPreview(root.color);
        }
    }
}
