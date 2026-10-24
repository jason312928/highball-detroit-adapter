# 安装、启动与恢复

[English](../usage.md)

本教程使用下载好的运行库，**不用自己编译 MoltenVK，也不用安装完整 Xcode**。

**当前是诊断版：可以安装独立测试环境，但尚未验证《底特律：变人》能完成首次着色器编译、进入主菜单和正常游玩。安装成功不代表故障已修复。**

## 已经安装过？

打开 Highball。如果环境列表中已有 **Detroit Isolated**，进入它，点击 **Detroit (isolated Steam)** 即可测试。不要从原环境的游戏图标启动，否则仍可能使用原来的库。不用重复下载、构建或安装。

没有这个环境时，按下面步骤首次安装。

## 开始前确认

- 已审查的组合是 **Highball 0.10.22 / x64-crossover26.3-r28**，检查程序会拒绝其他引擎版本。
- 游戏是完整安装的 **Steam Windows 版**，原 Highball 环境中已安装 Windows Steam。
- 磁盘需要容纳**原环境、引擎和整份游戏的副本，再加至少 5 GiB 余量**，通常超过 64 GiB。安装器会计算所需空间。
- 终端里能运行 `python3 --version` 和 `/usr/bin/lipo -version`。若 macOS 提示安装开发者工具，先完成 Command Line Tools 安装。这里用它检查架构，无需完整 Xcode。

这里的“环境”（Bottle）指 Highball 中装有 Windows Steam 的环境，例如 `Games`。

## 1. 下载

打开 macOS“终端”，复制下面一整块命令并按回车。任一下载或校验失败，括号内的后续步骤都会停止。

~~~bash
(
  set -e
  mkdir -p "$HOME/Downloads/highball-detroit-setup"
  cd "$HOME/Downloads/highball-detroit-setup"
  if [ -e highball-detroit-adapter-main ]; then
    echo "Download folder already exists; use it or choose another setup directory."
    exit 1
  fi
  curl --fail --location --output source.zip \
    https://github.com/jason312928/highball-detroit-adapter/archive/refs/heads/main.zip
  unzip -q source.zip
  cd highball-detroit-adapter-main
  mkdir -p release/candidate
  cd release
  RELEASE="https://github.com/jason312928/highball-detroit-adapter/releases/download/v0.1.0-diagnostic.1"
  ASSET="highball-detroit-moltenvk-v0.1.0-diagnostic.1-macos-x86_64.tar.gz"
  curl --fail --location --output "$ASSET" "$RELEASE/$ASSET"
  curl --fail --location --output 0001-strict-interfaces-and-pinned-spirv.patch \
    "$RELEASE/0001-strict-interfaces-and-pinned-spirv.patch"
  curl --fail --location --output SHA256SUMS "$RELEASE/SHA256SUMS"
  shasum -a 256 -c SHA256SUMS
  tar -xzf "$ASSET" -C candidate
  cd candidate
  shasum -a 256 -c SHA256SUMS
)
~~~

所有校验项显示 `OK` 后继续。如果目录里已有 `highball-detroit-adapter-main`，命令会停止以免覆盖文件；使用之前下载好的目录即可。

接下来的步骤在**同一个终端窗口**执行，先进入脚本目录：

~~~bash
cd "$HOME/Downloads/highball-detroit-setup/highball-detroit-adapter-main"
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
  --game-dir "$GAME_DIR" --candidate-manifest "$PWD/release/candidate/candidate.json"
~~~

看到 `DRY-RUN complete. No Highball or game files written.` 表示路径、库校验和引擎指纹通过，**尚未安装**。这一步只在下载目录记录日志和本地指纹，不启动游戏。

任何一步出现 `ERROR` 都先停下，按文末报错说明处理，不要继续安装。

## 3. 安装

正常退出 Windows Steam、游戏、其他 Wine 程序及 Highball，再执行：

~~~bash
./install.sh --apply --source-bottle "$SOURCE_BOTTLE" \
  --game-dir "$GAME_DIR" --candidate-manifest "$PWD/release/candidate/candidate.json" &&
./verify.sh
~~~

复制游戏可能需要较长时间。看到 `Private diagnostic engine and Bottle installed.`，随后出现 `Installed files verified:`，表示安装和文件校验完成。重复安装会核对已有结果，不要手动把 dylib 复制进共享引擎。

新环境叫 **Detroit Isolated**，使用独立引擎 **detroit-strict-003-r28**。原游戏、缓存、引擎及 EXE 保留；仅游戏副本的旧缓存会改名，以便首次启动重建。原环境内的其他文件也会复制，存档不与原环境自动同步。副本不是 macOS 安全沙箱，Wine 仍有正常的宿主文件访问能力。

## 4. 启动游戏

1. 打开 Highball，选择 **Detroit Isolated**。
2. 点击 **Detroit (isolated Steam)**。必要时在这份 Windows Steam 中登录拥有游戏的账号。
3. 等待首次着色器编译，记录是否超过 98% 并完成。
4. 如果完成，检查主菜单是否可操作，再启动一个场景，观察画面和崩溃情况。

如果 Steam 显示未安装游戏，先确认进入的是 `Detroit Isolated`，不要立即重下整份游戏。如果看不到新环境或启动项，退出并重新打开 Highball；仍没有时运行 `./verify.sh` 检查。

**着色器完成、菜单可操作、场景正常运行，才算游戏测试通过。** `verify.sh` 只核对文件，不会证明游戏内这些步骤完成。当前项目尚未完成这项验收。

## 5. 卡住或崩溃时

记录失败步骤、着色器百分比、是否出现游戏窗口。在 Highball 游戏详情页点击 **Show the last launch log** 查看最近启动日志；设置中的 **Show the logs folder** 也可打开日志目录。

要分析日志，在 Finder 选中日志、按 **⌥⌘C** 复制路径，替换下面引号里的内容再执行：

~~~bash
GAME_LOG="/这里粘贴启动日志路径"
./verify.sh --game-log "$GAME_LOG"
~~~

- `private_library_load_observed: true`：日志包含独立 MoltenVK 的加载证据。`false` 表示未找到证据，不等于已证明加载了错误的库。
- `failure_line_count`：识别出的错误行数。零错误也不代表游戏成功。

脚本日志在下载目录的 `logs/` 中，完整游戏日志留在 Highball 本地。分享前检查路径和账号信息；安装器不会自动上传。

## 6. 恢复原来的使用方式

退出测试游戏及其 Windows Steam，关闭 Wine 程序和 Highball，再执行：

~~~bash
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
| `Close Highball and Wine/Windows programs` | 正常退出这些程序再重试；安装器不会强制关闭它们。 |
| `Insufficient space` | 按提示准备空间；计算包含环境、引擎、游戏副本和余量。 |
| `SHA-256 mismatch` 或 `FAILED` | 停止使用该下载，重新下载核对，不要跳过校验。 |
| `Source engine differs` 或 `Existing fingerprint differs` | 原引擎发生变化，需重新审查；不要删除指纹绕过检查。 |

自定义 Highball 数据位置通常从 `HIGHBALL_HOME` 或配置读取。需显式指定时，对检查、安装、验证及回滚命令均传入相同的 `--highball-root "/实际数据目录"`。

## 可选：离线 Metal 缓存

**首次安装和启动不需要这一步。** 仅在游戏自身着色器编译完成、Wine 已退出，且已安装 Metal Toolchain 时使用：

~~~bash
./compile-cache.sh --dry-run 4 &&
./compile-cache.sh --apply 4
~~~

`4` 是并行任务数。离线缓存流程尚未完成实际验收，缺少 `metal` 编译器时可跳过；不要删除已生成的游戏缓存。自定义数据目录还需为这两条命令设置 `HIGHBALL_ROOT="/实际数据目录"`。需要自己编译库时，另见 [构建文档](build.md)。
