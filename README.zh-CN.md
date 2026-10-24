# 《底特律：变人》Highball 诊断工具

[English](README.md)

用于调查《底特律：变人》（Detroit: Become Human）在 [Highball](https://github.com/gauthierpiarrette/highball) 上的 MoltenVK 问题，并创建独立测试环境。

目前调查的故障发生在游戏首次编译着色器时：进度停在 98%，Metal 报告流水线的顶点输入描述缺失。

~~~text
Vertex attribute in_vfMsBindPosePosition(12) is missing from the vertex descriptor.
~~~

**状态：诊断预发布版。首次着色器编译完成、主菜单和场景渲染均未验收。**

## 补丁范围

补丁基于 MoltenVK-Detroit Release003，固定 SPIRV-Cross 依赖，并在流水线创建失败时记录 vertex-input 与 specialization 数据。缺失输入时返回错误，而不是分配默认格式和 buffer binding。这保留了原始故障，尚未实现未绑定属性的语义修复。

## 从这里开始

**已经安装过？** 打开 Highball → **Detroit Isolated** → **Detroit (isolated Steam)**。不用重新编译或安装。

**第一次安装？** 按 [一步一步的安装教程](docs/zh-CN/usage.md) 操作。里面提供下载命令，说明怎样找到环境名称和游戏文件夹，以及如何预检、安装、启动和恢复。使用下载包无需编译 MoltenVK 或安装完整 Xcode。

已审查组合为 Highball 0.10.22、x64-crossover26.3-r28 引擎及 Steam Windows 版游戏。安装会复制原环境、引擎和游戏，需为三者及至少 5 GiB 余量准备空间，通常超过 64 GiB。原游戏和共享引擎保留，回滚将测试环境的存档留在归档中。

下载内容是**诊断预发布版**，尚未验证能修复游戏运行。自己编译源码属于可选步骤，单独见 [构建说明](docs/zh-CN/build.md)。

## 验证

已验证完整库构建、Rosetta/Vulkan 探针、独立安装和真实游戏进程加载路径。游戏验收仍未完成，证据边界及待办见 [验证记录](docs/zh-CN/validation.md) 与 [顶点输入分析](docs/zh-CN/vertex-input.md)。

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
