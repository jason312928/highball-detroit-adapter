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
| 游戏场景 | 已进入；完整交互和场景正确性尚未验收 |
| 画面正确性 | 出现高光泛白，已准备 SDR 对比，结果待验证 |
| 场景鼠标输入 | 出现交互问题，已提供手势操作说明，是否解决仍待确认 |
| 音频崩溃定位 | 转储、寄存器和反汇编确认 FAudio 查询混音格式失败后读取空指针；Wine 还忽略了声音对象创建失败 |
| 音频错误路径测试 | 旧故障已复现，修补后的设备查询及包装函数测试通过 |
| 已安装音频 DLL | x86_64 加载、声音输出对象创建及静音缓冲区处理通过 |
| 音频修补后的游戏 / 设备重连 | 尚未实测 |
| 长时间稳定性 | 未验收，修补前一次运行以访问违规结束 |
| 离线 Metal cache | 缺少 metal 编译器，未执行 |

这些是本地工程观察，不构成跨平台兼容性声明。机器快照与原始日志不公开。构建、库加载和游戏验收分别记录；后续交互运行已证明能越过 98%、进入菜单及场景，同时暴露了画面、输入及音频访问违规问题。这次启动进展发生在音频修补之前，不表示修补后的游戏或长时间稳定性已验收，也不从空错误扫描推断成功。

[音频说明](../../audio/README.zh-CN.md) 单独记录源码故障注入测试与真实 DLL / 音频探针。原始日志、转储、截图、设备标识和机器记录均不公开。

## 回归测试

~~~bash
make static
make test
HIGHBALL_TEST_CLI="/path/to/highball" make test
~~~

测试需要 macOS clang/lipo，只使用临时合成 fixture，不启动 Wine 或游戏。未设置 HIGHBALL_TEST_CLI 时跳过可选 CLI 解码测试。覆盖哈希/架构拒绝、含空格路径、事务恢复、重复安装和回滚。

## 最小 Metal 复现

~~~bash
mkdir -p build
xcrun clang -arch x86_64 -fobjc-arc -framework Foundation -framework Metal \
  src/metal_descriptor_repro.m -o build/metal-repro
./build/metal-repro
~~~

返回 0 表示复现了预期拒绝，不代表游戏已修复。
