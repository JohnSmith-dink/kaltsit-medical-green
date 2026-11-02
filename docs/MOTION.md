# 动态壁纸 · v1.3.0

`kaltsit-motion` 是独立的可选扩展包，版本为 `1.3.0`。
包含独立的 Plasma 壁纸资源：**医疗白绿 · 动态壁纸**。
本包只提供动态壁纸，不安装启动画面。
安装资源不会自动启用；原版锁屏、D1 桌面、启动画面设置、CLI、Home Manager 模块和恢复记录格式不变。

## 行为

- 动态壁纸只读取本地视频，静音循环。支持保持比例裁切或完整显示、桌面右键暂停/继续。
- 暂停保留当前帧；组件隐藏时暂停。右键暂停写入 `Paused` 配置，跨会话保留，重启后仍为暂停。视频缺失或解码失败时显示静态图片。允许播放时每隔 60 秒最多额外重试 3 次；暂停期间不重开媒体，恢复后等待完整间隔。重试成功收到新帧后才显示视频，失败达到上限会记录日志并保留静图；更换视频源重置预算。
- 使用 Qt Multimedia 与 Qt Quick RHI。Qt Quick 的纯软件绘制后端使用静态图，不持续播放；RHI 使用软件 OpenGL 的隔离会话已验证播放。
- 不做亮度、对比度、饱和度或遮罩处理。不把视频接入锁屏。
- 电池供电默认自动暂停，可选“照常播放”；收到锁定状态时自动暂停。手动暂停优先，自动条件解除不会清除它。DPMS 和窗口完全遮挡尚未接入。

## 构建与安装

在本版本源码目录中构建：

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
已验收开发源码 `7c175b8` 部署至 NixOS generation 56；3120×2080 / 175% 内屏上，用户确认「画面流畅，暂停和继续正常」。
正式版沿用同一播放器逻辑，单独检查版本标识、构建与发行包。现有 84 项测试及 Nix flake check 通过。
硬件解码未确定测量，长期功耗和多屏未验收；不把内屏验收扩大到这些范围。见 [发布依据](V1.3-RELEASE.md)与[最小验收记录](v1.3-acceptance.json)。

实现依据：[Qt MediaPlayer](https://doc.qt.io/qt-6/qml-qtmultimedia-mediaplayer.html)、
[KDE 原生壁纸接口](https://raw.githubusercontent.com/KDE/plasma-workspace/Plasma/6.6/wallpapers/image/imagepackage/contents/ui/main.qml)。

## 自动暂停信号调研（Unreleased）

基线为锁定 nixpkgs `da6dc0e7b26060f2f71ce3ef7088fb56ee44fa36`，Plasma 6.6.6 / Qt 6.11.2。
2026-11-01 在独立 HOME、运行目录和 D-Bus 的 offscreen Qt 进程中，以假服务触发了真实 KDE QML 模块：

| 条件 | 来源与观察 | 接入决定 |
|---|---|---|
| 电池 | `powermanagement` 的 `AC Adapter / Plugged in` 随假服务的 `PowerSaveStatusChanged` 在 true/false 间变化；服务离开及重连也由 `DBusServiceWatcher` 观测到 | 直接读取同一服务的 `GetPowerSaveStatus` 并订阅通知，避免数据引擎在查询失败时把状态默认为接电 |
| 锁屏 | `org.freedesktop.ScreenSaver` 的 `/ScreenSaver`，初始 `GetActive=false`，`ActiveChanged(true/false)` 均到达真实 `SignalWatcher` | 接入初始查询及配对通知；不使用 `canLock` 或 `AboutToLock` |
| DPMS | 尚未找到并复现适合壁纸组件的每屏电源通知；没有观察到真实虚拟输出熄灭／唤醒 | 尚未接入；不把空闲或 `visible` 等同于 DPMS |
| 完全遮挡 | 未验证跨屏、虚拟桌面、活动及透明窗口的完全覆盖信号 | 尚未接入；最大化不足以判断遮挡 |

以上电池及锁屏变化来自**可控假 D-Bus 服务**，不是拔电源或真实认证锁屏；Qt、DataSource、SignalWatcher 和服务监视器是真实模块。未对日常桌面施加任何操作。没有为未接入条件新增进程轮询、守护进程或窗口跟踪服务。

来源：[电源引擎](https://github.com/KDE/plasma5support/blob/v6.6.6/src/dataengines/powermanagement/powermanagementengine.cpp)、[锁定状态实现](https://github.com/KDE/kscreenlocker/blob/v6.6.6/interface.cpp)、[QML 信号订阅接口](https://github.com/KDE/plasma-workspace/blob/v6.6.6/components/dbus/dbussignalwatcher.h)。
`GetActive` 比较的是 `KSldApp::Locked`；锁定、解锁分别发出 `ActiveChanged(true/false)`。
Qt Multimedia 的 `playbackRate` 是播放速度，未证明能保持原速度并可靠降低解码帧率，因此不提供 `reduce` 策略。

补完版原生检查：真实 Qt RHI / Mesa 软件 OpenGL 在独立 KWin 中通过 35 项行为检查，纯软件绘制后端通过静态回退检查。信号由私有假服务控制；同源文件修复、三次重试耗尽、暂停阻止重试、服务重连及重建组件后保留传入的暂停设置均已检查。测试把内部重试间隔缩为 700 ms；生产默认仍为 60000 ms。未执行物理拔电源、真实认证锁屏或 DPMS 验证。

## 准备视频

仓库不分发视频，视频版权与使用权限由使用者负责。独立脚本 [encode-wallpaper.sh](../scripts/encode-wallpaper.sh) 不包装进 Nix 包；需要 Bash、GNU coreutils 与 ffmpeg：

```sh
bash scripts/encode-wallpaper.sh /path/to/input.mp4
bash scripts/encode-wallpaper.sh --fps 24 --width 1280 --bitrate 4M /path/to/input.mp4 /path/to/wallpaper.mp4
```

默认静音 H.264 / yuv420p / faststart / 30 fps，宽度上限 1920，保持比例、不放大，尺寸为偶数，码率上限 6M。`--fps`、`--width`、`--bitrate` 可覆盖这些数值。
默认输出为输入真实目录下的 `<名称>-wallpaper.mp4`；指定输出也必须在同一真实目录，已有文件和符号链接均拒绝覆盖。只允许本地文件协议，不联网；不保留音轨、字幕、数据轨及元数据。失败留下的部分输出需自行处理后使用新文件名重试。
脚本参数及路径边界由假 ffmpeg 测试；未用此脚本进行真实转码验收。测量方法见[动态壁纸测量页](MOTION-MEASUREMENT.md)。
