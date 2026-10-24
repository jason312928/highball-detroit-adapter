# Patch series

## 0001-strict-interfaces-and-pinned-spirv.patch

Base: DiAvisoo/MoltenVK-Detroit at 8b511fdc5351a37c305bc246e161796ddca56b18 (Release003).

The patch pins the SPIRV-Cross fork and replaces fabricated vertex-input and stage-output mappings with explicit failures. Failed vertex-stage setup logs the Vulkan input descriptions and specialization entries.

Apply this patch once to the base checkout. Its SHA-256 is recorded in source-lock.json. Build scripts reject unrelated changes in that checkout.

## Reference diffs

These files document upstream changes and are not part of the patch series:

| File | Comparison |
|---|---|
| reference/upstream-detroit-full.patch | MoltenVK 5843e5da2e1f561261cb06a2f859ad39663d054f → Detroit Release003 |
| reference/upstream-spirv-cross.patch | SPIRV-Cross 146679ff8255a6068518685599d7fb8761d1b570 → 05583ac1537d777d304128142de2365bfa4a38df |

Do not apply the reference diffs on top of Release003.
