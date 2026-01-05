import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as DV

RowLayout {
    id: root

    property string labelText: ""
    property real value: 0
    property real minimum: 0
    property real maximum: 100
    property int decimals: 1
    property string suffix: ""
    property real fieldWidth: 50
    property real fieldHeight: DV.Styles.height.md
    property alias textField: input

    signal committed(real newValue)

    spacing: 6

    Label {
        text: root.labelText
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    TextField {
        id: input
        Layout.preferredWidth: root.fieldWidth
        Layout.preferredHeight: root.fieldHeight
        Layout.alignment: Qt.AlignVCenter
        text: Number(root.value).toFixed(root.decimals)
        horizontalAlignment: TextInput.AlignHCenter
        font.pixelSize: 11
        validator: DoubleValidator {
            bottom: root.minimum
            top: root.maximum
            decimals: root.decimals
        }

        function commitValue() {
            var parsed = parseFloat(text);
            if (!isNaN(parsed) && parsed >= root.minimum && parsed <= root.maximum) {
                root.committed(parsed);
                text = Number(parsed).toFixed(root.decimals);
            } else {
                text = Number(root.value).toFixed(root.decimals);
            }
        }

        onEditingFinished: commitValue()

        onActiveFocusChanged: {
            if (!activeFocus) {
                commitValue();
            }
        }

        background: Rectangle {
            color: DV.Themed.palette.base
            border.color: input.activeFocus ? DV.Themed.palette.highlight : DV.Themed.palette.mid
            border.width: 1
            radius: DV.Styles.rad.sm
        }
    }

    Label {
        visible: suffix !== ""
        text: suffix
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }
}
