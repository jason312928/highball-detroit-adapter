# 安装、启动与恢复

[English](../usage.md)

本教程使用下载好的运行库，**不用自己编译 MoltenVK，也不用安装完整 Xcode**。

**实测：首次着色器编译已越过原来的 98% 停止点。加入音频修复和离线 Metal 缓存后的运行反馈为正常游玩，不再反复进行长时间着色器编译。长时间稳定性和音频设备重连仍待专项验证。**

## 已经安装过？

使用 Highball 里正常的 **Detroit: Become Human** 游戏页面，展开 **Game settings**，检查 **Environment**。如果显示 `Games`，找到 **Also installed in Detroit Isolated**，在准备启动游戏时点击旁边的 **Play there**。Highball 会记住选择，之后直接点击主页面的 **Play** 就会使用 `Detroit Isolated`。不需要 command 启动器，也不用重新安装。

已有环境补装新音频修复时，按 [音频升级说明](../../audio/README.zh-CN.md) 操作。没有这个环境时，按下面步骤首次安装。

## 开始前确认

- 已审查的软件基线为 **macOS 27、Highball 0.10.22 / x64-crossover26.3-r28**。可从 [Highball 0.10.22 Release](https://github.com/gauthierpiarrette/highball/releases/tag/v0.10.22) 获取应用，在原环境设置里检查引擎。检查程序会拒绝其他版本，不要为了通过检查而更换其他游戏所在环境的引擎。
- 游戏是完整安装的 **Steam Windows 版**，原 Highball 环境中已安装 Windows Steam。
- 磁盘需要容纳**原环境、引擎和整份游戏的副本，再加至少 12 GiB 余量**，通常超过 75 GiB。安装器会计算所需空间。
- 终端里能运行 `python3 --version` 和 `/usr/bin/lipo -version`。若 macOS 提示安装开发者工具，先完成 Command Line Tools 安装。这里用它检查架构，无需完整 Xcode。

这里的“环境”（Bottle）指 Highball 中装有 Windows Steam 的环境，例如 `Games`。

原环境还需要 **x64 Visual C++ v14 运行库**，包括 `msvcp140.dll`、`mfc140.dll`、`vcruntime140.dll`。缺少时，从 [Microsoft 官方说明](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) 下载 x64 安装器，在 Highball 原环境的 **Run EXE** 中运行它。参考运行库版本为 14.51.36247.0，哈希记录在 `source-lock.json`；本包不分发 Microsoft DLL。已有运行库则无需重复安装，预检会检查文件及架构。

Python 需要 **3.9 或更新版本**。预编译库不需要安装完整 Xcode。

## 1. 下载

打开 macOS“终端”，复制下面一整块命令并按回车。任一下载或校验失败，括号内的后续步骤都会停止。

~~~bash
(
  set -e
  mkdir -p "$HOME/Downloads/highball-detroit-setup"
  cd "$HOME/Downloads/highball-detroit-setup"
  if [ -e highball-detroit-adapter-v0.3.0-preview.1 ]; then
    echo "This version is already extracted; use the existing folder."
    exit 1
  fi
  RELEASE="https://github.com/jason312928/highball-detroit-adapter/releases/download/v0.3.0-preview.1"
  ASSET="highball-detroit-adapter-v0.3.0-preview.1-macos-x86_64.tar.gz"
  curl --fail --location --output "$ASSET" "$RELEASE/$ASSET"
  curl --fail --location --output SHA256SUMS "$RELEASE/SHA256SUMS"
  awk -v asset="$ASSET" '$2 == asset { print; found=1 } END { if (!found) exit 1 }' \
    SHA256SUMS > selected.sha256
  shasum -a 256 -c selected.sha256
  tar -xzf "$ASSET"
  cd highball-detroit-adapter-v0.3.0-preview.1
  shasum -a 256 -c SHA256SUMS
)
~~~

所有校验项显示 `OK` 后继续。如果目录里已有 `highball-detroit-adapter-v0.3.0-preview.1`，命令会停止以免覆盖文件；使用之前下载好的目录即可。完整包已包含脚本和两种运行库，不必另下源码。

接下来的步骤在**同一个终端窗口**执行，先进入脚本目录：

~~~bash
cd "$HOME/Downloads/highball-detroit-setup/highball-detroit-adapter-v0.3.0-preview.1"
~~~

包中的 `candidate.json` 是运行库的校验说明文件。后面的命令已填好它的位置，不用编辑它。

## 2. 填写环境名称和游戏位置

只需准备两项信息：

1. **原环境名称**：在 Highball 查看装有 Windows Steam 的环境叫什么。下面用 `Games` 举例，名称不同就替换引号里的文字。
2. **游戏文件夹的 macOS 路径**：在 Finder 找到包含 `DetroitBecomeHuman.exe` 的 `Detroit Become Human` 文件夹。若安装在环境的 C 盘，可在 Highball 环境菜单选择 **Show the Windows drive**，再进入 Steam 的 `steamapps/common`；外置磁盘安装则去相应 Steam 库查找。选中文件夹，按 **⌥⌘C** 复制路径。

修改下面两行再执行。保留双引号，支持路径中的空格；不要填写 Windows 的 `C:\…` 路径。

~~~bash
SOURCE_BOTTLE="Games"
GAME_DIR="/这里粘贴刚复制的游戏文件夹路径"
~~~

执行只读检查：

~~~bash
python3 scripts/inspect_engine.py --source-bottle "$SOURCE_BOTTLE" &&
./install.sh --dry-run --source-bottle "$SOURCE_BOTTLE" \
  --game-dir "$GAME_DIR" --candidate-manifest "$PWD/candidate/candidate.json"
~~~

看到 `DRY-RUN complete. No Highball or game files written.` 表示路径、库校验和引擎指纹通过，**尚未安装**。这一步只在下载目录记录日志和本地指纹，不启动游戏。

任何一步出现 `ERROR` 都先停下，按文末报错说明处理，不要继续安装。

## 3. 安装

正常退出 Windows Steam、游戏、其他 Wine 程序及 Highball，再执行：

~~~bash
./install.sh --apply --source-bottle "$SOURCE_BOTTLE" \
  --game-dir "$GAME_DIR" --candidate-manifest "$PWD/candidate/candidate.json" &&
./verify.sh &&
./audio/install.sh --dry-run &&
./audio/install.sh --apply &&
./audio/verify.sh
~~~

复制游戏可能需要较长时间。看到 `Private diagnostic engine and Bottle installed.`，随后出现 `Installed files verified:`，表示安装和文件校验完成。重复安装会核对已有结果，不要手动把 dylib 复制进共享引擎。

新环境叫 **Detroit Isolated**，使用独立引擎 **detroit-strict-003-r28**。原游戏、缓存、引擎及 EXE 保留；仅游戏副本的旧缓存会改名，以便首次启动重建。原环境内的其他文件也会复制，存档不与原环境自动同步。副本不是 macOS 安全沙箱，Wine 仍有正常的宿主文件访问能力。

## 4. 准备 Metal 编译器

这一步会复现已测试的工具组合，**无需完整 Xcode**。脚本从 Apple 下载约 672 MiB，独立工具占用约 2.1 GiB；不启动游戏，不更改全局开发工具选择。只需准备一次：

~~~bash
./prepare-metal.sh --dry-run &&
./prepare-metal.sh --apply &&
./prepare-metal.sh --verify
~~~

归档 SHA-256、编译器 SHA-256 和 Apple 签名都必须通过。`metal-toolchain-lock.json` 中的解密键来自 Apple 公开分发元数据，不是账号凭据。重复运行会复用已验证的工具。

## 5. 首次游戏编译，然后生成持久缓存

1. 打开 Highball 里正常的 **Detroit: Become Human** 游戏页面，展开 **Game settings**。
2. 如果 **Environment** 已是 `Detroit Isolated`，直接点击主页面 **Play**；否则点击 **Also installed in Detroit Isolated** 旁的 **Play there**。这个按钮会启动游戏，并为以后记住选择。必要时在这份 Windows Steam 中登录拥有游戏的账号。
3. 等待首次着色器编译**全部完成**。到 98% 还不算结束，需等到进入菜单。检查一个场景后正常退出游戏，再退出 **Detroit Isolated 中的 Windows Steam**；不必退出其他环境。
4. 回到同一个已解压的安装目录，在终端执行：

~~~bash
./compile-cache.sh --dry-run 4 &&
./compile-cache.sh --apply 4
~~~

`4` 是并行任务数，参考构建使用过 `8`。这次性准备可能需要几十分钟，保持终端打开，直到出现 `Done:` 且命令成功结束。**运行期间不要启动《底特律》**。脚本保留源码，按保存的数学及位置不变性选项生成 `.metallib`，单个文件成功后才替换临时输出。

5. 再回到 Highball 正常的底特律游戏页面点击 **Play**，记住的环境应为 `Detroit Isolated`。不需要 `.command` 启动器。以后保留游戏的 `ShaderCache` 和独立环境的 `.detroit-cache/msl`，不要把删除缓存当作日常启动步骤。

参考构建生成了 28,635 份 `.metallib`，全部被原生 Metal 接受；复跑时新增 0 份、跳过全部 28,635 份。不同场景和设置下数量可以不同。后续游玩反馈为正常，不再反复进行长时间编译；新着色器、不同 GPU、软件或画质设置变化仍可能触发额外编译，不表示以后绝对不会编译。

原来 `Games` 环境中的 Steam 仍使用原引擎。要在 Steam 内点击开始，请使用 `Detroit Isolated` 中的 Windows Steam；这款游戏在 Highball 中的选择不会迁移其他游戏，也不会更改默认环境。

如果 Steam 显示未安装游戏，先确认进入的是 `Detroit Isolated`，不要立即重下整份游戏。如果看不到新环境或启动项，退出并重新打开 Highball；仍没有时运行 `./verify.sh` 检查。

**着色器完成、菜单可操作、场景正常运行，才算游戏测试通过。** `verify.sh` 只核对文件，不会证明游戏内这些步骤完成。最新普通游玩反馈正常，但不能代替长时间、所有场景的验收。

此流程不要求改图形设置或修改游戏 EXE；当前参考运行保留景深和原 EXE。若画面高光泛白，可在游戏图形菜单关闭 HDR，对比同一场景。这是诊断对比，尚未验证一定能修复画面。部分场景交互需要按住左键，再沿提示方向移动；菜单点击正常，不能证明这一输入路径也正常。

## 6. 卡住或崩溃时

记录失败步骤、着色器百分比、是否出现游戏窗口。在 Highball 游戏详情页点击 **Show the last launch log** 查看最近启动日志；设置中的 **Show the logs folder** 也可打开日志目录。

要分析日志，在 Finder 选中日志、按 **⌥⌘C** 复制路径，替换下面引号里的内容再执行：

~~~bash
GAME_LOG="/这里粘贴启动日志路径"
./verify.sh --game-log "$GAME_LOG"
~~~

- `private_library_load_observed: true`：日志包含独立 MoltenVK 的加载证据。`false` 表示未找到证据，不等于已证明加载了错误的库。
- `failure_line_count`：识别出的错误行数。零错误也不代表游戏成功。

脚本日志在下载目录的 `logs/` 中，完整游戏日志留在 Highball 本地。分享前检查路径和账号信息；安装器不会自动上传。

## 7. 恢复原来的使用方式

退出测试游戏及其 Windows Steam，关闭 Wine 程序和 Highball，再执行：

~~~bash
./prepare-metal.sh --rollback --dry-run &&
./prepare-metal.sh --rollback --apply &&
./audio/rollback.sh --dry-run &&
./audio/rollback.sh --apply &&
./rollback.sh --dry-run &&
./rollback.sh --apply
~~~

重新打开 Highball，使用原环境和原游戏启动项即可。回滚将独立引擎、环境、存档及诊断数据移到 Highball 数据目录下的 `.detroit-adapter/archived/`。**文件会保留，因此不会立即释放这部分磁盘空间。** 命令会打印归档位置；确认存档前不要删除它。重复回滚不会再次移动文件。

如果关过终端，先重新执行第 1 步末尾的 `cd` 命令，再运行验证或回滚。

## 常见报错

| 显示内容 | 如何处理 |
|---|---|
| `python3: command not found` 或开发者工具提示 | 安装 macOS Command Line Tools，再重新打开终端检查 Python 和 lipo。 |
| `Source bottle must be a real directory` | 核对原环境名称和空格；这里不是填游戏名。 |
| `Only the x64-crossover26.3-r28 engine baseline has been reviewed` | 当前引擎不在审查范围，停止安装，不要强改版本号。 |
| `Expected a regular file`，指向游戏 EXE 或 `appmanifest_1222140.acf` | 检查 Finder 路径；需要完整 Steam 版安装及相邻的 Steam 清单。 |
| `Metal Toolchain unavailable` | 先完成第 4 步，再重新生成缓存。 |
| `Missing x64 Visual C++ runtime` | 克隆前先在原环境安装 Microsoft x64 运行库。 |
| `Close Highball and Wine/Windows programs` | 正常退出这些程序再重试；安装器不会强制关闭它们。 |
| `Insufficient space` | 按提示准备空间；计算包含环境、引擎、游戏副本和余量。 |
| `SHA-256 mismatch` 或 `FAILED` | 停止使用该下载，重新下载核对，不要跳过校验。 |
| `Source engine differs` 或 `Existing fingerprint differs` | 原引擎发生变化，需重新审查；不要删除指纹绕过检查。 |

自定义 Highball 数据位置通常从 `HIGHBALL_HOME` 或配置读取。需显式指定时，对检查、安装、验证及回滚命令均传入相同的 `--highball-root "/实际数据目录"`。

## 自定义编译器或升级已有安装

已有旧版适配器时，把本次发布解压到**新目录**，运行 `./verify.sh` 和 `./audio/verify.sh`，再执行第 4、5 步。不要重新安装或删除已完成的缓存。若音频验证提示尚未安装修复，先按 [音频升级说明](../../audio/README.zh-CN.md) 补齐。

缓存脚本优先使用私有目录中固定版本的 Apple 编译器，没有时才尝试 Xcode。也可对两条缓存命令设置 `METAL_TOOL="/绝对路径/metal"`。已测试的 17A324 工具组合由 `prepare-metal.sh` 准备。脚本会读取 `HIGHBALL_HOME` 及 Highball 配置的数据位置；缓存脚本可用 `HIGHBALL_ROOT="/实际数据目录"` 覆盖。工具准备脚本则传入 `--highball-root "/实际数据目录"`。

工具回滚仅将私有工具移到 `.detroit-adapter/tools-archived-*`；整个适配器回滚会把游戏、存档和缓存保留在 `.detroit-adapter/archived/`。保留的归档仍占磁盘空间，需要时再自行清理。不会更换共享引擎、系统 Vulkan 或全局音频设置。
