# Neutrino Emojis

`neutrino_emojis` is an original, normalized emoji icon pack for the Neutrino Project.

It contains 1000 generated emoji-style icons, 10 color themes, and PNG exports in 16, 32, 64, 128 pixel sizes. Artwork is generated from original vector geometry rather than copied from third-party emoji projects.

## Contents

- 1000 master SVG files in `svg/master/`
- 10000 themed SVG files in `svg/<theme>/`
- 40000 PNG files in `png/<theme>/<size>/`
- `manifest.json` and `manifest.csv`
- `include/neutrino_emojis.h`
- `preview/index.html` and contact sheets
- `tools/generate_neutrino_emojis.py`

## Themes

- `classic_yellow`
- `neutrino_blue`
- `graphite_dark`
- `forest_mint`
- `royal_purple`
- `solar_gold`
- `candy_pink`
- `aqua_cyan`
- `lava_orange`
- `mono_ink`

## Regenerate

```bash
python3 tools/generate_neutrino_emojis.py --out /path/to/neutrino_emojis --clean
```

## Layout

```text
neutrino_emojis/
  LICENSE.md
  NOTICE.md
  README.md
  themes.json
  manifest.json
  manifest.csv
  generation_report.json
  include/neutrino_emojis.h
  svg/master/
  svg/<theme>/
  png/<theme>/16/
  png/<theme>/32/
  png/<theme>/64/
  png/<theme>/128/
  preview/
  tools/
```
