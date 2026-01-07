pragma Singleton

import QtQuick

// Theme detection and custom colors that follow the OS theme.
QtObject {
    readonly property SystemPalette palette: SystemPalette {
        colorGroup: SystemPalette.Active
    }

    // Direct system color scheme detection (Qt 6.5+)
    readonly property bool isDark: Qt.styleHints.colorScheme === Qt.Dark

    // Custom grid colors that switch with theme
    readonly property color gridBackground: isDark ? "#1e1e1e" : "#f2f2f2"
    readonly property color gridMajor: isDark ? "#3c3c3c" : "#d2d2d2"
    readonly property color gridMinor: isDark ? "#2d2d2d" : "#e6e6e6"

    // Selection overlay accent color
    readonly property color selector: "#409cff"

    // Default tool colors that switch with theme
    readonly property color defaultStroke: "#808080"
    readonly property color defaultFill: "#A0A0A0"
}
