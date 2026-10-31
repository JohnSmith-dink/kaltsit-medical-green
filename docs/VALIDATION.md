# 1.1.0-rc.1 验收记录

日期：2026-11-01（Asia/Shanghai）。环境：x86_64-linux / NixOS 26.05 / Plasma 6.6.6 / Wayland。
测试使用本机独立 D-Bus、临时 HOME 和虚拟 KWin 输出。分别验证 Qt Quick 软件后端，
以及通过 Mesa 软件 OpenGL 运行的默认 RHI 后端；未将虚拟渲染等同于物理 GPU 验收。

## 自动检查与素材

- 68 项单元测试通过，保留原有检查，并覆盖组件跳过、预演零写入、缺少工具、自选图片、恢复格式 1 / 2 / 3、父目录链接变更和恢复冲突。
- 复用原 `flake.lock`，没有新增 flake 输入。Nix 离线构建与 `flake check` 通过，构建检查阶段运行完整测试集。
- Home Manager 的 Ghostty 主题文件选项默认关闭，只安装文件；没有新增自动应用动作。
- CI 在 push / pull request 时运行单元测试与 Nix 检查，第三方 Action 固定完整提交。dev.2 的公开 GitHub CI 已通过；rc.1 最新状态见仓库 Actions。
- KSVG 实际渲染九宫格背景；面板/弹窗/通知显示白色表面和轻边框，未覆盖控件使用 Breeze。
- 30 个文件夹名称均有 16、22、32、64px 版本；主要分类经 Qt SVG 实际渲染检查，每档几何单独贴合网格。
- 17 个指针文件、68 个上游别名和 8 个旧版兼容别名完整；上游二进制哈希不变。
- dev.1 的 libXcursor 1.2.3 检查加载了 17×5=85 组动画，逐帧尺寸、延时和热点与固定上游报告一致；本轮资源未改变，哈希与二进制完整性重新检查。
- 用户目录的旧同名指针备份/还原、链接创建失败、后续用户改动及别名路径去重通过检查；同名指针重载不改变尺寸。
- 源 JPEG 哈希与第 707 帧记录一致，桌面和锁屏 `FillMode=2`；3:2 画面不拉伸，人物面部保留。
- 锁屏新增独立 WallpaperItem 插件，仅在底部叠加暖白渐淡衬底；桌面仍用 `org.kde.image`。
  原图字节与原生认证界面保持；插件资源缺失在配置修改前报错，跳过锁屏时不要求此资源。
  自选图片与旧锁屏插件/配置的精确恢复均有回归检查。
- Ghostty / Konsole 16 色一致。正文约 11.95:1；128 组 KDE 前景色与本组常规、交替背景的最低对比度为 4.5562:1；ANSI 普通/Intense 最低 5.58:1，Faint 最低 4.51:1。

## 独立 KDE 会话

- 3120×2080、1.75 缩放下，Qt Quick 软件与 RHI 后端均真实执行 `applied → already-applied → restored`，警告为空。
- 面板/桌面部件 ID、布局、字体、等宽字体、光标尺寸 36 和缩放保持；固定强调色恢复。
- 真实 KDE 工具在壁纸变更后注入故障，样式、壁纸、光标和相关键自动回滚，恢复记录清理。
- 由 v1.0 控制器创建旧记录，v1.1 拒绝覆盖；恢复后应用、重复应用、再次恢复均通过。
- 另用未修改的已公开 dev.2 控制器实际创建格式 3 记录：rc.1 拒绝覆盖原备份，恢复后可应用新锁屏插件、重复应用、再次恢复；原锁屏插件及配置键精确恢复。
- 启动真实 `gtkconfig` 模块后，将六个可选组件的配置设为符号链接：预演不写配置和状态；应用、重复应用、恢复后，链接与目标内容均不变，桌面壁纸不变。
- 单独跳过 GTK、继续应用指针时，记录到应用和恢复各一次 `breeze_cursors → Kaltsit-Sihengtu` 的刷新顺序，GTK 目标内容保持；这验证了刷新命令与文件边界，不替代物理鼠标热点验收。
- 自选 PNG 同时写入桌面与锁屏，`FillMode=2`，恢复后桌面壁纸回到原状态；已有自定义 GTK 字体保持。
- GTK 原先独立选择 Adwaita 指针时，恢复并等待后台同步后仍保留该选择；GTK 导出完成后才记录或恢复配置，避免异步覆盖。
- 配色与图标由系统默认值继承时，离线 `status` 仍显示有效值；本地配置覆盖系统默认值的优先级有单独回归检查。

机器可读摘要见 [nested-session-results.json](nested-session-results.json)，截图见 [预览](../previews/README.md)。

rc.1 另在 1920×1080、100% 缩放下复测，确认 16:9 与 3:2 的原生布局均可使用。
待机与解锁输入页均通过原生 greeter 的 `--testing` 模式捕获，不提交口令。
主组七张实际截图已在 rc.1 使用 RHI 后端重拍，包含待机与原生解锁提示，原始尺寸为 3120×2080；
另附三张 1920×1080 宽屏图与一张软件后端解锁页。对应文件哈希见
[预览清单](../previews/manifest.json)。锁屏由原生 greeter 的 `--testing` 模式生成，没有执行真实锁定或认证。

## 验收边界

独立会话截图是本机实际 KDE 渲染，不是日常会话或物理屏幕的验收截图。
本轮在独立临时会话完成；日常桌面仍使用已部署的 dev.2。最终观感、实际鼠标点击落点及物理多屏行为仍需实屏确认。
像素画的高分屏版本来自上游缩放，不等同于重新绘制高清素材。
原生锁屏使用浅色互补配色、深灰绿时钟与底部阅读衬底。
软件后端保留原生描边；RHI 后端保留 KDE 自身的文字阴影、输入页模糊与亮度变化。
不同壁纸上的可读性仍需实屏确认；
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
设置 `KALTSIT_PREVIOUS_CONTROLLER` 和 `KALTSIT_PREVIOUS_SHARE` 可同样验证前一开发版本的真实记录升级。

`tests/assets-preview.qml` 是 Qt/KSVG 素材检查程序，可用 qml 运行并在最后一个参数指定输出 PNG。
`scripts/generate-assets.py` 可重现原创 SVG；上游指针已 vendored，构建无需下载视频或指针仓库。

## 预览环境补充

从已登录 KDE 终端运行，保留系统的 XDG 资源目录；SSH 调用时需提供相同的系统资源与菜单目录，排除日常用户的配置目录。
验证目录建议使用短路径（如 `/tmp/kt-rc1-3x2`），避免 KIO 的 Unix socket 路径超过限制。
捕获使用独立 Spectacle 实例，并验证文件存在且为可解码 PNG；截图命令最多运行 30 秒。
私有虚拟 KWin 在捕获模式下单独启用测试截图权限，不改变日常 compositor 的权限或配置。

需要同时捕获原生输入提示时，可构建 `nix build path:.#preview-wakeup`，将
`KALTSIT_GREETER_WAKEUP` 指向构建结果的 `lib/kaltsit-preview-wakeup.so`。
此测试辅助库只在 `--testing`、临时 HOME/runtime 和 `kaltsit-test` socket 全部匹配时工作，
收到私有标记文件后只显示原生输入提示，并写入可检查的完成标记，不输入或提交口令。它不安装进主题包，不参与日常锁屏。
设置 `KALTSIT_TEST_WIDTH`、`KALTSIT_TEST_HEIGHT` 和 `KALTSIT_TEST_SCALE` 可检查其他虚拟输出尺寸。
`KALTSIT_QT_RENDERER=default` 使用默认 RHI，仍通过 `LIBGL_ALWAYS_SOFTWARE=1` 限定为测试软件 OpenGL；
默认 `KALTSIT_QT_RENDERER=software` 使用 Qt Quick 软件后端。
