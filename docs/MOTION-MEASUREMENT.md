# 动态壁纸测量方法

此页提供可重复的方法和空白记录表，不给出功耗结论。软件播放检查不能证明硬件解码、长期功耗或多屏表现。

## 控制条件

记录机器型号、内核、显卡与驱动、Plasma/Qt 版本、屏幕数量、分辨率、缩放、刷新率、亮度、电源模式、电池电量区间、视频哈希/分辨率/帧率/编码。关闭无关任务，让温度稳定。
每个状态先稳定 2 分钟，再按相同间隔采样至少 5 分钟，重复三轮并交换顺序。记录平均值、范围和异常；不要比较不同亮度或不同后台负载的样本。

分别由操作者选择：静态图像壁纸、动态播放、同一动态壁纸的右键手动暂停。窗口可见状态、鼠标活动和其他负载保持一致。
电池供电下测动态播放时，临时将 `BatteryPolicy` 设为 `ignore`（“照常播放”），结束后恢复原值；否则默认自动暂停使样本名称失真。手动暂停保留当前视频帧，不能当成卸载播放器。

## 采样

- 整机：优先用相同外接功率计，或在电池放电时读取实际电池的 `/sys/class/power_supply/BAT*/power_now`（通常为 µW，除以 1000000 得 W）。若仅有 `current_now` 与 `voltage_now`，按 µA × µV / 10^12 换算 W，先核对驱动提供的单位和放电状态。不要把充电电流或某一设备功率当整机输入。也可使用 powertop 的整机估计，但记录其数据来源，不把设备估算相加当精确整机功耗；不使用 `--auto-tune` 改变测试条件。
- CPU：找出壁纸所在的 `plasmashell` PID，使用 `pidstat -p <PID> 1 300`（sysstat）或同等工具。另记录总 CPU 占用；写清 100% 是单核还是整机。视频在 Plasma 进程内运行时，该 PID 也包含其他组件开销。
- GPU：按实际硬件选择工具，例如 Intel 的 `intel_gpu_top`；分别记录渲染与视频解码引擎占用。AMD/NVIDIA 使用对应驱动工具，注明支持程度和采样频率；未知值留空。GPU 占用不是 GPU 功率，进程占用也不是整机功率。

混合显卡 NVIDIA 笔记本先用 `lspci -D` 确认独显 PCI 地址，再被动读状态（替换示例地址）：

```sh
cat /sys/bus/pci/devices/0000:01:00.0/power/runtime_status
cat /sys/bus/pci/devices/0000:01:00.0/power/runtime_active_time
cat /sys/bus/pci/devices/0000:01:00.0/power/runtime_suspended_time
```

在三种状态的固定采样点记录 `active` / `suspended` 及计数变化，保持外接显示器和其他 GPU 应用一致。runtime PM 状态不是精确功率读数。
然后**单独一轮**执行 `nvidia-smi --query-gpu=pci.bus_id,pstate,utilization.gpu,power.draw --format=csv`，比较查询前后状态。查询工具可能干扰设备休眠，不能把查询后的唤醒直接归因于壁纸；未提供的字段留空。没有 NVIDIA 时跳过本项，不替换本机硬件事实。

## 结果表（由操作者填写）

| 状态 | 整机平均 W / 范围 | Plasma CPU % | 总 CPU % | GPU 渲染 % | GPU 解码 % | 独显 runtime 状态 | 温度 / 备注 |
|---|---|---|---|---|---|---|---|
| 静态壁纸 | | | | | | | |
| 动态播放 | | | | | | | |
| 手动暂停 | | | | | | | |

来源：[Linux runtime PM](https://docs.kernel.org/power/runtime_pm.html)、[电源属性单位](https://docs.kernel.org/power/power_supply_class.html)、[NVIDIA SMI](https://docs.nvidia.com/deploy/nvidia-smi/index.html)。
