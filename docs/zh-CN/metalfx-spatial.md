# Detroit MetalFX 空间超分实验版

[English](../metalfx-spatial.md)

这是一项单独编译的独立引擎功能，不包含在 v0.4.1 发布包中。它会降低呈现图像分辨率，再通过 MetalFX 放大到显示尺寸。默认宽高比例为 75%，约相当于原生 56% 的输出像素数，尺寸会取偶数；这不保证全部内部渲染步骤都同比减少，也不能换算为确定的 FPS 增益。不是时域超分或插帧，游戏 UI 也会一起放大，实际画质、输入和帧数待测。

只修改适配器拥有的独立 Detroit 引擎，先完整备份 MoltenVK；不修改 EXE、音频、存档、共享引擎或着色器缓存。不会伪造 Vulkan 功能或顶点映射，尺寸／格式／初始化／分配失败会报错。已验证的游戏输出格式为 BGRA8Unorm。

编译要求 macOS 13+、支持 MetalFX 的设备及当前 SDK。先按普通 CMake 构建流程构建严格接口版本，再在该源码上应用 `patches/0002-detroit-metalfx-spatial.patch`，用 `-DMVK_DETROIT_METALFX_DEFAULT=ON` 重新配置并构建 MoltenVK。源码默认 OFF，需明确选择构建开启版。先用 `src/metalfx_swapchain_probe.m` 检验候选库，完整命令参数和依赖见英文页。

```bash
# 预览与安装，先退出游戏：
python3 -B scripts/metalfx_engine.py install --library /绝对路径/libMoltenVK.dylib
python3 -B scripts/metalfx_engine.py install --library /绝对路径/libMoltenVK.dylib --apply
python3 -B scripts/metalfx_engine.py verify
./verify.sh
# 预览与恢复完整原引擎库：
python3 -B scripts/metalfx_engine.py rollback
python3 -B scripts/metalfx_engine.py rollback --apply
```

备份在私有适配器状态目录 `metalfx-spatial-v1/original.dylib`。校验要求所有权、安装后精确哈希及原始备份全部匹配；保留原始安装记录。工具不会启动或关闭游戏。若要安装另一候选库，先恢复原库。

新进程可用 `MVK_DTR_METALFX_SPATIAL=0` 关闭；`MVK_DTR_METALFX_SCALE` 可设置 0.5 至小于 1 的比例，默认 0.75。须留意 Highball／Steam 的环境变量继承，完整恢复原库可以避免继承问题。不要清缓存。

离屏验证已通过：x86_64／Rosetta 路径、Metal API Validation、两组尺寸与交换链重建；开启／关闭各提交 24 帧，并回读实际 drawable 像素检查。八项安装事务测试验证预览、重复、恢复、损坏备份、运行中拒绝和中途失败。没有启动游戏。

下次手动启动后，只有看到 `[detroit-metalfx] ... enabled spatial input=... output=...` 和 `encoded frame=...`，才能确认游戏进程实际使用 MetalFX。应对比相同场景的帧数、GPU 时间、字幕、菜单、鼠标、全屏、切换应用及剧情转场。原有顶点映射错误和编译卡顿仍需单独处理。
