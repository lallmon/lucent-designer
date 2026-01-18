// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

ToolBar {
    id: root
    height: 48

    property string activeTool: ""
    readonly property SystemPalette themePalette: Lucent.Themed.palette

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

    // Selection awareness: when a shape is selected, show its properties
    // Use a non-readonly property to avoid binding loops when itemModified updates the selection
    property var currentSelection: null
    property string currentSelectionType: ""

    // Update selection info when SelectionManager changes (but not during property edits)
    Connections {
        target: Lucent.SelectionManager
        function onSelectedItemChanged() {
            var item = Lucent.SelectionManager.selectedItem;
            root.currentSelection = item;
            root.currentSelectionType = item ? item.type : "";
        }
    }

    Component.onCompleted: {
        // Initialize from current selection
        var item = Lucent.SelectionManager.selectedItem;
        currentSelection = item;
        currentSelectionType = item ? item.type : "";
    }

    readonly property bool hasEditableSelection: {
        var t = currentSelectionType;
        return t === "rectangle" || t === "ellipse" || t === "path" || t === "text" || t === "artboard";
    }

    // Determine which settings to display: selected item type takes priority over active tool
    readonly property string displayType: hasEditableSelection ? currentSelectionType : activeTool

    // Expose tool settings components directly for reactive binding
    readonly property var toolSettings: ({
            "artboard": artboardSettings,
            "rectangle": rectangleSettings,
            "ellipse": ellipseSettings,
            "pen": penSettings,
            "text": textSettings
        })

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 8
        anchors.rightMargin: 8
        spacing: 4

        Lucent.ArtboardToolSettings {
            id: artboardSettings
            visible: root.displayType === "artboard"
            editMode: root.hasEditableSelection && root.currentSelectionType === "artboard"
            selectedItem: root.hasEditableSelection ? root.currentSelection : null
        }

        Lucent.RectangleToolSettings {
            id: rectangleSettings
            visible: root.displayType === "rectangle"
            editMode: root.hasEditableSelection && root.currentSelectionType === "rectangle"
            selectedItem: root.hasEditableSelection ? root.currentSelection : null
        }

        Lucent.EllipseToolSettings {
            id: ellipseSettings
            visible: root.displayType === "ellipse"
            editMode: root.hasEditableSelection && root.currentSelectionType === "ellipse"
            selectedItem: root.hasEditableSelection ? root.currentSelection : null
        }

        Lucent.PenToolSettings {
            id: penSettings
            visible: root.displayType === "pen" || root.displayType === "path"
            editMode: root.hasEditableSelection && root.currentSelectionType === "path"
            selectedItem: root.hasEditableSelection ? root.currentSelection : null
        }

        Lucent.TextToolSettings {
            id: textSettings
            visible: root.displayType === "text"
            editMode: root.hasEditableSelection && root.currentSelectionType === "text"
            selectedItem: root.hasEditableSelection ? root.currentSelection : null
        }

        // Empty state when no tool selected and no shape selected
        Item {
            visible: !root.hasEditableSelection && (root.activeTool === "select" || root.activeTool === "")
            Layout.fillHeight: true
            Layout.fillWidth: true
        }

        // Spacer
        Item {
            Layout.fillWidth: true
        }
    }
}
