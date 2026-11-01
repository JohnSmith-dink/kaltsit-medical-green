# 升级、恢复与卸载

v1.3 新增独立[动态壁纸](MOTION.md)。执行基础主题 restore/升级或移除扩展前，先在桌面设置恢复原图像壁纸；`kaltsit-theme restore` 不管理扩展选择。仅安装扩展无需重新应用基础主题。

[English](UPGRADE-RECOVERY.en.md) · [返回 README](../README.md)

## 升级顺序

1. 在当前 KDE 会话运行 `kaltsit-theme status`，记录已应用版本和组件。
2. 用当前安装的工具运行 `kaltsit-theme restore`。出现 `restore-incomplete` 时，先处理输出列出的冲突，再次恢复；不要删除备份来绕过检查。
3. 更新包来源并构建、安装。Home Manager 用户更新配置中的来源，然后执行自己的正常重建命令；不要再额外用 `nix profile` 安装另一份。
4. 先运行 `kaltsit-theme apply --dry-run`，再用需要的 `--skip` / `--wallpaper` 选项执行 `apply`，最后检查 `status`。

首次使用不需要 restore。相同版本、相同选项重复 apply 会保留最初备份；改变选项、自选壁纸或升级版本前必须先恢复。
v1.2 的验收开发包曾使用 `1.1.0` 版本号，正式构建为 `1.2.0`。`upgrade_available` 只比较版本字符串，不检测源码提交；从 v1.1 或 D1 开发包升级均须先用当前工具 restore，再安装并 apply 新版本。

## Plasma 升级与版本诊断

主题的完整 Plasma shell 资源层必须使用**系统同一套 `pkgs`** 构建。Home Manager 模块默认这样做；独立 flake 锁定的 KDE 版本可能与系统不同。
升级 Plasma 时同时重建主题，并注销、重新登录，使正在运行的会话跟上新包。

`status` 的 `lockscreen_resources` 包含：

| 字段 | 含义 |
|---|---|
| `built_for.plasma_desktop` / `plasma_workspace` | 构建时由 Nix 传入的版本，来自已安装包的 `lockscreen-rendering.json`。 |
| `running.version` | 当前会话总线中已运行的 Plasma 进程对应 Nix store 包版本。只读查询 PID 和 `/proc`，不启动另一个 plasmashell。 |
| `match` | 两个构建版本均与运行版本一致时为 `true`，不一致为 `false`；缺失元数据、没有会话、工具不可用或进程来源无法识别时为 `"unknown"`。 |

`true` 只表示版本号相同，不保证不同构建、补丁或多屏环境均兼容。`false` 附带重建提示，不自动修改设置，也不阻止命令。
离线 status 仍可读取原有配置与恢复记录。旧包缺少新元数据时显示 unknown，不猜测版本。

## 普通恢复与冲突

```sh
kaltsit-theme restore
kaltsit-theme status
```

恢复只涉及本次实际应用的组件。切换后新增的无关设置会保留；同一个主题键被用户改过时，会保留新值并报告冲突。
依照输出，将冲突键改回本次主题应用值后再次 restore。若希望保留个人新值，先单独记下它，完成恢复后再通过系统设置重新设置；保留冲突值直接重试仍会报告冲突。不要直接覆盖整份配置或编辑 active.json。
未再修改的配置尽量按原始字节恢复；有后续改动时按键恢复。GTK 只恢复归本主题负责的键，保留后台导出的字体等设置。
格式 1、2、3 的旧记录仍可读取。降级前用当前工具完成恢复；旧版工具会拒绝不认识的记录。

恢复记录：`${XDG_STATE_HOME:-$HOME/.local/state}/kaltsit-theme/active.json`。
其中包含个人配置内容，旁边可能还有指针目录备份；不要公开上传，也不要在恢复前删除。
旧指针目录或链接会原样还原。若旧 Nix 资源已被垃圾回收，恢复配置不会重新下载那些资源。

## 图形界面不可操作时

可在 TTY（通常为 Ctrl+Alt+F2）以**同一用户**登录，连接仍在运行的用户会话总线后恢复：

```sh
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
kaltsit-theme status
kaltsit-theme restore
```

这是恢复路径说明，尚未作为本轮真实锁屏故障演练验收。不要使用 sudo 执行主题切换。
若平时设置了自定义 `XDG_CONFIG_HOME`、`XDG_DATA_HOME` 或 `XDG_STATE_HOME`，TTY 中也要使用相同值。
若 Plasma 或会话总线已退出，restore 可能无法完成实时刷新；保留错误信息和备份，先恢复可用会话再重试。
如果问题来自 NixOS 系统或 Plasma 包升级，可在启动菜单选择上一代系统；这不会自动撤销用户配置，回到可用会话后仍需按实际状态恢复。

## 卸载

先 restore 成功，再移除资源。Home Manager 用户关闭 `programs.kaltsit-theme.enable`，移除相关 Ghostty 声明后正常重建。
用 profile 安装的用户先运行 `nix profile list` 确认对应条目，再运行 `nix profile remove <条目名称>`。
不要删除其他同名来源或整个 profile。卸载不应靠删除恢复记录完成。
