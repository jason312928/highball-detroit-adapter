#import <Foundation/Foundation.h>
#import <Metal/Metal.h>

/* Demonstrates the exact Metal interface failure without inventing attributes. */
int main(void) { @autoreleasepool {
    id<MTLDevice> device = MTLCreateSystemDefaultDevice();
    if (!device) return 2;
    NSString *source = @"#include <metal_stdlib>\nusing namespace metal;\n"
        "struct In { float3 in_vfMsBindPosePosition [[attribute(12)]]; };\n"
        "vertex float4 vertexMain(In in [[stage_in]]) { return float4(in.in_vfMsBindPosePosition, 1); }\n"
        "fragment float4 fragmentMain() { return float4(1); }\n";
    NSError *error = nil;
    id<MTLLibrary> lib = [device newLibraryWithSource:source options:nil error:&error];
    if (!lib) { NSLog(@"%@", error); return 3; }
    MTLRenderPipelineDescriptor *p = [MTLRenderPipelineDescriptor new];
    p.vertexFunction = [lib newFunctionWithName:@"vertexMain"];
    p.fragmentFunction = [lib newFunctionWithName:@"fragmentMain"];
    p.colorAttachments[0].pixelFormat = MTLPixelFormatBGRA8Unorm;
    p.vertexDescriptor = [MTLVertexDescriptor vertexDescriptor];
    id<MTLRenderPipelineState> pipeline = [device newRenderPipelineStateWithDescriptor:p error:&error];
    if (pipeline || !error || ![error.localizedDescription containsString:@"missing from the vertex descriptor"]) {
        NSLog(@"Unexpected result %@ %@", pipeline, error); return 4;
    }
    NSLog(@"Expected rejection: %@", error.localizedDescription);
    return 0;
} }
