# WLED configuration

This folder is the durable WLED snapshot for the Stella octangula. Read both
JSON files before changing the controller.

## Files

- `cfg.json` is the controller's native `/json/cfg` snapshot.
- `presets.json` is the controller's native `/presets.json` snapshot and can be
  uploaded directly as a complete preset-file restore.

## Controller

- Device: `STAR-TENT`, WLED `16.0.1`
- URL: `http://192.168.8.243/`
- mDNS: `http://wled-a52a34.local/`
- 276 WS2811 LEDs on two outputs: GPIO16 covers LEDs 0–137 and GPIO4 covers
  LEDs 138–275.

## Safe usage

1. Fetch the live `/json/cfg` and `/presets.json` before any edit and preserve
   the exact pre-edit files under `.codex-tmp/`.
2. Change only the requested JSON field. `presets.json` is a complete restore
   file, so retain every unrelated preset.
3. Upload a complete file only when the intended overwrite is explicit:

   ```sh
   curl -fsS -X POST \
     -F 'data=@wled/presets.json;filename=/presets.json;type=application/json' \
     http://192.168.8.243/upload
   ```

   Use the same form with `cfg.json` and `filename=/cfg.json` for the device
   configuration. A preset-file upload changes saved presets; it is separate
   from the current live LED state.
4. Re-fetch the uploaded file and verify the requested change plus all
   unrelated preset IDs. Verify `/json/state` separately if live output was
   intentionally changed.

Preset 1 (`Android`) must keep its single active segment at ID 0. This avoids a
WLED 16.0.1 web UI bug that assumes a one-segment layout has `seg0bri`; a sole
segment with ID 2 causes `Cannot read properties of null (reading 'value')` in
`populateSegments()`.

The saved Stella presets use IDs 2–12. Edge segments are IDs 0–11, overview
segments are IDs 12–14, and edge numbering follows electrical chain order.
