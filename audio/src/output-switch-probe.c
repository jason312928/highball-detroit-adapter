/* Run only in a disposable Wine test prefix. Temporarily overrides its Windows output preference and restores it; never selects a macOS system output. Keep both physical endpoints connected throughout. */
#define COBJMACROS
#include <windows.h>
#include <initguid.h>
#include <mmdeviceapi.h>
#include <xaudio2.h>
#include <devpkey.h>
#include <stdio.h>
#include <stdlib.h>
#include <wchar.h>
typedef HRESULT (WINAPI *create_fn)(IXAudio2**,UINT32,XAUDIO2_PROCESSOR);
static short silence[48000*2];
static void describe(IMMDevice *device,int phase){IPropertyStore *ps=NULL;PROPVARIANT v;PropVariantInit(&v);if(SUCCEEDED(IMMDevice_OpenPropertyStore(device,STGM_READ,&ps))){if(SUCCEEDED(IPropertyStore_GetValue(ps,(const PROPERTYKEY*)&DEVPKEY_Device_FriendlyName,&v))&&v.vt==VT_LPWSTR)printf("DTR_SWITCH phase=%d default_kind=%s\n",phase,wcsstr(v.pwszVal,L"AirPods")?"AirPods":"other");PropVariantClear(&v);IPropertyStore_Release(ps);}}

int main(void){
 setvbuf(stdout,NULL,_IONBF,0);
 IMMDeviceEnumerator *en=NULL;IMMDeviceCollection *col=NULL;IMMDevice *dev=NULL;
 WCHAR *initial=NULL,*other=NULL,*id=NULL;HKEY key=NULL;BYTE *previous=NULL;DWORD previous_size=0,previous_type=0;BOOL had_previous=FALSE;BOOL route_touched=FALSE;
 IXAudio2 *audio=NULL;IXAudio2MasteringVoice *master=NULL;IXAudio2SourceVoice *voice=NULL;HMODULE dll=NULL;HRESULT hr;int result=1;
 XAUDIO2_VOICE_STATE state={0};UINT64 last=0;UINT count=0;LONG err;
 CoInitializeEx(NULL,COINIT_MULTITHREADED);
 hr=CoCreateInstance(&CLSID_MMDeviceEnumerator,NULL,CLSCTX_INPROC_SERVER,&IID_IMMDeviceEnumerator,(void**)&en);if(FAILED(hr))goto cleanup;
 hr=IMMDeviceEnumerator_GetDefaultAudioEndpoint(en,eRender,eConsole,&dev);if(FAILED(hr))goto cleanup;
 describe(dev,-1);hr=IMMDevice_GetId(dev,&initial);IMMDevice_Release(dev);dev=NULL;if(FAILED(hr))goto cleanup;
 hr=IMMDeviceEnumerator_EnumAudioEndpoints(en,eRender,DEVICE_STATE_ACTIVE,&col);if(FAILED(hr))goto cleanup;
 IMMDeviceCollection_GetCount(col,&count);
 for(UINT i=0;i<count;i++){if(FAILED(IMMDeviceCollection_Item(col,i,&dev)))continue;hr=IMMDevice_GetId(dev,&id);IMMDevice_Release(dev);dev=NULL;if(SUCCEEDED(hr)&&wcscmp(initial,id)){other=id;id=NULL;break;}CoTaskMemFree(id);id=NULL;}
 if(!other){puts("DTR_SWITCH no second output; test skipped");result=2;goto cleanup;}
 err=RegCreateKeyExW(HKEY_CURRENT_USER,L"Software\\Wine\\Drivers\\winecoreaudio.drv",0,NULL,0,KEY_QUERY_VALUE|KEY_SET_VALUE,NULL,&key,NULL);if(err)goto cleanup;
 err=RegQueryValueExW(key,L"DefaultOutput",NULL,&previous_type,NULL,&previous_size);
 if(err==ERROR_SUCCESS){previous=malloc(previous_size);if(!previous)goto cleanup;err=RegQueryValueExW(key,L"DefaultOutput",NULL,&previous_type,previous,&previous_size);if(err)goto cleanup;had_previous=TRUE;puts("DTR_SWITCH pre-existing output override; use a disposable prefix without one");result=2;goto cleanup;}else if(err!=ERROR_FILE_NOT_FOUND)goto cleanup;
 dll=LoadLibraryA("xaudio2_8.dll");if(!dll)goto cleanup;HMODULE mm=LoadLibraryA("mmdevapi.dll");if(mm){IMAGE_NT_HEADERS *mh=(IMAGE_NT_HEADERS*)((BYTE*)mm+((IMAGE_DOS_HEADER*)mm)->e_lfanew);printf("DTR_SWITCH mmdev_timestamp=%lu\n",(unsigned long)mh->FileHeader.TimeDateStamp);FreeLibrary(mm);}create_fn create=(create_fn)GetProcAddress(dll,"XAudio2Create");if(!create)goto cleanup;
 hr=create(&audio,0,XAUDIO2_DEFAULT_PROCESSOR);if(FAILED(hr))goto cleanup;
 hr=IXAudio2_CreateMasteringVoice(audio,&master,0,0,0,NULL,NULL,AudioCategory_GameEffects);if(FAILED(hr))goto cleanup;
 WAVEFORMATEX fmt={WAVE_FORMAT_PCM,2,48000,192000,4,16,0};hr=IXAudio2_CreateSourceVoice(audio,&voice,&fmt,0,XAUDIO2_DEFAULT_FREQ_RATIO,NULL,NULL,NULL);if(FAILED(hr))goto cleanup;
 XAUDIO2_BUFFER buffer={0};buffer.AudioBytes=sizeof(silence);buffer.pAudioData=(BYTE*)silence;buffer.LoopCount=XAUDIO2_LOOP_INFINITE;
 hr=IXAudio2SourceVoice_SubmitSourceBuffer(voice,&buffer,NULL);if(FAILED(hr))goto cleanup;
 hr=IXAudio2SourceVoice_Start(voice,0,XAUDIO2_COMMIT_NOW);if(FAILED(hr))goto cleanup;
 for(int phase=0;phase<3;phase++){
  if(phase==1){err=RegSetValueExW(key,L"DefaultOutput",0,REG_SZ,(BYTE*)other,(wcslen(other)+1)*sizeof(WCHAR));if(err)goto cleanup;route_touched=TRUE;}
  if(phase==2){err=RegDeleteValueW(key,L"DefaultOutput");if(err&&err!=ERROR_FILE_NOT_FOUND)goto cleanup;}
  Sleep(2000);IXAudio2SourceVoice_GetState(voice,&state,0);
  printf("DTR_SWITCH phase=%d samples=%llu progressed=%d\n",phase,(unsigned long long)state.SamplesPlayed,state.SamplesPlayed>last);
  if(state.SamplesPlayed<=last)goto cleanup;last=state.SamplesPlayed;
  hr=IMMDeviceEnumerator_GetDefaultAudioEndpoint(en,eRender,eConsole,&dev);if(FAILED(hr))goto cleanup;describe(dev,phase);hr=IMMDevice_GetId(dev,&id);IMMDevice_Release(dev);dev=NULL;if(FAILED(hr))goto cleanup;
  DWORD checksize=0;LONG checkstatus=RegQueryValueExW(key,L"DefaultOutput",NULL,NULL,NULL,&checksize);printf("DTR_SWITCH phase=%d override_present=%d\n",phase,checkstatus==ERROR_SUCCESS);int matches=!wcscmp(id,phase==1?other:initial);CoTaskMemFree(id);id=NULL;printf("DTR_SWITCH phase=%d correct_default=%d\n",phase,matches);if(!matches)goto cleanup;
 }
 result=0;puts("DTR_SWITCH live-default -> other-real-endpoint -> live-default: PASS");
cleanup:
 if(voice)IXAudio2SourceVoice_DestroyVoice(voice);if(master)IXAudio2MasteringVoice_DestroyVoice(master);if(audio)IXAudio2_Release(audio);
 if(key&&route_touched){if(had_previous)RegSetValueExW(key,L"DefaultOutput",0,previous_type,previous,previous_size);else RegDeleteValueW(key,L"DefaultOutput");}if(key)RegCloseKey(key);free(previous);
 if(dll)FreeLibrary(dll);if(dev)IMMDevice_Release(dev);if(col)IMMDeviceCollection_Release(col);if(en)IMMDeviceEnumerator_Release(en);
 CoTaskMemFree(initial);CoTaskMemFree(other);CoTaskMemFree(id);CoUninitialize();printf("DTR_SWITCH result=%d\n",result);return result;
}
