// SPDX-License-Identifier: MIT
import QtQuick
import org.kde.breeze.components
import org.kde.kirigami as Kirigami

// Breeze keeps its activation, shortcuts and accessibility.
ActionButton {
    id: action
    implicitWidth: caption.implicitWidth + 12
    implicitHeight: 32
    leftInset: 0
    rightInset: 0
    padding: 4
    opacity: 1
    background: Item {}
    contentItem: MedicalButtonCaption {
        id: caption
        control: action
        text: action.Kirigami.MnemonicData.richTextLabel
        textFormat: Text.StyledText
    }
}
