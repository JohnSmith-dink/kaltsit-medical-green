# 预览来源

1.1.0 正式版沿用以下 rc.3 原始截图；正式版仅更新版本标识和发布文档，未重拍或修改图像。

rc.3 按用户反馈取消锁屏背景的全部遮罩和额外颜色变换，保留原生模糊。
待机显示原图；RHI 密码页仅模糊背景，不额外提亮、压暗或调整对比度与饱和度。
时钟使用浅色互补色组的深色文字，桌面继续使用暖白配色。
以下十张 PNG 来自本机独立 KDE Plasma 6.6.6 / Wayland 会话，使用临时 HOME 和独立 D-Bus。
主组七张为 3120×2080、175% 缩放、Qt Quick RHI / Mesa 软件 OpenGL；宽屏三张为
1920×1080、100% 缩放、Qt Quick 软件后端。所有文件保留原始截图字节，没有重绘、合成或后期调整。
这两组最终会话使用 Nix 构建产物的 share 目录，包含构建时生成的锁屏 shell。

| 画面 | 文件 |
| --- | --- |
| 桌面 | [desktop.png](actual/desktop.png) |
| 原生启动菜单 | [launcher.png](actual/launcher.png) |
| Dolphin 文件管理器 | [dolphin.png](actual/dolphin.png) |
| Konsole 浅色终端 | [terminal.png](actual/terminal.png) |
| 原生通知 | [notification.png](actual/notification.png) |
| 原生锁屏 · 待机 | [lockscreen.png](actual/lockscreen.png) |
| 原生锁屏 · 密码输入 | [lockscreen-unlock.png](actual/lockscreen-unlock.png) |

宽屏软件后端：[桌面](actual/wide/desktop.png) · [待机](actual/wide/lockscreen.png) · [密码输入](actual/wide/lockscreen-unlock.png)。

锁屏使用原生 greeter 的 `--testing` 模式，未执行真实锁定或口令认证。
RHI 输入页保留 KDE 自身的模糊，颜色矩阵的亮度、对比度和饱和度系数均为 1；
Qt Quick 软件后端不提供相同的 shader 模糊效果，直接显示原图与原生文字描边。
图中为测试会话默认布局及测试字体。
截图时测试机时钟显示 10 月 31 日；记录日期采用工作端 Asia/Shanghai 的 11 月 1 日，未修改系统时间。

rc.1 密码页过亮、rc.2 遮罩偏暗的反馈均已纳入本轮调整。
本页仅展示 rc.3 最终构建产物的新截图；前两版的检查和用户反馈单独保留为历史记录，
rc.3 已在第 54 代实机配置通过真实锁定/解锁，用户确认“亮度正常，解锁正常”。完整范围见
[发布验收](../docs/RELEASE-READINESS.md)。

[assets-preview.png](assets-preview.png) 是 Qt/KSVG 素材检查图，沿用本轮未改变的文件夹与面板素材。
[本地画廊](index.html) 汇总图像；[manifest.json](manifest.json) 逐图记录版本、尺寸、渲染后端和 SHA-256。
[kaltsit-medical-green.html](kaltsit-medical-green.html) 为保留的旧版 HTML 概念示意。
