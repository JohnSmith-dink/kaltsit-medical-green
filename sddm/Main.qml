// SPDX-FileCopyrightText: 2026 Xinyan
// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Controls.Basic as Controls
import "Palette.js" as Palette

Item {
    id: root
    readonly property real leftInset: 72
    readonly property real panelWidth: 288
    readonly property real opticalEdge: width >= 960 ? leftInset : Math.max(24, Math.floor(width * 0.075))
    readonly property real columnWidth: Math.min(panelWidth, width - 2 * opticalEdge)
    readonly property real inputOpacity: 1
    readonly property real surfaceOpacity: 0.90
    readonly property real hoverOpacity: 0.16
    readonly property real labelOpacity: 0.80
    readonly property real focusOpacity: 0.85
    readonly property real bodyOutlineOpacity: 0.85
    readonly property real errorOutlineOpacity: 0.90
    readonly property color bodyOutlineColor: Palette.text
    readonly property color inputColor: Palette.view
    readonly property color lightColor: Palette.selectedText
    readonly property color surfaceColor: Palette.window
    readonly property string resolvedFontFamily: typography.family
    Controls.Label { id: systemFont; visible: false }
    QtObject {
        id: typography
        readonly property string family: Qt.fontFamilies().indexOf("OPPO Sans 4.0") >= 0 ? "OPPO Sans 4.0" : systemFont.font.family
        readonly property int clockSize: 72
        readonly property int dateSize: 18
        readonly property int initialSize: 22
        readonly property int usernameSize: 18
        readonly property int inputSize: 15
        readonly property int smallSize: 14
        readonly property int normal: Font.Normal
        readonly property int medium: Font.Medium
    }
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
    function firstInput() { return manualUser ? (canChooseUser ? manualMenu : username) : userButton; }
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
    Timer { objectName: "clockTicker"; interval: 1000; running: root.visible; repeat: true; onTriggered: root.now = new Date() }

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
        property string label: ""
        property bool elideValue: false
        readonly property real firstInkInset: leftPadding + (contentItem.inkOffset || 0)
        implicitHeight: 32
        implicitWidth: contentItem.implicitWidth + leftPadding + rightPadding
        padding: 9
        topPadding: 0; bottomPadding: 0
        font.family: typography.family
        font.pixelSize: typography.smallSize
        font.weight: typography.medium
        focusPolicy: Qt.StrongFocus
        Accessible.name: label.length ? label + " " + text : text
        Keys.onReturnPressed: if (enabled) clicked()
        Keys.onEnterPressed: if (enabled) clicked()
        contentItem: Item {
            readonly property real inkOffset: button.label.length ? prefixInk.tightBoundingRect.x : valueInk.tightBoundingRect.x
            TextMetrics { id: prefixInk; font: prefix.font; text: prefix.text }
            TextMetrics { id: valueInk; font: value.font; text: value.text }
            implicitWidth: (prefix.visible ? prefix.implicitWidth + 6 : 0) + value.implicitWidth
            Text {
                id: prefix
                objectName: "controlLabel"
                visible: button.label.length > 0
                anchors.verticalCenter: parent.verticalCenter
                text: button.label; textFormat: Text.PlainText
                font.family: typography.family; font.pixelSize: typography.smallSize; font.weight: typography.normal
                color: Qt.rgba(root.inputColor.r, root.inputColor.g, root.inputColor.b, root.labelOpacity)
                style: Text.Outline
                styleColor: Qt.rgba(root.bodyOutlineColor.r, root.bodyOutlineColor.g, root.bodyOutlineColor.b, root.bodyOutlineOpacity)
            }
            Text {
                id: value
                objectName: "controlValue"
                x: prefix.visible ? prefix.implicitWidth + 6 : 0
                width: Math.max(0, parent.width - x)
                anchors.verticalCenter: parent.verticalCenter
                text: button.text; textFormat: Text.PlainText
                color: Palette.selectedText; font: button.font
                style: Text.Outline
                styleColor: Qt.rgba(root.bodyOutlineColor.r, root.bodyOutlineColor.g, root.bodyOutlineColor.b, root.bodyOutlineOpacity)
                elide: button.elideValue ? Text.ElideRight : Text.ElideNone
            }
        }
        background: Rectangle {
            radius: 6
            color: button.enabled && (button.activeFocus || button.hovered)
                ? Qt.rgba(root.inputColor.r, root.inputColor.g, root.inputColor.b, root.hoverOpacity) : "transparent"
            // A glyph-like dark edge keeps the light focus border visible on bright artwork.
            Rectangle {
                anchors.fill: parent; anchors.margins: -1; radius: 7
                color: "transparent"; visible: button.activeFocus
                border.color: Qt.rgba(root.bodyOutlineColor.r, root.bodyOutlineColor.g, root.bodyOutlineColor.b, root.bodyOutlineOpacity)
                border.width: 3
            }
            Rectangle {
                anchors.fill: parent; radius: 6; color: "transparent"; visible: button.activeFocus
                border.color: Qt.rgba(root.lightColor.r, root.lightColor.g, root.lightColor.b, root.focusOpacity)
                border.width: 1
            }
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
            color: Palette.selectedText; font.family: typography.family; font.pixelSize: typography.initialSize; font.weight: typography.medium
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
        implicitHeight: 42
        padding: 15.5
        topPadding: 0; bottomPadding: 0
        font.family: typography.family; font.pixelSize: typography.inputSize; font.weight: typography.normal
        color: Palette.text
        placeholderTextColor: Palette.secondary
        selectionColor: Palette.selected
        selectedTextColor: Palette.selectedText
        background: Rectangle {
            radius: 8
            color: Qt.rgba(root.inputColor.r, root.inputColor.g, root.inputColor.b, root.inputOpacity)
            border.color: field.warn ? Palette.negative : Palette.accent
            border.width: field.activeFocus || field.warn ? 2 : 1.5
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
            color: Qt.rgba(root.surfaceColor.r, root.surfaceColor.g, root.surfaceColor.b, root.surfaceOpacity)
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
                    font.family: typography.family; font.pixelSize: 16; font.weight: typography.normal; wrapMode: Text.WrapAnywhere
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    color: option.highlighted ? Palette.selected : "transparent"; radius: 4
                }
            }
            Controls.ScrollIndicator.vertical: Controls.ScrollIndicator { }
        }
    }

    Item {
        id: clock
        objectName: "clock"
        width: root.opticalEdge + root.columnWidth; height: 176
        TextMetrics { id: clockInk; font: clockTime.font; text: clockTime.text; renderType: clockTime.renderType }
        TextMetrics { id: dateInk; font: dateText.font; text: dateText.text; renderType: dateText.renderType }
        Text {
            id: clockTime
            objectName: "clockTime"
            x: root.opticalEdge - clockInk.tightBoundingRect.x
            y: 71.75 - baselineOffset - clockInk.tightBoundingRect.y
            text: Qt.formatTime(root.now, "HH:mm")
            color: Palette.text
            font.family: typography.family; font.pixelSize: typography.clockSize; font.weight: typography.normal
            font.letterSpacing: -0.5
            font.features: { "tnum": 1 }
            readonly property rect inkBounds: Qt.rect(x + clockInk.tightBoundingRect.x, y + baselineOffset + clockInk.tightBoundingRect.y, clockInk.tightBoundingRect.width, clockInk.tightBoundingRect.height)
        }
        Text {
            id: dateText
            objectName: "calendarDate"
            x: root.opticalEdge - dateInk.tightBoundingRect.x
            y: 152.25 - baselineOffset - dateInk.tightBoundingRect.y
            text: Qt.formatDate(root.now, qsTr("yyyy年M月d日")) + " " + root.weekdays[root.now.getDay()]
            color: Palette.text
            font.family: typography.family; font.pixelSize: typography.dateSize; font.weight: typography.normal
            readonly property rect inkBounds: Qt.rect(x + dateInk.tightBoundingRect.x, y + baselineOffset + dateInk.tightBoundingRect.y, dateInk.tightBoundingRect.width, dateInk.tightBoundingRect.height)
        }
    }
    Item {
        id: panel
        objectName: "loginPanel"
        readonly property real normalHeight: 150
        readonly property real baseTop: Math.max(220, Math.min(Math.round(root.height * 0.451), root.height - 24 - baseHeight))
        readonly property real baseHeight: normalHeight + (errorText.visible ? errorText.height + 8 : 0)
        x: root.opticalEdge; width: root.columnWidth
        y: baseTop - (sessionList.opened ? sessionList.height + 16 : 0)
        height: content.height
        Column {
            id: content
            width: parent.width
            spacing: 0
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
                    enabled: !root.busy
                    focusPolicy: Qt.StrongFocus
                    Accessible.name: root.canChooseUser ? qsTr("选择用户：%1").arg(root.selectedUser) : root.selectedUser
                    onClicked: root.openUsers(userButton)
                    contentItem: Row {
                        spacing: 14
                        Avatar { }
                        Text {
                            objectName: "usernameDisplay"
                            width: userRow.width - 62; height: 48
                            text: root.selectedUser; textFormat: Text.PlainText
                            font.family: typography.family; font.pixelSize: typography.usernameSize; font.weight: typography.medium; color: Palette.selectedText
                            style: Text.Outline
                            styleColor: Qt.rgba(root.bodyOutlineColor.r, root.bodyOutlineColor.g, root.bodyOutlineColor.b, root.bodyOutlineOpacity)
                            verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight
                        }
                    }
                    KeyNavigation.tab: password
                    KeyNavigation.backtab: rebootButton
                }
                Row {
                    anchors.fill: parent; spacing: 14
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
                        width: userRow.width - 62; height: 42; y: 3
                        enabled: !root.busy; placeholderText: qsTr("用户名")
                        inputMethodHints: Qt.ImhNoPredictiveText
                        onAccepted: password.forceActiveFocus()
                        KeyNavigation.tab: password
                        KeyNavigation.backtab: root.canChooseUser ? manualMenu : rebootButton
                    }
                }
            }
            Item { width: 1; height: userList.opened ? 16 : 0 }
            InlineChoices {
                id: userList
                objectName: "userList"
                width: parent.width
                itemCount: users.count + 1
                maximumHeight: Math.min(132, Math.max(44, root.height - 24 - panel.baseTop - panel.baseHeight - 16))
                labelFor: index => index === users.count ? qsTr("其他…") : users.textAt(index)
                onChosen: index => root.chooseUser(index)
            }
            Item { width: 1; height: 18 }
            Item {
                objectName: "passwordRow"
                width: parent.width; height: 42
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
                    KeyNavigation.backtab: root.manualUser ? username : userButton
                }
                Controls.Button {
                    id: loginButton
                    objectName: "loginButton"
                    anchors.right: parent.right; anchors.rightMargin: 4
                    anchors.verticalCenter: parent.verticalCenter
                    width: 33; height: 33; padding: 0
                    focusPolicy: Qt.StrongFocus
                    enabled: !root.busy && root.loginUser.length > 0 && root.selectedSession >= 0 && root.selectedSession < sessions.count
                    Accessible.name: root.busy ? qsTr("正在登录…") : qsTr("登录")
                    onClicked: root.login()
                    Keys.onReturnPressed: if (enabled) clicked()
                    Keys.onEnterPressed: if (enabled) clicked()
                    KeyNavigation.tab: sessionButton
                    KeyNavigation.backtab: password
                    background: Rectangle {
                        radius: parent.width / 2; color: Palette.accent
                        Rectangle {
                            anchors.fill: parent; anchors.margins: 3; radius: width / 2
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
            Item { width: 1; height: errorText.visible ? 8 : 0 }
            TextMetrics { id: errorInk; font: errorText.font; text: errorText.text; renderType: errorText.renderType }
            Text {
                id: errorText
                objectName: "loginError"
                x: -errorInk.tightBoundingRect.x
                width: parent.width; height: 18
                visible: text.length > 0
                text: sessions.count === 0 ? qsTr("没有可用会话，请检查系统配置。") : root.errorMessage
                textFormat: Text.PlainText
                color: Palette.negative; font.family: typography.family; font.pixelSize: typography.smallSize; font.weight: typography.medium
                style: Text.Outline
                styleColor: Qt.rgba(root.surfaceColor.r, root.surfaceColor.g, root.surfaceColor.b, root.errorOutlineOpacity)
                verticalAlignment: Text.AlignVCenter
            }
            Item { width: 1; height: 10 }
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
            Item { width: 1; height: sessionList.opened ? 16 : 0 }
            Item {
                id: footer
                objectName: "footer"
                x: -sessionButton.firstInkInset
                width: parent.width + 8 - x; height: 32
                GhostButton {
                    id: sessionButton
                    objectName: "sessionSelection"
                    width: Math.min(implicitWidth, Math.max(24, footer.width - keyboardText.width - shutdownButton.width - rebootButton.width - 12))
                    label: qsTr("会话")
                    text: root.selectedSession >= 0 && root.selectedSession < sessions.count ? sessions.textAt(root.selectedSession) : qsTr("无")
                    elideValue: true
                    enabled: !root.busy && sessions.count > 0
                    onClicked: {
                        userList.close();
                        sessionList.currentIndex = Math.max(0, root.selectedSession);
                        sessionList.open();
                    }
                    KeyNavigation.tab: keyboardText
                    KeyNavigation.backtab: loginButton
                }
                GhostButton {
                    id: keyboardText
                    objectName: "keyboardLayout"
                    x: sessionButton.width
                    width: implicitWidth; height: 32
                    enabled: !root.busy
                    label: qsTr("键盘")
                    text: keyboard.layouts.length > keyboard.currentLayout && keyboard.currentLayout >= 0 ? keyboard.layouts[keyboard.currentLayout].shortName : qsTr("未知")
                    Accessible.role: Accessible.StaticText
                    KeyNavigation.tab: shutdownButton
                    KeyNavigation.backtab: sessionButton
                }
                GhostButton {
                    id: shutdownButton
                    objectName: "shutdownButton"
                    anchors.right: rebootButton.left
                    text: qsTr("关机")
                    enabled: !root.busy && sddm.canPowerOff
                    onClicked: sddm.powerOff()
                    KeyNavigation.tab: rebootButton
                    KeyNavigation.backtab: keyboardText
                }
                GhostButton {
                    id: rebootButton
                    objectName: "rebootButton"
                    anchors.right: parent.right
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
