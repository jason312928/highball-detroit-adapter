# 顶点输入错误

[English](../vertex-input.md)

## 转换路径

SPIR-V 的 Location 经 SPIRV-Cross 转为 MSL attribute location。MoltenVK 根据 Vulkan 的 location、binding、format 和 offset 填充 MTLVertexDescriptor。location 12 不等于 buffer binding 12；仅凭 shader 无法推导缺失的绑定、格式或偏移。

Metal 错误能证明 shader 要求的输入没有出现在最终描述符中，但尚不能证明哪一层引入了不匹配。

## 证据与边界

原始故障同时包含 location 12 和 3。src/metal_descriptor_repro.m 的最小复现可触发同类拒绝。另一个缓存顶点模块已由固定 SPIRV-Cross fork 反射并转换，确认 location 12 存在且被读取，该模块没有 specialization constants。

缓存模块尚未关联到具体失败 pipeline。应用状态、缓存组合与转换/接口裁剪仍是可能原因。仓库不分发游戏 shader。

## 诊断补丁

Release003 对部分缺失输入补入 UChar4、已有 buffer 与 offset 0，还会调整不匹配的跨 stage 输出。这些值并非从缺失的 Vulkan 输入描述中推导。

诊断变体移除这些 fallback。失败时记录 entry point、binding/stride/rate、location/binding/format/offset、vertex-input pNext 类型和 specialization 字节。标记为 HB_DETROIT_STRICT_INTERFACE_V1，可通过 MVK_CONFIG_SHADER_DUMP_DIR 启用已有 SPIR-V/MSL dump。

下一步需要捕获同一失败 pipeline 的模块、entry point、specialization 值、完整 vertex-input state 与相关动态状态。语义修复应以这些数据为依据。

相关讨论：[MoltenVK #2054](https://github.com/KhronosGroup/MoltenVK/issues/2054)。

## 后续运行证据

实际严格诊断记录到 shader 使用 location 12，但某个提交的顶点布局只有 location 10、11、3、8，均使用 binding 0，stride 为 32。游戏能够进入菜单和场景时，仍可能同时存在这些流水线错误；启动进展不能证明所有受影响绘制都正确。
