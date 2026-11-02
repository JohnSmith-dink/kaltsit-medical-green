// SPDX-FileCopyrightText: 2026 Xinyan
// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic as Controls
import "Palette.js" as Palette

Item {
    id: root
    readonly property real surfaceOpacity: 0.96
    property bool busy: false
    property string errorMessage: ""
    property bool errorBorder: false
    property bool manualUser: false
    property string selectedUser: ""
    property int selectedSession: sessionModel.lastIndex
    readonly property string loginUser: manualUser ? username.text.trim() : selectedUser
    property date now: new Date()
    readonly property var weekdays: [qsTr("星期日"), qsTr("星期一"), qsTr("星期二"), qsTr("星期三"), qsTr("星期四"), qsTr("星期五"), qsTr("星期六")]

    // Model adapters only; they never draw or enter the keyboard focus chain.
    Controls.ComboBox { id: users; visible: false; enabled: false; activeFocusOnTab: false; model: userModel; textRole: "name" }
    Controls.ComboBox { id: sessions; visible: false; enabled: false; activeFocusOnTab: false; model: sessionModel; textRole: "name" }

    function userIndex(name) {
        for (let i = 0; i < users.count; ++i) if (users.textAt(i) === name) return i;
        return -1;
    }
    function userTarget() { return manualUser ? username : userButton; }
    function focusInput() {
        if (loginUser.length) password.forceActiveFocus();
        else userTarget().forceActiveFocus();
    }
    function clearAttempt() {
        password.clear(); errorMessage = ""; errorBorder = false; errorFlash.stop();
    }
    function chooseUser(index) {
        clearAttempt();
        manualUser = index === users.count;
        selectedUser = manualUser ? "" : users.textAt(index);
        username.text = "";
        Qt.callLater(focusInput);
    }
    function openUsers(trigger) {
        userPopup.triggerItem = trigger;
        userPopup.currentIndex = manualUser ? users.count : Math.max(0, userIndex(selectedUser));
        userPopup.open();
    }
    function login() {
        if (busy || !loginUser.length || selectedSession < 0 || selectedSession >= sessions.count) return;
        errorMessage = "";
        busy = true;
        // Only SDDM receives the credential; never log or persist it.
        sddm.login(loginUser, password.text, selectedSession);
        password.clear();
    }
    Component.onCompleted: Qt.callLater(() => {
        const remembered = userModel.lastUser || "";
        manualUser = users.count === 0 || (remembered.length > 0 && userIndex(remembered) < 0);
        selectedUser = manualUser ? "" : (remembered || users.textAt(0));
        username.text = manualUser ? remembered : "";
        focusInput();
    })
    Connections {
        target: sddm
        function onLoginFailed() {
            root.busy = false;
            root.errorMessage = qsTr("登录失败，请检查用户名和密码。");
            password.clear(); password.forceActiveFocus();
            root.errorBorder = true; errorFlash.restart();
        }
        function onLoginSucceeded() { password.clear(); }
    }
    Timer { id: errorFlash; interval: 600; onTriggered: root.errorBorder = false }
    Timer { interval: 1000; running: root.visible; repeat: true; onTriggered: root.now = new Date() }

    Rectangle { anchors.fill: parent; color: Palette.view }
    Image { anchors.fill: parent; source: Qt.resolvedUrl("background.jpg"); fillMode: Image.PreserveAspectCrop; autoTransform: true }

    component LightSurface: Rectangle {
        color: Palette.window
        opacity: root.surfaceOpacity
        radius: 8
    }
    component ThemeButton: Controls.Button {
        id: button
        property bool primary: false
        property bool round: false
        implicitHeight: 48
        padding: 12
        font.pixelSize: 16
        focusPolicy: Qt.StrongFocus
        Keys.onReturnPressed: if (enabled) clicked()
        Keys.onEnterPressed: if (enabled) clicked()
        contentItem: Text {
            text: button.text
            textFormat: Text.PlainText
            color: button.primary && button.enabled ? Palette.selectedText : (button.enabled ? Palette.text : Palette.secondary)
            font: button.font
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: Item {
            Rectangle {
                anchors.fill: parent
                radius: button.round ? height / 2 : 8
                color: button.primary && button.enabled ? Palette.selected : Palette.window
                opacity: button.primary && button.enabled ? 1 : root.surfaceOpacity
            }
            Rectangle {
                anchors.fill: parent
                anchors.margins: button.primary ? 3 : 0
                radius: button.round ? height / 2 : 8
                color: "transparent"
                visible: button.activeFocus || button.hovered
                border.color: button.primary && button.enabled ? Palette.selectedText : Palette.accent
                border.width: button.activeFocus ? 2 : 1
            }
        }
    }
    component ThemeInput: Controls.TextField {
        id: field
        property bool warn: false
        implicitHeight: 48
        padding: 12
        font.pixelSize: 16
        color: Palette.text
        placeholderTextColor: Palette.secondary
        selectionColor: Palette.selected
        selectedTextColor: Palette.selectedText
        background: Item {
            LightSurface { anchors.fill: parent }
            Rectangle {
                anchors.fill: parent; radius: 8; color: "transparent"
                border.color: field.activeFocus ? Palette.accent : Palette.secondary
                border.width: field.activeFocus ? 2 : 1
            }
            Rectangle {
                anchors.fill: parent; anchors.margins: 4; radius: 4; color: "transparent"
                visible: field.warn; border.color: Palette.negative; border.width: 1
            }
        }
    }
    component ChoicePopup: Controls.Popup {
        id: popup
        property int itemCount: 0
        property var labelFor
        property Item triggerItem
        property alias currentIndex: list.currentIndex
        signal chosen(int index)
        width: loginGroup.width
        height: Math.min(itemCount * 44 + 8, 272, root.height - 48)
        padding: 4
        parent: root
        focus: true
        modal: true
        dim: false
        enter: null
        exit: null
        closePolicy: Controls.Popup.CloseOnEscape | Controls.Popup.CloseOnPressOutside
        onOpened: { list.forceActiveFocus(); list.positionViewAtIndex(currentIndex, ListView.Contain); }
        onClosed: if (triggerItem && triggerItem.visible && triggerItem.enabled) triggerItem.forceActiveFocus();
        function choose(index) { close(); chosen(index); }
        background: Rectangle { color: Palette.window; radius: 8; border.color: Palette.accent; border.width: 2 }
        contentItem: ListView {
            id: list
            clip: true
            model: popup.itemCount
            keyNavigationWraps: true
            boundsBehavior: Flickable.StopAtBounds
            Keys.onPressed: event => {
                if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Space) {
                    if (currentIndex >= 0) popup.choose(currentIndex);
                    event.accepted = true;
                } else if (event.key === Qt.Key_Escape) {
                    popup.close(); event.accepted = true;
                } else if (event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab) {
                    popup.close(); event.accepted = true;
                }
            }
            delegate: Controls.ItemDelegate {
                required property int index
                width: ListView.view.width
                height: 44
                highlighted: ListView.isCurrentItem
                onClicked: popup.choose(index)
                contentItem: Text {
                    text: popup.labelFor(index); textFormat: Text.PlainText
                    color: parent.highlighted ? Palette.selectedText : Palette.text
                    font.pixelSize: 16; elide: Text.ElideRight
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle { color: parent.highlighted ? Palette.selected : Palette.window; radius: 4 }
            }
            Controls.ScrollIndicator.vertical: Controls.ScrollIndicator { }
        }
    }

    Column {
        id: clock
        objectName: "clock"
        anchors.horizontalCenter: parent.horizontalCenter
        y: Math.max(24, root.height * 0.12)
        spacing: 8
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Qt.formatTime(root.now, "HH:mm")
            color: Palette.text; style: Text.Outline; styleColor: Palette.window
            font.pixelSize: Math.max(64, Math.min(96, root.height * 0.1))
            font.bold: true
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            objectName: "calendarDate"
            text: Qt.formatDate(root.now, qsTr("yyyy年M月d日")) + " " + root.weekdays[root.now.getDay()]
            color: Palette.text; style: Text.Outline; styleColor: Palette.window
            font.pixelSize: 22
        }
    }
    Column {
        id: loginGroup
        objectName: "loginGroup"
        width: Math.min(336, root.width - 48)
        anchors.horizontalCenter: parent.horizontalCenter
        y: Math.max(clock.y + clock.height + 32, root.height * 0.61 - height / 2)
        spacing: 12
        Item {
            width: parent.width; height: 48
            ThemeButton {
                id: userButton
                objectName: "userSelection"
                anchors.horizontalCenter: parent.horizontalCenter
                width: Math.min(implicitWidth, parent.width)
                visible: !root.manualUser; enabled: !root.busy
                text: root.selectedUser; font.pixelSize: 20
                Accessible.name: qsTr("选择用户：%1").arg(text)
                onClicked: root.openUsers(userButton)
                KeyNavigation.tab: password
                KeyNavigation.backtab: rebootButton
            }
            Row {
                anchors.fill: parent
                spacing: 8; visible: root.manualUser
                ThemeInput {
                    id: username
                    objectName: "username"
                    width: parent.width - (manualMenu.visible ? 56 : 0)
                    enabled: !root.busy; placeholderText: qsTr("输入用户名")
                    inputMethodHints: Qt.ImhNoPredictiveText
                    onAccepted: password.forceActiveFocus()
                    KeyNavigation.tab: manualMenu.visible ? manualMenu : password
                    KeyNavigation.backtab: rebootButton
                }
                ThemeButton {
                    id: manualMenu
                    objectName: "manualUserMenu"
                    width: 48; text: "▾"
                    visible: users.count > 0; enabled: !root.busy
                    Accessible.name: qsTr("选择用户")
                    onClicked: root.openUsers(manualMenu)
                    KeyNavigation.tab: password
                    KeyNavigation.backtab: username
                }
            }
        }
        Row {
            width: parent.width; spacing: 8
            ThemeInput {
                id: password
                objectName: "password"
                width: parent.width - 56
                placeholderText: qsTr("输入密码")
                echoMode: TextInput.Password
                enabled: !root.busy; warn: root.errorBorder
                inputMethodHints: Qt.ImhSensitiveData | Qt.ImhHiddenText | Qt.ImhNoPredictiveText
                onAccepted: root.login()
                KeyNavigation.tab: loginButton
                KeyNavigation.backtab: root.manualUser && manualMenu.visible ? manualMenu : root.userTarget()
            }
            ThemeButton {
                id: loginButton
                objectName: "loginButton"
                width: 48; primary: true; round: true
                enabled: !root.busy && root.loginUser.length > 0 && root.selectedSession >= 0 && root.selectedSession < sessions.count
                Accessible.name: root.busy ? qsTr("正在登录…") : qsTr("登录")
                onClicked: root.login()
                KeyNavigation.tab: sessionButton
                KeyNavigation.backtab: password
                contentItem: Item {
                    Repeater {
                        model: 2
                        Rectangle {
                            required property int index
                            width: 13; height: 2
                            anchors.centerIn: parent
                            anchors.verticalCenterOffset: index === 0 ? -4 : 4
                            rotation: index === 0 ? 45 : -45
                            color: loginButton.enabled ? Palette.selectedText : Palette.secondary
                        }
                    }
                }
            }
        }
        Item {
            width: parent.width
            height: Math.max(44, errorText.implicitHeight + 16)
            LightSurface { anchors.fill: parent; visible: errorText.visible }
            Text {
                id: errorText
                objectName: "loginError"
                x: 10; y: 8; width: parent.width - 20
                text: sessions.count === 0 ? qsTr("没有可用会话，请检查系统配置。") : root.errorMessage
                visible: text.length > 0
                textFormat: Text.PlainText
                color: Palette.negative; font.pixelSize: 14
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }
    ChoicePopup {
        id: userPopup
        objectName: "userPopup"
        x: loginGroup.x
        y: Math.min(loginGroup.y + 56, root.height - height - 24)
        itemCount: users.count + 1
        labelFor: index => index === users.count ? qsTr("其他…") : users.textAt(index)
        onChosen: index => root.chooseUser(index)
    }
    ChoicePopup {
        id: sessionPopup
        objectName: "sessionPopup"
        x: footerLeft.x
        y: Math.max(24, footerLeft.y - height - 8)
        itemCount: sessions.count
        labelFor: index => sessions.textAt(index)
        triggerItem: sessionButton
        onChosen: index => root.selectedSession = index
    }
    Row {
        id: footerLeft
        objectName: "footerLeft"
        x: 24; y: root.height - height - 24; spacing: 8
        ThemeButton {
            id: sessionButton
            objectName: "sessionSelection"
            width: Math.min(320, Math.max(140, root.width - footerRight.width - keyboardPlate.width - 88), implicitWidth)
            font.pixelSize: 14
            text: qsTr("会话：%1").arg(root.selectedSession >= 0 && root.selectedSession < sessions.count ? sessions.textAt(root.selectedSession) : qsTr("无"))
            enabled: !root.busy && sessions.count > 0
            onClicked: { sessionPopup.currentIndex = Math.max(0, root.selectedSession); sessionPopup.open(); }
            KeyNavigation.tab: shutdownButton
            KeyNavigation.backtab: loginButton
        }
        Item {
            id: keyboardPlate
            width: keyboardText.implicitWidth + 24; height: 48
            LightSurface { anchors.fill: parent }
            Text {
                id: keyboardText
                anchors.centerIn: parent
                text: qsTr("键盘：%1").arg(keyboard.layouts.length > keyboard.currentLayout && keyboard.currentLayout >= 0 ? keyboard.layouts[keyboard.currentLayout].shortName : qsTr("未知"))
                textFormat: Text.PlainText
                font.pixelSize: 14; color: Palette.secondary
            }
        }
    }
    Row {
        id: footerRight
        objectName: "footerRight"
        anchors.right: parent.right; anchors.rightMargin: 24
        y: root.height - height - 24; spacing: 8
        ThemeButton {
            id: shutdownButton
            objectName: "shutdownButton"
            text: qsTr("关机"); font.pixelSize: 14
            enabled: !root.busy && sddm.canPowerOff
            onClicked: sddm.powerOff()
            KeyNavigation.tab: rebootButton
            KeyNavigation.backtab: sessionButton
        }
        ThemeButton {
            id: rebootButton
            objectName: "rebootButton"
            text: qsTr("重启"); font.pixelSize: 14
            enabled: !root.busy && sddm.canReboot
            onClicked: sddm.reboot()
            KeyNavigation.tab: root.userTarget()
            KeyNavigation.backtab: shutdownButton
        }
    }
}
