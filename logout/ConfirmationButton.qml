// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Layouts
import org.kde.breeze.components
import org.kde.kirigami as Kirigami
import "MedicalPalette.js" as Palette

// Keep Breeze's mnemonic, keyboard and accessible button behavior.
ActionButton {
    id: action
    implicitWidth: 120
    implicitHeight: Math.max(40, caption.implicitHeight + 8)
    padding: 4
    horizontalPadding: 4
    bottomPadding: 4
    leftInset: 0
    rightInset: 0
    opacity: 1
    background: Rectangle {
        radius: 5
        color: action.activeFocus || action.hovered ? Qt.alpha(Palette.window, 0.16) : "transparent"
        border.color: Palette.selectedText
        border.width: action.activeFocus ? 2 : 0
        Rectangle {
            anchors.fill: parent
            anchors.margins: -1
            radius: 6
            color: "transparent"
            border.color: Qt.alpha(Palette.text, 0.85)
            visible: action.activeFocus
        }
    }
    contentItem: RowLayout {
        spacing: 6
        Rectangle {
            Layout.preferredWidth: 30
            Layout.preferredHeight: 30
            radius: 15
            color: Palette.accent
            Kirigami.Icon {
                anchors.centerIn: parent
                width: 18; height: 18
                source: action.icon.name
                isMask: true
                color: Palette.selectedText
            }
        }
        Text {
            id: caption
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            text: action.Kirigami.MnemonicData.richTextLabel
            textFormat: Text.StyledText
            wrapMode: Text.Wrap
            color: Palette.selectedText
            font.family: action.font.family
            font.pixelSize: 14
            font.weight: Font.Medium
            style: Text.Outline
            styleColor: Qt.alpha(Palette.text, 0.85)
        }
    }
}
