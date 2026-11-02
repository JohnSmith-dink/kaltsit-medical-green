// Real Qt key/mouse events against fake SDDM models. Never authenticates.
import QtQuick
import QtQuick.Window
import QtQuick.Controls.Basic
import QtTest

Item {
    id: root
    property var args: [] // SDDM_TEST_ARGUMENTS
    width: Math.ceil(args[2] / args[4]); height: Math.ceil(args[3] / args[4])
    visible: true
    property alias sddm: proxy
    property alias userModel: users
    property alias sessionModel: sessions
    property alias keyboard: layout
    QtObject {
        id: proxy
        property bool canPowerOff: false
        property bool canReboot: false
        property int loginCalls: 0
        property int powerCalls: 0
        property int rebootCalls: 0
        property int credentialLength: 0
        property string submittedUser: ""
        property int submittedSession: -1
        signal loginFailed()
        signal loginSucceeded()
        function login(user, credential, index) {
            ++loginCalls; submittedUser = user; submittedSession = index;
            // Only a length is retained, never a credential or its hash.
            credentialLength = credential.length;
        }
        function powerOff() { ++powerCalls; }
        function reboot() { ++rebootCalls; }
    }
    ListModel { id: users; property int lastIndex: 0; property string lastUser: "fixture" }
    ListModel { id: sessions; property int lastIndex: 0 }
    QtObject { id: layout; property int currentLayout: 0; property var layouts: [{shortName: "us"}] }
    Item {
        id: stage
        width: root.args[2] / root.args[4]; height: root.args[3] / root.args[4]
        Loader { id: theme; anchors.fill: parent }
    }
    TestCase {
        id: test
        name: "SddmV6"
        when: windowShown
        function item(name) {
            let result = findChild(theme.item, name);
            verify(result !== null, "Missing control " + name);
            return result;
        }
        function focusControl(name) { item(name).forceActiveFocus(); tryCompare(item(name), "activeFocus", true); }
        function reset(names, remembered, sessionNames) {
            theme.source = "";
            tryCompare(theme, "item", null);
            users.clear(); sessions.clear();
            for (let name of names) users.append({name: name});
            for (let name of sessionNames) sessions.append({name: name});
            users.lastUser = remembered;
            users.lastIndex = Math.max(0, names.indexOf(remembered));
            sessions.lastIndex = sessionNames.length ? 0 : -1;
            proxy.canPowerOff = false; proxy.canReboot = false;
            proxy.loginCalls = 0; proxy.powerCalls = 0; proxy.rebootCalls = 0;
            proxy.credentialLength = 0; proxy.submittedUser = ""; proxy.submittedSession = -1;
            theme.source = root.args[0];
            tryCompare(theme, "status", Loader.Ready);
            item("clockTicker").running = false;
            theme.item.now = new Date(2026, 10, 2, 17, 5);
            root.Window.window.requestActivate();
            wait(40);
        }
        function init() { reset(["fixture"], "fixture", ["Test session"]); }
        function cleanup() { theme.source = ""; }
        function openUserMenu() {
            focusControl(theme.item.manualUser ? "manualUserMenu" : "userSelection");
            keyClick(Qt.Key_Return);
            tryCompare(item("userList"), "opened", true);
            wait(30); // Allow the inline Column positioner to finish its polish.
        }
        function capture(name) {
            let finished = false;
            // Popups live in the window Overlay, outside the loaded theme item.
            verify(root.Window.window.contentItem.grabToImage(result => {
                verify(result.saveToFile(root.args[1] + "/" + name + ".png"), "Save native capture");
                finished = true;
            }, Qt.size(stage.width, stage.height)));
            tryVerify(() => finished, 5000);
        }
        function inside(control) {
            let pos = control.mapToItem(stage, 0, 0);
            verify(pos.x >= -0.1 && pos.y >= -0.1, "Top/left in bounds");
            verify(pos.x + control.width <= stage.width + 0.1, "Right in bounds");
            verify(pos.y + control.height <= stage.height + 0.1, "Bottom in bounds");
        }
        function test_initial_single_user_and_capabilities() {
            compare(theme.item.manualUser, false);
            compare(theme.item.loginUser, "fixture");
            verify(!item("username").visible);
            verify(item("calendarDate").text.indexOf("星期") >= 0);
            tryCompare(item("password"), "activeFocus", true);
            verify(!item("shutdownButton").enabled && !item("rebootButton").enabled);
            compare(item("password").echoMode, TextInput.Password);
            compare(item("avatar").width, 48); compare(item("avatar").height, 48);
            item("password").text = "synthetic-only";
            verify(item("password").displayText !== item("password").text);
        }
        function test_tab_and_backtab_cycle() {
            proxy.canPowerOff = true; proxy.canReboot = true;
            focusControl("userSelection");
            for (let name of ["password", "loginButton", "sessionSelection", "keyboardLayout", "shutdownButton", "rebootButton", "userSelection"]) {
                keyClick(Qt.Key_Tab); tryCompare(item(name), "activeFocus", true);
            }
            for (let name of ["rebootButton", "shutdownButton", "keyboardLayout", "sessionSelection", "loginButton", "password", "userSelection"]) {
                keyClick(Qt.Key_Backtab, Qt.ShiftModifier); tryCompare(item(name), "activeFocus", true);
            }
            compare(proxy.loginCalls, 0);
            verify(item("userSelection").enabled);
            keyClick(Qt.Key_Return); keyClick(Qt.Key_Space);
            mouseClick(item("userSelection"));
            verify(!item("userList").opened);
            focusControl("keyboardLayout");
            keyClick(Qt.Key_Return); keyClick(Qt.Key_Space); mouseClick(item("keyboardLayout"));
            compare(layout.currentLayout, 0);
            verify(!item("userList").opened && !item("sessionList").opened);
            compare(proxy.loginCalls, 0); compare(proxy.powerCalls, 0); compare(proxy.rebootCalls, 0);
        }
        function test_tab_skips_unavailable_and_hidden_controls() {
            reset(["fixture"], "fixture", []);
            focusControl("password"); keyClick(Qt.Key_Tab);
            tryCompare(item("keyboardLayout"), "activeFocus", true);
            keyClick(Qt.Key_Tab); tryCompare(item("userSelection"), "activeFocus", true);
            reset([], "", ["Test session"]);
            focusControl("username"); keyClick(Qt.Key_Tab);
            tryCompare(item("password"), "activeFocus", true);
            keyClick(Qt.Key_Backtab, Qt.ShiftModifier);
            tryCompare(item("username"), "activeFocus", true);
            reset(["fixture", "omega"], "fixture", ["Test session"]);
            openUserMenu(); keyClick(Qt.Key_Tab);
            tryCompare(item("userSelection"), "activeFocus", true);
            verify(!item("userList").opened);
            keyClick(Qt.Key_Tab); tryCompare(item("password"), "activeFocus", true);
        }
        function test_multiple_users_other_and_back() {
            reset(["fixture", "omega"], "fixture", ["Test session"]);
            openUserMenu();
            keyClick(Qt.Key_Down); keyClick(Qt.Key_Down); keyClick(Qt.Key_Return);
            tryCompare(theme.item, "manualUser", true);
            tryCompare(item("username"), "activeFocus", true);
            compare(proxy.loginCalls, 0);
            verify(!item("loginButton").enabled);
            item("username").text = "manual";
            keyClick(Qt.Key_Return); tryCompare(item("password"), "activeFocus", true);
            item("password").text = "synthetic-only";
            openUserMenu();
            keyClick(Qt.Key_Up); keyClick(Qt.Key_Up); keyClick(Qt.Key_Return);
            tryCompare(theme.item, "manualUser", false);
            compare(theme.item.loginUser, "fixture");
            compare(item("password").text.length, 0);
            tryCompare(item("password"), "activeFocus", true);
        }
        function test_multiple_users_and_escape() {
            reset(["alpha", "fixture", "omega"], "fixture", ["Test session"]);
            item("password").text = "synthetic-only";
            openUserMenu();
            compare(item("userList").currentIndex, 1);
            keyClick(Qt.Key_Down); keyClick(Qt.Key_Return);
            tryCompare(theme.item, "selectedUser", "omega");
            compare(item("password").text.length, 0);
            compare(proxy.loginCalls, 0);
            openUserMenu(); keyClick(Qt.Key_Escape);
            tryCompare(item("userSelection"), "activeFocus", true);
            compare(theme.item.selectedUser, "omega");
        }
        function test_empty_users_manual_and_no_empty_submit() {
            reset([], "", ["Test session"]);
            verify(theme.item.manualUser);
            tryCompare(item("username"), "activeFocus", true);
            verify(!item("manualUserMenu").enabled && !item("userSelection").visible);
            item("username").text = "   ";
            theme.item.login(); compare(proxy.loginCalls, 0);
            item("username").text = "manual";
            keyClick(Qt.Key_Return); tryCompare(item("password"), "activeFocus", true);
            item("password").text = "synthetic-only";
            keyClick(Qt.Key_Return);
            compare(proxy.loginCalls, 1); compare(proxy.submittedUser, "manual");
        }
        function test_unlisted_remembered_user() {
            reset(["fixture"], "unlisted", ["Test session"]);
            verify(theme.item.manualUser);
            compare(item("username").text, "unlisted");
            tryCompare(item("password"), "activeFocus", true);
        }
        function test_sessions_no_enter_leak() {
            reset(["fixture"], "fixture", ["One", "Two"]);
            focusControl("sessionSelection"); keyClick(Qt.Key_Return);
            tryCompare(item("sessionList"), "opened", true);
            keyClick(Qt.Key_Down); keyClick(Qt.Key_Return);
            compare(theme.item.selectedSession, 1);
            compare(proxy.loginCalls, 0);
            tryCompare(item("sessionSelection"), "activeFocus", true);
            keyClick(Qt.Key_Return); keyClick(Qt.Key_Escape);
            compare(proxy.loginCalls, 0);
            focusControl("password"); item("password").text = "synthetic-only"; keyClick(Qt.Key_Return);
            compare(proxy.submittedSession, 1);
        }
        function test_no_session_blocks_login() {
            reset(["fixture"], "fixture", []);
            verify(!item("loginButton").enabled && !item("sessionSelection").enabled);
            verify(item("loginError").visible);
            theme.item.login(); compare(proxy.loginCalls, 0);
        }
        function test_error_clearing_focus_and_stable_layout() {
            let before = item("password").mapToItem(stage, 0, 0).y;
            let panelHeight = item("loginPanel").height;
            verify(!item("loginError").visible);
            item("password").text = "synthetic-only";
            keyClick(Qt.Key_Return);
            compare(proxy.loginCalls, 1); compare(proxy.credentialLength, 14);
            compare(item("password").text.length, 0); verify(theme.item.busy);
            proxy.loginFailed();
            tryCompare(item("password"), "activeFocus", true);
            verify(item("loginError").visible && theme.item.errorBorder);
            tryCompare(item("loginPanel"), "height", panelHeight + 26);
            compare(item("password").mapToItem(stage, 0, 0).y, before);
            wait(650);
            verify(!theme.item.errorBorder && item("password").activeFocus);
            verify(item("loginError").implicitWidth <= item("loginError").width);
            theme.item.clearAttempt();
            tryCompare(item("loginPanel"), "height", panelHeight);
            verify(!item("loginError").visible);
        }
        function test_busy_rejects_duplicates_and_switching() {
            item("password").text = "synthetic-only"; keyClick(Qt.Key_Return);
            theme.item.login(); keyClick(Qt.Key_Return);
            compare(proxy.loginCalls, 1);
            for (let name of ["password", "userSelection", "loginButton", "sessionSelection", "keyboardLayout", "shutdownButton", "rebootButton"])
                verify(!item(name).enabled, "Busy disables " + name);
        }
        function test_success_keeps_credential_empty() {
            item("password").text = "synthetic-only"; keyClick(Qt.Key_Return);
            proxy.loginSucceeded();
            compare(item("password").text.length, 0);
        }
        function test_power_calls_only_fake_backend() {
            proxy.canPowerOff = true; proxy.canReboot = true;
            focusControl("shutdownButton"); keyClick(Qt.Key_Return);
            compare(proxy.powerCalls, 1); compare(proxy.rebootCalls, 0);
            focusControl("rebootButton"); keyClick(Qt.Key_Return);
            compare(proxy.powerCalls, 1); compare(proxy.rebootCalls, 1);
            proxy.canPowerOff = false; proxy.canReboot = false;
            mouseClick(item("shutdownButton")); mouseClick(item("rebootButton"));
            compare(proxy.powerCalls, 1); compare(proxy.rebootCalls, 1);
        }
        function test_lists_are_inline_exclusive_and_bounded() {
            reset(["fixture", "two", "three", "four", "five"], "fixture", ["One", "Two", "Three", "Four"]);
            let top = item("loginPanel").y;
            let footerY = item("footer").mapToItem(stage, 0, 0).y;
            openUserMenu();
            compare(item("loginPanel").y, top);
            inside(item("userList"));
            focusControl("sessionSelection"); keyClick(Qt.Key_Return);
            verify(!item("userList").opened && item("sessionList").opened);
            tryVerify(() => Math.abs(item("footer").mapToItem(stage, 0, 0).y - footerY) < .1);
            verify(item("loginPanel").y >= item("clock").y + item("clock").height + 16 - .1);
            keyClick(Qt.Key_Escape);
            tryCompare(item("sessionSelection"), "activeFocus", true);
            compare(item("loginPanel").y, top);
        }
        function recordGeometry(state) {
            wait(30); // Record settled geometry, not the previous layout pass.
            let regions = {};
            for (let name of ["clockTime", "calendarDate", "loginPanel", "usernameDisplay", "username", "password", "loginError", "footer", "sessionSelection", "keyboardLayout", "shutdownButton", "rebootButton", "userList", "sessionList"]) {
                let control = item(name);
                if (control.visible) {
                    let p = control.mapToItem(stage, 0, 0);
                    verify(p.x >= theme.item.opticalEdge - 20 && p.x + control.width <= theme.item.opticalEdge + theme.item.columnWidth + 10, "Control stays in left column: " + name);
                    inside(control);
                    regions[name] = [p.x, p.y, control.width, control.height];
                    if (name === "clockTime" || name === "calendarDate") {
                        let ink = control.inkBounds;
                        regions[name] = [ink.x, ink.y, ink.width, ink.height];
                    }
                }
            }
            console.log("SDDM_GEOMETRY " + JSON.stringify({state: state, regions: regions}));
        }
        function test_geometry_and_native_captures() {
            for (let name of ["clock", "loginPanel", "footer"]) inside(item(name));
            compare(item("clockTime").inkBounds.x, theme.item.opticalEdge); compare(item("clockTime").font.pixelSize, 72);
            compare(item("clockTime").font.weight, Font.Normal);
            compare(item("calendarDate").font.pixelSize, 18);
            compare(item("loginPanel").width, 288);
            verify(item("loginPanel").y >= item("clock").y + item("clock").height + 16);
            for (let name of ["loginPanel", "footer"]) {
                let box = item(name), p = box.mapToItem(stage, 0, 0);
                verify(p.x >= theme.item.opticalEdge - 20 && p.x + box.width <= theme.item.opticalEdge + theme.item.columnWidth + 10);
            }
            recordGeometry("single-user"); capture("single-user");
            item("password").text = "synthetic-only"; keyClick(Qt.Key_Return); proxy.loginFailed();
            recordGeometry("error"); capture("error");
            reset(["alpha", "a-very-long-synthetic-username-that-must-fit-without-overlap", "omega"], "alpha", ["Plasma (Wayland)", "Two"]);
            openUserMenu();
            inside(item("userList")); inside(item("loginPanel"));
            recordGeometry("multi-user-menu"); capture("multi-user-menu");
            keyClick(Qt.Key_Down); keyClick(Qt.Key_Return);
            inside(item("userSelection"));
            recordGeometry("long-username"); capture("long-username");
            focusControl("sessionSelection"); keyClick(Qt.Key_Return);
            inside(item("sessionList")); inside(item("loginPanel"));
            recordGeometry("session-menu"); capture("session-menu");
            keyClick(Qt.Key_Escape);
            reset([], "", ["Test session"]);
            recordGeometry("empty-users"); capture("empty-users");
            reset(["tester"], "tester", ["Plasma (Wayland)"]);
            proxy.canPowerOff = true; proxy.canReboot = true;
            focusControl("shutdownButton"); capture("long-session-focus-shutdown");
            reset(["fixture"], "fixture", ["Test session"]);
            // Separate focused/hovered surfaces from the unpainted normal state.
            focusControl("userSelection"); capture("focus-user");
            focusControl("keyboardLayout"); capture("focus-keyboard");
            focusControl("password");
            item("clock").visible = false; item("loginPanel").visible = false;
            capture("background");
            item("clock").visible = true; item("loginPanel").visible = true;
        }
        function test_font_and_optical_clock_metrics() {
            compare(item("clockTime").font.features.tnum, 1);
            compare(item("clockTime").font.letterSpacing, -.5);
            if (root.args[5]) compare(theme.item.resolvedFontFamily, "OPPO Sans 4.0");
            else verify(theme.item.resolvedFontFamily !== "OPPO Sans 4.0");
            let powerValue = findChild(item("shutdownButton"), "controlValue");
            let sessionLabel = findChild(item("sessionSelection"), "controlLabel");
            compare(powerValue.fontInfo.weight, Font.Medium);
            compare(sessionLabel.fontInfo.weight, Font.Normal);
            for (let hour of [0, 10, 17, 23]) {
                theme.item.now = new Date(2026, 10, 2, hour, 5);
                wait(20);
                compare(item("clockTime").inkBounds.x, theme.item.opticalEdge);
                fuzzyCompare(item("clockTime").inkBounds.y, 71.75, .01);
                capture("clock-" + hour);
            }
            console.log("SDDM_FONT " + JSON.stringify({family: theme.item.resolvedFontFamily,
                clockFamily: item("clockTime").fontInfo.family, clockWeight: item("clockTime").fontInfo.weight,
                usernameFamily: item("usernameDisplay").fontInfo.family, usernameWeight: item("usernameDisplay").fontInfo.weight,
                controlFamily: powerValue.fontInfo.family, controlWeight: powerValue.fontInfo.weight,
                labelFamily: sessionLabel.fontInfo.family, labelWeight: sessionLabel.fontInfo.weight,
                powerButtonWidth: item("shutdownButton").width, keyboardButtonWidth: item("keyboardLayout").width}));
        }
        function test_footer_groups_and_elision() {
            reset(["tester"], "tester", ["Plasma (Wayland) with a very long name"]);
            let session = item("sessionSelection"), keyboard = item("keyboardLayout");
            let off = item("shutdownButton"), reboot = item("rebootButton");
            verify(session.elideValue && !keyboard.elideValue && !off.elideValue && !reboot.elideValue);
            compare(keyboard.width, keyboard.implicitWidth);
            compare(off.width, off.implicitWidth); compare(reboot.width, reboot.implicitWidth);
            verify(off.x - (keyboard.x + keyboard.width) >= 12 - .01);
            let p = session.mapToItem(stage, 0, 0);
            fuzzyCompare(p.x + session.firstInkInset, theme.item.opticalEdge, .01);
            let right = reboot.mapToItem(stage, reboot.width, 0).x;
            fuzzyCompare(right, theme.item.opticalEdge + theme.item.columnWidth + 8, .01);
            focusControl("sessionSelection"); keyClick(Qt.Key_Return);
            compare(item("sessionList").labelFor(0), "Plasma (Wayland) with a very long name");
        }
    }
}
