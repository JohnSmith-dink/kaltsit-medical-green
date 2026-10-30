# 凯尔希 · 医疗白绿

**Kal'tsit Medical Green v1.0.0** — 用于 NixOS / KDE Plasma 6 的白绿桌面主题。

暖白内容背景、纯白面板、青绿选中态与深灰绿文字，搭配凯尔希静态壁纸、
绿色文件夹和动态鼠标指针。沿用 Breeze 原生控件、窗口装饰与已有桌面布局。
安装后由用户主动切换，提供应用、状态查询和恢复命令。

![凯尔希壁纸静帧](previews/wallpaper-source.jpg)

## 安装与切换

已验证环境：x86_64-linux、NixOS 26.05、KDE Plasma 6.6.6 / Wayland。
需要已启用 Nix flakes 的 Nix 环境；完整主题包含具有单独权利范围的角色素材，
包按 `unfree` 标记，许可与署名见 [CREDITS.md](CREDITS.md)。

```sh
nix profile install github:JohnSmith-dink/kaltsit-medical-green/v1.0.0
kaltsit-theme status
kaltsit-theme apply
```

在已登录的 KDE 会话内执行 `apply`。恢复应用前的外观：

```sh
kaltsit-theme restore
```

也可先只构建，或从已解压/克隆的源码运行：

```sh
nix build .
nix run . -- status
nix run . -- apply
```

主题会出现在 KDE 的全局主题列表中。完整应用和恢复请使用命令，
因为全局主题选择器不管理 Ghostty 等附加配置。

## Home Manager

在自己的 flake 中添加输入：

```nix
inputs.kaltsit-theme.url = "github:JohnSmith-dink/kaltsit-medical-green/v1.0.0";
```

在 Home Manager 用户模块中导入并启用：

```nix
{ inputs, ... }:
{
  imports = [ inputs.kaltsit-theme.homeManagerModules.default ];
  programs.kaltsit-theme = {
    enable = true;
    package = inputs.kaltsit-theme.packages.x86_64-linux.default;
  };
}
```

按自己的配置方式将 `inputs` 传入用户模块。指定上面的 `package` 可复用项目锁定的包；
如果采用模块默认的 `pkgs.callPackage`，请在自己的包集合中允许 `kaltsit-theme`。
模块默认关闭，启用后仅安装主题与 Breeze GTK，没有自动切换钩子。

旧式 Nix 入口也可用：`nix-build`。此入口使用本机 `<nixpkgs>`，
要复现本项目的锁定版本请使用 flakes。

## 覆盖内容与恢复行为

- 桌面壁纸、面板、启动菜单、通知、窗口、Dolphin、图标与指针。
- 锁屏沿用原生认证控件，使用同源凯尔希壁纸。
- Ghostty 与 Konsole 的完整浅色 ANSI 配色；保留字体、Shell 和快捷键。
- GTK 通过 Breeze GTK 配色同步；独立绘制界面或 libadwaita 应用可能保留自身风格。
- 不重置面板或桌面部件，保留缩放和光标尺寸；桌面/锁屏壁纸使用等比裁切。

`apply` 记录外观相关键与原壁纸，重复应用保持幂等，失败时尝试回滚。
`restore` 保留之后添加的无关设置；发现用户后续修改了同一主题选项时会报告冲突，
保留该值与恢复记录，修正冲突后可再次执行。恢复记录位于
`${XDG_STATE_HOME:-$HOME/.local/state}/kaltsit-theme/active.json`，仅留在本机。

被 Home Manager 等工具管理为只读符号链接的配置会被拒绝覆盖。
使用声明式配置的用户可单独引用安装后的素材，或先让外观相关配置可由 KDE 写入。
SDDM、Plymouth、引导菜单与浏览器专属皮肤不在本版范围。

## 指针与素材

主题内指针是 [kaltsit-cursors](https://github.com/JohnSmith-dink/kaltsit-cursors)
对应的 **凯尔希 · 思衡托** 图像，原作者为
[一球咸鱼](https://space.bilibili.com/3585839)。本版保留已经验证的本地
`Kaltsit-Sihengtu` 32px 转换版本及别名；独立指针项目还提供多尺寸构建。
两者不共享一份安装目录，也不会替换彼此的文件。

壁纸是既有 4K 动画的第 707 帧，保持原始 JPEG 字节，不附带整段视频。
原始画面 3840×2160；KDE 按显示器比例裁切，无需固定为某台电脑的分辨率。
具体来源、哈希和权利边界见 [素材记录](docs/asset-provenance.json) 和
[署名说明](CREDITS.md)。原创代码与文件夹 SVG 使用 MIT；角色图像和指针不纳入 MIT。

## 验证与开发

```sh
python3 -m unittest discover -s tests -v
nix flake check
```

测试覆盖主题结构、图标链接、29 项控制器与素材检查、文本对比度、恢复与错误回滚。
已在独立 Plasma 会话中验证 3120×2080、175% 缩放下的应用、重复应用和恢复。
正文对比度约 11.95:1；终端普通/Intense 最低 5.58:1，Faint 最低 4.51:1。
详见 [验收记录](docs/VALIDATION.md)。

`previews/kaltsit-medical-green.html` 为聊天预览的设计示意源，包含桌面、菜单、
Dolphin、终端、锁屏五种状态；它不是当前桌面的截图，图标依赖预览容器。
本版没有将未验证的架构、X11 或其他桌面列为已支持环境。
