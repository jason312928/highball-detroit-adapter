// Offscreen feasibility probe. Never launches or modifies a game.
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#import <MetalFX/MetalFX.h>
#import <QuartzCore/CAMetalLayer.h>
#include <dlfcn.h>
#include <math.h>
#define VK_NO_PROTOTYPES
#define VK_USE_PLATFORM_METAL_EXT
#include <vulkan/vulkan.h>

#define REQUIRE(x) do { if (!(x)) { fprintf(stderr, "Failed: %s line %d\n", #x, __LINE__); exit(2); } } while (0)
#define CHECK(x) do { VkResult r=(x); if (r!=VK_SUCCESS) { fprintf(stderr, "%s: VkResult %d\n", #x, r); exit(3); } } while (0)
#define LOAD(n) PFN_vk##n n = (PFN_vk##n)dlsym(lib, "vk" #n); REQUIRE(n)

@interface ProbeLayer : CAMetalLayer
@property(nonatomic, retain) id<CAMetalDrawable> lastDrawable;
@end
@implementation ProbeLayer
- (id<CAMetalDrawable>)nextDrawable { id<CAMetalDrawable> drawable=[super nextDrawable]; self.lastDrawable=drawable;return drawable; }
- (void)dealloc { self.lastDrawable=nil;[super dealloc]; }
@end

static __attribute__((unused)) id<MTLTexture> texture(id<MTLDevice> device, MTLPixelFormat format, NSUInteger w, NSUInteger h, MTLTextureUsage usage) {
    MTLTextureDescriptor *td=[MTLTextureDescriptor texture2DDescriptorWithPixelFormat:format width:w height:h mipmapped:NO];
    td.storageMode=MTLStorageModePrivate;td.usage=usage;
    id<MTLTexture> tex=[device newTextureWithDescriptor:td];REQUIRE(tex);return tex;
}

static __attribute__((unused)) void clear(id<MTLCommandBuffer> cb, id<MTLTexture> tex, MTLClearColor color) {
    MTLRenderPassDescriptor *p=[MTLRenderPassDescriptor renderPassDescriptor];
    p.colorAttachments[0].texture=tex;p.colorAttachments[0].loadAction=MTLLoadActionClear;p.colorAttachments[0].storeAction=MTLStoreActionStore;p.colorAttachments[0].clearColor=color;
    id<MTLRenderCommandEncoder> enc=[cb renderCommandEncoderWithDescriptor:p];REQUIRE(enc);[enc endEncoding];
}

int main(int argc, const char **argv) {
 @autoreleasepool {
    REQUIRE(argc==2);
    void *lib=dlopen(argv[1], RTLD_NOW|RTLD_LOCAL); if (!lib) { fprintf(stderr,"%s\n",dlerror());return 1; }
    LOAD(CreateInstance); LOAD(DestroyInstance); LOAD(EnumeratePhysicalDevices); LOAD(EnumerateInstanceExtensionProperties);
    LOAD(GetPhysicalDeviceQueueFamilyProperties); LOAD(EnumerateDeviceExtensionProperties);
    LOAD(CreateDevice); LOAD(DestroyDevice); LOAD(GetDeviceQueue); LOAD(GetPhysicalDeviceMemoryProperties);
    LOAD(CreateImage); LOAD(DestroyImage); LOAD(GetImageMemoryRequirements); LOAD(AllocateMemory);
    LOAD(FreeMemory); LOAD(BindImageMemory); LOAD(ExportMetalObjectsEXT);
    LOAD(CreateMetalSurfaceEXT); LOAD(DestroySurfaceKHR); LOAD(GetPhysicalDeviceSurfaceCapabilitiesKHR); LOAD(GetPhysicalDeviceSurfaceFormatsKHR);
    LOAD(CreateSwapchainKHR); LOAD(DestroySwapchainKHR); LOAD(GetSwapchainImagesKHR); LOAD(AcquireNextImageKHR); LOAD(QueuePresentKHR);
    LOAD(CreateFence); LOAD(DestroyFence); LOAD(WaitForFences); LOAD(ResetFences); LOAD(ResetCommandBuffer);
    LOAD(CreateCommandPool); LOAD(DestroyCommandPool); LOAD(AllocateCommandBuffers);
    LOAD(BeginCommandBuffer); LOAD(EndCommandBuffer); LOAD(CmdPipelineBarrier);
    LOAD(CmdClearColorImage); LOAD(QueueSubmit); LOAD(QueueWaitIdle);
    const char *iext[]={"VK_KHR_portability_enumeration","VK_KHR_surface","VK_EXT_metal_surface"};
    uint32_t ic=0;CHECK(EnumerateInstanceExtensionProperties(NULL,&ic,NULL));
    VkExtensionProperties *ip=calloc(ic,sizeof(*ip));CHECK(EnumerateInstanceExtensionProperties(NULL,&ic,ip));
    BOOL instancePortability=NO;for(uint32_t i=0;i<ic;i++)if(!strcmp(ip[i].extensionName,iext[0]))instancePortability=YES;free(ip);
    VkApplicationInfo app={.sType=VK_STRUCTURE_TYPE_APPLICATION_INFO,.pApplicationName="MetalFX offscreen bridge probe",.apiVersion=VK_API_VERSION_1_1};
    VkInstanceCreateInfo ici={.sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,.flags=instancePortability?VK_INSTANCE_CREATE_ENUMERATE_PORTABILITY_BIT_KHR:0,.pApplicationInfo=&app,.enabledExtensionCount=instancePortability?3:2,.ppEnabledExtensionNames=instancePortability?iext:iext+1};
    VkInstance inst; CHECK(CreateInstance(&ici,NULL,&inst));
    uint32_t n=1; VkPhysicalDevice pd; CHECK(EnumeratePhysicalDevices(inst,&n,&pd)); REQUIRE(n);
    uint32_t qc=0; GetPhysicalDeviceQueueFamilyProperties(pd,&qc,NULL);
    VkQueueFamilyProperties *qp=calloc(qc,sizeof(*qp)); GetPhysicalDeviceQueueFamilyProperties(pd,&qc,qp);
    uint32_t qi=0; while(qi<qc && !(qp[qi].queueFlags & VK_QUEUE_GRAPHICS_BIT)) qi++; REQUIRE(qi<qc); free(qp);
    uint32_t ec=0; CHECK(EnumerateDeviceExtensionProperties(pd,NULL,&ec,NULL));
    VkExtensionProperties *ep=calloc(ec,sizeof(*ep)); CHECK(EnumerateDeviceExtensionProperties(pd,NULL,&ec,ep));
    BOOL hasMetal=NO,hasPortability=NO;
    for(uint32_t i=0;i<ec;i++){ if(!strcmp(ep[i].extensionName,"VK_EXT_metal_objects"))hasMetal=YES; if(!strcmp(ep[i].extensionName,"VK_KHR_portability_subset"))hasPortability=YES; }
    free(ep); REQUIRE(hasMetal);
    const char *dext[]={"VK_EXT_metal_objects","VK_KHR_swapchain","VK_KHR_portability_subset"}; float priority=1;
    VkDeviceQueueCreateInfo qci={.sType=VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,.queueFamilyIndex=qi,.queueCount=1,.pQueuePriorities=&priority};
    VkDeviceCreateInfo dci={.sType=VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,.queueCreateInfoCount=1,.pQueueCreateInfos=&qci,.enabledExtensionCount=hasPortability?3:2,.ppEnabledExtensionNames=dext};
    VkDevice dev; CHECK(CreateDevice(pd,&dci,NULL,&dev)); VkQueue vq; GetDeviceQueue(dev,qi,0,&vq);
    VkExportMetalCommandQueueInfoEXT eq={.sType=VK_STRUCTURE_TYPE_EXPORT_METAL_COMMAND_QUEUE_INFO_EXT,.queue=vq};
    VkExportMetalObjectsInfoEXT eo={.sType=VK_STRUCTURE_TYPE_EXPORT_METAL_OBJECTS_INFO_EXT,.pNext=&eq}; ExportMetalObjectsEXT(dev,&eo);
    id<MTLCommandQueue> queue=eq.mtlCommandQueue; REQUIRE(queue); id<MTLDevice> device=queue.device;

    ProbeLayer *layer=[ProbeLayer layer];layer.device=device;layer.pixelFormat=MTLPixelFormatBGRA8Unorm;
    layer.bounds=CGRectMake(0,0,1512,982);layer.contentsScale=1;layer.drawableSize=CGSizeMake(1512,982);layer.framebufferOnly=NO;
    VkMetalSurfaceCreateInfoEXT sci={.sType=VK_STRUCTURE_TYPE_METAL_SURFACE_CREATE_INFO_EXT,.pLayer=layer};VkSurfaceKHR surface;CHECK(CreateMetalSurfaceEXT(inst,&sci,NULL,&surface));
    VkSwapchainKHR previous=VK_NULL_HANDLE;
    for(int phase=0;phase<2;phase++){
    if(phase){layer.bounds=CGRectMake(0,0,1280,800);}
    uint32_t displayW=phase?1280:1512,displayH=phase?800:982;
    VkSurfaceCapabilitiesKHR caps;CHECK(GetPhysicalDeviceSurfaceCapabilitiesKHR(pd,surface,&caps));
    printf("initial_surface=%ux%u\n",caps.currentExtent.width,caps.currentExtent.height);fflush(stdout);
    BOOL enabled = !(getenv("MVK_DTR_METALFX_SPATIAL") && !strcmp(getenv("MVK_DTR_METALFX_SPATIAL"),"0"));
    REQUIRE(caps.currentExtent.width==(enabled?(uint32_t)(floor(displayW*.75/2)*2):displayW) && caps.currentExtent.height==(enabled?(uint32_t)(floor(displayH*.75/2)*2):displayH));
    VkSwapchainCreateInfoKHR sc={.sType=VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR,.surface=surface,.minImageCount=3,.imageFormat=VK_FORMAT_B8G8R8A8_UNORM,.imageColorSpace=VK_COLOR_SPACE_SRGB_NONLINEAR_KHR,.imageExtent=caps.currentExtent,.imageArrayLayers=1,.imageUsage=VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT|VK_IMAGE_USAGE_TRANSFER_DST_BIT,.imageSharingMode=VK_SHARING_MODE_EXCLUSIVE,.preTransform=VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR,.compositeAlpha=VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,.presentMode=VK_PRESENT_MODE_FIFO_KHR,.clipped=VK_TRUE};
    sc.oldSwapchain=previous;
    VkSwapchainKHR swap;CHECK(CreateSwapchainKHR(dev,&sc,NULL,&swap));
    if(previous)DestroySwapchainKHR(dev,previous,NULL);
    uint32_t count=0;CHECK(GetSwapchainImagesKHR(dev,swap,&count,NULL));VkImage *images=calloc(count,sizeof(*images));CHECK(GetSwapchainImagesKHR(dev,swap,&count,images));
    VkExportMetalTextureInfoEXT et={.sType=VK_STRUCTURE_TYPE_EXPORT_METAL_TEXTURE_INFO_EXT,.image=images[0],.plane=VK_IMAGE_ASPECT_COLOR_BIT};eo.pNext=&et;ExportMetalObjectsEXT(dev,&eo);
    REQUIRE(et.mtlTexture.width==sc.imageExtent.width && et.mtlTexture.height==sc.imageExtent.height);
    REQUIRE(layer.drawableSize.width==displayW && layer.drawableSize.height==displayH);
    CHECK(GetPhysicalDeviceSurfaceCapabilitiesKHR(pd,surface,&caps));REQUIRE(caps.currentExtent.width==sc.imageExtent.width && caps.currentExtent.height==sc.imageExtent.height);
    VkCommandPoolCreateInfo pci={.sType=VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,.flags=VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,.queueFamilyIndex=qi};VkCommandPool pool;CHECK(CreateCommandPool(dev,&pci,NULL,&pool));
    VkCommandBufferAllocateInfo cai={.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,.commandPool=pool,.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY,.commandBufferCount=1};VkCommandBuffer cb;CHECK(AllocateCommandBuffers(dev,&cai,&cb));
    VkFenceCreateInfo fci={.sType=VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};VkFence fence;CHECK(CreateFence(dev,&fci,NULL,&fence));
    for(int f=0;f<12;f++){
      uint32_t index;CHECK(AcquireNextImageKHR(dev,swap,5000000000ULL,VK_NULL_HANDLE,fence,&index));CHECK(WaitForFences(dev,1,&fence,VK_TRUE,5000000000ULL));CHECK(ResetFences(dev,1,&fence));
      CHECK(ResetCommandBuffer(cb,0));VkCommandBufferBeginInfo bi={.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};CHECK(BeginCommandBuffer(cb,&bi));
      VkImageSubresourceRange range={VK_IMAGE_ASPECT_COLOR_BIT,0,1,0,1};
      VkImageMemoryBarrier barrier={.sType=VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,.oldLayout=VK_IMAGE_LAYOUT_UNDEFINED,.newLayout=VK_IMAGE_LAYOUT_GENERAL,.srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,.image=images[index],.subresourceRange=range,.dstAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT};
      CmdPipelineBarrier(cb,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,0,0,NULL,0,NULL,1,&barrier);
      VkClearColorValue color={.float32={0.5,0.25,0.75,1}};CmdClearColorImage(cb,images[index],VK_IMAGE_LAYOUT_GENERAL,&color,1,&range);
      barrier.oldLayout=VK_IMAGE_LAYOUT_GENERAL;barrier.newLayout=VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;barrier.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;barrier.dstAccessMask=0;
      CmdPipelineBarrier(cb,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT,0,0,NULL,0,NULL,1,&barrier);CHECK(EndCommandBuffer(cb));
      VkSubmitInfo si={.sType=VK_STRUCTURE_TYPE_SUBMIT_INFO,.commandBufferCount=1,.pCommandBuffers=&cb};CHECK(QueueSubmit(vq,1,&si,VK_NULL_HANDLE));CHECK(QueueWaitIdle(vq));
      VkPresentInfoKHR present={.sType=VK_STRUCTURE_TYPE_PRESENT_INFO_KHR,.swapchainCount=1,.pSwapchains=&swap,.pImageIndices=&index};CHECK(QueuePresentKHR(vq,&present));CHECK(QueueWaitIdle(vq));
      id<MTLTexture> presented=layer.lastDrawable.texture;REQUIRE(presented && presented.width==displayW && presented.height==displayH);
      NSUInteger rb=((displayW*4+255)/256)*256;id<MTLBuffer> buf=[device newBufferWithLength:rb*displayH options:MTLResourceStorageModeShared];
      id<MTLCommandBuffer> read=[queue commandBuffer];id<MTLBlitCommandEncoder> be=[read blitCommandEncoder];
      [be copyFromTexture:presented sourceSlice:0 sourceLevel:0 sourceOrigin:MTLOriginMake(0,0,0) sourceSize:MTLSizeMake(displayW,displayH,1) toBuffer:buf destinationOffset:0 destinationBytesPerRow:rb destinationBytesPerImage:rb*displayH];[be endEncoding];[read commit];[read waitUntilCompleted];REQUIRE(!read.error);
      unsigned char *pixel=(unsigned char *)buf.contents+(displayH/2)*rb+(displayW/2)*4;
      REQUIRE(abs(pixel[0]-191)<=3 && abs(pixel[1]-64)<=3 && abs(pixel[2]-128)<=3 && pixel[3]>=250);[buf release];
    }
    printf("swapchain_frames=12 input=%ux%u display=%.0fx%.0f metalfx=%s\n",sc.imageExtent.width,sc.imageExtent.height,layer.drawableSize.width,layer.drawableSize.height,enabled?"on":"off");
    DestroyFence(dev,fence,NULL);DestroyCommandPool(dev,pool,NULL);free(images);previous=swap;
    }
    layer.lastDrawable=nil;DestroySwapchainKHR(dev,previous,NULL);DestroySurfaceKHR(inst,surface,NULL);DestroyDevice(dev,NULL);DestroyInstance(inst,NULL);dlclose(lib);return 0;
 }
}
