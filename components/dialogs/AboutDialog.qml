import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

Dialog {
    id: root
    modal: true
    focus: true
    standardButtons: Dialog.Ok
    readonly property SystemPalette themePalette: Lucent.Themed.palette

    // Inputs
    property string appVersion: ""
    property string rendererBackend: ""
    property string rendererType: ""
    property string glVendor: ""

    background: Rectangle {
        color: themePalette.base
        radius: Lucent.Styles.rad.sm
        border.color: themePalette.mid
        border.width: 1
    }

    contentItem: Item {
        implicitWidth: column.implicitWidth + 28
        implicitHeight: column.implicitHeight + 28

        Column {
            id: column
            anchors.fill: parent
            anchors.margins: 14
            spacing: 8

            Label {
                text: qsTr("Lucent")
                font.bold: true
                color: themePalette.text
            }

            Label {
                text: qsTr("Version: %1").arg(root.appVersion || "unknown")
                color: themePalette.text
            }

            Label {
                text: qsTr("Renderer backend: %1").arg(root.rendererBackend || "unknown")
                color: themePalette.text
            }

            Label {
                text: qsTr("Renderer type: %1").arg(root.rendererType || "unknown")
                color: themePalette.text
            }

            Label {
                text: qsTr("GL Vendor: %1").arg(root.glVendor || "unknown")
                color: themePalette.text
            }
        }
    }
}
