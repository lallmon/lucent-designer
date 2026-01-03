pragma Singleton

import QtQuick

// Single source of truth for system palette so components don't each create one.
QtObject {
    property SystemPalette active: SystemPalette {
        colorGroup: SystemPalette.Active
    }
}
