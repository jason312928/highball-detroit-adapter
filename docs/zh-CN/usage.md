# 安装与回滚

[English](../usage.md)

## 前置条件

已审查的引擎基线为 x64-crossover26.3-r28，运行库必须包含 x86_64 架构。其他引擎版本需单独审查兼容性。

安装预检前记录本地引擎身份：

~~~bash
python3 scripts/inspect_engine.py --source-bottle Games
~~~

此命令只读取引擎，写入被 Git 忽略的 engine-lock.local.json。该文件仅包含引擎标识和哈希，并不证明兼容性；指纹变化后需重新审查。

## 安装

先退出 Highball 和 Wine 程序。安装器不会自动关闭它们。

~~~bash
./install.sh --dry-run --game-dir "/path/to/steamapps/common/Detroit Become Human" \
  --candidate-manifest "$PWD/build/candidate.json"
./install.sh --apply --game-dir "/path/to/steamapps/common/Detroit Become Human" \
  --candidate-manifest "$PWD/build/candidate.json"
./verify.sh
~~~

使用 Release 中的二进制包时，将 build/candidate.json 替换为解压后的 candidate.json 路径。

新引擎名为 detroit-strict-003-r28，新 Bottle 为 Detroit Isolated。引擎、Bottle 与完整游戏会被复制。原缓存保留；仅副本中的缓存在首次启动前被改名。安装不会启动 Wine，也不修改游戏 EXE、景深设置、共享引擎或系统 Vulkan。

支持含空格路径。非默认布局可指定 --highball-root 和 --source-bottle。游戏目录必须对应 Steam 的 appmanifest_1222140.acf。

安装采用事务并支持重复执行。日志状态位于 Highball/.detroit-adapter。普通异常只清理本次拥有的新路径；中断后再次执行可恢复。

## 运行与采证

在 Highball 中选择 Detroit Isolated 及其 Detroit (isolated Steam) pin。先确认实际加载的 dylib，再评估 shader 进度。私有配置启用了库加载日志和 shader dump。

~~~bash
./verify.sh --game-log "/path/to/run.log"
~~~

此命令检查加载证据和可识别错误，不会推断着色器编译完成、菜单可操作或场景已渲染。Wine 仍有正常宿主文件访问能力；复制环境不是操作系统沙箱。

首次 shader 编译完成并退出 Wine 后，可编译私有 Metal cache：

~~~bash
./compile-cache.sh --dry-run 4
./compile-cache.sh --apply 4
~~~

离线编译需要 Metal Toolchain。后续正常启动应保留完成的游戏缓存。本项目不修改 EXE，也不自动更改景深。

## 回滚

~~~bash
./rollback.sh --dry-run
./rollback.sh --apply
~~~

只将本次事务拥有的引擎和 Bottle 移入 Highball/.detroit-adapter/archived，保留存档与诊断数据。原游戏与源引擎不动。
