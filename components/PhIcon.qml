import QtQuick
import Qt5Compat.GraphicalEffects
import "." as DV

Item {
    id: root
    readonly property SystemPalette palette: DV.PaletteBridge.active

    // Icon name (without extension), e.g. "cursor" or "square"
    property string name: ""
    // Icon weight directory under assets/phosphor/, defaults to "regular"
    property string weight: "regular"
    // Icon pixel size (width and height)
    property real size: DV.Styles.height.lg
    // Tint color; set to "transparent" to keep original SVG color
    property color color: "white"

    width: size
    height: size

    readonly property url resolvedSource: name === "" ? "" : Qt.resolvedUrl("../assets/phosphor/" + weight + "/" + name + ".svg")

    Image {
        id: image
        anchors.fill: parent
        source: root.resolvedSource
        sourceSize.width: size
        sourceSize.height: size
        fillMode: Image.PreserveAspectFit
        asynchronous: true
        cache: true
        antialiasing: true
        // Keep visible so ColorOverlay can sample it; hide the paint via opacity when tinted
        opacity: colorOverlay.visible ? 0 : 1
        onStatusChanged: {
            if (status === Image.Error && root.name !== "") {
                console.warn("PhIcon: icon not found", root.resolvedSource);
            }
        }
    }

    ColorOverlay {
        id: colorOverlay
        anchors.fill: image
        source: image
        color: root.color
        visible: root.color.a > 0 && root.name !== ""
    }

    // Graceful fallback if an icon is missing
    Rectangle {
        anchors.fill: parent
        visible: image.status === Image.Error
        color: "#00000000"
        border.color: palette.highlight
        radius: DV.Styles.rad.sm

        Text {
            anchors.centerIn: parent
            text: "?"
            color: palette.highlight
            font.pixelSize: 10
        }
    }
}
