// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Layouts

// Artboard tool settings - placeholder for future presets
RowLayout {
    id: root

    property bool editMode: false
    property var selectedItem: null

    Layout.fillHeight: true
    Layout.alignment: Qt.AlignVCenter
    spacing: 6

    // No settings controls for initial artboard implementation
}
