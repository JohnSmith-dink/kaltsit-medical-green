// SPDX-FileCopyrightText: 2026 Xinyan
// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic as Controls
import "Palette.js" as Palette

Item {
    id: root
    property bool busy: false
    property string errorMessage: ""

    function focusInput() {
        if (username.text.length) password.forceActiveFocus();
        else username.forceActiveFocus();
    }
    function login() {
        if (busy || !username.text.trim().length || sessions.currentIndex < 0) return;
        errorMessage = "";
        busy = true;
        // Only SDDM receives the credential; never log or persist it.
        sddm.login(username.text.trim(), password.text, sessions.currentIndex);
        password.clear();
    }
    Component.onCompleted: {
        username.text = userModel.lastUser || users.currentValue || "";
        Qt.callLater(focusInput);
    }
    Connections {
        target: sddm
        function onLoginFailed() {
            root.busy = false;
            root.errorMessage = qsTr("登录失败，请检查用户名和密码。");
            password.clear();
            password.forceActiveFocus();
        }
        function onLoginSucceeded() { password.clear(); }
    }

    Rectangle { anchors.fill: parent; color: Palette.view }
    Image {
        anchors.fill: parent
        source: Qt.resolvedUrl("background.jpg")
        fillMode: Image.PreserveAspectCrop
        autoTransform: true
    }

    component ThemeButton: Controls.Button {
        id: button
        property bool primary: false
        implicitHeight: 44
        focusPolicy: Qt.StrongFocus
        padding: 12
        contentItem: Text {
            text: button.text
            color: button.primary && button.enabled ? Palette.selectedText : (button.enabled ? Palette.text : Palette.secondary)
            font.pixelSize: 16
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            radius: 6
            color: button.primary && button.enabled ? Palette.selected : (button.hovered ? Palette.alternate : Palette.window)
            border.color: button.activeFocus ? Palette.accent : Palette.secondary
            border.width: button.activeFocus ? 3 : 1
        }
    }
    component ThemeInput: Controls.TextField {
        id: field
        implicitHeight: 46
        padding: 12
        font.pixelSize: 18
        color: Palette.text
        placeholderTextColor: Palette.secondary
        selectionColor: Palette.selected
        selectedTextColor: Palette.selectedText
        background: Rectangle {
            color: Palette.view
            radius: 6
            border.color: field.activeFocus ? Palette.accent : Palette.secondary
            border.width: field.activeFocus ? 3 : 1
        }
    }
    component ThemeSelect: Controls.ComboBox {
        id: select
        implicitHeight: 44
        padding: 12
        font.pixelSize: 16
        focusPolicy: Qt.StrongFocus
        palette.window: Palette.window
        palette.base: Palette.window
        palette.text: Palette.text
        palette.buttonText: Palette.text
        palette.highlight: Palette.selected
        palette.highlightedText: Palette.selectedText
        contentItem: Text {
            text: select.displayText
            color: Palette.text
            font: select.font
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            rightPadding: 26
        }
        indicator: Text {
            text: "▾"
            color: Palette.text
            font.pixelSize: 20
            x: select.width-width-12
            anchors.verticalCenter: parent.verticalCenter
        }
        background: Rectangle {
            color: select.hovered ? Palette.alternate : Palette.window
            radius: 6
            border.color: select.activeFocus ? Palette.accent : Palette.secondary
            border.width: select.activeFocus ? 3 : 1
        }
        delegate: Controls.ItemDelegate {
            required property int index
            required property var model
            width: select.width
            text: model[select.textRole] || model.name || ""
            highlighted: select.highlightedIndex === index
            contentItem: Text {
                text: parent.text
                color: parent.highlighted ? Palette.selectedText : Palette.text
                font.pixelSize: 16
                elide: Text.ElideRight
            }
            background: Rectangle { color: parent.highlighted ? Palette.selected : Palette.window }
        }
        popup: Controls.Popup {
            y: select.height+4
            width: select.width
            implicitHeight: Math.min(contentItem.implicitHeight+2, 240)
            padding: 1
            contentItem: ListView {
                clip: true
                implicitHeight: contentHeight
                model: select.popup.visible ? select.delegateModel : null
                currentIndex: select.highlightedIndex
                Controls.ScrollIndicator.vertical: Controls.ScrollIndicator { }
            }
            background: Rectangle { color: Palette.window; border.color: Palette.secondary; radius: 6 }
        }
    }

    Rectangle {
        id: panel
        width: Math.min(440, Math.max(0, root.width-48))
        height: Math.min(form.implicitHeight+48, Math.max(0, root.height-48))
        x: root.width >= 1000 ? Math.round(root.width*0.09) : Math.round((root.width-width)/2)
        anchors.verticalCenter: parent.verticalCenter
        color: Palette.window
        radius: 12
        border.color: Palette.secondary
        border.width: 1
        Controls.ScrollView {
            id: scroll
            anchors.fill: parent
            anchors.margins: 24
            clip: true
            contentWidth: availableWidth
            ColumnLayout {
                id: form
                width: scroll.availableWidth
                spacing: 12
                Text { text: qsTr("凯尔希 · 医疗白绿"); color: Palette.text; font.pixelSize: 25; font.bold: true; Layout.fillWidth: true; wrapMode: Text.WordWrap }
                Text { text: qsTr("登录"); color: Palette.secondary; font.pixelSize: 16 }
                Text { text: qsTr("用户"); color: Palette.text; font.pixelSize: 15; visible: users.count>0 }
                ThemeSelect {
                    id: users
                    objectName: "userSelection"
                    Layout.fillWidth: true
                    visible: count>0
                    model: userModel
                    textRole: "name"
                    valueRole: "name"
                    currentIndex: userModel.lastIndex
                    enabled: !root.busy
                    onActivated: { username.text=currentValue || ""; password.clear(); root.errorMessage=""; root.focusInput(); }
                }
                Text { text: qsTr("用户名"); color: Palette.text; font.pixelSize: 15 }
                ThemeInput {
                    id: username
                    objectName: "username"
                    Layout.fillWidth: true
                    placeholderText: qsTr("输入用户名")
                    enabled: !root.busy
                    inputMethodHints: Qt.ImhNoPredictiveText
                    onAccepted: password.forceActiveFocus()
                }
                Text { text: qsTr("密码"); color: Palette.text; font.pixelSize: 15 }
                ThemeInput {
                    id: password
                    objectName: "password"
                    Layout.fillWidth: true
                    placeholderText: qsTr("输入密码")
                    echoMode: TextInput.Password
                    enabled: !root.busy
                    inputMethodHints: Qt.ImhSensitiveData | Qt.ImhHiddenText | Qt.ImhNoPredictiveText
                    onAccepted: root.login()
                }
                Text { text: qsTr("会话"); color: Palette.text; font.pixelSize: 15 }
                ThemeSelect {
                    id: sessions
                    objectName: "sessionSelection"
                    Layout.fillWidth: true
                    model: sessionModel
                    textRole: "name"
                    currentIndex: sessionModel.lastIndex
                    enabled: !root.busy
                }
                Text {
                    Layout.fillWidth: true
                    text: qsTr("键盘布局：%1").arg(keyboard.layouts.length>keyboard.currentLayout && keyboard.currentLayout>=0 ? keyboard.layouts[keyboard.currentLayout].shortName : qsTr("未知"))
                    color: Palette.secondary
                    font.pixelSize: 14
                    elide: Text.ElideRight
                }
                Text {
                    objectName: "loginError"
                    Layout.fillWidth: true
                    text: sessions.count===0 ? qsTr("没有可用会话，请检查系统配置。") : root.errorMessage
                    visible: text.length>0
                    color: Palette.negative
                    font.pixelSize: 15
                    wrapMode: Text.WordWrap
                }
                ThemeButton {
                    objectName: "loginButton"
                    Layout.fillWidth: true
                    primary: true
                    text: root.busy ? qsTr("正在登录…") : qsTr("登录")
                    enabled: !root.busy && username.text.trim().length>0 && sessions.currentIndex>=0
                    onClicked: root.login()
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12
                    ThemeButton { objectName: "shutdownButton"; Layout.fillWidth: true; text: qsTr("关机"); enabled: !root.busy && sddm.canPowerOff; onClicked: sddm.powerOff() }
                    ThemeButton { objectName: "rebootButton"; Layout.fillWidth: true; text: qsTr("重启"); enabled: !root.busy && sddm.canReboot; onClicked: sddm.reboot() }
                }
            }
        }
    }
}
