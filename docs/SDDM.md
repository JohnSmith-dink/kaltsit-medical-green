# 登录界面（SDDM，实验性）

`kaltsit-sddm` 是独立的 Qt 6 静态登录主题，默认不启用。它不改变原桌面、锁屏、Home Manager、认证策略或日常恢复记录。仅使用仓库已有静帧，颜色在构建时从既有配色提取。
设计依据、锁定版本及回退边界见 [SDDM 设计](SDDM-DESIGN.md)。

## 安装与启用

在系统 flake 中引用本地开发分支，并让 `inputs.kaltsit.inputs.nixpkgs.follows = "nixpkgs"`；将 inputs 通过 `specialArgs` 传给系统模块。尚未发布的源码请使用本地 `path`，不要把公开 1.3.0 当成本轮代码。

```nix
{ inputs, ... }: {
  imports = [ inputs.kaltsit.nixosModules.default ];
  programs.kaltsit-sddm.enable = true;
  # SDDM 服务须由你的系统配置自行启用；主题模块不会启用它。
}
```

将 `kaltsit-sddm` 加入现有 `nixpkgs.config.allowUnfreePredicate` 白名单，保留其他包的规则。独立包包含已有角色壁纸，因此不是全自由素材包；[原有署名](../CREDITS.md)及许可叙述保持不变。模块使用系统的 `pkgs.callPackage`，要求 Qt 6 的 SDDM。当前锁定依赖已包含 QtQuick、Controls.Basic、Layouts，不需要新增 `extraPackages`。

模块导入、或仅把包加入 `environment.systemPackages`，都不会启用主题。只有选项为 true 时设置主题名和安装资源，仍不会启用 SDDM 服务。
主题默认值优先级为 900：覆盖 Plasma 的 `mkDefault "breeze"`（1000），用户显式 `services.displayManager.sddm.theme = "…"`（100）优先。已有显式主题时，须自行移除旧值或明确选择 `KaltsitMedicalGreen`；模块不会强行覆盖。

未来真机首次启用建议：保留已知可用的配置与上一代系统，先完成下面的 VM 验证，再在系统配置中加入上述选项，依次运行：

```sh
sudo nixos-rebuild build --flake /path/to/system#host
sudo nixos-rebuild boot --flake /path/to/system#host
# 在方便时重启，下次启动生效；首次不要用 switch。
```

这些是未来由操作者执行的说明。本轮只构建和运行测试 VM，没有部署主机配置，也没有运行主机 switch、boot、test 或重启登录服务。

## 关闭与恢复

将 `programs.kaltsit-sddm.enable = false`，恢复之前显式设置的主题（若有），再 build、boot，并在下次重启观察。若自行额外安装了主题包，可从原安装列表移除。关闭模块不自动改写用户其他 SDDM 设置。
界面无法使用时，从启动菜单选择上一代；或尝试 Ctrl+Alt+F3 登录 TTY，再执行 `sudo nixos-rebuild boot --rollback` 和 `sudo reboot`。命令来源、上一代保留要求及未验证的主机恢复边界见[设计中的恢复说明](SDDM-DESIGN.md#风险与恢复)。
SDDM 的内置回退只处理 QML 加载错误，不能保证显示服务器、插件或认证故障可恢复。本主题没有自动切换脚本。

## 可重复的隔离验证

先构建主题；用同一锁定 nixpkgs 的 `kdePackages.sddm` 和 `kdePackages.qtdeclarative` 提供测试工具。以下命令只用测试脚本创建的私有 HOME、XDG 目录、D-Bus 和 offscreen，不操作日常会话：

```sh
nix build --no-write-lock-file path:.#kaltsit-sddm
python3 tests/run-sddm-native.py "$(realpath result)" \
  --greeter /path/to/matching/sddm-greeter-qt6 \
  --qml /path/to/matching/qml --output /tmp/kaltsit-sddm-native-result
```

脚本先加载真实 greeter 的 `--test-mode --theme`，六秒后结束测试进程，再用假 SDDM 模型检查焦点、密码遮挡、失败清空、错误提示及电源能力。`ui-mock.png` 明确是假模型的原生 Qt 渲染，不能当真实登录截图或认证证明。

VM 配置在 [tests/sddm-vm.nix](../tests/sddm-vm.nix)，**仅用于测试，不得导入物理机器配置**。使用 2 核 / 2048 MiB、1280×800、静态壁纸与 X11 greeter；用一个 xterm 会话隔离验证 SDDM，不把它当 Plasma 桌面验收。测试账号 `tester`，公开的一次性密码 `wallpaper-test`。没有主机 HOME 共享、真实密钥或主机配置导入；Nix store 使用只含测试闭包的独立只读镜像，禁用默认共享目录及外网访问。

在新的临时目录创建测试 flake（替换源码路径）：

```nix
{
  inputs.theme = { type = "path"; path = "/absolute/path/to/kaltsit-medical-green"; };
  inputs.nixpkgs.follows = "theme/nixpkgs";
  outputs = { theme, nixpkgs, ... }: {
    nixosConfigurations.sddm-test = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [ (theme + "/tests/sddm-vm.nix") ];
    };
  };
}
```

然后仅在该临时目录执行：

```sh
nixos-rebuild build-vm --flake path:.#sddm-test
./result/bin/run-sddm-test-vm
```

先试错误密码，再用测试密码登录；xterm 中执行 `exit` 返回 greeter。关机和重启按钮只在 VM 中检查。
损坏主题回退测试必须在 VM 内：复制主题到 VM 的临时目录，故意写入无效 Main.qml，并通过 VM 的 SDDM 临时配置指向它，再重启 **VM 内** 的 display-manager。检查 `Fallback to embedded theme` 与可用登录控件后移除 VM 临时覆盖。不要对主机照做。

## 本轮实际验证

2026-11-01（America/Los_Angeles），运行资源来自 `4e9363d`，模块来自 `e50d903`，锁定 nixpkgs 与设计文档一致。

- 真实 SDDM 0.21.0 / Qt 6.11.2 greeter 在独立 HOME、D-Bus、offscreen 软件后端加载成功，没有触发内置回退；另在私有 KWin Wayland 中加载。假模型 UI 的 5 项检查通过，这部分不含认证。
- `nixos-rebuild build-vm --flake path:.#sddm-test` 成功。VM 为 NixOS 26.05、2 核 / 2048 MiB、1280×800、X11 greeter、xterm 会话；使用只读测试闭包镜像，不共享主机 HOME。控制连接仅转发至主机回环地址，使用一次性测试 SSH 密钥。
- 在 VM 中实际提交错误密码，观察错误提示、密码清空与焦点；再以测试密码通过 PAM 进入 xterm，退出后返回主题 greeter。用户与会话下拉框可打开，当前各只有一个条目；键盘布局显示 `us`。
- 仅损坏 VM 临时副本的 QML 后，日志出现 `DeliberatelyMissingTestType is not a type` 和 `Fallback to embedded theme`，并显示 SDDM 内置界面。未在内置回退界面再次完成密码认证，不将这个结果扩大为所有故障可登录。
- **电源流程未通过完整验证**：点击 VM 的重启、关机按钮均进入系统停止流程，随后停在 `Failed unmounting /nix/store` 附近；重启未取得新 boot ID，关机等待 90 秒仍未退出。结束了这两次测试 VM 进程，原因尚未定位，不把它记为按钮完成重启／关机，也不推断为实机表现。

[登录页](../previews/sddm/login.png)与[错误密码页](../previews/sddm/wrong-password.png)保留 QEMU 原始截图字节；[清单](../previews/manifest.json)逐项标记 VM 环境、来源提交和 SHA-256。没有修改旧截图，也没有生成概念图替代验收。
本轮没有启用主机 SDDM 主题、重启主机服务或执行主机系统部署。真机启用仍待后续决定，不能把以上 VM 登录结果视作完整实机验收。

## 验证清单（新环境结果留空）

| 项目 | 结果 | 环境 / 证据 |
|---|---|---|
| 主题加载，无隐式回退 | | |
| 用户选择、用户名与密码焦点 | | |
| 错误密码提示、密码清空 | | |
| 正确密码进入会话 | | |
| 退出会话返回 greeter | | |
| 会话选择、键盘布局显示 | | |
| VM 关机、重启按钮 | | |
| VM 损坏主题回退 | | |
| 实机首次启动与 TTY 恢复 | | |

## 已知限制

这是实验性 Qt 6 登录主题。真机、启动菜单回滚、TTY 恢复、多屏、特殊输入法和辅助认证尚未验证。系统需要可显示中文的字体；主题不在模块中修改用户的字体配置。
独立 Wayland test-mode 中键盘布局可能显示“未知”，不推断为物理键盘布局。实际认证由 SDDM/PAM 决定。主题没有指纹、智能卡、多因素提示的定制交互，不宣称覆盖这些环境。
