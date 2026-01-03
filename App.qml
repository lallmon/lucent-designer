import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Controls.Material
import "components"
import "components" as DV

ApplicationWindow {
    id: root
    width: 1920
    height: 1080
    visible: true
    title: qsTr("Lucent")
    font: Qt.application.font
    readonly property SystemPalette palette: DV.PaletteBridge.active

    readonly property var systemFont: Qt.application.font

    menuBar: MenuBar {
        viewport: viewport
        canvas: canvas
        onAboutRequested: aboutDialog.open()
    }

    footer: StatusBar {
        zoomLevel: viewport.zoomLevel
        cursorX: canvas.cursorX
        cursorY: canvas.cursorY
    }

    Shortcut {
        sequences: [StandardKey.Duplicate, "Ctrl+D"]
        onActivated: {
            canvas.duplicateSelectedItem();
        }
    }

    // Main layout with tool settings and content
    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        ToolSettings {
            id: toolSettings
            Layout.fillWidth: true
            Layout.preferredHeight: 32
            activeTool: canvas.drawingMode === "" ? "select" : canvas.drawingMode
        }

        // Main content area with toolbar and canvas
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // Left tool palette
            ToolPalette {
                id: toolPalette
                Layout.fillHeight: true
                activeTool: canvas.drawingMode === "" ? "select" : canvas.drawingMode

                onToolSelected: toolName => {
                    canvas.setDrawingMode(toolName);
                }
            }

            // Main content with viewport and right panel
            SplitView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                orientation: Qt.Horizontal

                handle: Rectangle {
                    implicitWidth: 6
                    implicitHeight: 6
                    color: SplitHandle.hovered ? palette.highlight : palette.mid
                }

                // Main Viewport with Canvas
                Viewport {
                    id: viewport
                    SplitView.fillWidth: true
                    SplitView.fillHeight: true

                    Canvas {
                        id: canvas
                        anchors.fill: parent
                        zoomLevel: viewport.zoomLevel
                        offsetX: viewport.offsetX
                        offsetY: viewport.offsetY
                        toolSettings: toolSettings.toolSettings

                        onPanRequested: (dx, dy) => {
                            viewport.pan(dx, dy);
                        }
                    }
                }

                RightPanel {
                    id: rightPanel
                    SplitView.preferredWidth: 280
                    SplitView.minimumWidth: 128
                    SplitView.maximumWidth: 400
                    SplitView.fillHeight: true
                }
            }
        }
    }

    AboutDialog {
        id: aboutDialog
        anchors.centerIn: parent
        appVersion: appInfo ? appInfo.appVersion : ""
        rendererBackend: appInfo ? appInfo.rendererBackend : ""
        rendererType: appInfo ? appInfo.rendererType : ""
        glVendor: appInfo ? appInfo.glVendor : ""
    }
}
