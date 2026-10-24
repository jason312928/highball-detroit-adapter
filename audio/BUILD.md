# Rebuild the audio DLL

[简体中文](BUILD.zh-CN.md)

The build uses the CrossOver source archive and toolchain versions in `source-lock.json`. It builds only `xaudio2_8.dll`; do not install the configured Wine tree as a complete engine. Optional-library warnings from configure do not change the existing Highball runtime.

Prepare three directories: `SOURCE` is the archive's `sources/wine`, `MINGW` is the extracted LLVM-MinGW root, and `BISON` is a local Bison 3.8.2 installation. Check their archive SHA-256 values against `source-lock.json`. A full Xcode installation is unnecessary; macOS Command Line Tools supply the host compiler.

From an unmodified source tree, apply these patches in order:

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

The result is at `dlls/xaudio2_8/x86_64-windows/xaudio2_8.dll`. Compilation embeds timestamps, so rebuilding need not produce the identical binary hash. The installer deliberately accepts only the exact reviewed artifact; a new build needs separate inspection and a new manifest.

The regression fixtures in `src/` include the exact pre/post functions under test, mocked COM endpoint operations and a guarded baseline access-violation reproduction. Compile with LLVM-MinGW against the pinned source's `libs/faudio/include`, linking `ole32` and `uuid`, and run only in the private test Bottle. `device-error-test.c` uses `NDEBUG` to reproduce the shipped release behavior. `mastering-error-test.c` checks failure propagation, normal creation and duplicate creation. `xaudio-load-probe.c` checks the full DLL and silently consumes a real output buffer.
