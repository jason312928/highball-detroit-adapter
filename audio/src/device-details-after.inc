uint32_t FAudio_PlatformGetDeviceDetails(
	uint32_t index,
	FAudioDeviceDetails *details
) {
	WAVEFORMATEX *format = NULL, *obtained = NULL;
	WAVEFORMATEXTENSIBLE *ext;
	IAudioClient *client = NULL;
	IMMDevice *device = NULL;
	IPropertyStore* properties = NULL;
	PROPVARIANT deviceName;
	uint32_t count = 0;
	uint32_t ret = 0;
	HRESULT hr;
	WCHAR *str = NULL;
	GUID sub;

	FAudio_memset(details, 0, sizeof(FAudioDeviceDetails));

	PropVariantInit(&deviceName);
	FAudio_PlatformAddRef();

	count = FAudio_PlatformGetDeviceCount();
	if (index >= count)
	{
		FAudio_PlatformRelease();
		return FAUDIO_E_INVALID_CALL;
	}

	hr = FAudio_OpenDevice(index, &device);
	if (FAILED(hr))
	{
		ret = hr;
		goto cleanup;
	}

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
	if (FAILED(hr))
	{
		ret = hr;
		goto cleanup;
	}
	hr = IPropertyStore_GetValue(properties, (PROPERTYKEY*)&DEVPKEY_Device_FriendlyName, &deviceName);
	if (FAILED(hr))
	{
		ret = hr;
		goto cleanup;
	}
	lstrcpynW((LPWSTR)details->DisplayName, deviceName.pwszVal, ARRAYSIZE(details->DisplayName) - 1);
	PropVariantClear(&deviceName);
	IPropertyStore_Release(properties);
	properties = NULL;

	/* Set the Device ID */
	hr = IMMDevice_GetId(device, &str);
	if (FAILED(hr))
	{
		ret = hr;
		goto cleanup;
	}
	lstrcpynW((LPWSTR)details->DeviceID, str, ARRAYSIZE(details->DeviceID) - 1);
	CoTaskMemFree(str);
	str = NULL;

	hr = IMMDevice_Activate(
		device,
		&IID_IAudioClient,
		CLSCTX_ALL,
		NULL,
		(void **)&client
	);
	if (FAILED(hr))
	{
		ret = hr;
		goto cleanup;
	}

	hr = IAudioClient_GetMixFormat(client, &format);
	if (FAILED(hr))
	{
		ret = hr;
		goto cleanup;
	}

	if (!format)
	{
		ret = E_FAIL;
		goto cleanup;
	}

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

cleanup:
	CoTaskMemFree(format);
	CoTaskMemFree(str);
	PropVariantClear(&deviceName);
	if (properties) IPropertyStore_Release(properties);
	if (client) IAudioClient_Release(client);
	if (device) IMMDevice_Release(device);
	FAudio_PlatformRelease();

	return ret;
}
