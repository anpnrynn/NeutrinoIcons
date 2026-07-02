# Neutrino Icon Pack CC0

This package contains **500 original normalized system/UI icons** generated for the Neutrino project.

## What is included

- SVG master icons: `svg/master/*.svg`
- Fixed-color themed SVGs: `svg/<theme>/*.svg`
- PNG exports: `png/<theme>/<size>/*.png`
- Sizes: 16, 24, 32, 48, 64, 128
- Themes: classic_gray, neutrino_blue, graphite_dark_ui, forest_green, royal_purple
- Manifest: `manifest.json` and `manifest.csv`
- Neutrino C header: `include/neutrino_icons.h`
- Preview contact sheets: `preview/*_contact_sheet.png` and `preview/index.html`
- Regeneration script: `tools/generate_neutrino_icons.py`

## Visual normalization rules

- 128 x 128 SVG design grid
- Transparent backgrounds
- Rounded 8 px primary strokes with round caps and joins
- Secondary detail strokes for internal structure
- Consistent bottom-right action badges for add, delete, edit, search, upload, download, lock, warning, etc.
- PNG exports are generated from the SVG masters, with the 128 px render downsampled for smaller sizes.

## Recommended use

For toolbars, use 16 or 24 px. For palettes and trees, use 24 or 32 px. For splash/help/about screens, use 48, 64, or 128 px.

## License

The icon artwork in this package is original generated geometry and is provided under the CC0-1.0 style public-domain dedication in `LICENSE.md`. No third-party icon artwork was imported.
