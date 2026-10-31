# 1.1.0-dev.2 验收记录

日期：2026-10-31。环境：x86_64-linux / NixOS 26.05 / Plasma 6.6.6 / Wayland。
测试使用本机独立 D-Bus、临时 HOME、虚拟 KWin 输出和软件渲染。

## 自动检查与素材

- 67 项单元测试通过，保留原有检查，并覆盖组件跳过、预演零写入、缺少工具、自选图片、恢复格式 1 / 2 / 3、父目录链接变更和恢复冲突。
- 复用原 `flake.lock`，没有新增 flake 输入。Nix 离线构建与 `flake check` 通过，构建检查阶段运行完整测试集。
- Home Manager 的 Ghostty 主题文件选项默认关闭，只安装文件；没有新增自动应用动作。
- CI 在 push / pull request 时运行单元测试与 Nix 检查，第三方 Action 固定完整提交。本轮验证在本地执行，尚未推送触发 GitHub 托管任务。
- KSVG 实际渲染九宫格背景；面板/弹窗/通知显示白色表面和轻边框，未覆盖控件使用 Breeze。
- 30 个文件夹名称均有 16、22、32、64px 版本；主要分类经 Qt SVG 实际渲染检查，每档几何单独贴合网格。
- 17 个指针文件、68 个上游别名和 8 个旧版兼容别名完整；上游二进制哈希不变。
- dev.1 的 libXcursor 1.2.3 检查加载了 17×5=85 组动画，逐帧尺寸、延时和热点与固定上游报告一致；本轮资源未改变，哈希与二进制完整性重新检查。
- 用户目录的旧同名指针备份/还原、链接创建失败、后续用户改动及别名路径去重通过检查；同名指针重载不改变尺寸。
- 源 JPEG 哈希与第 707 帧记录一致，桌面和锁屏 `FillMode=2`；3:2 画面不拉伸，人物面部保留。
- Ghostty / Konsole 16 色一致。正文约 11.95:1；128 组 KDE 前景色与本组常规、交替背景的最低对比度为 4.5562:1；ANSI 普通/Intense 最低 5.58:1，Faint 最低 4.51:1。

## 独立 KDE 会话

- 3120×2080、1.75 缩放下真实执行 `applied → already-applied → restored`，警告为空。
- 面板/桌面部件 ID、布局、字体、等宽字体、光标尺寸 36 和缩放保持；固定强调色恢复。
- 真实 KDE 工具在壁纸变更后注入故障，样式、壁纸、光标和相关键自动回滚，恢复记录清理。
- 由 v1.0 控制器创建旧记录，v1.1 拒绝覆盖；恢复后应用、重复应用、再次恢复均通过。
- 启动真实 `gtkconfig` 模块后，将六个可选组件的配置设为符号链接：预演不写配置和状态；应用、重复应用、恢复后，链接与目标内容均不变，桌面壁纸不变。
- 单独跳过 GTK、继续应用指针时，记录到应用和恢复各一次 `breeze_cursors → Kaltsit-Sihengtu` 的刷新顺序，GTK 目标内容保持；这验证了刷新命令与文件边界，不替代物理鼠标热点验收。
- 自选 PNG 同时写入桌面与锁屏，`FillMode=2`，恢复后桌面壁纸回到原状态；已有自定义 GTK 字体保持。
- GTK 原先独立选择 Adwaita 指针时，恢复并等待后台同步后仍保留该选择；GTK 导出完成后才记录或恢复配置，避免异步覆盖。
- 配色与图标由系统默认值继承时，离线 `status` 仍显示有效值；本地配置覆盖系统默认值的优先级有单独回归检查。

机器可读摘要见 [nested-session-results.json](nested-session-results.json)，截图见 [预览](../previews/README.md)。
六张实际截图已在 dev.2 重拍，来自本机独立会话，原始尺寸为 3120×2080；对应文件哈希见
[预览清单](../previews/manifest.json)。锁屏由原生 greeter 的 `--testing` 模式生成，没有执行真实锁定或认证。

## 验收边界

独立会话截图是本机实际 KDE 渲染，不是日常会话或物理屏幕的验收截图。
本轮没有修改日常桌面或私有 NixOS 配置；最终观感、实际鼠标点击落点、多屏行为仍待用户主动应用后确认。
像素画的高分屏版本来自上游缩放，不等同于重新绘制高清素材。
原生锁屏待机时钟仍使用 Breeze 的文字/描边，在浅色壁纸区域的可读性需要实屏确认；
正文对比度数字适用于配色表中的纯色前景/背景，不代表任意壁纸上的所有文字。

壁纸强调色模式启用时，KDE 会在恢复后重新计算派生的 `AccentColor`。
工具恢复原策略，不冻结 KDE 后续计算；实机会话用关闭壁纸强调色的固定值验证精确恢复，
启用策略的键恢复另有单元测试。

## 重复验证

```sh
nix develop --command python3 -m unittest discover -s tests -v
nix flake check --no-write-lock-file path:.
nix build --no-write-lock-file path:.#kaltsit-theme
nix develop --command bash tests/run-nested.sh "$(realpath result/share)" /tmp/kaltsit-validation-new --capture
```

运行目录必须不存在。脚本会创建私有 HOME、运行目录和 D-Bus，绝不能将日常 HOME 传入。
开发 shell 提供 Python 与 Pillow。还需要 KWin、Plasma、KScreen、Spectacle、Konsole、Dolphin
及 KDE / D-Bus 命令在 PATH。
若要锁屏预览，设置 `KALTSIT_GREETER` 为本机 `kscreenlocker_greet` 的绝对路径。
如有已验证的 v1.0 源码，设置 `KALTSIT_LEGACY_CONTROLLER`、`KALTSIT_LEGACY_SHARE`，
即可额外运行真实旧版迁移探针；不设置时仍运行失败回滚。

`tests/assets-preview.qml` 是 Qt/KSVG 素材检查程序，可用 qml 运行并在最后一个参数指定输出 PNG。
`scripts/generate-assets.py` 可重现原创 SVG；上游指针已 vendored，构建无需下载视频或指针仓库。
