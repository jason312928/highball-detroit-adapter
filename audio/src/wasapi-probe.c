#define COBJMACROS
#include <windows.h>
#include <stdio.h>
#include <initguid.h>
#include <mmdeviceapi.h>
#include <audioclient.h>
#include <functiondiscoverykeys_devpkey.h>
static void inspect(IMMDevice *device, const char *kind, unsigned index) {
 LPWSTR id=NULL;IPropertyStore *props=NULL;PROPVARIANT name;IAudioClient *client=NULL;WAVEFORMATEX *format=NULL;
 IMMDevice_GetId(device,&id);PropVariantInit(&name);
 if(SUCCEEDED(IMMDevice_OpenPropertyStore(device,STGM_READ,&props))) { IPropertyStore_GetValue(props,&PKEY_Device_FriendlyName,&name);IPropertyStore_Release(props); }
 HRESULT active=IMMDevice_Activate(device,&IID_IAudioClient,CLSCTX_ALL,NULL,(void**)&client);
 HRESULT mix=FAILED(active)?active:IAudioClient_GetMixFormat(client,&format);
 char label[2048]="?", identifier[1024]="?";
 if(name.vt==VT_LPWSTR && name.pwszVal)WideCharToMultiByte(CP_UTF8,0,name.pwszVal,-1,label,sizeof(label),NULL,NULL);
 if(id)WideCharToMultiByte(CP_UTF8,0,id,-1,identifier,sizeof(identifier),NULL,NULL);
 printf("DTR_AUDIO %s[%u] name=%s activate=0x%08lx mix=0x%08lx pointer=%s",kind,index,label,(unsigned long)active,(unsigned long)mix,format?"valid":"NULL");
 if(SUCCEEDED(mix)&&format)printf(" channels=%u rate=%lu bits=%u",format->nChannels,(unsigned long)format->nSamplesPerSec,format->wBitsPerSample);
 printf(" id=%s\n",identifier);fflush(stdout);
 if(format)CoTaskMemFree(format);if(client)IAudioClient_Release(client);PropVariantClear(&name);CoTaskMemFree(id);
}
int main(void) {
 HRESULT hr=CoInitializeEx(NULL,COINIT_MULTITHREADED);IMMDeviceEnumerator *enumerator=NULL;IMMDeviceCollection *devices=NULL;IMMDevice *device=NULL;UINT count=0;
 printf("DTR_AUDIO CoInitialize=0x%08lx\n",(unsigned long)hr);
 hr=CoCreateInstance(&CLSID_MMDeviceEnumerator,NULL,CLSCTX_ALL,&IID_IMMDeviceEnumerator,(void**)&enumerator);
 if(FAILED(hr))return 1;
 hr=IMMDeviceEnumerator_GetDefaultAudioEndpoint(enumerator,eRender,eConsole,&device);
 if(SUCCEEDED(hr)) { inspect(device,"default",0);IMMDevice_Release(device); }
 else printf("DTR_AUDIO default error=0x%08lx\n",(unsigned long)hr);
 hr=IMMDeviceEnumerator_EnumAudioEndpoints(enumerator,eRender,DEVICE_STATE_ACTIVE,&devices);
 if(SUCCEEDED(hr)) {
  IMMDeviceCollection_GetCount(devices,&count);
  for(UINT i=0;i<count;i++)if(SUCCEEDED(IMMDeviceCollection_Item(devices,i,&device))) {inspect(device,"active",i);IMMDevice_Release(device);}
  IMMDeviceCollection_Release(devices);
 }
 IMMDeviceEnumerator_Release(enumerator);CoUninitialize();return 0;
}
