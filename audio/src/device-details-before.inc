uint32_t FAudio_PlatformGetDeviceDetails(
	uint32_t index,
	FAudioDeviceDetails *details
) {
	WAVEFORMATEX *format, *obtained;
	WAVEFORMATEXTENSIBLE *ext;
	IAudioClient *client;
	IMMDevice *device;
	IPropertyStore* properties;
	PROPVARIANT deviceName;
	uint32_t count = 0;
	uint32_t ret = 0;
	HRESULT hr;
	WCHAR *str;
	GUID sub;

	FAudio_memset(details, 0, sizeof(FAudioDeviceDetails));

	FAudio_PlatformAddRef();

	count = FAudio_PlatformGetDeviceCount();
	if (index >= count)
	{
		FAudio_PlatformRelease();
		return FAUDIO_E_INVALID_CALL;
	}

	hr = FAudio_OpenDevice(index, &device);
	FAudio_assert(!FAILED(hr) && "Failed to get audio endpoint!");

	if (index == 0)
	{
		details->Role = FAudioGlobalDefaultDevice;
	}
	else
	{
		details->Role = FAudioNotDefaultDevice;
	}

	/* Set the Device Display Name */
	hr = IMMDevice_OpenPropertyStore(device, STGM_READ, &properties);
	FAudio_assert(!FAILED(hr) && "Failed to open device property store!");
	hr = IPropertyStore_GetValue(properties, (PROPERTYKEY*)&DEVPKEY_Device_FriendlyName, &deviceName);
	FAudio_assert(!FAILED(hr) && "Failed to get audio device friendly name!");
	lstrcpynW((LPWSTR)details->DisplayName, deviceName.pwszVal, ARRAYSIZE(details->DisplayName) - 1);
	PropVariantClear(&deviceName);
	IPropertyStore_Release(properties);

	/* Set the Device ID */
	hr = IMMDevice_GetId(device, &str);
	FAudio_assert(!FAILED(hr) && "Failed to get audio endpoint id!");
	lstrcpynW((LPWSTR)details->DeviceID, str, ARRAYSIZE(details->DeviceID) - 1);
	CoTaskMemFree(str);

	hr = IMMDevice_Activate(
		device,
		&IID_IAudioClient,
		CLSCTX_ALL,
		NULL,
		(void **)&client
	);
	FAudio_assert(!FAILED(hr) && "Failed to activate audio client!");

	hr = IAudioClient_GetMixFormat(client, &format);
	FAudio_assert(!FAILED(hr) && "Failed to get audio client mix format!");

	if (format->wFormatTag == WAVE_FORMAT_EXTENSIBLE)
	{
		ext = (WAVEFORMATEXTENSIBLE *)format;
		sub = ext->SubFormat;
		FAudio_memcpy(
			&ext->SubFormat,
			&DATAFORMAT_SUBTYPE_PCM,
			sizeof(GUID)
		);

		hr = IAudioClient_IsFormatSupported(client, AUDCLNT_SHAREMODE_SHARED, format, &obtained);
		if (FAILED(hr))
		{
			ext->SubFormat = sub;
		}
		else if (obtained)
		{
			CoTaskMemFree(format);
			format = obtained;
		}
	}

	details->OutputFormat.Format.wFormatTag = format->wFormatTag;
	details->OutputFormat.Format.nChannels = format->nChannels;
	details->OutputFormat.Format.nSamplesPerSec = format->nSamplesPerSec;
	details->OutputFormat.Format.nAvgBytesPerSec = format->nAvgBytesPerSec;
	details->OutputFormat.Format.nBlockAlign = format->nBlockAlign;
	details->OutputFormat.Format.wBitsPerSample = format->wBitsPerSample;
	details->OutputFormat.Format.cbSize = format->cbSize;

	if (format->wFormatTag == WAVE_FORMAT_EXTENSIBLE)
	{
		ext = (WAVEFORMATEXTENSIBLE *)format;
		details->OutputFormat.Samples.wValidBitsPerSample = ext->Samples.wValidBitsPerSample;
		details->OutputFormat.dwChannelMask = ext->dwChannelMask;
		FAudio_memcpy(
			&details->OutputFormat.SubFormat,
			&ext->SubFormat,
			sizeof(GUID)
		);
	}
	else
	{
		details->OutputFormat.dwChannelMask = GetMask(format->nChannels);
	}

	CoTaskMemFree(format);

	IAudioClient_Release(client);

	IMMDevice_Release(device);

	FAudio_PlatformRelease();

	return ret;
}
