# v1.1 开发版验收记录

日期：2026-10-31。环境：x86_64-linux / NixOS 26.05 / Plasma 6.6.6 / Wayland。
测试使用本机独立 D-Bus、临时 HOME、虚拟 KWin 输出和软件渲染。

## 已完成

- 43 项 Python 测试全部通过，保留原有 29 项检查。
- Nix 使用原 `flake.lock` 离线构建成功，无新依赖输入。
- KSVG 实际渲染九宫格背景；面板/弹窗/通知显示白色表面和轻边框，未覆盖控件使用 Breeze。
- 30 个文件夹名称均有 16、22、32、64px 版本；主要分类经 Qt SVG 实际渲染检查，每档几何单独贴合网格。
- 17 个指针文件、68 个上游别名和 8 个旧版兼容别名完整；上游二进制哈希不变。
- libXcursor 1.2.3 加载 17×5=85 组动画，逐帧尺寸、延时和热点与固定上游报告一致。
- 用户目录的旧同名指针备份/还原、链接创建失败、后续用户改动及别名路径去重通过检查；同名指针重载不改变尺寸。
- 3120×2080、1.75 缩放下真实执行 `applied → already-applied → restored`，警告为空。
- 面板/桌面部件 ID、布局、字体、等宽字体、光标尺寸 36 和缩放保持；固定强调色恢复。
- 真实 KDE 工具在壁纸变更后注入故障，样式、壁纸、光标和相关键自动回滚，恢复记录清理。
- 由 v1.0 控制器创建旧记录，v1.1 拒绝覆盖；恢复后应用、重复应用、再次恢复均通过。
- 源 JPEG 哈希与第 707 帧记录一致，桌面和锁屏 `FillMode=2`；3:2 画面不拉伸，人物面部保留。
- Ghostty / Konsole 16 色一致。正文约 11.95:1；KDE 普通前景最低 4.75:1；ANSI 普通/Intense 最低 5.58:1，Faint 最低 4.51:1。

机器可读摘要见 [nested-session-results.json](nested-session-results.json)，截图见 [预览](../previews/README.md)。
全部截图为原始捕获文件；锁屏由原生 greeter 的 `--testing` 模式生成，没有执行真实锁定或认证。

## 验收边界

独立会话截图是本机实际 KDE 渲染，不是日常会话或物理屏幕的验收截图。
本轮没有切换日常桌面；最终观感、实际鼠标点击落点、多屏行为仍待用户主动应用后确认。
像素画的高分屏版本来自上游缩放，不等同于重新绘制高清素材。
原生锁屏待机时钟仍使用 Breeze 的文字/描边，在浅色壁纸区域的可读性需要实屏确认；
正文对比度数字适用于配色表中的纯色前景/背景，不代表任意壁纸上的所有文字。

壁纸强调色模式启用时，KDE 会在恢复后重新计算派生的 `AccentColor`。
工具恢复原策略，不冻结 KDE 后续计算；实机会话用关闭壁纸强调色的固定值验证精确恢复，
启用策略的键恢复另有单元测试。

## 重复验证

```sh
python3 -m unittest discover -s tests -v
nix build --no-write-lock-file path:.#kaltsit-theme
bash tests/run-nested.sh "$(realpath result/share)" /tmp/kaltsit-validation-new --capture
```

运行目录必须不存在。脚本会创建私有 HOME、运行目录和 D-Bus，绝不能将日常 HOME 传入。
需要 KWin、Plasma、KScreen、Spectacle、Konsole、Dolphin、Python 与 KDE 命令在 PATH。
若要锁屏预览，设置 `KALTSIT_GREETER` 为本机 `kscreenlocker_greet` 的绝对路径。
如有已验证的 v1.0 源码，设置 `KALTSIT_LEGACY_CONTROLLER`、`KALTSIT_LEGACY_SHARE`，
即可额外运行真实旧版迁移探针；不设置时仍运行失败回滚。

`tests/assets-preview.qml` 是 Qt/KSVG 素材检查程序，可用 qml 运行并在最后一个参数指定输出 PNG。
`scripts/generate-assets.py` 可重现原创 SVG；上游指针已 vendored，构建无需下载视频或指针仓库。
