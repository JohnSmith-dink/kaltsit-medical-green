# 素材、署名与许可范围

## 原创主题代码

医疗白绿配色、原创 Plasma 背景与文件夹 SVG、KDE / Ghostty / Konsole 配置、Nix 包装、
切换与恢复工具、测试和新写文档使用 MIT，见 [LICENSE](LICENSE)。
下述 KDE 上游派生 QML 不属于此 MIT 许可范围。
KDE Breeze 控件、装饰与图标由系统依赖提供；本项目通过主题继承使用，
没有把 Breeze 应用图标复制进自己的图标包。

## KDE 锁屏 QML 与构建适配

rc.3 的 Nix 构建使用匹配的 `plasma-desktop` 和 `plasma-workspace` 依赖，
在构建时原样复制完整 Plasma shell，并从以下 KDE 上游文件生成局部差异：

- [LockScreenUi.qml](https://raw.githubusercontent.com/KDE/plasma-desktop/Plasma/6.6/desktoppackage/contents/lockscreen/LockScreenUi.qml)：生成文件仅替换 Fader 类型引用。
- [WallpaperFader.qml](https://raw.githubusercontent.com/KDE/plasma-workspace/Plasma/6.6/lookandfeel/components/WallpaperFader.qml)：生成文件仅在本主题锁屏插件生效时将颜色变换系数设为 1；其余壁纸沿用上游行为。

上述文件原始版权声明包含 Aleix Pol Gonzalez，许可为 **GPL-2.0-or-later**。
生成的派生文件保留上游版权及 SPDX 许可声明，继续适用 GPL-2.0-or-later；本项目的 MIT 许可不涵盖它们。
随包提供 [GPL-2.0-or-later 许可文本](LICENSES/GPL-2.0-or-later.txt)。
未改动的认证和界面文件在构建时从对应 KDE 依赖逐字节复制，遵循各自上游许可。
仓库不维护独立的认证源码分支，原生认证、输入及焦点行为保留；这些实现仍属于 KDE 上游，而非本项目原创。

## 凯尔希 · 思衡托鼠标指针

- 原作者：[一球咸鱼](https://space.bilibili.com/3585839)。
- 原 Windows 作品：[凯尔希 · 思衡托](https://www.bilibili.com/video/BV1L5Vq6vEaX/)。
- 作者视频（用户提供的短链接）：[b23.tv/zHvHCpF](https://b23.tv/zHvHCpF)。
- 本主题中的指针对应维护者的 [kaltsit-cursors](https://github.com/JohnSmith-dink/kaltsit-cursors) 项目。
- [已有授权记录](https://github.com/JohnSmith-dink/kaltsit-cursors/blob/main/CREDITS.md)
  与 [许可范围](https://github.com/JohnSmith-dink/kaltsit-cursors/blob/main/LICENSE)：
  原作者于 2026-10-24 同意 Linux 适配及 nixpkgs 提交；维护者承诺署名、原作链接与非商业用途。

本版固定使用提交 `7ef139a6210fd8eb03d0296b624d71eaa3120589` 的 `theme/Kaltsit/cursors`，
17 个文件与 68 个别名保持原样；另保留 8 个旧版本兼容别名。
保留原始动态帧、延时与热点，支持 24 / 32 / 48 / 64 / 96px；这些是上游对 32px 像素画的最近邻缩放。
安装标识仍为 `Kaltsit-Sihengtu`，不改变既有恢复记录。上游许可、署名和构建报告随指针打包，
固定来源及文件清单见 [cursor-source.json](docs/cursor-source.json)。指针绘图与转换后图像保留原作者权利。
已有专项授权不等于通用 MIT / GPL / CC 许可，也不推定商业使用或再授权权利。
新增作者视频链接用于署名与来源说明，不改变上述已有授权范围。

## 壁纸

壁纸来自维护者已有的凯尔希动画素材，从本地 4K VBG 中无损取出第 707 帧。
本次来源记录没有提供可核实的原画作者或通用再分发许可；不将壁纸声明为 MIT。
来源文件哈希、静帧偏移及图像哈希见 [asset-provenance.json](docs/asset-provenance.json)。

可选动态壁纸的原创 QML 和 Nix 包装使用 MIT。
本轮用户提供的原视频与私人衍生视频不加入仓库，也不因这些代码的许可获得再分发授权；
来源和 SHA-256 见 [动态扩展说明](docs/MOTION.md)。默认扩展仍使用上述已有壁纸，完整包保留 unfree 标记。

本项目为非官方同人主题。明日方舟、凯尔希及相关原游戏美术的权利归相应权利人；
本项目不表示与原作权利人有官方关联。素材归属补充与移除请求可通过仓库 Issues 提交。
