# 《底特律：变人》Highball 诊断工具

## 音频输出切换 — v0.4.1-preview.1

新的音频候选修补支持播放中跟随系统默认输出、重建失效的 WASAPI 音频流，并在初始化失败时安全返回，保留 XAudio 声音对象和混音格式。只安装到 Detroit 独立引擎和环境。

设备切换与端点模拟测试、真实 DLL 加载、静音缓冲消耗和安装事务测试通过。**真实 AirPods 切换及修改后的游戏运行仍待验证；不宣称已修复最新退出和顶点输入缺失。剧情局部模糊尚未确认原因。**

已有独立安装请参阅[音频切换说明](audio/routing/README.zh-CN.md)。保留现有 Metal 缓存。


[English](README.md)

用于适配和调查《底特律：变人》（Detroit: Become Human）在 [Highball](https://github.com/gauthierpiarrette/highball) 上的 MoltenVK 问题，并创建独立测试环境。

**实测进展：在已审查的 Highball 引擎上，游戏已通过首次着色器编译原先卡住的 98% 阶段，进入主菜单及游戏场景。**

原启动故障包含以下 Metal 顶点输入错误：

~~~text
Vertex attribute in_vfMsBindPosePosition(12) is missing from the vertex descriptor.
~~~

**状态：预发布。加入音频修复和持久 Metal 缓存后的最新运行反馈为正常游玩，不再每次启动都进行长时间编译。长时间稳定性、所有场景正确性和音频设备重连仍未完成专项验收。**

## 补丁范围

补丁基于 MoltenVK-Detroit Release003，固定 SPIRV-Cross 依赖，并在流水线创建失败时记录 vertex-input 与 specialization 数据。缺失输入时返回错误，而不是分配默认格式和 buffer binding。这保留了失败流水线的诊断证据；能够进入场景，不表示所有顶点输入不匹配都已修复。

新增 [XAudio2 音频修复](audio/README.zh-CN.md)，处理音频设备查询失败并正确传递声音对象创建错误，修补已定位的音频访问违规路径，不编造设备格式或为无效对象返回成功。

## 从这里开始

**已经安装过？** 打开 Highball → **Detroit: Become Human** → **Game settings**，在 **Detroit Isolated** 旁点击一次 **Play there**。Highball 会记住选择，以后直接使用主页面的 **Play**。补装新音频修复时，按 [音频升级说明](audio/README.zh-CN.md) 操作。

**第一次安装？** 按 [一步一步的安装教程](docs/zh-CN/usage.md) 操作。里面提供下载命令，说明怎样找到环境名称和游戏文件夹，以及如何预检、安装、启动和恢复。使用下载包无需编译 MoltenVK 或安装完整 Xcode。

已审查组合为 Highball 0.10.22、x64-crossover26.3-r28 引擎及 Steam Windows 版游戏。安装会复制原环境、引擎和游戏，需为三者及至少 12 GiB 余量准备空间，通常超过 75 GiB。原游戏和共享引擎保留，回滚将测试环境的存档留在归档中。

[v0.4.1-preview.1 Release](https://github.com/jason312928/highball-detroit-adapter/releases/tag/v0.4.1-preview.1) 提供完整安装包和较小的音频升级包，日常游玩的稳定性尚未验收。自己编译源码属于可选步骤，单独见 [构建说明](docs/zh-CN/build.md)。

## 验证

首次编译已越过 98%，并进入菜单和场景。持久缓存构建生成 28,635 份 Metal 二进制，全部加载通过；复跑新增 0 份。后续普通游玩反馈正常，不再反复长时间编译。文件探针、编译器复用与游玩反馈分别记录，详见 [验证记录](docs/zh-CN/validation.md) 和 [复现审查](docs/zh-CN/reproduction.md)。

正常入口为 **Highball → Detroit: Become Human → Play**，使用记住的 `Detroit Isolated` 环境。首次设置需先完成游戏自己的编译，再生成离线 Metal 缓存；漏掉后一步仍可能每次慢启动。不要求 `.command`、修改游戏 EXE 或关闭景深。

完整包包含 `prepare-metal.sh`，从 Apple 获取并验证固定版本的独立编译器，不需要完整 Xcode。本项目不分发 Apple 工具、Microsoft DLL 或游戏着色器。

## 开发

~~~bash
make static
make test
~~~

测试仅使用临时 fixture，不启动 Wine 或游戏。设置 HIGHBALL_TEST_CLI 可额外用已有 Highball CLI 验证配置解码。

本地引擎指纹只保存在被忽略的 engine-lock.local.json 中。机器记录、游戏文件、shader dump 与运行日志不入库。

- [patches/](patches)：补丁系列与上游差异。
- [scripts/](scripts)：安装事务与诊断工具。
- [src/](src)：ABI 探针和最小复现。
- [tests/](tests)：安装器回归测试。
- [source-lock.json](source-lock.json)：源码版本和输入哈希。

## 许可

新增脚本、测试与文档采用 [MIT](LICENSE)。上游代码保留各自许可，见 [第三方说明](THIRD_PARTY_NOTICES.md)。
