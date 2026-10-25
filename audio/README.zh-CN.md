# Detroit: Become Human — 音频修补

[English](README.md)

v0.4 候选版本将原有音频查询/声音对象创建失败保护，与运行中跟随默认输出合并。它更新 **Detroit Isolated** 独立引擎及环境中的 `xaudio2_8.dll`、`mmdevapi.dll`，并启用该环境专用的默认输出设置。切换或恢复音频流时保留游戏的声音对象。

## 安装

已有独立环境可从 [v0.4.0-preview.1 Release](https://github.com/jason312928/highball-detroit-adapter/releases/tag/v0.4.0-preview.1) 下载音频升级包和 SHA256SUMS，按[英文说明](README.md#use)校验并解压；完整包也包含此 audio 目录。Git 源码不包含编译好的 DLL。

关闭游戏及独立 Steam，在音频包目录执行：

```bash
./install.sh --dry-run
./install.sh --apply
./verify.sh
```

支持含空格路径和自定义 `--highball-root`。脚本默认 dry-run，核对 x86_64 DLL 校验值，备份此前的四个文件和路由设置，失败恢复并拒绝覆盖冲突改动。日志保存在 logs 目录。标准 install/verify/rollback 脚本现在操作 v2，与显式的 install-routing/verify-routing/rollback-routing 脚本相同。

之后从 Highball 正常点 Play。AirPods 须已连接并成为 macOS 输出；补丁不替用户强制选择系统输出。原 Metal 缓存保留。

## 回滚

关闭游戏及独立 Steam 后执行：

```bash
./rollback.sh --dry-run
./rollback.sh --apply
```

备份保存在 `.detroit-adapter/audio-routing-v2/`。回滚恢复升级前状态；若升级前装有 v1，仍会保留 v1。若还要卸载 v1，再执行 `python3 audiofix.py rollback --apply`。卸载整个独立适配环境前先回滚音频。

## 验证范围

8 个路由模拟场景及端点对象保持/失败/缺席/扩容/并发测试通过，真实加载的 PE 映像与构建一致，静音缓冲正常消耗。Python 测试共 43 项，42 项通过，未配置的可选 CLI 检查跳过。5 个补丁可从锁定源码包准确重建修改文件。

真实 AirPods 切换、物理采样率与声道变化，以及更新后游戏运行仍待验证。不宣称已修复最新退出、缺失的 Vulkan 顶点输入或剧情局部模糊。详见[路由说明](routing/README.zh-CN.md)、[构建说明](BUILD.zh-CN.md)、[来源锁](source-lock.json)。

保留 Wine/FAudio 原许可证，提供完整对应源码；不发布游戏文件、着色器、原始日志、存档、设备身份或个人配置。
