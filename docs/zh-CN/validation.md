# 验证

[English](../validation.md)

## 软件基线

Highball 0.10.22 / x64-crossover26.3-r28；MoltenVK-Detroit Release003 加本补丁；SPIRV-Cross 05583ac1537d777d304128142de2365bfa4a38df。完整版本与输入哈希见 [source-lock.json](../../source-lock.json)。

Release003 发行包注明 MoltenVK 工作树为 dirty，无法只凭 tag 精确重现该二进制。本项目构建的是单独标识的诊断变体。

## 检查记录

| 检查 | 结果与范围 |
|---|---|
| 完整库构建 | CMake 编译、链接通过，保留 SPIRV-Tools 和 cereal |
| 运行探针 | Rosetta 加载、配置回读、Vulkan instance 与设备枚举通过 |
| 独立安装器 | 安装、哈希检查与重复执行通过 |
| 游戏进程加载 | dyld/lsof 确认私有 EXE 和 dylib 路径，采样确认架构 |
| 首次 shader 编译越过原 98% 停止点 | 已在审查组合上实测通过，随后进入菜单及场景 |
| 主菜单 | 已进入，交互测试中菜单点击正常 |
| 游戏场景 | 已进入，最新普通游玩反馈正常；未记录所有场景覆盖 |
| 画面正确性 | 保留此前泛白记录；最新普通游玩反馈正常，未记录同场景受控对比 |
| 场景鼠标输入 | 保留此前交互记录；最新普通游玩反馈正常，未记录各类手势的专项覆盖 |
| 音频崩溃定位 | 转储、寄存器和反汇编确认 FAudio 查询混音格式失败后读取空指针；Wine 还忽略了声音对象创建失败 |
| 音频错误路径测试 | 旧故障已复现，修补后的设备查询及包装函数测试通过 |
| 已安装音频 DLL | x86_64 加载、声音输出对象创建及静音缓冲区处理通过 |
| 音频修补后的游戏 | 加入缓存后的最新普通游玩反馈正常 |
| 实际音频设备重连 | 尚未专项实测 |
| 长时间稳定性 | 未验收，修补前一次运行以访问违规结束 |
| 离线 Metal cache | 28,635 份全部构建并被 Metal 接受；复跑新增 0、跳过 28,635 |
| 独立编译器准备 | Apple 17A324 归档、哈希、签名、独立空目录安装、重复运行和归档回滚通过 |
| Highball 正常 Play | 界面及持久记录选中 Detroit Isolated，无需 command |

这些检查包括工程探针和明确标注的游玩反馈。最新反馈确认普通游玩正常，不再重复进行之前的长时间启动编译；但没有记录时长、所有场景/输入覆盖或实际音频设备重连。没有把错误扫描为空当作游戏成功。此前画面、输入和音频崩溃记录保留为历史，此流程不修改游戏 EXE 或关闭景深。

[复现审查](reproduction.md) 将每个实际组件对应到公开步骤。独立空目录中已真实验证 Apple 归档解包、签名、哈希与编译器安装；这不等于重置整台 Mac 或重新安装完整游戏。跨设备兼容性和长时间稳定性仍待验证。

[音频说明](../../audio/README.zh-CN.md) 单独记录源码故障注入测试与真实 DLL / 音频探针。原始日志、转储、截图、设备标识和机器记录均不公开。

## 回归测试

~~~bash
make static
make test
HIGHBALL_TEST_CLI="/path/to/highball" make test
~~~

测试需要 macOS clang/lipo，只使用临时合成 fixture，不启动 Wine 或游戏。未设置 HIGHBALL_TEST_CLI 时跳过可选 CLI 解码测试。本次含可选 CLI 检查共 35 项通过，覆盖哈希/架构/运行库拒绝、含空格路径、事务恢复、重复安装、缓存数学及位置不变性选项、失败时保留已有缓存和工具回滚。

## 最小 Metal 复现

~~~bash
mkdir -p build
xcrun clang -arch x86_64 -fobjc-arc -framework Foundation -framework Metal \
  src/metal_descriptor_repro.m -o build/metal-repro
./build/metal-repro
~~~

返回 0 表示复现了预期拒绝，不代表游戏已修复。
