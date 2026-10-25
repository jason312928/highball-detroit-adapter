# 《底特律：变人》XAudio2 音频设备查询修复

[English](README.md)

此候选修复处理 Highball / CrossOver 26.3 音频实现中的两处错误处理缺陷，仅用于已建立的 **Detroit Isolated** 环境及 **detroit-strict-003-r28** 独立引擎。

## 修复内容

1. FAudio 查询设备混音格式失败后，原代码只靠断言检查；发布版移除断言后会继续读取空指针。现改为检查错误、释放已取得的资源并返回失败。成功路径仍使用设备真实的声道数和采样率，不编造格式。
2. Wine 的 XAudio 包装层忽略底层声音对象创建失败，仍返回成功。现改为返回失败、清理效果链、保持输出指针为空，避免游戏取得无效声音对象。

第一处参考 [FAudio 上游修复](https://github.com/FNA-XNA/FAudio/commit/67ed0a1eac0c52cc51e2bb892ccdb741d01bdec3)，并补齐引用释放；第二处修复 Wine 的错误传递。独立补丁在 `patches/`，源码与工具链固定版本见 `source-lock.json`。

## 现在怎样启动

完整 Release 包已将此目录放在 `audio/` 下。若已经安装独立环境，只需在 [Release](https://github.com/jason312928/highball-detroit-adapter/releases/tag/v0.3.0-preview.1) 下载 `highball-detroit-audiofix-v0.3.0-preview.1-macos-x86_64.tar.gz` 和 `SHA256SUMS`，核对清单中对应的 SHA-256 后解压。在终端进入解压后的 `highball-detroit-audiofix-v0.3.0-preview.1` 文件夹。包内带有 DLL，Git 源码目录不含二进制。

只下载音频升级包时，可直接复制以下整块命令到终端。若已经解压过此版本，命令会停止，直接使用已有目录即可。

```bash
(
  set -e
  mkdir -p "$HOME/Downloads/highball-detroit-setup"
  cd "$HOME/Downloads/highball-detroit-setup"
  test ! -e highball-detroit-audiofix-v0.3.0-preview.1
  RELEASE="https://github.com/jason312928/highball-detroit-adapter/releases/download/v0.3.0-preview.1"
  ASSET="highball-detroit-audiofix-v0.3.0-preview.1-macos-x86_64.tar.gz"
  curl --fail --location --output "$ASSET" "$RELEASE/$ASSET"
  curl --fail --location --output SHA256SUMS "$RELEASE/SHA256SUMS"
  awk -v asset="$ASSET" '$2 == asset { print; found=1 } END { if (!found) exit 1 }' \
    SHA256SUMS > selected.sha256
  shasum -a 256 -c selected.sha256
  tar -xzf "$ASSET"
  cd highball-detroit-audiofix-v0.3.0-preview.1
  shasum -a 256 -c SHA256SUMS
)
```

然后进入音频目录；使用完整包时则进入其中的 `audio/`：

```bash
cd "$HOME/Downloads/highball-detroit-setup/highball-detroit-audiofix-v0.3.0-preview.1"
```

在相同引擎基线上另行安装时，先退出游戏和独立环境的 Windows Steam / Wine 程序，再执行：

```bash
./install.sh --dry-run &&
./install.sh --apply &&
./verify.sh
```

支持含空格路径。自定义 Highball 数据位置需给各命令传入相同的 `--highball-root "/实际数据目录"`。安装器校验独立环境所有权、SHA-256 和 PE 架构，备份原库；普通异常自动恢复，中断后下次 `--apply` 恢复；遇到被另行修改的库会停止。日志只保留在本地 `logs/`。

只替换独立引擎与独立 Bottle 的两份 `xaudio2_8.dll`。共享引擎、原 Games 环境、EXE、存档、系统音频路由和设备权限不改动。HDR 对比属于单独的图形排查，本音频补丁不改图形配置。

安装后使用 Highball 正常的 **Detroit: Become Human** 页面；必要时在 **Game settings** 里点击 `Detroit Isolated` 旁的 **Play there**，以后主 **Play** 按钮会记住环境。还需按 [完整教程](../docs/zh-CN/usage.md) 生成持久 Metal 缓存。音频修复和缓存准备后的普通游玩反馈正常，设备重连及长时间压力测试仍未验收。

## 恢复原音频库

先退出游戏及独立环境的 Windows Steam / Wine 程序，然后执行：

```bash
./rollback.sh --dry-run &&
./rollback.sh --apply
```

备份位于 Highball 数据目录的 `.detroit-adapter/audio-v1/`。如果准备卸载整个独立测试环境，应先回滚本音频补丁，再运行原适配器的回滚。回滚后该环境使用原来的音频实现。

## 已验证与未验证

- 旧格式查询函数复现空指针访问违规；修补后正常查询、六个 API 失败、成功却返回空格式、非法索引均通过，资源释放平衡。
- 旧声音对象包装函数复现“底层失败却返回成功”；修补后失败、成功及重复创建三种情况通过。
- 安装器通过含空格路径、重复操作、写入失败自动恢复、中断恢复及冲突保护检查。
- 新 DLL 为 x86_64 PE，导出名称与序号匹配原库。已在当前 Wine 中加载，并通过声音对象创建及静音缓冲区处理测试。
- **修补后真实游戏场景、物理耳机重新连接、长时间游玩仍未验收。**

底层格式查询当时返回 `E_FAIL`，其瞬时触发条件尚未复现。补丁处理这一失败，不保证游戏在收到音频初始化错误后一定能恢复声音或继续运行，也没有解决独立的 MoltenVK 顶点输入问题。不能把本次构建和音频测试通过等同于日常游戏稳定。

完整运行日志和崩溃转储只留在本机，不能随此代码包上传。新增脚本采用 MIT；Wine 和 FAudio 改动保留各自原许可，见 `licenses/`。重建方法见 [构建说明](BUILD.zh-CN.md)。
