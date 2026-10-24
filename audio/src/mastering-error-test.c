#define COBJMACROS
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <xaudio2.h>
#include "FAudio.h"
#define XAUDIO2_VER 8
#define TRACE(...) ((void)0)
#define WARN(...) ((void)0)
#define debugstr_w(x) "test"
#define COMPAT_E_INVALID_CALL XAUDIO2_E_INVALID_CALL
static HRESULT result_to_return;
static int chains;
typedef struct {
 IXAudio2 iface;
 CRITICAL_SECTION lock;
 FAudio *faudio;
 struct { IXAudio2MasteringVoice IXAudio2MasteringVoice_iface;CRITICAL_SECTION lock;BOOL in_use;FAudioEffectChain *effect_chain;FAudioMasteringVoice *faudio_voice; } mst;
} IXAudio2Impl;
static IXAudio2Impl *impl_from_IXAudio2(IXAudio2 *p) { return (IXAudio2Impl*)p; }
static FAudioEffectChain *wrap_effect_chain(const XAUDIO2_EFFECT_CHAIN *p) { if(!p)return NULL;++chains;return calloc(1,sizeof(FAudioEffectChain)); }
static void free_effect_chain(FAudioEffectChain *p) { if(p){--chains;free(p);} }
static uint32_t mock_create(FAudio *audio,FAudioMasteringVoice **out,uint32_t c,uint32_t rate,uint32_t flags,uint16_t *id,const FAudioEffectChain *chain,FAudioStreamCategory cat) {
 *out=FAILED(result_to_return)?NULL:(FAudioMasteringVoice*)(uintptr_t)0x1000;return result_to_return;
}
#define FAudio_CreateMasteringVoice8 mock_create
#ifndef WRAPPER_FUNCTION_FILE
#define WRAPPER_FUNCTION_FILE "mastering-after.inc"
#endif
#include WRAPPER_FUNCTION_FILE
int main(void) {
 IXAudio2Impl obj={0};IXAudio2MasteringVoice *voice=(void*)(uintptr_t)0xdead;
 XAUDIO2_EFFECT_CHAIN chain={0};HRESULT hr;
 InitializeCriticalSection(&obj.lock);InitializeCriticalSection(&obj.mst.lock);
 result_to_return=E_FAIL;
 hr=IXAudio2Impl_CreateMasteringVoice(&obj.iface,&voice,0,0,0,NULL,&chain,AudioCategory_GameEffects);
 if(hr!=E_FAIL || voice!=NULL || obj.mst.in_use || obj.mst.effect_chain || obj.mst.faudio_voice || chains) {printf("DTR_WRAPPER failure propagation FAILED hr=0x%08lx voice=%p\n",(unsigned long)hr,voice);return 11;}
 if(obj.lock.LockCount!=-1 || obj.mst.lock.LockCount!=-1)return 12;
 puts("DTR_WRAPPER underlying failure returned; output NULL; resources and locks balanced PASS");
 result_to_return=S_OK;
 hr=IXAudio2Impl_CreateMasteringVoice(&obj.iface,&voice,0,0,0,NULL,&chain,AudioCategory_GameEffects);
 if(hr!=S_OK || voice!=&obj.mst.IXAudio2MasteringVoice_iface || !obj.mst.in_use || chains!=1)return 21;
 puts("DTR_WRAPPER normal mastering voice PASS");
 hr=IXAudio2Impl_CreateMasteringVoice(&obj.iface,&voice,0,0,0,NULL,&chain,AudioCategory_GameEffects);
 if(hr!=COMPAT_E_INVALID_CALL || voice!=NULL || chains!=1)return 31;
 puts("DTR_WRAPPER duplicate voice rejects and frees new chain PASS");
 free_effect_chain(obj.mst.effect_chain);DeleteCriticalSection(&obj.mst.lock);DeleteCriticalSection(&obj.lock);return 0;
}
