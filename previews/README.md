# 预览来源

`actual/` 中六张原始 PNG 来自本机独立 KDE Plasma 6.6.6 / Wayland 会话：
3120×2080、175% 缩放、软件渲染，使用临时 HOME 和独立 D-Bus。
它们是真实应用截图，不是 HTML、AI 概念图或日常物理屏幕的验收截图。

| 画面 | 文件 |
| --- | --- |
| 桌面 | [desktop.png](actual/desktop.png) |
| 原生启动菜单 | [launcher.png](actual/launcher.png) |
| Dolphin，测试文件夹和选中态 | [dolphin.png](actual/dolphin.png) |
| Konsole，16 色 ANSI | [terminal.png](actual/terminal.png) |
| 原生通知 | [notification.png](actual/notification.png) |
| 原生锁屏测试模式，待机视图 | [lockscreen.png](actual/lockscreen.png) |

锁屏截图未执行真实锁屏或认证。用户日常桌面的布局、固定应用、字体和缩放没有被改动；
本组截图显示的是测试会话的原生布局，不能用来推断用户桌面被重排。

[assets-preview.png](assets-preview.png) 由 `tests/assets-preview.qml` 调用 Qt/KSVG 渲染，
用于检查文件夹尺寸、边缘和九宫格面板背景；它是素材检查图，不是桌面截图。

[本地画廊](index.html) 汇总以上图像。[manifest.json](manifest.json) 记录尺寸、来源和 SHA-256。
[kaltsit-medical-green.html](kaltsit-medical-green.html) 是保留的旧版 HTML 概念示意，
用于说明设计方向，不代表 v1.1 实际布局。
