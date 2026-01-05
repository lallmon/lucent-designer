pragma Singleton

import QtQuick

// Single SystemPalette that follows the OS theme.
QtObject {
    readonly property SystemPalette palette: SystemPalette {
        colorGroup: SystemPalette.Active
    }
}
