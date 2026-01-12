// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import "." as Lucent

// Main menu bar component
MenuBar {
    id: root

    readonly property SystemPalette themePalette: Lucent.Themed.palette

    // Property to reference the viewport for zoom operations
    property var viewport: null

    background: Rectangle {
        color: themePalette.window
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 1
            color: themePalette.mid
        }
    }
    // Property to reference the canvas for edit operations
    property var canvas: null

    // Signals for file operations (handled by App.qml)
    signal aboutRequested
    signal newRequested
    signal openRequested
    signal saveRequested
    signal saveAsRequested
    signal exitRequested

    Menu {
        title: qsTr("&File")

        Action {
            text: qsTr("&New (Ctrl+N)")
            shortcut: StandardKey.New
            onTriggered: root.newRequested()
        }

        Action {
            text: qsTr("&Open... (Ctrl+O)")
            shortcut: StandardKey.Open
            onTriggered: root.openRequested()
        }

        Action {
            text: qsTr("&Save (Ctrl+S)")
            shortcut: StandardKey.Save
            enabled: documentManager ? (documentManager.dirty || documentManager.filePath === "") : false
            onTriggered: root.saveRequested()
        }

        Action {
            text: qsTr("Save &As... (Ctrl+Shift+S)")
            shortcut: "Ctrl+Shift+S"
            onTriggered: root.saveAsRequested()
        }

        MenuSeparator {}

        Action {
            text: qsTr("Export &Layer... (Ctrl+E)")
            shortcut: "Ctrl+E"
            enabled: Lucent.SelectionManager.selectedItem && Lucent.SelectionManager.selectedItem.type === "layer"
            onTriggered: {
                var item = Lucent.SelectionManager.selectedItem;
                if (item && item.type === "layer") {
                    appController.openExportDialog(item.id, item.name || "Layer");
                }
            }
        }

        MenuSeparator {}

        Action {
            text: qsTr("E&xit (Ctrl+Q)")
            shortcut: StandardKey.Quit
            onTriggered: root.exitRequested()
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
            enabled: root.canvas && Lucent.SelectionManager.hasSelection()
            onTriggered: {
                if (root.canvas) {
                    root.canvas.duplicateSelectedItem();
                }
            }
        }
        Action {
            text: qsTr("&Group Selection (Ctrl+G)")
            shortcut: "Ctrl+G"
            enabled: canvasModel && Lucent.SelectionManager.hasSelection()
            onTriggered: {
                if (!canvasModel)
                    return;
                let indices = Lucent.SelectionManager.currentSelectionIndices();
                if (indices.length === 0)
                    return;
                const finalGroupIndex = canvasModel.groupItems(indices);
                if (finalGroupIndex >= 0) {
                    Lucent.SelectionManager.setSelection([finalGroupIndex]);
                }
            }
        }
        Action {
            text: qsTr("&Ungroup (Ctrl+Shift+G)")
            shortcut: "Ctrl+Shift+G"
            enabled: canvasModel && Lucent.SelectionManager.selectedItem && Lucent.SelectionManager.selectedItem.type === "group"
            onTriggered: {
                if (!canvasModel)
                    return;
                const groupIndex = Lucent.SelectionManager.selectedItemIndex;
                if (groupIndex < 0)
                    return;
                const groupData = canvasModel.getItemData(groupIndex);
                if (!groupData || groupData.type !== "group")
                    return;
                canvasModel.ungroup(groupIndex);
                Lucent.SelectionManager.selectedItemIndex = -1;
                Lucent.SelectionManager.selectedItem = null;
            }
        }
    }

    Menu {
        title: qsTr("&View")
        Action {
            text: qsTr("Show &Grid")
            checkable: true
            checked: root.viewport ? root.viewport.gridVisible : false
            onTriggered: {
                if (root.viewport) {
                    root.viewport.gridVisible = !root.viewport.gridVisible;
                }
            }
        }
        MenuSeparator {}
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
