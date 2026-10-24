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
| 首次 shader 编译完成 | 未验证 |
| 主菜单、场景与画面正确性 | 未验证 |
| 离线 Metal cache | 缺少 metal 编译器，未执行 |

这些是本地工程观察，不构成跨平台兼容性声明。机器快照与原始日志不公开。构建、库加载和游戏验收分别记录；首次运行在 shader/菜单/场景验收前结束，不从空错误扫描推断成功。

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
