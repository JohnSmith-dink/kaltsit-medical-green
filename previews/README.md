# 预览来源

rc.2 修复原生密码输入页过亮：锁屏采用白字、深绿衬底和原生压暗效果，桌面继续使用暖白配色。
以下十张 PNG 来自本机独立 KDE Plasma 6.6.6 / Wayland 会话，使用临时 HOME 和独立 D-Bus。
主组七张为 3120×2080、175% 缩放、Qt Quick RHI / Mesa 软件 OpenGL；宽屏三张为
1920×1080、100% 缩放、Qt Quick 软件后端。所有文件保留原始截图字节，没有重绘、合成或后期调整。

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
RHI 输入页保留 KDE 自身的模糊和压暗效果；Qt Quick 软件后端不提供相同的 shader 效果，
依靠主题自身的深绿衬底与原生文字描边保持可读。图中为测试会话默认布局及测试字体。
截图时测试机时钟显示 10 月 31 日；记录日期采用工作端 Asia/Shanghai 的 11 月 1 日，未修改系统时间。

rc.1 已在实机完成正常锁定/解锁，用户随后反馈密码页几乎全白，因此其观感验收未通过。
本页展示 rc.2 新截图，不能将 rc.1 的实机反馈当作 rc.2 的验收结论；最新状态见
[正式版准备](../docs/RELEASE-READINESS.md)。

[assets-preview.png](assets-preview.png) 是 Qt/KSVG 素材检查图，沿用本轮未改变的文件夹与面板素材。
[本地画廊](index.html) 汇总图像；[manifest.json](manifest.json) 逐图记录版本、尺寸、渲染后端和 SHA-256。
[kaltsit-medical-green.html](kaltsit-medical-green.html) 为保留的旧版 HTML 概念示意。
