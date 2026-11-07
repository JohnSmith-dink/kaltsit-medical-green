// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents
import "MedicalPalette.js" as Palette

PlasmaComponents.Label {
    Layout.fillWidth: true
    Layout.minimumWidth: 0
    font.pixelSize: 14
    font.weight: Font.Medium
    horizontalAlignment: Text.AlignLeft
    wrapMode: Text.Wrap
    color: Palette.selectedText
    style: Text.Outline
    styleColor: Qt.alpha(Palette.text, 0.85)
}
