import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as DV

Pane {
    id: root
    padding: 0
    readonly property SystemPalette palette: DV.PaletteBridge.active

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Properties section
        Pane {
            Layout.fillWidth: true
            Layout.preferredHeight: parent.height * 0.35
            Layout.minimumHeight: 150
            padding: 12

            ObjectPropertiesInspector {
                id: propertiesInspector
                anchors.fill: parent
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: palette.mid
        }

        // Layers section
        Pane {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 150
            padding: 12

            LayerPanel {
                anchors.fill: parent
            }
        }
    }

    // Keep inspector selection in sync without introducing a binding loop
    Component.onCompleted: {
        propertiesInspector.selectedItem = DV.SelectionManager.selectedItem;
    }
    Connections {
        target: DV.SelectionManager
        function onSelectedItemChanged() {
            propertiesInspector.selectedItem = DV.SelectionManager.selectedItem;
        }
        function onSelectedItemIndexChanged() {
            propertiesInspector.selectedItem = DV.SelectionManager.selectedItem;
        }
        function onSelectedIndicesChanged() {
            propertiesInspector.selectedItem = DV.SelectionManager.selectedItem;
        }
    }
}
