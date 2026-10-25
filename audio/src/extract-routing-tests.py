#!/usr/bin/env python3
"""Extract the exact patched functions for the deterministic Windows fixtures."""
from pathlib import Path
import sys
source = Path(sys.argv[1])
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
s = (source / "libs/faudio/src/FAudio_platform_win32.c").read_text()
a = s.index("struct FAudioWin32PlatformData")
b = s.index("void FAudio_Log", a)
c = s.index("static HRESULT FAudio_FillAudioClientBuffer")
d = s.index("/* Sets `defaultDeviceIndex`", c)
(out / "routing-under-test.inc").write_text(s[a:b] + s[c:d])
s = (source / "dlls/mmdevapi/devenum.c").read_text()
a = s.index("static HRESULT detroit_default_render_device")
b = s.index("static HRESULT WINAPI MMDevEnum_GetDefaultAudioEndpoint", a)
(out / "endpoint-under-test.inc").write_text(s[a:b])
