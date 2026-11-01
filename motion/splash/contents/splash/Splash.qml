// SPDX-FileCopyrightText: 2026 Xinyan
// SPDX-License-Identifier: MIT
import QtQuick
import org.kde.kirigami as Kirigami

Rectangle {
    id: root
    color: "#F4F7F2"
    property int stage: 0
    property url backgroundSource: Qt.resolvedUrl("../../../../../wallpapers/KaltsitMedicalGreenMotion/contents/images/poster.jpg")
    readonly property bool reduceMotion: Kirigami.Units.longDuration <= 1
    readonly property real margin: Math.max(24, Math.min(96, width * 0.06))
    readonly property bool ready: stage >= 5
    readonly property string stageLabel: stage <= 2 ? qsTr("正在启动会话")
        : stage === 3 ? qsTr("正在加载工作环境")
        : stage === 4 ? qsTr("正在准备桌面") : qsTr("桌面即将就绪")

    Image {
        anchors.fill: parent
        source: root.backgroundSource
        asynchronous: true
        fillMode: Image.PreserveAspectCrop
    }
    Rectangle {
        anchors.fill: parent
        color: "#F4F7F2"
        opacity: root.stage > 0 ? 0 : 1
        Behavior on opacity { NumberAnimation { duration: root.reduceMotion ? 0 : 650; easing.type: Easing.OutCubic } }
    }
    Rectangle {
        id: card
        x: root.margin
        y: root.height - root.margin - height + (root.stage > 0 ? 0 : 12)
        width: Math.min(392, Math.max(260, root.width * 0.32), root.width - 2 * root.margin)
        height: 208
        radius: 10
        color: "#F4F7F2"
        border.width: 1
        border.color: "#C5D2C8"
        opacity: root.stage > 0 && !root.ready ? 0.97 : 0
        Behavior on opacity { NumberAnimation { duration: root.reduceMotion ? 0 : 320; easing.type: Easing.OutCubic } }
        Behavior on y { NumberAnimation { duration: root.reduceMotion ? 0 : 420; easing.type: Easing.OutCubic } }

        Rectangle { x: 25; y: 26; width: 15; height: 3; color: "#2E6B57" }
        Rectangle { x: 31; y: 20; width: 3; height: 15; color: "#2E6B57" }
        Text {
            x: 51; y: 19
            text: "KAL’TSIT / MEDICAL GREEN"
            color: "#2E6B57"
            font.pixelSize: 10
            font.letterSpacing: 1.3
        }
        Text {
            x: 24; y: 56; width: parent.width - 48
            text: qsTr("医疗白绿")
            color: "#25352D"
            font.pixelSize: 32
            font.weight: Font.Normal
            elide: Text.ElideRight
        }
        Text {
            x: 25; y: 105; width: parent.width - 50
            text: root.stageLabel
            color: "#607265"
            font.pixelSize: 13
            elide: Text.ElideRight
            Accessible.name: text
            Accessible.role: Accessible.StaticText
        }
        Row {
            x: 25; y: 151; spacing: 5
            Repeater {
                model: 5
                Rectangle {
                    required property int index
                    width: (card.width - 70) / 5; height: 2
                    color: root.stage > index ? "#2E6B57" : "#D8E2D7"
                    Behavior on color { ColorAnimation { duration: root.reduceMotion ? 0 : 180 } }
                }
            }
        }
        Text {
            x: 25; y: 171
            text: "PLASMA / NIXOS"
            color: "#607265"
            font.pixelSize: 9
            font.letterSpacing: 1.8
        }
    }
    // KSplash owns the stage and exits when the desktop reports readiness.
    // No minimum-duration timer, fabricated percentage, or login logic.
}
