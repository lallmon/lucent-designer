// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

pragma Singleton

import QtQuick

QtObject {
    readonly property QtObject height: QtObject {
        readonly property int xxxsm: 4
        readonly property int xxsm: 8
        readonly property int xs: 12
        readonly property int sm: 16
        readonly property int md: 20
        readonly property int lg: 24
        readonly property int xlg: 32
        readonly property int xxlg: 40
        readonly property int xxxlg: 48
    }

    readonly property QtObject margin: QtObject {
        readonly property int sm: 4
        readonly property int md: 8
        readonly property int lg: 12
    }

    readonly property QtObject pad: QtObject {
        readonly property int xsm: 4
        readonly property int sm: 4
        readonly property int md: 8
        readonly property int lg: 12
    }

    readonly property QtObject rad: QtObject {
        readonly property int sm: 2
        readonly property int md: 4
        readonly property int lg: 6
    }
}
