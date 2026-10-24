# Third-party materials

| Material | Location | License |
|---|---|---|
| MoltenVK API header | src/include/mvk_private_api.h | Apache-2.0 |
| Vulkan headers | src/include/vulkan/, src/include/vk_video/ | See [Vulkan-Headers license](licenses/Vulkan-Headers-LICENSE.md) and individual SPDX headers |
| MoltenVK changes | patches/ | Apache-2.0; upstream copyright retained |
| MSL cache compiler | vendor/compile_msl_library_cache.sh | MoltenVK distribution terms; see [release notices](licenses/Release003-LICENSES.txt) |
| Release provenance | vendor/Release003-VERSION.txt | Upstream build metadata |
| Highball dependency lock | vendor/Highball-Package.resolved | Metadata from the pinned GPL-3.0 project |

[MoltenVK license](licenses/MoltenVK-Apache-2.0.txt) and [Highball license](licenses/Highball-GPL-3.0.txt) are retained for reference. Downloaded dependencies retain their upstream licenses.

Wine, D3DMetal, game files and prebuilt dylibs are not distributed by this repository.

The diagnostic library links SPIRV-Cross, SPIRV-Tools and cereal. Their complete notices are retained in licenses/ along with SPIRV-Headers notices. Binary release archives include these files.
