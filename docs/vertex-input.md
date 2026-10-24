# Vertex-input failure

[简体中文](zh-CN/vertex-input.md)

## Translation path

A SPIR-V Location decoration becomes an MSL attribute location through SPIRV-Cross. MoltenVK populates MTLVertexDescriptor from the Vulkan location, binding, format and offset descriptions. Location 12 is not buffer binding 12; the shader alone cannot supply the missing binding, format or offset.

The Metal error establishes that the shader requires an input absent from the final descriptor. It does not establish which earlier stage introduced the mismatch.

## Evidence and limits

The original failure included locations 12 and 3. The minimal Metal reproduction in src/metal_descriptor_repro.m produces the same descriptor rejection. A cached vertex module was separately reflected and converted with the pinned SPIRV-Cross fork; its location-12 input was present and read, with no specialization constants in that module.

The cached module has not been associated with a specific failed pipeline. Application state, cache selection and translation/interface pruning remain possible explanations. No game shader is distributed here.

## Diagnostic patch

Release003 supplies UChar4, an existing buffer and offset zero for some missing inputs. It also adjusts unmatched stage outputs. Those values are not derived from the missing Vulkan input descriptions.

The diagnostic variant removes these fallbacks. A failure logs entry point, binding/stride/rate, location/binding/format/offset, vertex-input pNext types and specialization bytes. The marker is HB_DETROIT_STRICT_INTERFACE_V1. Existing SPIR-V/MSL dumping can be enabled through MVK_CONFIG_SHADER_DUMP_DIR.

The next required capture is a single failed pipeline with its module, entry point, specialization values, complete vertex-input state and relevant dynamic state. A semantic correction depends on that evidence.

Related investigation: [MoltenVK #2054](https://github.com/KhronosGroup/MoltenVK/issues/2054).
