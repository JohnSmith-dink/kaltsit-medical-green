// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import "MedicalPalette.js" as Palette

// The clock and the identity row use the same geometry as the wake screen.
// Long firmware/update notices and extra actions can scroll in this column.
Flickable {
    id: view
    default property alias rows: body.data
    required property string displayName
    readonly property string displayFamily: Qt.fontFamilies().includes("OPPO Sans 4.0")
                                            ? "OPPO Sans 4.0" : Kirigami.Theme.defaultFont.family
    readonly property real leftEdge: parent.width >= 960 ? 72 : Math.max(24, Math.floor(parent.width * 0.075))
    readonly property real formWidth: Math.max(1, Math.min(288, parent.width - 2 * leftEdge))
    readonly property real gutter: 4 // Allow outlines and focus borders outside the aligned content edge.
    x: leftEdge - gutter
    width: formWidth + 2 * gutter
    height: parent.height
    contentWidth: width
    contentHeight: Math.max(height, body.y + body.implicitHeight + 24)
    clip: true
    interactive: contentHeight > height
    flickableDirection: Flickable.VerticalFlick
    boundsBehavior: Flickable.StopAtBounds

    function revealFocus() {
        if (!interactive) return;
        const item = view.Window.window?.activeFocusItem;
        for (let ancestor = item; ancestor; ancestor = ancestor.parent) {
            if (ancestor !== body) continue;
            const top = item.mapToItem(view.contentItem, 0, 0).y - view.gutter;
            const bottom = top + item.height + 2 * view.gutter;
            if (top < contentY) contentY = Math.max(0, top);
            else if (bottom > contentY + height) contentY = Math.min(contentHeight - height, bottom - height);
            break;
        }
    }
    Connections {
        target: view.Window.window
        function onActiveFocusItemChanged() { Qt.callLater(view.revealFocus); }
    }
    onContentHeightChanged: Qt.callLater(revealFocus)
    Controls.ScrollIndicator.vertical: Controls.ScrollIndicator {}

    MedicalClock {
        id: clock
        x: view.gutter
        width: view.formWidth
        family: view.displayFamily
    }
    ColumnLayout {
        id: body
        x: view.gutter
        width: view.formWidth
        y: Math.max(clock.height + 16,
                    Math.min(Math.round(view.height * 0.451), view.height - 24 - implicitHeight))
        spacing: 12
        RowLayout {
            objectName: "confirmationIdentity"
            Layout.fillWidth: true
            spacing: 14
            Rectangle {
                Layout.preferredWidth: 48
                Layout.preferredHeight: 48
                radius: 24
                color: Palette.accent
                Text {
                    anchors.centerIn: parent
                    text: Array.from(view.displayName.trim())[0]?.toUpperCase() || ""
                    textFormat: Text.PlainText
                    color: Palette.selectedText
                    font.family: view.displayFamily
                    font.pixelSize: 22
                    font.weight: Font.Medium
                }
            }
            Text {
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                text: view.displayName
                textFormat: Text.PlainText
                elide: Text.ElideRight
                color: Palette.selectedText
                font.family: view.displayFamily
                font.pixelSize: 18
                font.weight: Font.Medium
                style: Text.Outline
                styleColor: Qt.alpha(Palette.text, 0.85)
            }
        }
    }
}
