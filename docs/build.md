# Build

[简体中文](zh-CN/build.md)

Run commands from the repository root. Requirements: macOS Command Line Tools, Python 3.12+, git and curl. CMake and Ninja are installed in a local virtual environment. Downloads and build products stay under the ignored work/ and build/ directories.

## Sources and tools

~~~bash
mkdir -p work
git clone https://github.com/DiAvisoo/MoltenVK-Detroit.git work/MoltenVK-Detroit
git -C work/MoltenVK-Detroit checkout --detach 8b511fdc5351a37c305bc246e161796ddca56b18
git -C work/MoltenVK-Detroit apply ../../patches/0001-strict-interfaces-and-pinned-spirv.patch
git clone https://github.com/alexdremov/SPIRV-Cross.git work/SPIRV-Cross
git -C work/SPIRV-Cross checkout --detach 05583ac1537d777d304128142de2365bfa4a38df
python3 -m venv work/build-tools
work/build-tools/bin/python -m pip install cmake==4.4.4 ninja==1.13.2
~~~

## Dependencies

Download each archive to the filename shown, then verify the pinned hashes before extraction.

| work/ file | Download |
|---|---|
| cereal.tar.gz | [cereal](https://codeload.github.com/USCiLab/cereal/tar.gz/a56bad8bbb770ee266e930c95d37fff2a5be7fea) |
| spirv-tools.tar.gz | [SPIRV-Tools](https://codeload.github.com/KhronosGroup/SPIRV-Tools/tar.gz/c8bda961df8dcdc07cdd6fc59dac3b35a4b73739) |
| spirv-headers.tar.gz | [SPIRV-Headers](https://codeload.github.com/KhronosGroup/SPIRV-Headers/tar.gz/126038020c2bd47efaa942ccc364ca5353ffccde) |
| vulkan-headers.tar.gz | [Vulkan-Headers](https://codeload.github.com/KhronosGroup/Vulkan-Headers/tar.gz/8864cdc896bbc2a9b6eb36b3218fc9ef57908d77) |
| CPM_0.40.8.cmake | [CPM](https://github.com/cpm-cmake/CPM.cmake/releases/download/v0.40.8/CPM.cmake) |

~~~bash
python3 - <<'CHECK'
import hashlib, json, pathlib
lock = json.loads(pathlib.Path("source-lock.json").read_text())
for name, expected in lock["cmake_build"]["inputs"].items():
    if hashlib.sha256(pathlib.Path(name).read_bytes()).hexdigest() != expected:
        raise SystemExit("SHA-256 mismatch: " + name)
CHECK
mkdir -p work/cereal work/spirv-tools work/spirv-headers work/headers work/cpm-cache/cpm
tar -xzf work/cereal.tar.gz -C work/cereal --strip-components=1
tar -xzf work/spirv-tools.tar.gz -C work/spirv-tools --strip-components=1
tar -xzf work/spirv-headers.tar.gz -C work/spirv-headers --strip-components=1
tar -xzf work/vulkan-headers.tar.gz -C work/headers --strip-components=1
cp work/CPM_0.40.8.cmake work/cpm-cache/cpm/
./build.sh
~~~

Without full Xcode, build.sh selects the CMake backend. Both SPIRV-Tools and cereal remain enabled. A successful build runs the Rosetta/config/Vulkan probe and writes build/libMoltenVK.dylib plus build/candidate.json. It never installs the result.

The offline Metal cache compiler is a separate toolchain requirement. The library build itself does not require an offline metal compiler.

## Upstream comparison

For probe-release.sh, download the Release003 ZIP from the URL in source-lock.json and verify both the ZIP and dylib hashes. Place the extracted library at vendor/release003-probe-only.dylib. This upstream binary is for comparison only and is not accepted by the diagnostic installer.
