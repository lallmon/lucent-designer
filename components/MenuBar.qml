import QtQuick
import QtQuick.Controls
import "." as DV

// Main menu bar component
MenuBar {
    id: root

    // Property to reference the viewport for zoom operations
    property var viewport: null
    // Property to reference the canvas for edit operations
    property var canvas: null
    // Signal to request About dialog from parent
    signal aboutRequested

    Menu {
        title: qsTr("&File")
        Action {
            text: qsTr("E&xit (Ctrl+Q)")
            shortcut: StandardKey.Quit
            onTriggered: Qt.quit()
        }
    }

    Menu {
        title: qsTr("&Edit")
        Action {
            text: qsTr("&Undo (Ctrl+Z)")
            shortcut: StandardKey.Undo
            enabled: canvasModel ? canvasModel.canUndo : false
            onTriggered: if (canvasModel)
                canvasModel.undo()
        }
        Action {
            text: qsTr("&Redo (Ctrl+Shift+Z)")
            shortcut: StandardKey.Redo
            enabled: canvasModel ? canvasModel.canRedo : false
            onTriggered: if (canvasModel)
                canvasModel.redo()
        }
        Action {
            text: qsTr("&Duplicate Selection (Ctrl+D)")
            shortcut: StandardKey.Duplicate
            enabled: root.canvas && DV.SelectionManager.hasSelection()
            onTriggered: {
                if (root.canvas) {
                    root.canvas.duplicateSelectedItem();
                }
            }
        }
        Action {
            text: qsTr("&Group Selection (Ctrl+G)")
            shortcut: "Ctrl+G"
            enabled: canvasModel && DV.SelectionManager.hasSelection()
            onTriggered: {
                if (!canvasModel)
                    return;
                let indices = DV.SelectionManager.currentSelectionIndices();
                if (indices.length === 0)
                    return;
                const finalGroupIndex = canvasModel.groupItems(indices);
                if (finalGroupIndex >= 0) {
                    DV.SelectionManager.setSelection([finalGroupIndex]);
                }
            }
        }
        Action {
            text: qsTr("&Ungroup (Ctrl+Shift+G)")
            shortcut: "Ctrl+Shift+G"
            enabled: canvasModel && DV.SelectionManager.selectedItem && DV.SelectionManager.selectedItem.type === "group"
            onTriggered: {
                if (!canvasModel)
                    return;
                const groupIndex = DV.SelectionManager.selectedItemIndex;
                if (groupIndex < 0)
                    return;
                const groupData = canvasModel.getItemData(groupIndex);
                if (!groupData || groupData.type !== "group")
                    return;
                canvasModel.ungroup(groupIndex);
                DV.SelectionManager.selectedItemIndex = -1;
                DV.SelectionManager.selectedItem = null;
            }
        }
    }

    Menu {
        title: qsTr("&View")
        Action {
            text: qsTr("Zoom &In (Ctrl++)")
            shortcut: StandardKey.ZoomIn
            onTriggered: {
                if (root.viewport) {
                    root.viewport.zoomIn();
                }
            }
        }
        Action {
            text: qsTr("Zoom &Out (Ctrl+-)")
            shortcut: StandardKey.ZoomOut
            onTriggered: {
                if (root.viewport) {
                    root.viewport.zoomOut();
                }
            }
        }
        Action {
            text: qsTr("&Reset Zoom (Ctrl+0)")
            shortcut: "Ctrl+0"
            onTriggered: {
                if (root.viewport) {
                    root.viewport.resetZoom();
                }
            }
        }
    }

    Menu {
        title: qsTr("&Help")
        Action {
            text: qsTr("&About")
            onTriggered: root.aboutRequested()
        }
    }
}
