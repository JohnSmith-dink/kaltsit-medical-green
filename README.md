# 凯尔希 · 医疗白绿

**Kal'tsit Medical Green 1.1.0-dev.1 · 克制日常**

适用于 NixOS / KDE Plasma 6 的浅色主题：暖白 `#F4F7F2`、白色面板、
深灰绿正文 `#25352D`、青绿强调色 `#2E6B57`。轻边框与柔和阴影覆盖面板和弹窗，
其余 Plasma 元素回退到 Breeze；Dolphin、系统设置和窗口装饰保留原生控件。
终端保持浅色，安装后需要主动切换。

![Dolphin 实际渲染：独立 Plasma 测试会话，3120×2080，175%](previews/actual/dolphin.png)

上图来自本机独立 KWin/Plasma 会话中的真实应用，并非概念样图。
完整的桌面、菜单、Dolphin、终端、通知与锁屏画面见 [预览说明](previews/README.md)
或本地打开 [预览画廊](previews/index.html)。物理屏幕上的最终观感仍需用户确认。

## 安装与切换

这是独立的 **v1.1 开发版本**，不替换已发布的 v1.0.0。已验证环境为
x86_64-linux、NixOS 26.05、Plasma 6.6.6 / Wayland；复用现有 `flake.lock`。
主题素材含单独权利范围，完整包标记为 `unfree`，见 [CREDITS.md](CREDITS.md)。

在本开发源码目录中：

```sh
# 构建与安装均不切换外观
nix build --no-write-lock-file path:.#kaltsit-theme
nix profile install path:.#kaltsit-theme
kaltsit-theme status
```

如果已经通过 Home Manager 安装，应更新其包来源，避免同时安装两份同名包。
**先安装资源，再应用**：已经运行的 Plasma 要能从用户/系统数据目录发现新样式；
仅用未安装的 `nix run` 执行 apply 不保证已有进程能找到它。

```sh
# 已应用旧版本时先恢复。失败或冲突时先处理输出，不要删除恢复记录。
kaltsit-theme restore
kaltsit-theme apply
kaltsit-theme status

# 返回应用前状态
kaltsit-theme restore
```

首次使用可直接 `apply`。重复应用同版本不覆盖备份；旧版本处于 active 状态时，
v1.1 会明确要求先 restore 再 apply。`status` 显示安装版本、应用版本和当前 Plasma 样式。
主题也能在 KDE 全局主题列表中发现，但完整切换请用命令，以覆盖终端等附加设置。

## Home Manager

将源码纳入自己的配置，然后导入模块：

```nix
{ ... }: {
  imports = [ ./path/to/kaltsit-medical-green/home-manager.nix ];
  programs.kaltsit-theme.enable = true;
}
```

模块复用调用者的 `pkgs`，允许 `kaltsit-theme` 的 unfree 标记后即可构建；也可用
`programs.kaltsit-theme.package` 指定 flake 的 `packages.x86_64-linux.kaltsit-theme`。
模块默认关闭，只安装主题与 Breeze GTK，不包含 activation 切换命令。
无需 Stylix 或 plasma-manager。旧式入口 `nix-build` 使用本机 `<nixpkgs>`。

## 覆盖与恢复

- 桌面、原生启动菜单、通知、面板，以及窗口、Dolphin 和系统设置的统一配色。
- 30 种文件夹名称，分别绘制 16 / 22 / 32px 与可缩放版本，应用图标继承 Breeze。
- 24 / 32 / 48 / 64 / 96px 动态指针，保留 `Kaltsit-Sihengtu` 标识、动画、热点与用户尺寸。
- 第 707 帧原始静帧用于桌面和锁屏，按比例裁切；原生锁屏认证行为不变。
- Ghostty、Konsole 的完整浅色 ANSI 配色；GTK 通过 Breeze GTK 跟随系统。

切换工具通过 KDE 命令修改配置键，备份新增 Plasma 样式键并按键恢复。
不重置面板位置、固定应用、桌面图标，不修改字体、缩放、Shell 或快捷键。
失败时尝试恢复本次修改；恢复时保留之后添加的无关设置。
用户后来改动同一个主题键时会报告冲突并保留该值和备份，解决冲突后可再次 restore。
备份位于 `${XDG_STATE_HOME:-$HOME/.local/state}/kaltsit-theme/active.json`，不打包上传。

若用户目录存在同名旧指针（`~/.icons` 或 XDG 用户图标目录），apply 会将其原样移入
私有备份目录，再链接至已安装的新资源；restore 会还原原目录或原链接。
这避免旧 32px 副本遮盖 Nix 的多尺寸版本。同名主题会重新加载动画，尺寸设置保持不变。
恢复记录格式升级为 2，仍能读取旧格式；降级安装前必须用 v1.1 执行 restore，
旧版工具会拒绝新记录，以免丢失指针目录备份。

配置为只读符号链接时拒绝覆盖。声明式用户可自行引用素材，或让相关键由 KDE 管理。
SDDM、Plymouth、引导界面与浏览器专属皮肤不在本版范围；独立绘制界面的应用可能保留自己的样式。

## 指针与素材来源

指针固定为 [kaltsit-cursors 的 7ef139a](https://github.com/JohnSmith-dink/kaltsit-cursors/tree/7ef139a6210fd8eb03d0296b624d71eaa3120589)。
17 个 Xcursor 文件及上游 68 个别名原样纳入，并补留 v1.0 的 8 个兼容别名。
原画为 32px 像素画，多尺寸采用上游最近邻缩放，未声称新增高清原画。
原作者：[一球咸鱼](https://space.bilibili.com/3585839)；
作者视频：[b23.tv/zHvHCpF](https://b23.tv/zHvHCpF)；
原作品：[凯尔希 · 思衡托](https://www.bilibili.com/video/BV1L5Vq6vEaX/)。
文件哈希、别名和固定提交见 [cursor-source.json](docs/cursor-source.json)。

壁纸为既有 4K VBG 的第 707 帧原始 JPEG，3840×2160，不附带整段视频。
3120×2080 屏幕按 3:2 居中裁切，相当于原图左右各裁 300px，人物面部保留、比例不变。
详情见 [素材记录](docs/asset-provenance.json)。原创代码、Plasma SVG 与文件夹使用 MIT；角色图像和指针不纳入 MIT。

## 开发验证

```sh
python3 scripts/generate-assets.py
python3 -m unittest discover -s tests -v
nix flake check --no-write-lock-file path:.
```

43 项测试覆盖原有 29 项及新增样式恢复、旧版记录、文件夹尺寸、指针完整性和本地副本恢复。
真实 KDE 会话验证了应用、重复应用、恢复、失败回滚和从 v1.0 恢复后升级。
libXcursor 成功加载 85 组指针/尺寸并核对全部动画与热点。
正文对比度约 11.95:1，KDE 普通前景最低 4.75:1；ANSI 普通/Intense 最低 5.58:1，Faint 最低 4.51:1。
检查范围、运行方式和待确认事项见 [验收记录](docs/VALIDATION.md)。
