#!/usr/bin/env python3
"""Render IGDB cover art in an original PSP case template, with transparent margins.
No PS2 template or region-specific serial is used. Requires Pillow and NumPy.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from export_psp_covers import atomic_json, digest, inspect_image

VERSION = "psp-case-v13-clean-spine"
TEMPLATE_HASH = hashlib.sha256(
    Path(__file__).read_bytes().replace(b"\r\n", b"\n")
    + (Path(__file__).parent / "assets/playstation-logo.png").read_bytes()
    + (Path(__file__).parent / "assets/psp-logo.png").read_bytes()
).hexdigest()
SIZE = (1200, 1800)
FRONT = [(76, 43), (568, 73), (568, 819), (76, 853)]
SPINE = [(35, 59), (76, 43), (76, 853), (35, 834)]
FRONT = [(x * 2, y * 2) for x, y in FRONT]
SPINE = [(x * 2, y * 2) for x, y in SPINE]


def warp(source: Image.Image, corners: list[tuple[int, int]]) -> Image.Image:
    width, height = source.size
    original = [(0, 0), (width, 0), (width, height), (0, height)]
    matrix, values = [], []
    for (x, y), (u, v) in zip(corners, original):
        matrix.extend([[x, y, 1, 0, 0, 0, -u*x, -u*y], [0, 0, 0, x, y, 1, -v*x, -v*y]])
        values.extend([u, v])
    coefficients = np.linalg.solve(np.array(matrix, dtype=float), np.array(values, dtype=float))
    return source.transform(SIZE, Image.Transform.PERSPECTIVE, coefficients, Image.Resampling.BICUBIC)


def template() -> Image.Image:
    out = Image.new("RGBA", SIZE)
    shadow = Image.new("RGBA", SIZE)
    ImageDraw.Draw(shadow).polygon([(x*2, y*2) for x,y in [(35, 75), (100, 33), (577, 69), (579, 835), (88, 874), (29, 847)]], fill=(0, 0, 0, 100))
    out.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)))
    draw = ImageDraw.Draw(out)
    def polygon(points, fill):
        draw.polygon([(x*2, y*2) for x,y in points], fill=fill)
    polygon([(29, 51), (78, 29), (578, 65), (578, 830), (79, 865), (29, 841)], fill=(32, 34, 38, 255))
    polygon([(29, 51), (78, 29), (578, 65), (568, 73), (81, 43), (35, 59)], fill=(67, 70, 76, 255))
    polygon([(29, 51), (35, 59), (35, 834), (76, 853), (79, 865), (29, 841)], fill=(41, 43, 48, 255))
    polygon([(76, 43), (81, 43), (81, 852), (76, 853)], fill=(64, 67, 72, 255))
    polygon([(568, 73), (578, 65), (578, 830), (568, 819)], fill=(56, 59, 64, 255))
    return out


def render(source: Image.Image) -> Image.Image:
    out = template()
    # Fill the printable area proportionally: a small edge crop replaces letterboxing.
    # Flat originals remain untouched and available separately.
    face = Image.new("RGBA", (600, 900), (22, 24, 28, 255))
    wrap_art = ImageOps.fit(source.convert("RGBA"), (650, 838), Image.Resampling.LANCZOS)
    art = wrap_art.crop((50, 0, 650, 838))
    face.alpha_composite(art, (0, 62))
    with Image.open(Path(__file__).parent / "assets/psp-logo.png") as psp_source:
        psp_source = psp_source.convert("RGBA")
        psp_mark = Image.new("RGBA", psp_source.size, "white")
        psp_mark.putalpha(psp_source.getchannel("A"))
    wordmark = ImageOps.contain(psp_mark.crop((135, 232, 751, 295)), (440, 38), Image.Resampling.LANCZOS)
    face.alpha_composite(wordmark, (24, (62-wordmark.height)//2))
    with Image.open(Path(__file__).parent / "assets/playstation-logo.png") as logo_source:
        logo = ImageOps.contain(logo_source.convert("RGBA"), (54, 44), Image.Resampling.LANCZOS)
    face.alpha_composite(logo, (530, (62-logo.height)//2))
    out.alpha_composite(warp(face, FRONT))
    # One continuous print wraps around the shared front/spine edge.
    spine = Image.new("RGBA", (50, 900), (22, 24, 28, 255))
    spine.alpha_composite(wrap_art.crop((0, 0, 50, 838)), (0, 62))
    # Keep only the PlayStation emblem on the short spine header.
    panel = Image.new("RGBA", (50, 62), (22, 24, 28, 255))
    small_logo = ImageOps.contain(logo, (30, 26), Image.Resampling.LANCZOS)
    panel.alpha_composite(small_logo, ((50-small_logo.width)//2, (62-small_logo.height)//2))
    spine.alpha_composite(panel)
    spine.alpha_composite(Image.new("RGBA", spine.size, (0, 0, 0, 42)))
    out.alpha_composite(warp(spine, SPINE))
    d = ImageDraw.Draw(out)
    d.line([FRONT[0], FRONT[1], FRONT[2]], fill=(88, 92, 98, 255), width=2)
    return out.resize((600, 900), Image.Resampling.LANCZOS)


def generate_one(task: tuple[str, str, str, str]) -> tuple[str, dict]:
    root, game_id, source_path, source_hash = task
    directory = Path(root)
    target = directory / "covers/3d" / f"{game_id}.webp"
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(directory / source_path) as source:
        image = render(source)
    temporary = target.with_suffix(".webp.part")
    image.save(temporary, "WEBP", quality=92, method=4)
    info = inspect_image(temporary)
    os.replace(temporary, target)
    return game_id, dict(info, path=f"covers/3d/{game_id}.webp", source_sha256=source_hash, template=VERSION, template_sha256=TEMPLATE_HASH)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--ids", nargs="*", help="Render a small sample before the full batch")
    parser.add_argument("--workers", type=int, choices=range(1, 9), default=4)
    args = parser.parse_args()
    root = args.repository.resolve()
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    cache_path = root / "3d-manifest.json"
    previous = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.is_file() else {}
    lock = root / ".render.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        parser.error("A render may already be running; inspect .render.lock before retrying")
    os.close(fd)
    try:
        tasks = []
        for key, game in manifest["games"].items():
            if game["status"] != "downloaded" or (args.ids and key not in args.ids):
                continue
            old = previous.get(key, {})
            target = root / "covers/3d" / f"{key}.webp"
            if old.get("template_sha256") == TEMPLATE_HASH and old.get("source_sha256") == game["sha256"] and target.is_file() and digest(target) == old.get("sha256"):
                continue
            if digest(root / game["path"]) != game["sha256"]:
                raise ValueError(f"Source checksum mismatch for {key}")
            tasks.append((str(root), key, game["path"], game["sha256"]))
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            for count, (key, result) in enumerate(pool.map(generate_one, tasks), 1):
                previous[key] = result
                if count % 100 == 0:
                    atomic_json(cache_path, previous)
                    print(f"Rendered {count}/{len(tasks)}", flush=True)
        atomic_json(cache_path, previous)
        print(f"Current-template covers: {sum(v.get('template_sha256') == TEMPLATE_HASH for v in previous.values())}/{len(manifest['games'])}", flush=True)
    finally:
        lock.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
