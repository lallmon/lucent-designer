pragma Singleton

import QtQuick

// Centralized UI constants for DesignVibe (QML-native).
// Keep this file small and stable; add tokens here rather than hard-coding
// values throughout components.
QtObject {
    readonly property QtObject colors: QtObject {
        // App surfaces
        readonly property color canvasBackground: "#2b2b2b"
        readonly property color panelBackground: "#3c3c3c"
        readonly property color panelHover: "#4c4c4c"
        readonly property color panelActive: "#5c5c5c"

        // Lines / borders
        readonly property color borderDefault: "#6c6c6c"
        readonly property color borderSubtle: "#555555"

        // Grid
        readonly property color gridMinor: "#3a3a3a"
        readonly property color gridMajor: "#5a5a5a"

        // Text / icons
        readonly property color textSubtle: "#dcdcdc"

        // Accents / feedback
        readonly property color accent: "#0078d4"
        readonly property color accentHover: "#1a8ae6"
        readonly property color error: "#ff7373"
    }

    readonly property QtObject sizes: QtObject {
        // Toolbar
        readonly property int toolBarWidth: 48
        readonly property int toolBarPadding: 8
        readonly property int toolBarSpacing: 8

        // Right Panel
        readonly property int rightPanelDefaultWidth: 220
        readonly property int rightPanelMinWidth: 128
        readonly property int rightPanelMaxWidth: 256
        readonly property int rightPanelPadding: 12

        // Buttons / icons
        readonly property int toolButtonSize: 32
        readonly property int iconSize: 24
        readonly property int statusIconSize: 16

        // Radii
        readonly property int radiusSm: 2
        readonly property int radiusMd: 4
        readonly property int radiusLg: 6

        // Form controls
        readonly property int settingsFieldHeight: 20
        readonly property int settingsStrokeWidthFieldWidth: 50
        readonly property int settingsOpacityFieldWidth: 35

        // Slider
        readonly property int sliderHeight: 16
        readonly property int sliderTrackHeight: 4
        readonly property int sliderHandleSize: 12
    }
}


