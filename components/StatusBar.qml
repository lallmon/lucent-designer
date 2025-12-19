import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ToolBar {
    id: root
    property real zoomLevel: 1.0
    property real cursorX: 0
    property real cursorY: 0
    
    RowLayout {
        anchors.fill: parent
        Item {
            Layout.fillWidth: true
        }
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 6      
            PhIcon {
                name: "crosshair-simple"
                size: 16
                color: "white"
            }        
            Label {
                text: qsTr("X: %1  Y: %2").arg(root.cursorX.toFixed(1)).arg(root.cursorY.toFixed(1))
                horizontalAlignment: Text.AlignHCenter
            }
        }
        Item {
            Layout.fillWidth: true
        } 
        RowLayout {
            Layout.rightMargin: 10
            spacing: 6
            PhIcon {
                name: "magnifying-glass"
                size: 16
                color: "white"
            }    
            Label {
                text: qsTr("Zoom: %1%").arg(Math.round(root.zoomLevel * 100))
            }
        }
    }
}

