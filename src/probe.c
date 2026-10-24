#define VK_NO_PROTOTYPES
#include "mvk_private_api.h"
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/sysctl.h>

/* Read-only ABI/config/device probe; never opens a Wine prefix or a game. */
int main(int argc, char **argv) {
    if (argc != 2) { fprintf(stderr, "usage: probe /absolute/libMoltenVK.dylib\n"); return 2; }
    int translated = 0; size_t n = sizeof(translated);
    sysctlbyname("sysctl.proc_translated", &translated, &n, NULL, 0);
    printf("process_translated=%d\n", translated);
    void *h = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!h) { fprintf(stderr, "dlopen: %s\n", dlerror()); return 3; }
#define GET(type, var, name) type var = (type)dlsym(h, name); if (!var) { fprintf(stderr,"missing %s\n",name); return 4; }
    GET(PFN_vkGetInstanceProcAddr, gpa, "vkGetInstanceProcAddr");
    GET(PFN_vkEnumerateInstanceVersion, version, "vkEnumerateInstanceVersion");
    GET(PFN_vkGetMoltenVKConfigurationMVK, config, "vkGetMoltenVKConfigurationMVK");
    Dl_info info = {0}; dladdr((void *)gpa, &info);
    printf("loaded_image=%s\n", info.dli_fname);
    uint32_t v = 0; if (version(&v) != VK_SUCCESS) return 5;
    printf("vulkan=%u.%u.%u\n", VK_VERSION_MAJOR(v), VK_VERSION_MINOR(v), VK_VERSION_PATCH(v));
    MVKConfiguration c = {0}; n = sizeof(c);
    VkResult r = config(VK_NULL_HANDLE, &c, &n);
    if ((r != VK_SUCCESS && r != VK_INCOMPLETE) || n < offsetof(MVKConfiguration, shouldMaximizeConcurrentCompilation) + sizeof(VkBool32)) return 6;
    printf("config_bytes=%zu compression=%u concurrent=%u\n", n, c.shaderSourceCompressionAlgorithm, c.shouldMaximizeConcurrentCompilation);
    const char *e = getenv("MVK_CONFIG_SHADER_COMPRESSION_ALGORITHM");
    if (e && c.shaderSourceCompressionAlgorithm != (unsigned)atoi(e)) return 7;
    e = getenv("MVK_CONFIG_SHOULD_MAXIMIZE_CONCURRENT_COMPILATION");
    if (e && c.shouldMaximizeConcurrentCompilation != (unsigned)atoi(e)) return 8;
    PFN_vkCreateInstance create = (PFN_vkCreateInstance)gpa(NULL, "vkCreateInstance");
    if (!create) return 9;
    VkApplicationInfo ai = { .sType = VK_STRUCTURE_TYPE_APPLICATION_INFO, .pApplicationName = "Detroit ABI probe", .apiVersion = VK_API_VERSION_1_1 };
    VkInstanceCreateInfo ci = { .sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO, .pApplicationInfo = &ai };
    VkInstance instance = VK_NULL_HANDLE;
    r = create(&ci, NULL, &instance); printf("create_instance=%d\n", r); if (r) return 10;
    PFN_vkEnumeratePhysicalDevices enumerate = (PFN_vkEnumeratePhysicalDevices)gpa(instance, "vkEnumeratePhysicalDevices");
    PFN_vkGetPhysicalDeviceProperties properties = (PFN_vkGetPhysicalDeviceProperties)gpa(instance, "vkGetPhysicalDeviceProperties");
    PFN_vkDestroyInstance destroy = (PFN_vkDestroyInstance)gpa(instance, "vkDestroyInstance");
    if (!enumerate || !properties || !destroy) return 11;
    uint32_t count = 0; r = enumerate(instance, &count, NULL);
    printf("enumerate=%d physical_devices=%u\n", r, count);
    if (r || !count) { destroy(instance, NULL); return 12; }
    VkPhysicalDevice *devices = calloc(count, sizeof(*devices));
    if (!devices) { destroy(instance, NULL); return 13; }
    r = enumerate(instance, &count, devices);
    if (!r && count) { VkPhysicalDeviceProperties p; properties(devices[0], &p); printf("gpu=%s\n", p.deviceName); }
    free(devices); destroy(instance, NULL);
    /* Do not unload ObjC/Metal code. The process is the lifetime boundary. */
    return r ? 14 : 0;
}
