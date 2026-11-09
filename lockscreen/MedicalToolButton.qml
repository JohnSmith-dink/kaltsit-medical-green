// SPDX-License-Identifier: MIT
import QtQuick
import org.kde.plasma.components as PlasmaComponents

PlasmaComponents.ToolButton {
    id: button
    implicitWidth: caption.implicitWidth + 12
    implicitHeight: 32
    padding: 4
    background: Item {}
    contentItem: MedicalButtonCaption { id: caption; control: button }
}
