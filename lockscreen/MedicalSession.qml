// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import "MedicalPalette.js" as Palette

// Layout for the *native* MainBlock and NoPasswordUnlock components. Their
// controls, password handling and authenticator connections stay with KDE.
FocusScope {
    id: page
    default property alias controls: form.children
    property alias userListModel: accounts.model
    property alias userList: accounts
    property alias actionItems: actions.children
    property alias notificationMessage: message.text
    property bool showUserList: true
    signal userSelected()
    function playHighlightAnimation() { pulse.restart(); }
    readonly property real contentBottom: body.y + body.implicitHeight

    ListView {
        id: accounts
        width: page.width
        height: 48
        y: Math.max(0, Math.min(Math.round(page.height * 0.451),
                                page.height - height - 18 - body.implicitHeight - 56))
        visible: page.showUserList
        activeFocusOnTab: true
        orientation: ListView.Horizontal
        interactive: count > 1
        snapMode: ListView.SnapOneItem
        highlightRangeMode: ListView.StrictlyEnforceRange
        preferredHighlightBegin: 0
        preferredHighlightEnd: 0
        clip: true
        delegate: Controls.ItemDelegate {
            id: account
            required property int index
            required property string name
            required property string realName
            readonly property string displayName: realName || name
            width: accounts.width
            height: accounts.height
            leftPadding: 0; rightPadding: 0
            topPadding: 0; bottomPadding: 0
            focusPolicy: Qt.NoFocus
            Accessible.name: displayName
            onClicked: {
                accounts.currentIndex = index;
                page.userSelected();
            }
            background: Item { }
            contentItem: Row {
                spacing: 14
                Rectangle {
                    width: 48; height: 48; radius: 24
                    color: Palette.accent
                    border.width: accounts.activeFocus ? 2 : 0
                    border.color: Palette.selectedText
                    Text {
                        anchors.centerIn: parent
                        text: Array.from(account.displayName.trim())[0]?.toUpperCase() || ""
                        textFormat: Text.PlainText
                        color: Palette.selectedText
                        font.family: lockScreenUi.displayFamily
                        font.pixelSize: 22
                        font.weight: Font.Medium
                    }
                }
                Text {
                    width: Math.max(0, account.width - 62); height: account.height
                    text: account.displayName
                    textFormat: Text.PlainText
                    color: Palette.selectedText
                    font.family: lockScreenUi.displayFamily
                    font.pixelSize: 18
                    font.weight: Font.Medium
                    style: Text.Outline
                    styleColor: Qt.alpha(Palette.text, 0.85)
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
            }
        }
        Keys.onEscapePressed: page.userSelected()
        Keys.onEnterPressed: page.userSelected()
        Keys.onReturnPressed: page.userSelected()
    }
    ColumnLayout {
        id: body
        anchors.top: accounts.bottom
        anchors.topMargin: 18
        width: page.width
        spacing: 8
        ColumnLayout {
            id: form
            Layout.fillWidth: true
            spacing: 6
        }
        Text {
            id: message
            objectName: "medicalLockMessage"
            Layout.fillWidth: true
            visible: text.length > 0
            textFormat: Text.PlainText
            wrapMode: Text.Wrap
            color: Palette.negative
            font.family: lockScreenUi.displayFamily
            font.pixelSize: 14
            font.weight: Font.Medium
            style: Text.Outline
            styleColor: Qt.alpha(Palette.window, 0.90)
            SequentialAnimation {
                id: pulse
                NumberAnimation { target: message; property: "opacity"; to: 0.6; duration: 100 }
                NumberAnimation { target: message; property: "opacity"; to: 1; duration: 100 }
            }
        }
        Flow {
            id: actions
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
            spacing: 4
        }
    }
}
