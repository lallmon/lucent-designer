import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Status Bar component showing application status information
ToolBar {
    id: root
    
    // Property to bind to canvas zoom level
    property real zoomLevel: 1.0
    
    // Properties for cursor position
    property real cursorX: 0
    property real cursorY: 0
    
    RowLayout {
        anchors.fill: parent
        
        // Left spacer
        Item {
            Layout.fillWidth: true
        }
        
        // Cursor position (centered)
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 6
            
            PhIcon {
                name: "crosshair-simple"
                size: 16
                color: "#dcdcdc"
            }
            
            Label {
                text: qsTr("X: %1  Y: %2").arg(root.cursorX.toFixed(1)).arg(root.cursorY.toFixed(1))
                horizontalAlignment: Text.AlignHCenter
            }
        }
        
        // Right spacer
        Item {
            Layout.fillWidth: true
        }
        
        // Zoom level (right aligned)
        RowLayout {
            Layout.rightMargin: 10
            spacing: 6
            
            PhIcon {
                name: "magnifying-glass"
                size: 16
                color: "#dcdcdc"
            }
            
            Label {
                text: qsTr("Zoom: %1%").arg(Math.round(root.zoomLevel * 100))
            }
        }
    }
}

