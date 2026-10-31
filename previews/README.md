# 预览来源

rc.1 截图来自本机独立 KDE Plasma 6.6.6 / Wayland 会话，使用临时 HOME 和独立 D-Bus。
主组七张原始 PNG 为 3120×2080、175% 缩放，Qt Quick RHI / Mesa 软件 OpenGL 渲染。
补充组包含 1920×1080、100% 的宽屏视图，以及 Qt Quick 软件后端的解锁页。
所有 PNG 均保留原始截图字节，没有重绘、合成或后期调整。

| 画面 | 文件 |
| --- | --- |
| 桌面 | [desktop.png](actual/desktop.png) |
| 原生启动菜单 | [launcher.png](actual/launcher.png) |
| Dolphin 文件管理器 | [dolphin.png](actual/dolphin.png) |
| Konsole 浅色终端 | [terminal.png](actual/terminal.png) |
| 原生通知 | [notification.png](actual/notification.png) |
| 原生锁屏 · 待机 | [lockscreen.png](actual/lockscreen.png) |
| 原生锁屏 · 解锁提示 | [lockscreen-unlock.png](actual/lockscreen-unlock.png) |

宽屏：[桌面](actual/wide/desktop.png) · [待机](actual/wide/lockscreen.png) · [解锁提示](actual/wide/lockscreen-unlock.png)。
软件后端：[解锁提示](actual/software/lockscreen-unlock.png)。

锁屏使用原生 greeter 的 `--testing` 模式；仅显示原生输入页，没有执行实际锁屏或口令认证。
RHI 解锁页保留 KDE 自身的模糊与亮度变化，软件后端没有相同的 shader 效果。
截图时测试机时钟显示 10 月 31 日；记录日期采用工作端 Asia/Shanghai 的 11 月 1 日，未修改系统时间。
日常桌面的布局、固定应用、字体和缩放没有被改动；图中为测试会话的默认布局与测试字体。

[assets-preview.png](assets-preview.png) 由 `tests/assets-preview.qml` 调用 Qt/KSVG 渲染，
用于检查图标尺寸与九宫格面板背景，是素材检查图。
[本地画廊](index.html) 汇总图像；[manifest.json](manifest.json) 记录尺寸、后端和 SHA-256。
[kaltsit-medical-green.html](kaltsit-medical-green.html) 为保留的旧版 HTML 概念示意。
