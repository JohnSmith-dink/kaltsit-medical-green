// SPDX-FileCopyrightText: 2026 Xinyan
// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Controls.Basic as Controls
import "Palette.js" as Palette

Item {
    id: root
    readonly property real leftInset: 64
    readonly property real panelWidth: 320
    readonly property real panelOpacity: 0.86
    readonly property real inputOpacity: 0.9
    readonly property color panelColor: Palette.view
    readonly property color inputColor: Palette.window
    readonly property bool canChooseUser: users.count > 1
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
    function firstInput() { return manualUser ? (canChooseUser ? manualMenu : username) : (canChooseUser ? userButton : password); }
    function focusInput() {
        if (loginUser.length) password.forceActiveFocus();
        else username.forceActiveFocus();
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
        if (!canChooseUser || busy) return;
        sessionList.close();
        userList.triggerItem = trigger;
        userList.currentIndex = manualUser ? users.count : Math.max(0, userIndex(selectedUser));
        userList.open();
    }
    function login() {
        if (busy || !loginUser.length || selectedSession < 0 || selectedSession >= sessions.count) return;
        userList.close(); sessionList.close();
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
    Image {
        objectName: "wallpaper"
        anchors.fill: parent
        source: Qt.resolvedUrl("background.jpg")
        fillMode: Image.PreserveAspectCrop
        autoTransform: true
    }

    component GhostButton: Controls.Button {
        id: button
        implicitHeight: 32
        padding: 4
        font.pixelSize: 14
        focusPolicy: Qt.StrongFocus
        Keys.onReturnPressed: if (enabled) clicked()
        Keys.onEnterPressed: if (enabled) clicked()
        contentItem: Text {
            text: button.text; textFormat: Text.PlainText
            color: Palette.text; font: button.font
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: Rectangle {
            radius: 6
            color: button.enabled && (button.activeFocus || button.hovered)
                ? Qt.rgba(root.inputColor.r, root.inputColor.g, root.inputColor.b, root.inputOpacity) : "transparent"
            border.color: Palette.accent
            border.width: button.activeFocus ? 2 : (button.enabled && button.hovered ? 1 : 0)
        }
    }
    component Avatar: Rectangle {
        objectName: "avatar"
        property bool focused: false
        width: 48; height: 48; radius: 24
        color: Palette.accent
        Text {
            anchors.centerIn: parent
            text: Array.from(root.loginUser)[0] || ""
            textFormat: Text.PlainText
            color: Palette.selectedText; font.pixelSize: 22
        }
        Rectangle {
            anchors.fill: parent; anchors.margins: 3
            radius: 21; color: "transparent"
            border.color: Palette.selectedText; border.width: 2
            visible: parent.focused
        }
    }
    component ThemeInput: Controls.TextField {
        id: field
        property bool warn: false
        implicitHeight: 44
        padding: 10
        font.pixelSize: 16
        color: Palette.text
        placeholderTextColor: Palette.secondary
        selectionColor: Palette.selected
        selectedTextColor: Palette.selectedText
        background: Rectangle {
            radius: 8
            color: Qt.rgba(root.inputColor.r, root.inputColor.g, root.inputColor.b, root.inputOpacity)
            border.color: field.warn ? Palette.negative : (field.activeFocus ? Palette.accent : Palette.secondary)
            border.width: field.activeFocus || field.warn ? 2 : 1
        }
    }
    component InlineChoices: Item {
        id: choices
        property bool opened: false
        property int itemCount: 0
        property var labelFor
        property Item triggerItem
        property real maximumHeight: 132
        property alias currentIndex: list.currentIndex
        signal chosen(int index)
        visible: opened
        height: opened ? Math.min(maximumHeight, Math.max(44, list.contentHeight)) : 0
        function open() {
            opened = true;
            Qt.callLater(() => { list.forceActiveFocus(); list.positionViewAtIndex(currentIndex, ListView.Contain); });
        }
        function close() {
            if (!opened) return;
            opened = false;
            list.focus = false;
            if (triggerItem && triggerItem.visible && triggerItem.enabled) triggerItem.forceActiveFocus();
        }
        function choose(index) { close(); chosen(index); }
        Rectangle {
            anchors.fill: parent; radius: 6
            color: Qt.rgba(root.inputColor.r, root.inputColor.g, root.inputColor.b, root.inputOpacity)
            border.color: Palette.accent; border.width: list.activeFocus ? 2 : 1
        }
        ListView {
            id: list
            anchors.fill: parent; anchors.margins: 3
            clip: true
            model: choices.itemCount
            keyNavigationWraps: true
            boundsBehavior: Flickable.StopAtBounds
            Keys.onPressed: event => {
                if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Space) {
                    if (currentIndex >= 0) choices.choose(currentIndex);
                    event.accepted = true;
                } else if (event.key === Qt.Key_Escape || event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab) {
                    choices.close(); event.accepted = true;
                }
            }
            delegate: Controls.ItemDelegate {
                id: option
                required property int index
                width: ListView.view.width
                height: Math.max(44, optionText.implicitHeight + 16)
                padding: 8
                highlighted: ListView.isCurrentItem
                focusPolicy: Qt.NoFocus
                onClicked: choices.choose(index)
                contentItem: Text {
                    id: optionText
                    text: choices.labelFor(option.index); textFormat: Text.PlainText
                    color: option.highlighted ? Palette.selectedText : Palette.text
                    font.pixelSize: 16; wrapMode: Text.WrapAnywhere
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    color: option.highlighted ? Palette.selected : "transparent"; radius: 4
                }
            }
            Controls.ScrollIndicator.vertical: Controls.ScrollIndicator { }
        }
    }

    Column {
        id: clock
        objectName: "clock"
        x: root.leftInset; y: 64; width: root.panelWidth
        spacing: 8
        Text {
            objectName: "clockTime"
            width: parent.width; height: 88
            text: Qt.formatTime(root.now, "HH:mm")
            color: Palette.text
            font.pixelSize: 72; font.weight: Font.Light
            verticalAlignment: Text.AlignVCenter
        }
        Text {
            objectName: "calendarDate"
            width: parent.width; height: 24
            text: Qt.formatDate(root.now, qsTr("yyyy年M月d日")) + " " + root.weekdays[root.now.getDay()]
            color: Palette.text
            font.pixelSize: 18; font.weight: Font.Normal
            verticalAlignment: Text.AlignVCenter
        }
    }
    Item {
        id: panel
        objectName: "loginPanel"
        readonly property real normalHeight: 188
        readonly property real baseTop: Math.max(clock.y + clock.height + 16, root.height * 0.55 - normalHeight / 2)
        readonly property real baseHeight: normalHeight + (errorText.visible ? errorText.height + 16 : 0)
        x: root.leftInset; width: root.panelWidth
        y: baseTop - (sessionList.opened ? sessionList.height + 16 : 0)
        height: content.height + 32
        Rectangle {
            anchors.fill: parent; radius: 12
            color: Qt.rgba(root.panelColor.r, root.panelColor.g, root.panelColor.b, root.panelOpacity)
        }
        Column {
            id: content
            x: 16; y: 16; width: parent.width - 32
            spacing: 16
            Item {
                id: userRow
                objectName: "userRow"
                width: parent.width; height: 48
                GhostButton {
                    id: userButton
                    objectName: "userSelection"
                    anchors.fill: parent
                    leftPadding: 0; rightPadding: 0; topPadding: 0; bottomPadding: 0
                    visible: !root.manualUser
                    enabled: root.canChooseUser && !root.busy
                    focusPolicy: root.canChooseUser ? Qt.StrongFocus : Qt.NoFocus
                    Accessible.name: root.canChooseUser ? qsTr("选择用户：%1").arg(root.selectedUser) : root.selectedUser
                    onClicked: root.openUsers(userButton)
                    contentItem: Row {
                        spacing: 16
                        Avatar { }
                        Text {
                            objectName: "usernameDisplay"
                            width: userRow.width - 64; height: 48
                            text: root.selectedUser; textFormat: Text.PlainText
                            font.pixelSize: 18; color: Palette.text
                            verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight
                        }
                    }
                    KeyNavigation.tab: password
                    KeyNavigation.backtab: rebootButton
                }
                Row {
                    anchors.fill: parent; spacing: 16
                    visible: root.manualUser
                    GhostButton {
                        id: manualMenu
                        objectName: "manualUserMenu"
                        width: 48; height: 48
                        leftPadding: 0; rightPadding: 0; topPadding: 0; bottomPadding: 0
                        enabled: root.canChooseUser && !root.busy
                        focusPolicy: root.canChooseUser ? Qt.StrongFocus : Qt.NoFocus
                        Accessible.name: qsTr("选择用户")
                        background: Item { }
                        contentItem: Avatar { focused: manualMenu.activeFocus }
                        onClicked: root.openUsers(manualMenu)
                        KeyNavigation.tab: username
                        KeyNavigation.backtab: rebootButton
                    }
                    ThemeInput {
                        id: username
                        objectName: "username"
                        width: userRow.width - 64; height: 44; y: 2
                        enabled: !root.busy; placeholderText: qsTr("用户名")
                        inputMethodHints: Qt.ImhNoPredictiveText
                        onAccepted: password.forceActiveFocus()
                        KeyNavigation.tab: password
                        KeyNavigation.backtab: root.canChooseUser ? manualMenu : rebootButton
                    }
                }
            }
            InlineChoices {
                id: userList
                objectName: "userList"
                width: parent.width
                itemCount: users.count + 1
                maximumHeight: Math.min(132, Math.max(44, root.height - 24 - panel.baseTop - panel.baseHeight - 16))
                labelFor: index => index === users.count ? qsTr("其他…") : users.textAt(index)
                onChosen: index => root.chooseUser(index)
            }
            Item {
                objectName: "passwordRow"
                width: parent.width; height: 44
                ThemeInput {
                    id: password
                    objectName: "password"
                    anchors.fill: parent
                    rightPadding: 48
                    placeholderText: qsTr("输入密码")
                    echoMode: TextInput.Password
                    enabled: !root.busy; warn: root.errorBorder
                    inputMethodHints: Qt.ImhSensitiveData | Qt.ImhHiddenText | Qt.ImhNoPredictiveText
                    onAccepted: root.login()
                    KeyNavigation.tab: loginButton
                    KeyNavigation.backtab: root.manualUser ? username : (root.canChooseUser ? userButton : rebootButton)
                }
                Controls.Button {
                    id: loginButton
                    objectName: "loginButton"
                    anchors.right: parent.right; anchors.rightMargin: 4
                    anchors.verticalCenter: parent.verticalCenter
                    width: 36; height: 36; padding: 0
                    focusPolicy: Qt.StrongFocus
                    enabled: !root.busy && root.loginUser.length > 0 && root.selectedSession >= 0 && root.selectedSession < sessions.count
                    Accessible.name: root.busy ? qsTr("正在登录…") : qsTr("登录")
                    onClicked: root.login()
                    Keys.onReturnPressed: if (enabled) clicked()
                    Keys.onEnterPressed: if (enabled) clicked()
                    KeyNavigation.tab: sessionButton
                    KeyNavigation.backtab: password
                    background: Rectangle {
                        radius: 18; color: Palette.accent
                        Rectangle {
                            anchors.fill: parent; anchors.margins: 3; radius: 15
                            color: "transparent"; border.color: Palette.selectedText
                            border.width: 2; visible: loginButton.activeFocus
                        }
                    }
                    contentItem: Item {
                        Repeater {
                            model: 2
                            Rectangle {
                                required property int index
                                width: 11; height: 2
                                anchors.centerIn: parent
                                anchors.verticalCenterOffset: index === 0 ? -3 : 3
                                rotation: index === 0 ? 45 : -45
                                color: Palette.selectedText
                            }
                        }
                    }
                }
            }
            Text {
                id: errorText
                objectName: "loginError"
                width: parent.width; height: 20
                visible: text.length > 0
                text: sessions.count === 0 ? qsTr("没有可用会话，请检查系统配置。") : root.errorMessage
                textFormat: Text.PlainText
                color: Palette.negative; font.pixelSize: 14
                verticalAlignment: Text.AlignVCenter
            }
            InlineChoices {
                id: sessionList
                objectName: "sessionList"
                width: parent.width
                itemCount: sessions.count
                maximumHeight: Math.min(132, Math.max(44, panel.baseTop - clock.y - clock.height - 32))
                triggerItem: sessionButton
                labelFor: index => sessions.textAt(index)
                onChosen: index => root.selectedSession = index
            }
            Row {
                id: footer
                objectName: "footer"
                width: parent.width; height: 32; spacing: 8
                GhostButton {
                    id: sessionButton
                    objectName: "sessionSelection"
                    width: footer.width - keyboardText.width - shutdownButton.width - rebootButton.width - 24
                    text: qsTr("会话:%1").arg(root.selectedSession >= 0 && root.selectedSession < sessions.count ? sessions.textAt(root.selectedSession) : qsTr("无"))
                    enabled: !root.busy && sessions.count > 0
                    onClicked: {
                        userList.close();
                        sessionList.currentIndex = Math.max(0, root.selectedSession);
                        sessionList.open();
                    }
                    KeyNavigation.tab: shutdownButton
                    KeyNavigation.backtab: loginButton
                }
                Text {
                    id: keyboardText
                    objectName: "keyboardLayout"
                    width: Math.min(72, implicitWidth); height: 32
                    text: qsTr("键盘:%1").arg(keyboard.layouts.length > keyboard.currentLayout && keyboard.currentLayout >= 0 ? keyboard.layouts[keyboard.currentLayout].shortName : qsTr("未知"))
                    textFormat: Text.PlainText
                    font.pixelSize: 14; color: Palette.text
                    verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight
                }
                GhostButton {
                    id: shutdownButton
                    objectName: "shutdownButton"
                    text: qsTr("关机")
                    enabled: !root.busy && sddm.canPowerOff
                    onClicked: sddm.powerOff()
                    KeyNavigation.tab: rebootButton
                    KeyNavigation.backtab: sessionButton
                }
                GhostButton {
                    id: rebootButton
                    objectName: "rebootButton"
                    text: qsTr("重启")
                    enabled: !root.busy && sddm.canReboot
                    onClicked: sddm.reboot()
                    KeyNavigation.tab: root.firstInput()
                    KeyNavigation.backtab: shutdownButton
                }
            }
        }
    }
}
