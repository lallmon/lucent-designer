// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as Lucent

ToolBar {
    id: root
    implicitHeight: 32

    readonly property SystemPalette themePalette: Lucent.Themed.palette

    property var viewport: null
    property var canvas: null
    property string documentTitle: "Untitled"
    property bool documentDirty: false

    signal aboutRequested
    signal newRequested
    signal openRequested
    signal saveRequested
    signal saveAsRequested
    signal exitRequested

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

    RowLayout {
        anchors.fill: parent
        spacing: 0

        MenuBar {
            id: menuBar
            Layout.alignment: Qt.AlignVCenter
            background: Item {} // Transparent - inherits from ToolBar

            Menu {
                title: qsTr("&File")

                Action {
                    text: qsTr("&New")
                    shortcut: StandardKey.New
                    onTriggered: root.newRequested()
                }

                Action {
                    text: qsTr("&Open...")
                    shortcut: StandardKey.Open
                    onTriggered: root.openRequested()
                }

                Action {
                    text: qsTr("&Save")
                    shortcut: StandardKey.Save
                    enabled: documentManager ? (documentManager.dirty || documentManager.filePath === "") : false
                    onTriggered: root.saveRequested()
                }

                Action {
                    text: qsTr("Save &As...")
                    shortcut: "Ctrl+Shift+S"
                    onTriggered: root.saveAsRequested()
                }

                MenuSeparator {}

                Action {
                    text: qsTr("Export &Layer...")
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
                    text: qsTr("E&xit")
                    shortcut: StandardKey.Quit
                    onTriggered: root.exitRequested()
                }
            }

            Menu {
                title: qsTr("&Edit")
                Action {
                    text: qsTr("&Undo")
                    shortcut: StandardKey.Undo
                    enabled: historyManager ? historyManager.canUndo : false
                    onTriggered: if (historyManager)
                        historyManager.undo()
                }
                Action {
                    text: qsTr("&Redo")
                    shortcut: StandardKey.Redo
                    enabled: historyManager ? historyManager.canRedo : false
                    onTriggered: if (historyManager)
                        historyManager.redo()
                }
                Action {
                    text: qsTr("&Duplicate")
                    shortcut: StandardKey.Duplicate
                    enabled: root.canvas && Lucent.SelectionManager.hasSelection()
                    onTriggered: {
                        if (root.canvas) {
                            root.canvas.duplicateSelectedItem();
                        }
                    }
                }
                Action {
                    text: qsTr("&Group")
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
                    text: qsTr("U&ngroup")
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
                title: qsTr("&Document")

                Menu {
                    title: qsTr("&Units")

                    ActionGroup {
                        id: unitsGroup
                        exclusive: true
                    }

                    Action {
                        text: qsTr("&Inches")
                        checkable: true
                        checked: unitSettings && unitSettings.displayUnit === "in"
                        ActionGroup.group: unitsGroup
                        onTriggered: if (unitSettings)
                            unitSettings.displayUnit = "in"
                    }
                    Action {
                        text: qsTr("&Millimeters")
                        checkable: true
                        checked: unitSettings && unitSettings.displayUnit === "mm"
                        ActionGroup.group: unitsGroup
                        onTriggered: if (unitSettings)
                            unitSettings.displayUnit = "mm"
                    }
                    Action {
                        text: qsTr("&Pixels")
                        checkable: true
                        checked: unitSettings && unitSettings.displayUnit === "px"
                        ActionGroup.group: unitsGroup
                        onTriggered: if (unitSettings)
                            unitSettings.displayUnit = "px"
                    }
                }

                Menu {
                    title: qsTr("Preview &DPI")

                    ActionGroup {
                        id: dpiGroup
                        exclusive: true
                    }

                    Action {
                        text: "72"
                        checkable: true
                        checked: unitSettings && unitSettings.previewDPI === 72
                        ActionGroup.group: dpiGroup
                        onTriggered: if (unitSettings)
                            unitSettings.previewDPI = 72
                    }
                    Action {
                        text: "96"
                        checkable: true
                        checked: unitSettings && unitSettings.previewDPI === 96
                        ActionGroup.group: dpiGroup
                        onTriggered: if (unitSettings)
                            unitSettings.previewDPI = 96
                    }
                    Action {
                        text: "300"
                        checkable: true
                        checked: unitSettings && unitSettings.previewDPI === 300
                        ActionGroup.group: dpiGroup
                        onTriggered: if (unitSettings)
                            unitSettings.previewDPI = 300
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
                    text: qsTr("Zoom &In")
                    shortcut: StandardKey.ZoomIn
                    onTriggered: {
                        if (root.viewport) {
                            root.viewport.zoomIn();
                        }
                    }
                }
                Action {
                    text: qsTr("Zoom &Out")
                    shortcut: StandardKey.ZoomOut
                    onTriggered: {
                        if (root.viewport) {
                            root.viewport.zoomOut();
                        }
                    }
                }
                Action {
                    text: qsTr("&Reset Zoom")
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

        Item {
            Layout.fillWidth: true
        }
    }

    // Centered: file name, dirty indicator, zoom
    Row {
        anchors.centerIn: parent
        spacing: 6

        Label {
            text: root.documentTitle
            color: themePalette.windowText
            font.pixelSize: 12
            anchors.verticalCenter: parent.verticalCenter
        }

        Label {
            visible: root.documentDirty
            text: "●"
            color: themePalette.highlight
            font.pixelSize: 10
            anchors.verticalCenter: parent.verticalCenter
        }

        Label {
            text: "(" + Math.round((root.viewport ? root.viewport.zoomLevel : 1) * 100) + "%)"
            color: themePalette.text
            font.pixelSize: 11
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}
