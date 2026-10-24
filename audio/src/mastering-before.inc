static HRESULT WINAPI IXAudio2Impl_CreateMasteringVoice(IXAudio2 *iface,
        IXAudio2MasteringVoice **ppMasteringVoice, UINT32 inputChannels,
        UINT32 inputSampleRate, UINT32 flags,
#if XAUDIO2_VER >= 8
        const WCHAR *deviceId,
#else
        UINT32 index,
#endif
        const XAUDIO2_EFFECT_CHAIN *pEffectChain
#if XAUDIO2_VER >= 8
        , AUDIO_STREAM_CATEGORY streamCategory
#endif
        )
{
    IXAudio2Impl *This = impl_from_IXAudio2(iface);
    FAudioEffectChain *chain;

    TRACE("(%p)->(%p, %u, %u, 0x%x, %p)\n", This,
            ppMasteringVoice, inputChannels, inputSampleRate, flags, pEffectChain);

    chain = wrap_effect_chain(pEffectChain);
#if XAUDIO2_VER >= 8
    if (pEffectChain && !chain)
        return XAUDIO2_E_INVALID_CALL;
#endif

    EnterCriticalSection(&This->lock);

    *ppMasteringVoice = &This->mst.IXAudio2MasteringVoice_iface;

    EnterCriticalSection(&This->mst.lock);

    if(This->mst.in_use){
        LeaveCriticalSection(&This->mst.lock);
        LeaveCriticalSection(&This->lock);
        return COMPAT_E_INVALID_CALL;
    }

    LeaveCriticalSection(&This->lock);

    This->mst.effect_chain = chain;

#if XAUDIO2_VER >= 8
    TRACE("device id %s, category %#x\n", debugstr_w(deviceId), streamCategory);

    FAudio_CreateMasteringVoice8(This->faudio, &This->mst.faudio_voice, inputChannels,
            inputSampleRate, flags, NULL /* TODO: (uint16_t*)deviceId */,
            This->mst.effect_chain, (FAudioStreamCategory)streamCategory);
#else
    TRACE("device index %u\n", index);

    FAudio_CreateMasteringVoice(This->faudio, &This->mst.faudio_voice, inputChannels,
            inputSampleRate, flags, index, This->mst.effect_chain);
#endif

    This->mst.in_use = TRUE;

    LeaveCriticalSection(&This->mst.lock);

    return S_OK;
}
