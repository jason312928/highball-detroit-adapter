# Audio regression fixtures

The `.inc` files extract the exact pre/post functions from the pinned Wine and bundled FAudio source described in `../source-lock.json`. They are test inputs, not alternative runtime implementations. Wine-derived fixtures retain LGPL-2.1-or-later; FAudio-derived fixtures retain its upstream zlib-style terms. Full notices are in `../licenses/`, and the release's corresponding-source archive includes the complete patched tree.

`device-error-test.c` injects endpoint-query failures and checks reference counts. `mastering-error-test.c` checks voice-creation failure propagation and lock/resource state. The `*-before.inc` variants deliberately retain the bugs to establish the regression.

`xaudio-load-probe.c` loads a real DLL and consumes a silent output buffer. `wasapi-probe.c` reports real endpoint query results; its output may contain local device names and identifiers and should be reviewed before sharing.

中文：`.inc` 文件是固定 Wine / FAudio 源码中修补前后的实际函数体，用作回归测试输入；`before` 版本故意保留缺陷。两个测试分别验证设备查询错误与声音对象创建错误。运行探针会输出本地设备信息，分享日志前需检查。许可见 `../licenses/`，完整修补源码随 Release 的对应源码包提供。
