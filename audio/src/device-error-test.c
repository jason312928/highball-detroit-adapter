#define COBJMACROS
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <initguid.h>
#include <mmdeviceapi.h>
#include <audioclient.h>
#include <devpkey.h>
#include <ks.h>
#include <ksmedia.h>
#include "FAudio.h"
FAudioGUID DATAFORMAT_SUBTYPE_PCM={1,0,0x10,{0x80,0,0,0xaa,0,0x38,0x9b,0x71}};
#define FAudio_memset memset
#define FAudio_memcpy memcpy
#define FAudio_assert assert
static int stage, platform_refs, device_refs, property_refs, client_refs;
static IMMDevice device;
static IPropertyStore properties;
static IAudioClient client;
static ULONG WINAPI device_release(IMMDevice *p) { return --device_refs; }
static ULONG WINAPI property_release(IPropertyStore *p) { return --property_refs; }
static ULONG WINAPI client_release(IAudioClient *p) { return --client_refs; }
static HRESULT WINAPI open_properties(IMMDevice *p,DWORD access,IPropertyStore **out) {
 if(stage==2)return E_FAIL;*out=&properties;++property_refs;return S_OK;
}
static HRESULT WINAPI property_value(IPropertyStore *p,REFPROPERTYKEY key,PROPVARIANT *out) {
 if(stage==3)return E_FAIL;
 out->vt=VT_LPWSTR;out->pwszVal=CoTaskMemAlloc(32*sizeof(WCHAR));lstrcpyW(out->pwszVal,L"Test output");return S_OK;
}
static HRESULT WINAPI get_id(IMMDevice *p,LPWSTR *out) {
 if(stage==4)return E_FAIL;*out=CoTaskMemAlloc(32*sizeof(WCHAR));lstrcpyW(*out,L"test-device");return S_OK;
}
static HRESULT WINAPI activate(IMMDevice *p,REFIID iid,DWORD cls,PROPVARIANT *a,void **out) {
 if(stage==5)return E_FAIL;*out=&client;++client_refs;return S_OK;
}
static HRESULT WINAPI mix_format(IAudioClient *p,WAVEFORMATEX **out) {
 *out=NULL;if(stage==6)return E_FAIL;if(stage==7)return S_OK;
 *out=CoTaskMemAlloc(sizeof(**out));memset(*out,0,sizeof(**out));
 (*out)->wFormatTag=WAVE_FORMAT_PCM;(*out)->nChannels=2;(*out)->nSamplesPerSec=48000;
 (*out)->nAvgBytesPerSec=192000;(*out)->nBlockAlign=4;(*out)->wBitsPerSample=16;return S_OK;
}
static IMMDeviceVtbl device_vt={.Release=device_release,.Activate=activate,.OpenPropertyStore=open_properties,.GetId=get_id};
static IPropertyStoreVtbl properties_vt={.Release=property_release,.GetValue=property_value};
static IAudioClientVtbl client_vt={.Release=client_release,.GetMixFormat=mix_format};
static void FAudio_PlatformAddRef(void) { ++platform_refs; }
static void FAudio_PlatformRelease(void) { --platform_refs; }
static uint32_t FAudio_PlatformGetDeviceCount(void) { return 1; }
static HRESULT FAudio_OpenDevice(uint32_t index,IMMDevice **out) {
 if(stage==1)return E_FAIL;*out=&device;++device_refs;return S_OK;
}
static DWORD GetMask(unsigned channels) { return channels==2?SPEAKER_FRONT_LEFT|SPEAKER_FRONT_RIGHT:0; }
#ifndef TEST_FUNCTION_FILE
#define TEST_FUNCTION_FILE "device-details-after.inc"
#endif
#include TEST_FUNCTION_FILE
static LONG CALLBACK exception_handler(EXCEPTION_POINTERS *p) {
 if(p->ExceptionRecord->ExceptionCode==0xc0000005) {
  puts("DTR_TEST baseline reproduced access violation with failed GetMixFormat and NULL format");fflush(stdout);ExitProcess(99);
 }
 return EXCEPTION_CONTINUE_SEARCH;
}
int main(int argc,char **argv) {
 device.lpVtbl=&device_vt;properties.lpVtbl=&properties_vt;client.lpVtbl=&client_vt;
 AddVectoredExceptionHandler(1,exception_handler);
 FAudioDeviceDetails details;
 if(argc>1) {stage=6;FAudio_PlatformGetDeviceDetails(0,&details);return 98;}
 for(stage=0;stage<=7;stage++) {
  platform_refs=device_refs=property_refs=client_refs=0;
  uint32_t result=FAudio_PlatformGetDeviceDetails(0,&details);
  if((stage==0 && result!=0)||(stage!=0 && result!=(uint32_t)E_FAIL))return 10+stage;
  if(platform_refs||device_refs||property_refs||client_refs)return 30+stage;
  if(stage==0 && (details.OutputFormat.Format.nChannels!=2||details.OutputFormat.Format.nSamplesPerSec!=48000))return 50;
  printf("DTR_TEST stage=%d hr=0x%08lx resources=balanced PASS\n",stage,(unsigned long)result);
 }
 if(FAudio_PlatformGetDeviceDetails(1,&details)!=FAUDIO_E_INVALID_CALL||platform_refs)return 60;
 puts("DTR_TEST invalid index PASS");return 0;
}
