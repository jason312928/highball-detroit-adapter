# Third-party materials

| Material | Location | License |
|---|---|---|
| MoltenVK API header | src/include/mvk_private_api.h | Apache-2.0 |
| Vulkan headers | src/include/vulkan/, src/include/vk_video/ | See [Vulkan-Headers license](licenses/Vulkan-Headers-LICENSE.md) and individual SPDX headers |
| MoltenVK changes | patches/ | Apache-2.0; upstream copyright retained |
| MSL cache compiler (adapted to accept an explicit `METAL_TOOL` path) | vendor/compile_msl_library_cache.sh | MoltenVK distribution terms; see [release notices](licenses/Release003-LICENSES.txt) |
| Release provenance | vendor/Release003-VERSION.txt | Upstream build metadata |
| Highball dependency lock | vendor/Highball-Package.resolved | Metadata from the pinned GPL-3.0 project |

[MoltenVK license](licenses/MoltenVK-Apache-2.0.txt) and [Highball license](licenses/Highball-GPL-3.0.txt) are retained for reference. Downloaded dependencies retain their upstream licenses.

D3DMetal, game files, runtime logs and crash dumps are not distributed. Git contains source and patches; release archives contain the reviewed MoltenVK and XAudio2 binaries.

The audio changes derive from Wine (LGPL-2.1-or-later) and its bundled FAudio (zlib-style license). Notices are in [audio/licenses](audio/licenses/). Each audio binary release also provides a corresponding-source archive containing the patched Wine tree and build instructions, with the original source URL/hash and independent patches in [audio/source-lock.json](audio/source-lock.json).

The diagnostic library links SPIRV-Cross, SPIRV-Tools and cereal. Their complete notices are retained in licenses/ along with SPIRV-Headers notices. Binary release archives include these files.

`prepare-metal.sh` downloads a pinned Apple Metal Toolchain to the local installation only. Apple binaries remain subject to Apple’s terms and are not included in this repository or its release assets. The asset key in the lock is public Apple distribution metadata. Microsoft Visual C++ runtimes are prerequisites obtained from Microsoft, not redistributed here.
