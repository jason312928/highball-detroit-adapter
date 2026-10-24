# 构建

[English](../build.md)

从仓库根目录执行。需要 macOS Command Line Tools、Python 3.12+、git 与 curl。CMake 和 Ninja 安装在本地虚拟环境，下载文件与构建产物位于被忽略的 work/ 和 build/。

## 源码和工具

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

## 依赖

将文件下载到表中指定名称，解包前先核对固定哈希。

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

没有完整 Xcode 时，build.sh 选择 CMake 后端。SPIRV-Tools 和 cereal 均保留。构建成功后执行 Rosetta/config/Vulkan 探针，再生成 build/libMoltenVK.dylib 与 build/candidate.json，不执行安装。

离线 Metal cache 编译需要单独的工具链；库构建本身不依赖离线 metal 编译器。

## 上游对照

运行 probe-release.sh 前，按 source-lock.json 指定 URL 下载 Release003 ZIP，核对 ZIP 和 dylib 哈希，再将库放在 vendor/release003-probe-only.dylib。该库只用于对照探针，诊断安装器不会接受它。
