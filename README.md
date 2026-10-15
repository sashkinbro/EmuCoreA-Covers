# EmuCoreA PSP Covers

Individually downloadable PSP cover artwork from the EmuCoreA IGDB catalogue, with regional serial mappings and optional PSP 3D cases.

## Use

Download `index.json` once. Normalize a disc ID by uppercasing and removing spaces, hyphens, periods and underscores, then look up `serials[discId]`. This gives an IGDB ID; `games[id].path` is the flat cover and `games[id].path_3d` is the optional 3D cover. Prefix paths with `https://raw.githubusercontent.com/sashkinbro/EmuCoreA-Covers/main/`. For reproducible clients, replace `main` with a reviewed commit SHA. Each image has a SHA-256 checksum in the index.

Multiple regional serials deliberately reference one canonical game image. A shared image is not a claim that it is the original packaging for every region. Never infer another region by swapping a serial prefix or incrementing its number.

## Coverage and limitations

The snapshot contains 3,168 original IGDB images and 3,168 generated 3D images. There are 2,749 mapped serials and 278 unresolved entries from the 3,027-entry source list (3,022 bundled product-code titles plus reviewed serials for discs the list omits). The unresolved remainder is dominated by Asia/China-exclusive discs, demo and sampler UMDs and hardware utility discs. `review.json` lists every unresolved/ambiguous entry and small source image; `manifest.json` records every mapping method, source URL and checksum. Missing entries should retain the game's embedded icon or a placeholder, not an approximate title match.

Mappings use explicit database serials, unique normalized title equality, unique normalized equality against IGDB alternative names (this is what links romanised Japanese titles such as `Irregular Hunter X` or `Yuusha 30` to their catalogue entries), unique romanisation-folded title equality, or reviewed overrides. Romanisation folding only canonicalises long vowels and Hepburn variants (`ou`/`oo`/`uu`, `sya`/`sha`, `tu`/`tsu`, ...) for whole-string equality; it is never used for partial or fuzzy matching. Duplicate titles are not resolved automatically. The bundled serial source is a title index, not an authoritative guarantee of every retail reprint, PSN edition, demo or homebrew identity. Source errors remain possible and corrections should identify the serial, correct title and supporting evidence.

Flat images preserve IGDB bytes and aspect ratio, requested at `t_1080p`; this does not guarantee the source artwork was high resolution. Clients should fit artwork without stretching. 3D images are 600x900 transparent WebP, quality 92, using an independently drawn dark PSP case with PlayStation Portable branding and a short spine header containing the PlayStation emblem. The 3D printable area fills to the bottom edge using a proportional crop, without stretching or letterbox bars; full uncropped originals remain available as flat images. No PS2 template, PS2 branding or invented regional serial is included.

## Maintenance

This repository publishes catalog metadata and finished cover artwork. Build tools are excluded from version control. The application bundles a reviewed index and pins downloads to a reviewed commit SHA.

## Attribution

Artwork source: [IGDB](https://www.igdb.com/), via [IGDB image CDN](https://api-docs.igdb.com/#images). Cover artwork and game/platform trademarks belong to their respective owners. Repository tooling and metadata do not grant ownership or a new license to that artwork. The 3D case was implemented independently after reviewing the approach in [xlenore/ps2-covers](https://github.com/xlenore/ps2-covers); its PS2 template and code are not included.

PlayStation emblem: [Wikimedia Commons source](https://commons.wikimedia.org/wiki/File:Playstation_logo_colour.svg), credited there to Sony / Manabu Sakamoto (PD-textlogo; trademark).

PSP wordmark: [Wikimedia Commons source](https://commons.wikimedia.org/wiki/File:PSP_Logo.svg), vector credited there to Afrank99 (PD-textlogo; trademark). The renderer uses its letterforms rather than substituting a system font.
