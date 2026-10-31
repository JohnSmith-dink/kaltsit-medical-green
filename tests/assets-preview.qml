// Original assets rendered by Qt/KSVG, not a desktop screenshot or mockup.
import QtQuick
import QtQuick.Window
import org.kde.ksvg as KSvg

Window {
    id: window
    width: 960
    height: 570
    visible: true
    color: "#F4F7F2"
    title: "Medical Green asset inspection"
    Rectangle { anchors.fill: parent; color: "#F4F7F2" }
    property var sizes: [16, 22, 32, 64]
    property var names: ["folder", "folder-documents", "folder-download", "folder-home", "folder-favorites", "folder-pictures", "folder-music", "folder-videos", "folder-code", "folder-cloud", "folder-recent", "folder-locked"]
    Text { x: 32; y: 24; text: "Medical Green  /  native SVG sizes + Plasma frames"; color: "#25352D"; font.pixelSize: 22 }
    Repeater {
        model: window.sizes
        delegate: Item {
            required property int index
            required property int modelData
            x: 32; y: 90 + index * 82
            width: 900; height: 76
            Text { y: 20; text: modelData + " px"; color: "#607265"; font.pixelSize: 14 }
            Row {
                x: 88; spacing: 4
                Repeater {
                    model: window.names
                    delegate: Item {
                        required property string modelData
                        width: 62; height: 70
                        Image {
                            anchors.centerIn: parent
                            width: parent.parent.parent.modelData
                            height: width
                            sourceSize.width: width
                            sourceSize.height: height
                            source: Qt.resolvedUrl("../share/icons/KaltsitMedicalGreen/places/" + (width === 64 ? "scalable" : width) + "/" + parent.modelData + ".svg")
                        }
                    }
                }
            }
        }
    }
    KSvg.FrameSvgItem {
        id: panel
        x: 32; y: 462; width: 896; height: 62
        imagePath: Qt.resolvedUrl("../share/plasma/desktoptheme/KaltsitMedicalGreen/widgets/panel-background.svg").toString().replace("file://", "")
        Text { anchors.centerIn: parent; text: "Panel frame: white / 1 px border / Breeze interaction controls"; color: "#25352D"; font.pixelSize: 16 }
    }
    Timer {
        interval: 1500; running: true; repeat: false
        onTriggered: {
            console.log("frame margins", panel.margins.left, panel.margins.top, panel.margins.right, panel.margins.bottom)
            window.contentItem.grabToImage(function(result) {
                if (!result.saveToFile(Qt.application.arguments[Qt.application.arguments.length-1])) {
                    Qt.exit(1)
                } else {
                    Qt.quit()
                }
            })
        }
    }
}
