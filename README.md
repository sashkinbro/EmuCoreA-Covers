# EmuCoreA PSP Covers

Individually downloadable PSP cover artwork from the EmuCoreA IGDB catalogue, with regional serial mappings and optional PSP 3D cases.

## Use

Download `index.json` once. Normalize a disc ID by uppercasing and removing spaces, hyphens, periods and underscores, then look up `serials[discId]`. This gives an IGDB ID; `games[id].path` is the flat cover and `games[id].path_3d` is the optional 3D cover. Prefix paths with `https://raw.githubusercontent.com/sashkinbro/EmuCoreA-Covers/main/`. For reproducible clients, replace `main` with a reviewed commit SHA. Each image has a SHA-256 checksum in the index.

Multiple regional serials deliberately reference one canonical game image. A shared image is not a claim that it is the original packaging for every region. Never infer another region by swapping a serial prefix or incrementing its number.

## Coverage and limitations

The snapshot contains 3,168 original IGDB images and 3,168 generated 3D images. There are 1,967 mapped serials and 1,055 unresolved entries from the 3,022-entry source list. This is not complete PSP regional coverage. `review.json` lists every unresolved/ambiguous entry and small source image; `manifest.json` records every mapping method, source URL and checksum. Missing entries should retain the game's embedded icon or a placeholder, not an approximate title match.

Mappings use explicit database serials, unique normalized title equality, or reviewed overrides. Duplicate titles are not resolved automatically. The bundled serial source is a title index, not an authoritative guarantee of every retail reprint, PSN edition, demo or homebrew identity. Source errors remain possible and corrections should identify the serial, correct title and supporting evidence.

Flat images preserve IGDB bytes and aspect ratio, requested at `t_1080p`; this does not guarantee the source artwork was high resolution. Clients should fit artwork without stretching. 3D images are 600x900 transparent WebP, quality 92, using an original generic PSP case with PSP/PlayStation Portable/UMD text. The 3D printable area fills to the bottom edge using a proportional crop, without stretching or letterbox bars; full uncropped originals remain available as flat images. No PS2 template, PS2 branding or invented regional serial is included.

## Rebuild

Python 3.11+, Pillow and NumPy are required. No API token is needed for these existing public image URLs.

```sh
python -m pip install -r tools/requirements.txt
python tools/export_psp_covers.py --database data/catalog.json --titles data/psp_titles.json --overrides tools/psp_cover_overrides.json --output .
# Review the plan before downloading. The next command downloads/resumes verified images.
python tools/export_psp_covers.py --database data/catalog.json --titles data/psp_titles.json --overrides tools/psp_cover_overrides.json --output . --download
python tools/render_psp_covers_3d.py --repository .
python tools/build_psp_cover_index.py --repository . --output index.json
python -m unittest discover -s tools -p test_psp_covers.py
```

Exports use bounded concurrency, retries, image validation, checksums, atomic files and process locks. Inspect a stale lock before removing it. Downloads resume only when the existing image matches its recorded source and checksum. Keep previous manifests when updating an existing export. A plan-only run produces a new pending manifest; use a separate output directory for previewing changes to an existing published snapshot.

The application bundles a reviewed index and downloads only the user's games. Update that snapshot when publishing mapping corrections. Images are stored once per canonical ID rather than duplicated per serial. There are no game files, emulator binaries or credentials in this repository.

## Attribution

Artwork source: [IGDB](https://www.igdb.com/), via [IGDB image CDN](https://api-docs.igdb.com/#images). Cover artwork and game/platform trademarks belong to their respective owners. Repository tooling and metadata do not grant ownership or a new license to that artwork. The 3D case was implemented independently after reviewing the approach in [xlenore/ps2-covers](https://github.com/xlenore/ps2-covers); its PS2 template and code are not included.

PlayStation emblem: [Wikimedia Commons source](https://commons.wikimedia.org/wiki/File:Playstation_logo_colour.svg), credited there to Sony / Manabu Sakamoto (PD-textlogo; trademark). A raster copy is in `tools/assets/playstation-logo.png`.
