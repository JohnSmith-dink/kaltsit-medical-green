// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Templates as T
import "MedicalPalette.js" as Palette

Text {
    required property T.AbstractButton control
    text: control.text
    textFormat: Text.PlainText
    font.family: lockScreenUi.displayFamily
    font.pixelSize: 14
    font.weight: Font.Medium
    color: Palette.selectedText
    style: Text.Outline
    styleColor: Qt.alpha(Palette.text, 0.85)
    verticalAlignment: Text.AlignVCenter
    horizontalAlignment: Text.AlignHCenter
    Rectangle {
        z: -1
        anchors.fill: parent
        anchors.margins: -3
        radius: 5
        color: control.hovered || control.activeFocus ? Qt.alpha(Palette.window, 0.16) : "transparent"
        border.width: control.activeFocus ? 2 : 0
        border.color: Palette.selectedText
        Rectangle {
            anchors.fill: parent
            anchors.margins: -1
            radius: 6
            color: "transparent"
            border.color: Qt.alpha(Palette.text, 0.85)
            visible: control.activeFocus
        }
    }
}
