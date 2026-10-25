# 游戏运行中切换音频输出

[English](README.md)

此候选版本更新 Detroit 独立引擎和环境中的 `xaudio2_8.dll` 与 `mmdevapi.dll`。音频工作线程每 500 毫秒检查默认输出；切换时以原有混音格式创建共享模式 WASAPI 流，通过自动转换适配输出，不重建游戏的声音对象。重建失败时保留仍可用的旧流；失效的流会释放并重试。没有输出设备时仍能正常退出。

安装器只在 Detroit Isolated 中启用 `HB_DETROIT_AUDIO_FOLLOW_DEFAULT=1`。已有 Wine 注册表输出偏好仍受尊重。AirPods 必须已连接并成为 macOS 输出，本补丁不代替系统配对或强制选择耳机。

## 已有独立安装

先关闭游戏和 Detroit Isolated 中的 Steam，在适配包目录执行：

```bash
./audio/install-routing.sh --dry-run
./audio/install-routing.sh --apply
./audio/verify-routing.sh
```

之后正常从 Highball 点 Play。如果独立 Steam 在安装前已运行，需要退出后重开，以继承新设置。这次音频更新不要求删除或重编着色器缓存。

```bash
./audio/rollback-routing.sh --dry-run
./audio/rollback-routing.sh --apply
```

回滚校验并恢复此前的四个 DLL 和音频设置值，保留其他设置。若还要卸载旧版 v1 音频修补，先回滚此版本。中断的安装可在下次 `--apply` 时恢复；检测到用户另行修改时会拒绝覆盖。

## 验证范围

8 个音频流模拟场景覆盖默认输出变化、固定输出、切换失败重试、设备失效、暂时没有设备和初始化失败。端点测试覆盖对象保持、失败、设备缺席、缓冲扩容和并发复用。真实 DLL 的内存映像时间戳与构建产物一致，真实静音缓冲已被消耗。安装器测试覆盖部分写入失败恢复、回滚、设置保留及路径篡改。

真实 AirPods 重连、物理设备采样率与声道变化、游戏内稳定性仍待验证。没有证据证明最新的退出码 1 由音频引起。Vulkan 顶点属性缺失与剧情局部模糊仍未解决；此更新没有补造属性或修改游戏 EXE。
