#include "spirv_msl.hpp"
#include <cassert>
#include <cstring>
#include <iostream>
#include <vector>

// A real, minimal SPIR-V vertex shader. Location is a Vulkan location, not a buffer binding.
static std::vector<uint32_t> shader() {
    using namespace spv;
    std::vector<uint32_t> w = {0x07230203, 0x00010000, 0, 18, 0};
    auto emit = [&](Op op, std::initializer_list<uint32_t> a) {
        w.push_back((uint32_t(a.size() + 1) << 16) | uint32_t(op)); w.insert(w.end(), a);
    };
    emit(OpCapability, {CapabilityShader});
    emit(OpMemoryModel, {AddressingModelLogical, MemoryModelGLSL450});
    emit(OpEntryPoint, {ExecutionModelVertex, 1, 0x6e69616d, 0, 2, 3}); // "main"
    emit(OpDecorate, {2, DecorationLocation, 12});
    emit(OpDecorate, {3, DecorationBuiltIn, BuiltInPosition});
    emit(OpTypeVoid, {4});
    emit(OpTypeFunction, {5, 4});
    emit(OpTypeFloat, {6, 32});
    emit(OpTypeVector, {7, 6, 3});
    emit(OpTypeVector, {8, 6, 4});
    emit(OpTypePointer, {9, StorageClassInput, 7});
    emit(OpTypePointer, {10, StorageClassOutput, 8});
    emit(OpVariable, {9, 2, StorageClassInput});
    emit(OpVariable, {10, 3, StorageClassOutput});
    emit(OpConstant, {6, 11, 0x3f800000});
    emit(OpFunction, {4, 1, FunctionControlMaskNone, 5});
    emit(OpLabel, {12});
    emit(OpLoad, {7, 13, 2});
    emit(OpCompositeExtract, {6, 14, 13, 0});
    emit(OpCompositeExtract, {6, 15, 13, 1});
    emit(OpCompositeExtract, {6, 16, 13, 2});
    emit(OpCompositeConstruct, {8, 17, 14, 15, 16, 11});
    emit(OpStore, {3, 17});
    emit(OpReturn, {});
    emit(OpFunctionEnd, {});
    return w;
}

int main() {
    spirv_cross::CompilerMSL compiler(shader());
    auto source = compiler.compile();
    if (!compiler.is_msl_shader_input_used(12) || compiler.is_msl_shader_input_used(3) ||
        source.find("[[attribute(12)]]") == std::string::npos) {
        std::cerr << source; return 1;
    }
    std::cout << "PASS: active Vulkan Location 12 -> MSL [[attribute(12)]].\n";
    std::cout << "No buffer binding or Metal vertex format can be inferred from this shader alone.\n";
    std::cout << source;
}
