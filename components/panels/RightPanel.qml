import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

Pane {
    id: root
    padding: 0
    readonly property SystemPalette themePalette: Lucent.Themed.palette

    signal exportLayerRequested(string layerId, string layerName)
    signal focusCanvasRequested

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Transform section - fixed height based on content
        Pane {
            Layout.fillWidth: true
            padding: 12

            TransformPanel {
                id: transformPanel
                anchors.left: parent.left
                anchors.right: parent.right
                onFocusCanvasRequested: root.focusCanvasRequested()
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: themePalette.mid
        }

        // Layers section
        Pane {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 150
            padding: 12

            LayerPanel {
                anchors.fill: parent
                onExportLayerRequested: (layerId, layerName) => root.exportLayerRequested(layerId, layerName)
            }
        }
    }

    // Keep panel selection in sync without introducing a binding loop
    Component.onCompleted: {
        transformPanel.selectedItem = Lucent.SelectionManager.selectedItem;
    }
    Connections {
        target: Lucent.SelectionManager
        function onSelectedItemChanged() {
            transformPanel.selectedItem = Lucent.SelectionManager.selectedItem;
        }
        function onSelectedItemIndexChanged() {
            transformPanel.selectedItem = Lucent.SelectionManager.selectedItem;
        }
        function onSelectedIndicesChanged() {
            transformPanel.selectedItem = Lucent.SelectionManager.selectedItem;
        }
    }
}
