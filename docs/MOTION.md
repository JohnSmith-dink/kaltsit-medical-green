# 动态壁纸（开发版）

`kaltsit-motion` 是 v1.2 之外的可选包，目前版本为 `1.3.0-dev.2`。
包含独立的 Plasma 壁纸资源：**医疗白绿 · 动态壁纸**。
用户选定只部署动态壁纸，启动过渡已从本版移除。
安装资源不会自动启用；原版锁屏、D1 桌面、启动画面设置、CLI、Home Manager 模块和恢复记录格式不变。

## 行为

- 动态壁纸只读取本地视频，静音循环。支持保持比例裁切或完整显示、桌面右键暂停/继续。
- 暂停保留当前帧；组件隐藏时暂停。视频缺失或解码失败时显示静态图片，修正路径后可恢复。
- 使用 Qt Multimedia 与 Qt Quick RHI。Qt Quick 的纯软件绘制后端使用静态图，不持续播放；RHI 使用软件 OpenGL 的隔离会话已验证播放。
- 不做亮度、对比度、饱和度或遮罩处理。不把视频接入锁屏。
- 不承诺被窗口遮挡、锁屏、电池供电时自动暂停；这些状态尚未接入。可在需要时手动暂停。

## 构建与安装

在本开发分支目录中可构建默认包：

```sh
nix build --no-write-lock-file path:.#kaltsit-motion
```

默认包不含视频，未选视频时显示已有静态壁纸。安装应复用系统的 `pkgs`，与当前 Plasma/Qt 版本匹配，例如在 NixOS 配置中：

```nix
{ pkgs, ... }:
let
  source = /absolute/path/to/kaltsit-medical-green;
  baseTheme = pkgs.callPackage (source + "/package.nix") { };
  motion = pkgs.callPackage (source + "/motion.nix") {
    inherit baseTheme;
    # 可省略，在桌面壁纸设置中选择本地视频。
    videoFile = /absolute/path/to/balanced.mp4;
    # 可选：与视频开头一致的静帧，默认沿用原版壁纸。
    posterFile = /absolute/path/to/poster.jpg;
  };
in {
  environment.systemPackages = [ motion ];
}
```

按原有配置方式允许 `kaltsit-theme` 和 `kaltsit-motion` 的 unfree 标记。
传入 `videoFile` / `posterFile` 会复制到本机 Nix store，并作为构建依赖；不要把私人素材随源码上传或发往公开二进制缓存。
仅从桌面设置选择本地路径时不会把该视频复制进 Nix store，需保证文件持续存在。

1. 安装资源后，在桌面「配置桌面和壁纸」中选择「医疗白绿 · 动态壁纸」。留空使用安装时的视频，也可选择自己的本地文件。
2. 如果既有 Plasma 进程未发现新安装的 QML 依赖，注销后重新登录。

`kaltsit-theme apply/restore` 仍只管理原版主题组件，不负责启用或备份动态壁纸。
启用前记下原有壁纸选择；停用时在相同页面恢复原壁纸插件（通常为「图像」）与图片，再移除可选包。

## 本次私人视频素材

来源：用户本地 Wallpaper Engine 创意工坊项目 `3722159822` 的 `明日方舟 - 凯尔希.mp4`。
原片 3840×2160 / 60 fps，约 23.57 秒，SHA-256：

```text
d1e60abcb03a0a2a7dc687886f23ba8e0ff741a125f6d8ee17e2b4aad1d5254e
```

私人预览使用 2560×1440 / 30 fps 的静音转码，保留原时间线与原色，不插帧，不增加装饰。
原片和衍生视频均不加入 Git；保留已有素材署名与许可范围，不因用户提供本地文件推定公开再分发授权。

## 验证范围

本轮使用与锁定依赖一致的 Plasma 6.6.6 / Qt 6.11.2，在独立 HOME、D-Bus 和 KWin 虚拟输出中验证。
覆盖 1920×1080 / 100% 与 3120×2080 / 175%，以及原生播放、暂停、隐藏、循环、错误回退和恢复。
硬件解码、长期功耗、多屏与桌面右键交互需实机验收。
具体结果与录屏保存在本次私人预览报告中；现有 84 项测试及 Nix 构建检查另行记录。

实现依据：[Qt MediaPlayer](https://doc.qt.io/qt-6/qml-qtmultimedia-mediaplayer.html)、
[KDE 原生壁纸接口](https://raw.githubusercontent.com/KDE/plasma-workspace/Plasma/6.6/wallpapers/image/imagepackage/contents/ui/main.qml)。
