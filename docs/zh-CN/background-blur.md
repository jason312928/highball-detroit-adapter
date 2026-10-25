# 可选的背景模糊绕过方案

[English](../background-blur.md)

这会修改游戏 EXE，需用户明确选择，不属于自动安装步骤，也不是正常启动的前提。画面效果仍待实测，不能宣称解决卡顿或顶点输入错误。

[上游说明](https://github.com/DiAvisoo/MoltenVK-Detroit/blob/8b511fdc5351a37c305bc246e161796ddca56b18/README.md) 除了设置 `DEPTH_OF_FIELD: 0`，还建议单独修改一个字节来关闭有问题的背景模糊。它可能同时去掉正常剧情模糊，具体内部参数尚未独立确认。另有[实验性 RenoDX 插件](https://github.com/decoded-brain/game-graphical-mods/blob/main/mods/detroit-become-human/README.md)，但需要额外安装 ReShade Full Add-On，其文档未证明本套 Highball／MoltenVK 环境兼容，目前不足以认定更可靠。

## 使用当前源码中的工具

v0.4.1-preview.1 发布包不包含这项工具，旧版校验脚本会拒绝修改后的 EXE。请使用当前源码中的配套脚本。仓库不提供游戏文件、备份或个人着色器。

先退出 Detroit，操作期间不要启动游戏或运行 Steam 更新／验证文件。仅修改 EXE 不需要重新启动 Steam 或 Highball。

```bash
# 预览，不修改文件：
python3 -B scripts/blur_workaround.py apply
# 明确选择后，备份并应用：
python3 -B scripts/blur_workaround.py apply --apply
python3 -B scripts/blur_workaround.py verify
./verify.sh
# 预览恢复，然后恢复完整原版 EXE：
python3 -B scripts/blur_workaround.py rollback
python3 -B scripts/blur_workaround.py rollback --apply
```

工具只支持已核对的一个 Steam EXE 版本，完整 SHA-256、唯一字节模式和固定位置须全部匹配，否则拒绝操作。只修改适配器拥有的独立 Detroit 环境，先独立复制完整 EXE，再原子替换；不会改共享环境或源游戏。完整备份保存在 Highball 私有适配器状态目录的 `blur-workaround/original.exe`。原始安装记录哈希保持不变，校验只额外接受有完好备份支持的这一种已知补丁哈希。准备途中失败可重试。

文件偏移 `0x34e760` 的 `41` 改为 `7F`，反汇编显示其把浮点常量 16.0 改为正无穷。Steam 更新或验证完整性可能覆盖修改；若 EXE 已更新为其他版本，工具会拒绝回滚覆盖。

九项合成文件事务测试覆盖预览、应用／验证／重复／回滚、损坏备份、未知或变化版本、游戏运行中拒绝、无记录补丁、中途发布失败和符号链接拒绝。这不能替代游戏画面实测。
