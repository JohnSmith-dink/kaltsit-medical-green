// SPDX-FileCopyrightText: 2026 Xinyan
// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: root
    property string cfg_Video: ""
    property string cfg_VideoDefault: ""
    property string cfg_Image: ""
    property string cfg_ImageDefault: ""
    property int cfg_FillMode: 2
    property int cfg_FillModeDefault: 2
    property bool cfg_Paused: false
    property bool cfg_PausedDefault: false

    Kirigami.FormLayout {
        Layout.fillWidth: true
        RowLayout {
            Kirigami.FormData.label: qsTr("本地视频：")
            Controls.TextField {
                Layout.fillWidth: true
                text: root.cfg_Video
                placeholderText: qsTr("留空使用安装时提供的视频")
                onEditingFinished: root.cfg_Video = text
            }
            Controls.Button { text: qsTr("选择…"); onClicked: videoDialog.open() }
        }
        RowLayout {
            Kirigami.FormData.label: qsTr("静态回退：")
            Controls.TextField {
                Layout.fillWidth: true
                text: root.cfg_Image
                placeholderText: qsTr("留空使用医疗白绿壁纸")
                onEditingFinished: root.cfg_Image = text
            }
            Controls.Button { text: qsTr("选择…"); onClicked: imageDialog.open() }
        }
        Controls.ComboBox {
            Kirigami.FormData.label: qsTr("画面适配：")
            model: [qsTr("填满屏幕，保持比例"), qsTr("完整显示，保持比例")]
            currentIndex: root.cfg_FillMode === 1 ? 1 : 0
            onActivated: root.cfg_FillMode = currentIndex === 1 ? 1 : 2
        }
        Controls.CheckBox {
            text: qsTr("暂停播放（也可通过桌面右键菜单切换）")
            checked: root.cfg_Paused
            onToggled: root.cfg_Paused = checked
        }
    }
    Controls.Label {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: qsTr("视频静音循环，保持原色。视频不可用时显示静态图片。建议先试用 1440p / 30 fps；本功能只作用于选用它的桌面。")
        opacity: 0.8
    }
    Item { Layout.fillHeight: true }
    FileDialog {
        id: videoDialog
        title: qsTr("选择动态壁纸视频")
        nameFilters: [qsTr("视频文件 (*.mp4 *.mkv *.webm *.mov)"), qsTr("所有文件 (*)")]
        onAccepted: root.cfg_Video = selectedFile.toString()
    }
    FileDialog {
        id: imageDialog
        title: qsTr("选择静态回退图片")
        nameFilters: [qsTr("图片文件 (*.png *.jpg *.jpeg *.webp)"), qsTr("所有文件 (*)")]
        onAccepted: root.cfg_Image = selectedFile.toString()
    }
}
