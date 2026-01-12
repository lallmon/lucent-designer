// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform as Platform
import "components"
import "components" as Lucent

ApplicationWindow {
    id: root
    width: 1920
    height: 1080
    visible: true
    title: (documentManager && documentManager.dirty ? "• " : "") + (documentManager ? documentManager.documentTitle : "Untitled") + " — Lucent"
    font: Qt.application.font
    readonly property SystemPalette themePalette: Lucent.Themed.palette

    readonly property var systemFont: Qt.application.font

    // Track if we're in the process of closing
    property bool isClosing: false
    property bool forceClose: false

    // Start tracking changes after app is fully loaded
    Component.onCompleted: {
        if (documentManager) {
            documentManager.startTracking();
        }
    }

    // Handle cross-cutting UI actions from nested components
    Connections {
        target: appController
        function onExportRequested(layerId, layerName) {
            root.openExportDialog(layerId, layerName);
        }
        function onFocusCanvasRequested() {
            viewport.forceActiveFocus();
        }
    }

    menuBar: MenuBar {
        viewport: viewport
        canvas: canvas
        onAboutRequested: aboutDialog.open()
        onNewRequested: root.handleNew()
        onOpenRequested: openDialog.open()
        onSaveRequested: root.handleSave()
        onSaveAsRequested: saveDialog.open()
        onExitRequested: root.close()
    }

    footer: StatusBar {
        zoomLevel: viewport.zoomLevel
        cursorX: canvas.cursorX
        cursorY: canvas.cursorY
        onZoomRequested: value => {
            viewport.zoomLevel = value;
        }
    }

    Shortcut {
        sequences: [StandardKey.Duplicate, "Ctrl+D"]
        onActivated: {
            canvas.duplicateSelectedItem();
        }
    }

    // Helper to check if focused item is a text input
    function isTextInputActive() {
        var item = root.activeFocusItem;
        if (!item)
            return false;
        // Check if the focused item is a text editing control
        var typeName = item.toString();
        return typeName.indexOf("TextField") >= 0 || typeName.indexOf("TextInput") >= 0 || typeName.indexOf("TextEdit") >= 0 || typeName.indexOf("TextArea") >= 0 || typeName.indexOf("SpinBox") >= 0;  // SpinBox has editable text
    }

    // Global delete shortcut - works regardless of focus (except in text inputs)
    Shortcut {
        sequence: "Del"
        context: Qt.ApplicationShortcut
        onActivated: {
            if (!root.isTextInputActive()) {
                canvas.deleteSelectedItem();
            }
        }
    }
    Shortcut {
        sequence: "Backspace"
        context: Qt.ApplicationShortcut
        onActivated: {
            if (!root.isTextInputActive()) {
                canvas.deleteSelectedItem();
            }
        }
    }

    Platform.FileDialog {
        id: openDialog
        title: qsTr("Open Document")
        nameFilters: [qsTr("Lucent files (*.lucent)"), qsTr("All files (*)")]
        fileMode: Platform.FileDialog.OpenFile
        onAccepted: {
            if (documentManager) {
                documentManager.setViewport(viewport.zoomLevel, viewport.offsetX, viewport.offsetY);
                if (documentManager.openDocument(file)) {
                    var vp = documentManager.getViewport();
                    viewport.zoomLevel = vp.zoomLevel;
                    viewport.offsetX = vp.offsetX;
                    viewport.offsetY = vp.offsetY;
                }
            }
        }
    }

    Platform.FileDialog {
        id: saveDialog
        title: qsTr("Save Document")
        nameFilters: [qsTr("Lucent files (*.lucent)")]
        fileMode: Platform.FileDialog.SaveFile
        defaultSuffix: "lucent"
        onAccepted: {
            if (documentManager) {
                documentManager.setViewport(viewport.zoomLevel, viewport.offsetX, viewport.offsetY);
                documentManager.saveDocumentAs(file);
            }
            if (root.isClosing) {
                root.forceClose = true;
                root.close();
            }
        }
        onRejected: {
            root.isClosing = false;
        }
    }

    Platform.MessageDialog {
        id: unsavedDialog
        title: qsTr("Unsaved Changes")
        text: qsTr("Do you want to save changes before closing?")
        buttons: Platform.MessageDialog.Save | Platform.MessageDialog.Discard | Platform.MessageDialog.Cancel

        onSaveClicked: {
            if (documentManager.filePath === "") {
                root.isClosing = true;
                saveDialog.open();
            } else {
                documentManager.setViewport(viewport.zoomLevel, viewport.offsetX, viewport.offsetY);
                documentManager.saveDocument();
                root.forceClose = true;
                root.close();
            }
        }

        onDiscardClicked: {
            root.forceClose = true;
            root.close();
        }
        // Cancel - do nothing, dialog closes automatically
    }

    onClosing: function (close) {
        if (root.forceClose) {
            close.accepted = true;
            return;
        }

        if (documentManager && documentManager.dirty) {
            close.accepted = false;
            unsavedDialog.open();
        } else {
            close.accepted = true;
        }
    }

    function handleNew() {
        if (documentManager && documentManager.dirty) {
            unsavedDialog.open();
        } else {
            if (documentManager) {
                documentManager.newDocument();
                viewport.resetZoom();
            }
        }
    }

    function handleSave() {
        if (!documentManager)
            return;

        documentManager.setViewport(viewport.zoomLevel, viewport.offsetX, viewport.offsetY);

        if (documentManager.filePath === "") {
            saveDialog.open();
        } else {
            documentManager.saveDocument();
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        ToolSettings {
            id: toolSettings
            Layout.fillWidth: true
            Layout.preferredHeight: 32
            activeTool: canvas.drawingMode === "" ? "select" : canvas.drawingMode
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            ToolPalette {
                id: toolPalette
                Layout.fillHeight: true
                activeTool: canvas.drawingMode === "" ? "select" : canvas.drawingMode

                onToolSelected: toolName => {
                    canvas.setDrawingMode(toolName);
                }
            }

            SplitView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                orientation: Qt.Horizontal

                handle: Rectangle {
                    implicitWidth: 6
                    implicitHeight: 6
                    color: SplitHandle.hovered ? palette.highlight : palette.mid
                }

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

    ExportDialog {
        id: exportDialog
        anchors.centerIn: parent
    }

    function openExportDialog(layerId, layerName) {
        exportDialog.layerId = layerId;
        exportDialog.layerName = layerName;
        exportDialog.open();
    }
}
