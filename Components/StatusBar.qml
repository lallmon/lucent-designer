import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Status Bar component showing application status information
ToolBar {
    id: root
    
    // Property to bind to canvas zoom level
    property real zoomLevel: 1.0
    
    RowLayout {
        anchors.fill: parent
        
        Label {
            text: qsTr("Zoom: %1%").arg(Math.round(root.zoomLevel * 100))
            Layout.leftMargin: 10
        }
    }
}

