#define COBJMACROS
#include <windows.h>
#include <initguid.h>
#include <audioclient.h>
#include <mmdeviceapi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

typedef struct FAudio { int active; } FAudio;
#define FAudio_free free
#define FAudio_zero(p,n) memset(p,0,n)
static void FAudio_set_thread_name(const char *n) { (void)n; }
static void FAudio_INTERNAL_UpdateEngine(FAudio *a, float *b) { (void)a; (void)b; }
static int step, scenario, created, released, rebound, unavailable, started, updates;
static BYTE samples[48000];
static IMMDevice devices[2];
static IMMDeviceEnumerator enumerator;
static IAudioRenderClient renderer;
struct fake_client { IAudioClient iface; int device, serial; };

static HRESULT WINAPI render_get(IAudioRenderClient *p, UINT32 n, BYTE **b) { *b=samples; updates++; return S_OK; }
static HRESULT WINAPI render_release(IAudioRenderClient *p, UINT32 n, DWORD f) { return S_OK; }
static ULONG WINAPI render_unref(IAudioRenderClient *p) { return 1; }
static IAudioRenderClientVtbl render_vtbl={.Release=render_unref,.GetBuffer=render_get,.ReleaseBuffer=render_release};
static HRESULT WINAPI client_init(IAudioClient *p,AUDCLNT_SHAREMODE m,DWORD f,REFERENCE_TIME d,REFERENCE_TIME per,const WAVEFORMATEX *fmt,LPCGUID g) {
 assert(m==AUDCLNT_SHAREMODE_SHARED && (f&AUDCLNT_STREAMFLAGS_AUTOCONVERTPCM));
 assert(fmt->nChannels==2 && fmt->nSamplesPerSec==48000);
 return scenario==2 && step==1?E_FAIL:S_OK;
}
static ULONG WINAPI client_unref(IAudioClient *p) { released++; free(p); return 0; }
static HRESULT WINAPI client_size(IAudioClient *p,UINT32 *frames) { *frames=1440; return scenario==5?E_FAIL:S_OK; }
static HRESULT WINAPI client_padding(IAudioClient *p,UINT32 *frames) {
 struct fake_client *c=(struct fake_client *)p; *frames=0;
 if((scenario==3 && step==1)||(scenario==4 && step>=1 && step<=2))return AUDCLNT_E_DEVICE_INVALIDATED;
 if(scenario==1 && step>=1 && c->device==0)return AUDCLNT_E_DEVICE_INVALIDATED;
 return S_OK;
}
static HRESULT WINAPI client_start(IAudioClient *p) { started++; return scenario==6 && step==1?E_FAIL:S_OK; }
static HRESULT WINAPI client_stop(IAudioClient *p) { return scenario==3?AUDCLNT_E_DEVICE_INVALIDATED:S_OK; }
static HRESULT WINAPI client_event(IAudioClient *p,HANDLE h) { return S_OK; }
static HRESULT WINAPI client_service(IAudioClient *p,REFIID i,void **r) { *r=&renderer; return S_OK; }
static IAudioClientVtbl client_vtbl={.Release=client_unref,.Initialize=client_init,.GetBufferSize=client_size,
 .GetCurrentPadding=client_padding,.Start=client_start,.Stop=client_stop,.SetEventHandle=client_event,.GetService=client_service};
static HRESULT WINAPI device_id(IMMDevice *p,LPWSTR *id) {
 const WCHAR *n=p==&devices[0]?L"speakers":L"headphones";size_t bytes=(wcslen(n)+1)*sizeof(WCHAR);
 *id=CoTaskMemAlloc(bytes);memcpy(*id,n,bytes);return S_OK;
}
static ULONG WINAPI device_unref(IMMDevice *p) { return 1; }
static HRESULT WINAPI device_activate(IMMDevice *p,REFIID i,DWORD d,PROPVARIANT *v,void **r) {
 struct fake_client *c=calloc(1,sizeof(*c)); c->iface.lpVtbl=&client_vtbl;c->device=p==&devices[1];c->serial=++created;*r=c;return S_OK;
}
static IMMDeviceVtbl device_vtbl={.Release=device_unref,.GetId=device_id,.Activate=device_activate};
static ULONG WINAPI enum_unref(IMMDeviceEnumerator *p) { return 1; }
static HRESULT WINAPI enum_default(IMMDeviceEnumerator *p,EDataFlow f,ERole r,IMMDevice **d) {
 if(scenario==4 && step>=1 && step<=2){*d=NULL;return E_NOTFOUND;}
 *d=&devices[(scenario==1 || scenario==2 || scenario==6)&&step>=1?1:0];return S_OK;
}
static IMMDeviceEnumeratorVtbl enum_vtbl={.Release=enum_unref,.GetDefaultAudioEndpoint=enum_default};
static HRESULT fake_create(REFCLSID c,LPUNKNOWN u,DWORD d,REFIID r,LPVOID *p){*p=&enumerator;return S_OK;}
static DWORD fake_wait_one(HANDLE h,DWORD ms){return step>=6?WAIT_OBJECT_0:WAIT_TIMEOUT;}
static DWORD fake_wait_many(DWORD n,const HANDLE *h,BOOL all,DWORD ms){assert(ms!=INFINITE);step++;return WAIT_OBJECT_0;}
static ULONGLONG fake_ticks(void){return step*600;}
static void fake_debug(const char *s){if(strstr(s,"rebound"))rebound++;if(strstr(s,"unavailable"))unavailable++;}
#define CoCreateInstance fake_create
#define WaitForSingleObject fake_wait_one
#define WaitForMultipleObjects fake_wait_many
#define GetTickCount64 fake_ticks
#define OutputDebugStringA fake_debug
#include "routing-under-test.inc"

static void run(int which,int follow) {
 struct FAudioAudioClientThreadArgs *args=calloc(1,sizeof(*args));
 struct FAudioWin32PlatformData data={0};FAudio audio={0};
 step=0;scenario=which;created=released=rebound=unavailable=started=updates=0;
 args->format.Format.nChannels=2;args->format.Format.nSamplesPerSec=48000;args->format.Format.nBlockAlign=8;
 args->format.Format.wFormatTag=WAVE_FORMAT_IEEE_FLOAT;args->format.Format.wBitsPerSample=32;
 args->audio=&audio;args->platform=&data;args->duration=100000;args->updateSize=480;args->followDefault=follow;
 args->events[0]=(HANDLE)1;args->events[1]=(HANDLE)2;
 device_id(&devices[0],&args->endpointId);
 assert(SUCCEEDED(FAudio_CreateAudioClient(&devices[0],&args->format,args->events[0],args->duration,&args->client)));
 data.client=args->client;
 FAudio_AudioClientThread(args);
 assert(created==released && data.client==NULL);
 if(which==0)assert(created==1 && rebound==0);
 if(which==1 && follow)assert(created==2 && rebound==1);
 if(which==1 && !follow)assert(created==1 && rebound==0);
 if(which==6)assert(created==3 && rebound==1);
 if(which==2)assert(created==3 && rebound==1);
 if(which==3)assert(rebound>=1 && unavailable>=1);
 if(which==4)assert(rebound==1 && unavailable>=1);
 if(which==5)assert(created==released && started==0);
 printf("routing case=%d follow=%d clients=%d balanced=yes rebinds=%d PASS\n",which,follow,created,rebound);
}
int main(void){
 devices[0].lpVtbl=devices[1].lpVtbl=&device_vtbl;renderer.lpVtbl=&render_vtbl;enumerator.lpVtbl=&enum_vtbl;
 run(0,1);run(1,1);run(1,0);run(2,1);run(3,1);run(4,1);run(5,1);run(6,1);return 0;
}
