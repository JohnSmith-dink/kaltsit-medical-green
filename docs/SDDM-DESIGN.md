# SDDM 实验性主题设计

此设计对应 Unreleased，版本号保持 1.3.0。仓库不存在 `docs/ROADMAP-v1.2.md`；现有 `V1.2-DEVELOPMENT.md` 仅把 SDDM 列为暂缓。本轮将它作为独立、默认关闭的系统级扩展，不扩大原主题包或 Home Manager 的运行职责。

## 已检查的依赖与主题格式

实际求值锁定 nixpkgs `da6dc0e7b26060f2f71ce3ef7088fb56ee44fa36`：`kdePackages.sddm.version = 0.21.0`，`kdePackages.qtbase.version = 6.11.2`，`qtdeclarative.version = 6.11.2`。
检查位置：

- nixpkgs [`pkgs/applications/display-managers/sddm/unwrapped.nix`](https://github.com/NixOS/nixpkgs/blob/da6dc0e7b26060f2f71ce3ef7088fb56ee44fa36/pkgs/applications/display-managers/sddm/unwrapped.nix)：版本、`BUILD_WITH_QT6`、qtbase/qtdeclarative 依赖与四个补丁。
- 同目录 [`default.nix`](https://github.com/NixOS/nixpkgs/blob/da6dc0e7b26060f2f71ce3ef7088fb56ee44fa36/pkgs/applications/display-managers/sddm/default.nix)：包装 greeter，`extraPackages` 加到构建环境并由 Qt 包装钩子处理 QML 导入。
- SDDM 0.21.0 [`ThemeMetadata.cpp`](https://github.com/sddm/sddm/blob/v0.21.0/src/common/ThemeMetadata.cpp)：INI 格式 `metadata.desktop`，组 `[SddmGreeterTheme]`，`MainScript=Main.qml`、`ConfigFile=theme.conf`、`QtVersion=6`。不写 QtVersion 会默认 Qt 5，故必须显式写 6。

交付包含 `Main.qml`、`metadata.desktop`、`theme.conf`、构建生成的配色及已有静态 JPEG。仅使用 QtQuick、QtQuick.Layouts、QtQuick.Controls.Basic 与 greeter 注入的 `sddm/userModel/sessionModel/keyboard` 上下文。上述 Qt 模块由锁定 SDDM 的 qtdeclarative 依赖提供；不预先加入 Kirigami、Plasma 或第三方 QML 包。是否实际导入成功须由后续 test-mode 验证，设计阶段未验证。

## NixOS 接入

依据锁定 [`nixos/modules/services/display-managers/sddm.nix`](https://github.com/NixOS/nixpkgs/blob/da6dc0e7b26060f2f71ce3ef7088fb56ee44fa36/nixos/modules/services/display-managers/sddm.nix)：

- `services.displayManager.sddm.theme` 是字符串，默认空；`extraPackages` 是额外 Qt 插件／QML 库列表。
- 模块将配置中的 ThemeDir 设为 `/run/current-system/sw/share/sddm/themes`，在 SDDM 启用时链接 `/share/sddm`。
- 主题包安装到 `$out/share/sddm/themes/KaltsitMedicalGreen`，加入 `environment.systemPackages` 后由系统环境提供发现路径。
- 新模块 `programs.kaltsit-sddm.enable` 默认 false；仅显式启用时安装独立 `kaltsit-sddm` 包，并用 `lib.mkDefault` 设置主题名。用户显式设置的主题优先，不启用 SDDM 服务本身，不改 PAM、自动登录或其他系统设置。
- 现有 greeter 依赖已涵盖计划中的 Qt 导入，预期无需额外 `extraPackages`；加载检查若发现确切缺失才补对应包。保持调用者的 `pkgs`，不引入第二套 nixpkgs。

## 外观与交互范围

沿用现有静态壁纸和 `share/color-schemes/KaltsitMedicalGreen.colors`，构建时提取色值，不新增或改动色板。使用保持比例裁切背景和不透明登录面板。
仅提供用户选择、用户名输入、密码、错误提示、会话选择、键盘布局显示、关机和重启；无视频、动画、头像上传或额外语言切换器。中文可翻译字符串沿用 `qsTr`，不新增翻译流水线。
错误正文对比度至少 4.5:1，控件边界至少 3:1，输入框具有键盘焦点标记。密码仅交给 SDDM 的登录 API，不写日志或文件；失败清空并恢复焦点。认证与会话启动仍由 SDDM 负责。
完整包保留混合素材的 unfree 处理，署名及来源叙述不修改。SDDM 资源独立；主包按既有规则收录文档造成哈希变化是预期行为。

## 风险与恢复

[`GreeterApp.cpp`](https://github.com/sddm/sddm/blob/v0.21.0/src/greeter/GreeterApp.cpp) 在 QQuickView 加载错误时切换到 `qrc:/theme/Main.qml`，并报告 `Fallback to embedded theme`。本主题不添加自动切换逻辑。这仅覆盖 QML 加载错误，不能保证显示服务器、Qt 插件、守护进程或 PAM 故障时仍可登录。
`--test-mode` 只加载界面，不提供真实 PAM 认证或会话启动证明；无 daemon 时电源能力默认 false（[`GreeterProxy.cpp`](https://github.com/sddm/sddm/blob/v0.21.0/src/greeter/GreeterProxy.cpp)）。

未来真机首次启用：先保留上一代启动项与已知可用的声明式配置，确认 TTY 登录可用；先 `sudo nixos-rebuild build --flake /path/to/system#host`，再 `sudo nixos-rebuild boot --flake /path/to/system#host`，下次启动观察。不要用 `switch` 首次启用。
若失败，在启动菜单选择上一代 NixOS；菜单名称因启动器配置而异，当前主机回滚未验证。也可用 Ctrl+Alt+F3 尝试 TTY，登录后执行：

```sh
sudo nixos-rebuild boot --rollback
sudo reboot
```

或者把 `programs.kaltsit-sddm.enable` 改回 false，恢复之前显式设置的主题，再执行上述 build、boot 和重启。`boot --rollback` 的依据是锁定 nixpkgs 中 `nixos-rebuild-ng/src/nixos_rebuild/__init__.py` 接受 BOOT 与 rollback，`nix.py` 使用系统 profile 的 `nix-env --rollback`，随后执行所选代的启动安装动作。这里只核对源码，未在主机执行这些恢复命令；没有上一代或已清理旧闭包时不能依赖回滚。

## 验证顺序

1. 构建 `nix build --no-write-lock-file path:.#kaltsit-sddm`。以同一锁定 nixpkgs 构建 `kdePackages.sddm`，运行它的 `bin/sddm-greeter-qt6 --test-mode --theme /nix/store/<主题包>/share/sddm/themes/KaltsitMedicalGreen`。实际执行时必须提供独立 HOME、XDG 目录、D-Bus、offscreen 或私有显示服务器。锁定 greeter 的 `--help` 已确认这两个参数。
2. 为独立测试 flake 定义 `nixosConfigurations.sddm-test`，仅在该 VM 启用 SDDM 和主题、创建虚构测试账号；不导入主机配置、共享 HOME 或真实密钥。进入临时工作目录后运行 `nixos-rebuild build-vm --flake /absolute/path/to/test-flake#sddm-test`，再运行 `./result/bin/run-sddm-test-vm`。完整配置和执行记录在验证阶段补齐；设计阶段未构建 VM。
3. 在 VM 内检查错误密码、正确密码、进入会话、退出返回 greeter、故意损坏主题的 SDDM 自带回退；电源按钮只在 VM 内测试。截图明确标记 test-mode 或 VM，新增到 `previews/sddm/`，清单只追加。

## 尚未确认

设计阶段尚未加载新主题、未测 VM 认证／电源操作／损坏主题回退，未验证真机或恢复路径，也未验证多屏、特殊输入法与无障碍辅助认证。不会把后续截图当作这些项目的证明。若 VM 环境受阻，保留未验证状态和复现步骤，不启用主机主题。
