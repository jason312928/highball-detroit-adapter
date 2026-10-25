#define WIN32_LEAN_AND_MEAN
#define VK_NO_PROTOTYPES
#define VK_USE_PLATFORM_WIN32_KHR
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <vulkan/vulkan.h>
#define CHECK(x) do { VkResult r=(x);if(r!=VK_SUCCESS){fprintf(stderr,"%s: %d line %d\n",#x,r,__LINE__);return 2;} }while(0)
#define REQUIRE(x) do {if(!(x)){fprintf(stderr,"%s failed line %d (winerr=%lu)\n",#x,__LINE__,GetLastError());return 3;}}while(0)
#define LOAD(n) PFN_vk##n n=(PFN_vk##n)GetInstanceProcAddr(inst,"vk"#n); REQUIRE(n)

int main(void) {
 HMODULE vulkan=LoadLibraryW(L"vulkan-1.dll");REQUIRE(vulkan);
 PFN_vkGetInstanceProcAddr GetInstanceProcAddr=(PFN_vkGetInstanceProcAddr)GetProcAddress(vulkan,"vkGetInstanceProcAddr");REQUIRE(GetInstanceProcAddr);
 PFN_vkCreateInstance CreateInstance=(PFN_vkCreateInstance)GetInstanceProcAddr(VK_NULL_HANDLE,"vkCreateInstance");REQUIRE(CreateInstance);
 const char *extensions[]={"VK_KHR_surface","VK_KHR_win32_surface"};
 VkApplicationInfo app={.sType=VK_STRUCTURE_TYPE_APPLICATION_INFO,.pApplicationName="Detroit MetalFX WSI regression probe",.apiVersion=VK_API_VERSION_1_0};
 VkInstanceCreateInfo ci={.sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,.pApplicationInfo=&app,.enabledExtensionCount=2,.ppEnabledExtensionNames=extensions};VkInstance inst;CHECK(CreateInstance(&ci,NULL,&inst));
 LOAD(DestroyInstance);LOAD(EnumeratePhysicalDevices);LOAD(GetPhysicalDeviceQueueFamilyProperties);LOAD(CreateDevice);LOAD(DestroyDevice);LOAD(GetDeviceQueue);
 LOAD(CreateWin32SurfaceKHR);LOAD(DestroySurfaceKHR);LOAD(GetPhysicalDeviceSurfaceCapabilitiesKHR);LOAD(CreateSwapchainKHR);LOAD(DestroySwapchainKHR);LOAD(GetSwapchainImagesKHR);LOAD(AcquireNextImageKHR);LOAD(QueuePresentKHR);
 LOAD(CreateCommandPool);LOAD(DestroyCommandPool);LOAD(AllocateCommandBuffers);LOAD(ResetCommandBuffer);LOAD(BeginCommandBuffer);LOAD(EndCommandBuffer);LOAD(CmdPipelineBarrier);LOAD(CmdClearColorImage);LOAD(QueueSubmit);LOAD(QueueWaitIdle);
 LOAD(CreateFence);LOAD(DestroyFence);LOAD(WaitForFences);LOAD(ResetFences);
 uint32_t n=1;VkPhysicalDevice pd;CHECK(EnumeratePhysicalDevices(inst,&n,&pd));REQUIRE(n);
 uint32_t count=0;GetPhysicalDeviceQueueFamilyProperties(pd,&count,NULL);VkQueueFamilyProperties *qps=calloc(count,sizeof(*qps));GetPhysicalDeviceQueueFamilyProperties(pd,&count,qps);uint32_t qi=0;while(qi<count&&!(qps[qi].queueFlags&VK_QUEUE_GRAPHICS_BIT))qi++;REQUIRE(qi<count);free(qps);
 float priority=1;VkDeviceQueueCreateInfo qci={.sType=VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,.queueFamilyIndex=qi,.queueCount=1,.pQueuePriorities=&priority};const char *de[]={"VK_KHR_swapchain"};
 VkDeviceCreateInfo dci={.sType=VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,.queueCreateInfoCount=1,.pQueueCreateInfos=&qci,.enabledExtensionCount=1,.ppEnabledExtensionNames=de};VkDevice dev;CHECK(CreateDevice(pd,&dci,NULL,&dev));VkQueue queue;GetDeviceQueue(dev,qi,0,&queue);
 SetProcessDPIAware();HINSTANCE hi=GetModuleHandleW(NULL);WNDCLASSW wc={.lpfnWndProc=DefWindowProcW,.hInstance=hi,.lpszClassName=L"DetroitMetalFXWSIProbe"};REQUIRE(RegisterClassW(&wc));
 RECT wr={0,0,1024,576};AdjustWindowRect(&wr,WS_OVERLAPPEDWINDOW,FALSE);HWND window=CreateWindowExW(0,wc.lpszClassName,L"MetalFX offscreen regression probe",WS_OVERLAPPEDWINDOW,-30000,-30000,wr.right-wr.left,wr.bottom-wr.top,NULL,NULL,hi,NULL);REQUIRE(window);ShowWindow(window,SW_SHOWNOACTIVATE);
 HDC dc=GetDC(window);SIZE text;REQUIRE(GetTextExtentPoint32W(dc,L"MetalFX",7,&text)&&text.cx>0&&text.cy>0);ReleaseDC(window,dc);printf("font_metrics_ok=1\n");fflush(stdout);
 VkWin32SurfaceCreateInfoKHR sci={.sType=VK_STRUCTURE_TYPE_WIN32_SURFACE_CREATE_INFO_KHR,.hinstance=hi,.hwnd=window};VkSurfaceKHR surface;CHECK(CreateWin32SurfaceKHR(inst,&sci,NULL,&surface));
 VkCommandPoolCreateInfo pci={.sType=VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,.flags=VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,.queueFamilyIndex=qi};VkCommandPool pool;CHECK(CreateCommandPool(dev,&pci,NULL,&pool));
 VkCommandBufferAllocateInfo cai={.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,.commandPool=pool,.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY,.commandBufferCount=1};VkCommandBuffer cb;CHECK(AllocateCommandBuffers(dev,&cai,&cb));VkFenceCreateInfo fci={.sType=VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};VkFence fence;CHECK(CreateFence(dev,&fci,NULL,&fence));
 VkSwapchainKHR previous=VK_NULL_HANDLE;
 BOOL enabled=GetEnvironmentVariableW(L"MVK_DTR_METALFX_SPATIAL",NULL,0)==0; /* Off test explicitly sets 0. */
 for(int phase=0;phase<3;phase++) {
  UINT w=phase==0?1024:(phase==1?1280:960),h=phase==0?576:(phase==1?720:600);wr=(RECT){0,0,w,h};AdjustWindowRect(&wr,WS_OVERLAPPEDWINDOW,FALSE);SetWindowPos(window,NULL,-30000,-30000,wr.right-wr.left,wr.bottom-wr.top,SWP_NOACTIVATE|SWP_NOZORDER);
  RECT actual;GetClientRect(window,&actual);printf("actual_client=%ldx%ld\n",actual.right,actual.bottom);fflush(stdout);
  VkSurfaceCapabilitiesKHR caps;uint32_t ew=enabled&&phase?((w*3/4)/2)*2:w,eh=enabled&&phase?((h*3/4)/2)*2:h;
  for(int attempt=0;attempt<40;attempt++){MSG msg;while(PeekMessageW(&msg,NULL,0,0,PM_REMOVE)){TranslateMessage(&msg);DispatchMessageW(&msg);}CHECK(GetPhysicalDeviceSurfaceCapabilitiesKHR(pd,surface,&caps));if(caps.currentExtent.width==ew&&caps.currentExtent.height==eh)break;Sleep(25);}
  printf("phase=%d window=%ux%u caps=%ux%u expected=%ux%u\n",phase,w,h,caps.currentExtent.width,caps.currentExtent.height,ew,eh);fflush(stdout);REQUIRE(caps.currentExtent.width==ew&&caps.currentExtent.height==eh);REQUIRE(caps.minImageExtent.width==ew&&caps.maxImageExtent.width==ew);
  VkSwapchainCreateInfoKHR sc={.sType=VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR,.surface=surface,.minImageCount=3,.imageFormat=VK_FORMAT_B8G8R8A8_UNORM,.imageColorSpace=VK_COLOR_SPACE_SRGB_NONLINEAR_KHR,.imageExtent=phase==0?(VkExtent2D){w,h}:caps.currentExtent,.imageArrayLayers=1,.imageUsage=VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT|VK_IMAGE_USAGE_TRANSFER_DST_BIT,.imageSharingMode=VK_SHARING_MODE_EXCLUSIVE,.preTransform=VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR,.compositeAlpha=VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,.presentMode=VK_PRESENT_MODE_FIFO_KHR,.clipped=VK_TRUE,.oldSwapchain=previous};
  VkSwapchainKHR swap;CHECK(CreateSwapchainKHR(dev,&sc,NULL,&swap));if(previous)DestroySwapchainKHR(dev,previous,NULL);count=0;CHECK(GetSwapchainImagesKHR(dev,swap,&count,NULL));VkImage *images=calloc(count,sizeof(*images));CHECK(GetSwapchainImagesKHR(dev,swap,&count,images));
  for(int f=0;f<8;f++) {
   uint32_t index;CHECK(AcquireNextImageKHR(dev,swap,5000000000ULL,VK_NULL_HANDLE,fence,&index));CHECK(WaitForFences(dev,1,&fence,VK_TRUE,5000000000ULL));CHECK(ResetFences(dev,1,&fence));CHECK(ResetCommandBuffer(cb,0));VkCommandBufferBeginInfo bi={.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};CHECK(BeginCommandBuffer(cb,&bi));
   VkImageSubresourceRange range={VK_IMAGE_ASPECT_COLOR_BIT,0,1,0,1};VkImageMemoryBarrier b={.sType=VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,.oldLayout=VK_IMAGE_LAYOUT_UNDEFINED,.newLayout=VK_IMAGE_LAYOUT_GENERAL,.srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,.image=images[index],.subresourceRange=range,.dstAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT};CmdPipelineBarrier(cb,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,0,0,NULL,0,NULL,1,&b);
   VkClearColorValue color={.float32={.5,.25,.75,1}};CmdClearColorImage(cb,images[index],VK_IMAGE_LAYOUT_GENERAL,&color,1,&range);b.oldLayout=VK_IMAGE_LAYOUT_GENERAL;b.newLayout=VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;b.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;b.dstAccessMask=0;CmdPipelineBarrier(cb,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT,0,0,NULL,0,NULL,1,&b);CHECK(EndCommandBuffer(cb));VkSubmitInfo si={.sType=VK_STRUCTURE_TYPE_SUBMIT_INFO,.commandBufferCount=1,.pCommandBuffers=&cb};CHECK(QueueSubmit(queue,1,&si,VK_NULL_HANDLE));CHECK(QueueWaitIdle(queue));
   VkResult per;VkPresentInfoKHR pi={.sType=VK_STRUCTURE_TYPE_PRESENT_INFO_KHR,.swapchainCount=1,.pSwapchains=&swap,.pImageIndices=&index,.pResults=&per};CHECK(QueuePresentKHR(queue,&pi));REQUIRE(per==VK_SUCCESS);CHECK(QueueWaitIdle(queue));
  }
  free(images);previous=swap;printf("phase=%d frames=8 input=%ux%u ok\n",phase,sc.imageExtent.width,sc.imageExtent.height);fflush(stdout);
 }
 CHECK(QueueWaitIdle(queue));DestroySwapchainKHR(dev,previous,NULL);DestroyFence(dev,fence,NULL);DestroyCommandPool(dev,pool,NULL);DestroySurfaceKHR(inst,surface,NULL);DestroyDevice(dev,NULL);DestroyInstance(inst,NULL);DestroyWindow(window);printf("WINDOWS_WSI_PROBE_PASS\n");return 0;
}
