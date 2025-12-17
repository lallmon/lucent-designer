import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Components"

ApplicationWindow {
    id: root
    width: 1920
    height: 1080
    visible: true
    title: qsTr("DesignVibe")

    // Menu Bar
    menuBar: MenuBar {
        Menu {
            title: qsTr("&File")
            Action {
                text: qsTr("E&xit (Ctrl+Q)")
                shortcut: StandardKey.Quit
                onTriggered: Qt.quit()
            }
        }
        Menu {
            title: qsTr("&View")
            Action {
                text: qsTr("Zoom &In (Ctrl++)")
                shortcut: StandardKey.ZoomIn
                onTriggered: canvas.zoomIn()
            }
            Action {
                text: qsTr("Zoom &Out (Ctrl+-)")
                shortcut: StandardKey.ZoomOut
                onTriggered: canvas.zoomOut()
            }
            Action {
                text: qsTr("&Reset Zoom (Ctrl+0)")
                shortcut: "Ctrl+0"
                onTriggered: canvas.resetZoom()
            }
        }
    }

    // Status Bar
    footer: StatusBar {
        zoomLevel: canvas.zoomLevel
    }

    // Main Canvas Area
    InfiniteCanvas {
        id: canvas
        anchors.fill: parent
    }
}
