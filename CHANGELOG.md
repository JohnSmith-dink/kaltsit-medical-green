# 版本记录

## v1.0.0 — 2026-10-29

首个公开版本：凯尔希 · 医疗白绿。

- 完整浅色 KDE Plasma 6 主题、青绿文件夹图标、已有凯尔希动态指针与 4K 静帧壁纸。
- 桌面、锁屏、Ghostty、Konsole 与 Breeze GTK 配色。
- 显式 `apply` / `restore` / `status`，保留桌面布局、字体、缩放与光标尺寸。
- 按键恢复、失败回滚、重复应用幂等、KConfig 实时通知，以及 GTK 后台同步兼容。
- 独立 Nix flake、锁定依赖、Home Manager 可选安装模块和完整署名说明。
- 空值或相对 XDG 目录按规范回退到 HOME，避免写入调用者的工作目录。
- 29 项测试；已在 x86_64-linux / NixOS 26.05 / Plasma 6.6.6 / Wayland 验证。

安装不自动切换外观。SDDM、开机动画、引导菜单及软件专属皮肤不属于此版。
