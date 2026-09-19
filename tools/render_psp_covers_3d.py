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

VERSION = "psp-case-v2-webp"
SIZE = (600, 900)
FRONT = [(81, 43), (568, 73), (568, 819), (81, 852)]
SPINE = [(35, 59), (76, 43), (76, 853), (35, 834)]


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
    ImageDraw.Draw(shadow).polygon([(35, 75), (100, 33), (577, 69), (579, 835), (88, 874), (29, 847)], fill=(0, 0, 0, 100))
    out.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(9)))
    draw = ImageDraw.Draw(out)
    draw.polygon([(29, 51), (78, 29), (578, 65), (578, 830), (79, 865), (29, 841)], fill=(185, 191, 197, 255))
    draw.polygon([(29, 51), (78, 29), (578, 65), (568, 73), (81, 43), (35, 59)], fill=(242, 245, 247, 255))
    draw.polygon([(29, 51), (35, 59), (35, 834), (76, 853), (79, 865), (29, 841)], fill=(117, 124, 132, 255))
    draw.polygon([(76, 43), (81, 43), (81, 852), (76, 853)], fill=(247, 249, 251, 255))
    draw.polygon([(568, 73), (578, 65), (578, 830), (568, 819)], fill=(130, 137, 145, 255))
    return out


def render(source: Image.Image) -> Image.Image:
    out = template()
    # Fit, never stretch or crop. Source pixels and original files are untouched.
    face = Image.new("RGBA", (600, 900), (22, 24, 28, 255))
    art = ImageOps.contain(source.convert("RGBA"), face.size, Image.Resampling.LANCZOS)
    face.alpha_composite(art, ((face.width-art.width)//2, (face.height-art.height)//2))
    out.alpha_composite(warp(face, FRONT))
    spine = Image.new("RGBA", (76, 1400), (232, 235, 238, 255))
    d = ImageDraw.Draw(spine)
    d.rectangle((0, 0, 76, 205), fill=(25, 28, 32, 255))
    font = ImageFont.load_default(size=30)
    d.text((38, 60), "PSP", font=font, anchor="mm", fill="white")
    label = Image.new("RGBA", (1000, 66))
    ld = ImageDraw.Draw(label)
    ld.text((500, 32), "PLAYSTATION PORTABLE", font=ImageFont.load_default(size=34), anchor="mm", fill=(34, 38, 43, 255))
    label = label.rotate(-90, expand=True)
    spine.alpha_composite(label, (5, 250))
    d.text((38, 1300), "UMD", font=ImageFont.load_default(size=23), anchor="mm", fill=(52, 57, 63, 255))
    out.alpha_composite(warp(spine, SPINE))
    d = ImageDraw.Draw(out)
    d.line([FRONT[0], FRONT[1], FRONT[2]], fill=(255, 255, 255, 110), width=2)
    return out


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
    return game_id, dict(info, path=f"covers/3d/{game_id}.webp", source_sha256=source_hash, template=VERSION)


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
            if old.get("template") == VERSION and old.get("source_sha256") == game["sha256"] and target.is_file() and digest(target) == old.get("sha256"):
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
        print(f"Verified 3D covers: {len(previous)}", flush=True)
    finally:
        lock.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
