# 验证记录

日期：2026-10-29（America/Los_Angeles）。已验证环境为 Plasma 6.6.6 / Wayland。

## 已执行的检查

- 29 项 Python 测试通过：主题与图标结构、原始壁纸哈希/尺寸、完整终端配色、
  文本对比度、恢复原始键、失败回滚、幂等、后续无关修改、配置符号链接保护、
  强调色、KConfig 通知以及 KDE 后台 GTK 同步。
- `kpackagetool6 --type Plasma/LookAndFeel --show org.xinyan.kaltsit.medicalgreen`
  使用主题数据路径时能识别正确名称、标识、作者和包路径。
- Ghostty 1.3.1 的 `+validate-config` 接受对应终端主题。
- 在独立 D-Bus、临时 HOME 和虚拟 KWin/Plasma 会话中运行真实 KDE 工具。
  屏幕为 3120×2080，使用 `kscreen-doctor` 显式设为 1.75 缩放，应用和恢复后均断言保持。
- 实际结果为 `applied` → `already-applied` → `restored`，应用/恢复警告均为空。
  桌面与面板部件 ID 不变，字体、等宽字体、光标尺寸 36 和原强调色设置均恢复。
  主题的选中态与链接色未被旧强调色或壁纸强调色覆盖。
- 安装前，正在使用的桌面布局、kdeglobals 与 kcminputrc 的 SHA-256 均与记录一致。
  主题切换测试使用独立会话，未在当前桌面执行 apply。
- Nix 离线构建预查不需要下载新依赖；模块仅安装资源与命令，没有主题切换 activation。

隔离会话的机器可读结果见 `nested-session-results.json`。构建通过后生成的公开压缩包及校验值随 v1.0.0 发布。

## 视觉检查与边界

- 正文在暖白背景的对比度约 11.95:1；KDE 正常前景最低 4.75:1。
- 终端普通/Intense ANSI 最低 5.58:1，Faint 最低 4.51:1。
- 3840×2160 静帧保持原始 JPEG 字节。桌面与锁屏均设 `FillMode=2`，保持比例裁切。
- 交互设计示意的五个状态及 320px 窄屏已检查；示意不是实机截图。
- 本次实机软件验证使用虚拟输出和软件渲染，未执行真实锁屏、登录认证或替换当前桌面。
  原生屏幕上的最终观感由用户主动应用后确认；独立绘制界面的应用可能保留自身样式。

## 重复运行

```sh
python3 -m unittest discover -s tests -v
```

`tests/nested-session.sh` 必须放在临时 HOME、独立 XDG 目录、独立运行目录及
`dbus-run-session` 内执行；它会修改该测试会话的桌面。不要直接在日常会话执行。
所需命令包括 KWin、Plasma、KScreen、Python、qdbus、busctl 和 KDE 配置工具。
