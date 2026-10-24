#define COBJMACROS
#include <windows.h>
#include <stdio.h>
#include <xaudio2.h>
typedef HRESULT (WINAPI *create_fn)(IXAudio2**,UINT32,XAUDIO2_PROCESSOR);
int main(int argc,char **argv) {
 HMODULE module=LoadLibraryA(argc>1?argv[1]:"xaudio2_8.dll");
 if(!module){printf("DTR_XAUDIO load failed %lu\n",GetLastError());return 1;}
 char name[2048];GetModuleFileNameA(module,name,sizeof(name));printf("DTR_XAUDIO module=%s\n",name);
 create_fn create=(create_fn)GetProcAddress(module,"XAudio2Create");IXAudio2 *audio=NULL;IXAudio2MasteringVoice *voice=NULL;
 if(!create)return 2;
 HRESULT hr=create(&audio,0,XAUDIO2_DEFAULT_PROCESSOR);printf("DTR_XAUDIO create=0x%08lx\n",(unsigned long)hr);if(FAILED(hr))return 3;
 hr=IXAudio2_CreateMasteringVoice(audio,&voice,0,0,0,NULL,NULL,AudioCategory_GameEffects);
 printf("DTR_XAUDIO mastering=0x%08lx voice=%s\n",(unsigned long)hr,voice?"valid":"NULL");
 if(SUCCEEDED(hr)&&voice) {
  WAVEFORMATEX fmt={WAVE_FORMAT_PCM,2,48000,192000,4,16,0};IXAudio2SourceVoice *source=NULL;
  HRESULT stream_hr=IXAudio2_CreateSourceVoice(audio,&source,&fmt,0,XAUDIO2_DEFAULT_FREQ_RATIO,NULL,NULL,NULL);
  if(SUCCEEDED(stream_hr)) {
   short silence[4800*2]={0};XAUDIO2_BUFFER buffer={0};buffer.Flags=XAUDIO2_END_OF_STREAM;buffer.AudioBytes=sizeof(silence);buffer.pAudioData=(const BYTE*)silence;
   stream_hr=IXAudio2SourceVoice_SubmitSourceBuffer(source,&buffer,NULL);
   if(SUCCEEDED(stream_hr))stream_hr=IXAudio2SourceVoice_Start(source,0,XAUDIO2_COMMIT_NOW);
   Sleep(350);XAUDIO2_VOICE_STATE state={0};IXAudio2SourceVoice_GetState(source,&state,0);
   printf("DTR_XAUDIO silent_stream=0x%08lx queued=%lu\n",(unsigned long)stream_hr,(unsigned long)state.BuffersQueued);
   IXAudio2SourceVoice_DestroyVoice(source);
   if(FAILED(stream_hr)||state.BuffersQueued)hr=E_FAIL;
  } else { printf("DTR_XAUDIO source_voice=0x%08lx\n",(unsigned long)stream_hr);hr=stream_hr; }
  IXAudio2MasteringVoice_DestroyVoice(voice);
 }
 IXAudio2_Release(audio);FreeLibrary(module);return FAILED(hr)?4:0;
}
