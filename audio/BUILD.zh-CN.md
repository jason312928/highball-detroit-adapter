# 重建音频 DLL

[English](BUILD.md)

使用 `source-lock.json` 中固定的 CrossOver 源码和工具链，只构建 `xaudio2_8.dll`。不要将此 configure 生成的 Wine 树当成完整引擎安装；配置中的可选库警告不改变现有 Highball 运行环境。

准备三个绝对路径：`SOURCE` 指向源码包中的 `sources/wine`；`MINGW` 指向 LLVM-MinGW 解压目录；`BISON` 指向单独安装在本地目录的 Bison 3.8.2。先按 `source-lock.json` 核对下载包 SHA-256。宿主编译器由 macOS Command Line Tools 提供，无需完整 Xcode。

在未修改的源码树上按顺序应用两份补丁，再进入另一个空的构建目录执行 configure 和限定 DLL 的 make 目标。以下命令中的路径变量需先由开发者设置：

```bash
patch -d "$SOURCE" -p1 < patches/0001-faudio-propagate-device-query-errors.patch
patch -d "$SOURCE" -p1 < patches/0002-xaudio-propagate-mastering-voice-errors.patch
```

Configure a separate empty build directory, then build with at most two jobs:

```bash
mkdir -p build-audio
cd build-audio
export PATH="$BISON/bin:$PATH:$MINGW/bin"
"$SOURCE/configure" --host=x86_64-apple-darwin --enable-win64 \
  --enable-archs=x86_64 --disable-tests --without-x --without-gstreamer \
  --without-gnutls --without-freetype --without-sdl --without-alsa \
  --without-pulse --without-oss --without-cups --without-unwind --with-mingw \
  CC='/usr/bin/clang -arch x86_64' CXX='/usr/bin/clang++ -arch x86_64' \
  x86_64_CC="$MINGW/bin/x86_64-w64-mingw32-clang"
make -j2 "x86_64_CFLAGS=-g -O2 -ffile-prefix-map=$SOURCE=source -ffile-prefix-map=$PWD=build" \
  dlls/xaudio2_8/x86_64-windows/xaudio2_8.dll
```


结果位于 `dlls/xaudio2_8/x86_64-windows/xaudio2_8.dll`。构建含时间戳，因此重新构建不保证产生完全相同的二进制哈希。安装器只接受已审查的候选 SHA-256，自建文件必须重新审查并更新清单。

`src/` 中的回归测试保留了修补前后实际函数体，使用模拟 COM 设备操作，并用异常处理器捕获旧代码的空指针复现。用 LLVM-MinGW 编译，头文件使用固定源码树的 `libs/faudio/include`，链接 `ole32` 和 `uuid`，仅在独立测试 Bottle 运行。`device-error-test.c` 使用 `NDEBUG` 复现发行版行为；`mastering-error-test.c` 检查失败传递、正常创建和重复创建；`xaudio-load-probe.c` 验证完整 DLL 并静默处理真实输出缓冲区。

## v2 音频路由构建与验证

v2 需按顺序应用 `patches/0001` 至 `patches/0005`，构建 `dlls/xaudio2_8/x86_64-windows/xaudio2_8.dll` 和 `dlls/mmdevapi/x86_64-windows/mmdevapi.dll` 两个目标。第五个补丁保留 Highball 原引擎已有的空间音频声道顺序修正。随版本发布的完整对应源码已经打好补丁，无需重复应用。

Apple Silicon 构建时将 `/Library/Developer/CommandLineTools/usr/bin` 放在 PATH 的 `/usr/bin` 前，避免 Rosetta 中的编译器选择器尝试加载仅有 arm64 的 libxcrun。完整命令及从真实函数提取的回归测试见[英文构建说明](BUILD.md#routing-regression-fixtures)。

Highball 的真实 DLL 探针必须用 `WINEDLLPATH_PREPEND` 指向包含两个新版 DLL 的 `x86_64-windows` 上级目录，并核对内存映像时间戳。普通 `WINEDLLPATH` 排在引擎内建库之后，不能证明候选库实际加载。测试不会启动游戏，也不能替代真实 AirPods 切换验收。
