import QtQuick

// Centralizes default tool settings for canvas tools.
QtObject {
    id: toolDefaults

    property var values: ({
            "rectangle": {
                strokeWidth: 1,
                strokeColor: "#ffffff",
                fillColor: "#ffffff",
                fillOpacity: 0.0
            },
            "ellipse": {
                strokeWidth: 1,
                strokeColor: "#ffffff",
                fillColor: "#ffffff",
                fillOpacity: 0.0
            },
            "pen": {
                strokeWidth: 1,
                strokeColor: "#ffffff",
                strokeOpacity: 1.0,
                fillColor: "#ffffff",
                fillOpacity: 0.0
            }
        })
}
