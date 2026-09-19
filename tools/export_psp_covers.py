#!/usr/bin/env python3
"""Export the bundled PSP catalogue to a resumable, reviewable cover repository.
Requires Python 3.11+ and Pillow. No IGDB API credentials are used.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 16 * 1024 * 1024
SERIAL = re.compile(r"[A-Z]{4}\d{5}")
IMAGE_PATH = re.compile(r"/igdb/image/upload/t_[a-z0-9_]+/([A-Za-z0-9_-]+)\.(jpg|png)")


def normalize_title(value: str) -> str:
    # Exact normalized equality only: no token dropping, region guessing or fuzzy matching.
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(c for c in value if not unicodedata.combining(c) and c not in "™®©")
    return " ".join("".join(c if c.isalnum() else " " for c in value).split())


def normalize_serial(value: str) -> str:
    value = re.sub(r"[-_.\s]", "", value.upper())
    if not SERIAL.fullmatch(value):
        raise ValueError(f"Invalid PSP serial: {value!r}")
    return value


def image_url(value: str, size: str) -> tuple[str, str]:
    parsed = urlsplit("https:" + value if value.startswith("//") else value)
    match = IMAGE_PATH.fullmatch(parsed.path)
    if parsed.scheme != "https" or parsed.hostname != "images.igdb.com" or parsed.port or not match or parsed.query or parsed.fragment:
        raise ValueError(f"Unexpected IGDB image URL: {value!r}")
    image_id, extension = match.groups()
    return f"https://images.igdb.com/igdb/image/upload/t_{size}/{image_id}.{extension}", extension


def digest(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def inspect_image(path: Path) -> dict:
    if not 0 < path.stat().st_size <= MAX_BYTES:
        raise ValueError("Image size outside allowed bounds")
    with Image.open(path) as image:
        width, height = image.size
        fmt = image.format
        if fmt not in ("JPEG", "PNG", "WEBP") or width <= 0 or height <= 0 or width * height > 40_000_000:
            raise ValueError("Unsupported image dimensions or format")
        image.verify()
    with Image.open(path) as image:
        image.load()  # Detect truncated pixel data as well as invalid headers.
    return {"width": width, "height": height, "bytes": path.stat().st_size, "sha256": digest(path), "format": fmt}


def build_plan(database: Path, titles_path: Path, overrides_path: Path | None, size: str) -> tuple[dict, dict]:
    explicit = defaultdict(set)
    if database.suffix == ".json":
        catalog = json.loads(database.read_text(encoding="utf-8"))
        games = {str(row["igdb_id"]): dict(row) for row in catalog["games"]}
        for row in catalog.get("serials", []):
            explicit[normalize_serial(row["serial"])].add(str(row["igdb_id"]))
    else:
        with sqlite3.connect(database.resolve().as_uri() + "?mode=ro&immutable=1", uri=True) as db:
            db.row_factory = sqlite3.Row
            games = {str(row["igdb_id"]): dict(row) for row in db.execute("SELECT igdb_id, name, cover_url FROM games ORDER BY igdb_id")}
            for row in db.execute("SELECT serial, igdb_id FROM game_serials ORDER BY serial"):
                explicit[normalize_serial(row[0])].add(str(row[1]))
    title_index = defaultdict(set)
    for key, game in games.items():
        title_index[normalize_title(game["name"])].add(key)
        game["serials"] = []
        game["status"] = "pending"
        try:
            game["source_url"], extension = image_url(game["cover_url"] or "", size)
            game["path"] = f"covers/{key}.{extension}"
        except ValueError as error:
            game["status"] = "missing_source"
            game["error"] = str(error)
    titles = json.loads(titles_path.read_text(encoding="utf-8"))
    overrides = json.loads(overrides_path.read_text(encoding="utf-8")) if overrides_path else {}
    unknown_override_fields = set(overrides) - {"serials", "titles"}
    if unknown_override_fields:
        raise ValueError(f"Unknown override fields: {unknown_override_fields}")
    serial_overrides = {normalize_serial(s): str(i) for s, i in overrides.get("serials", {}).items()}
    title_overrides = {normalize_title(t): str(i) for t, i in overrides.get("titles", {}).items()}
    for key in list(serial_overrides.values()) + list(title_overrides.values()):
        if key not in games:
            raise ValueError(f"Override references absent IGDB ID: {key}")
    serials, unresolved = {}, []
    for raw_serial in sorted(set(titles) | set(explicit) | set(serial_overrides)):
        title = titles.get(raw_serial, "")
        try:
            serial = normalize_serial(raw_serial)
        except ValueError:
            unresolved.append({"serial": raw_serial, "title": title, "reason": "non_disc_product_code", "candidate_igdb_ids": []})
            continue
        if serial in serial_overrides:
            candidates, method = {serial_overrides[serial]}, "reviewed_serial_override"
        elif explicit.get(serial):
            candidates, method = explicit[serial], "database_serial"
        elif normalize_title(title) in title_overrides:
            candidates, method = {title_overrides[normalize_title(title)]}, "reviewed_title_alias"
        else:
            candidates, method = title_index[normalize_title(title)], "unique_normalized_title"
        if len(candidates) != 1:
            unresolved.append({"serial": serial, "title": title, "reason": "ambiguous" if candidates else "no_exact_match", "candidate_igdb_ids": sorted(candidates)})
            continue
        key = next(iter(candidates))
        if key not in games:
            raise ValueError(f"Serial {serial} references absent game {key}")
        serials[serial] = {"igdb_id": int(key), "path": games[key].get("path"), "title": title, "match_method": method}
        games[key]["serials"].append(serial)
    plan = {"schema_version": 1, "platform": "Sony PlayStation Portable", "image_size": size,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sources": {"catalog_sha256": digest(database), "titles_sha256": digest(titles_path),
                        "overrides_sha256": digest(overrides_path) if overrides_path else None},
            "games": games, "serials": serials}
    return plan, {"unresolved_serials": unresolved, "games_without_serials": [int(k) for k, g in games.items() if not g["serials"]]}


def fetch_cover(output: Path, game: dict, previous: dict | None, attempts: int) -> dict:
    if game["status"] == "missing_source":
        return game
    target = output / game["path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    if previous and previous.get("status") == "downloaded" and previous.get("source_url") == game["source_url"] and target.is_file():
        try:
            metadata = inspect_image(target)
            if metadata["sha256"] == previous.get("sha256"):
                return dict(game, **metadata, status="downloaded")
        except (ValueError, OSError):
            pass
    temporary = target.with_suffix(target.suffix + ".part")
    error = "Download failed"
    for attempt in range(attempts):
        retry_after = None
        try:
            request = Request(game["source_url"], headers={"User-Agent": "EmuCoreA-Cover-Exporter/1.0"})
            with urlopen(request, timeout=30) as response:
                final = urlsplit(response.url)
                if final.scheme != "https" or final.hostname != "images.igdb.com":
                    raise ValueError("Unexpected image redirect")
                if int(response.headers.get("Content-Length", "0")) > MAX_BYTES:
                    raise ValueError("Image exceeds download limit")
                with temporary.open("wb") as f:
                    total = 0
                    while chunk := response.read(65536):
                        total += len(chunk)
                        if total > MAX_BYTES:
                            raise ValueError("Image exceeds download limit")
                        f.write(chunk)
            metadata = inspect_image(temporary)
            expected = "JPEG" if target.suffix == ".jpg" else "PNG"
            if metadata["format"] != expected:
                raise ValueError("Image format does not match its extension")
            os.replace(temporary, target)
            return dict(game, **metadata, status="downloaded")
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            error = f"{type(exc).__name__}: {exc}"
            if isinstance(exc, HTTPError):
                if exc.code in (400, 401, 403, 404, 410):
                    break
                value = exc.headers.get("Retry-After", "")
                retry_after = min(int(value), 60) if value.isdigit() else None
            if attempt + 1 < attempts:
                time.sleep(retry_after if retry_after is not None else 2 ** attempt)
        finally:
            temporary.unlink(missing_ok=True)
    return dict(game, status="failed", error=error)


def save_outputs(output: Path, plan: dict, report: dict, download: bool) -> dict:
    games = plan["games"]
    report["summary"] = {"games": len(games), "mapped_serials": len(plan["serials"]),
                         "unresolved_serials": len(report["unresolved_serials"]),
                         "downloaded": sum(g["status"] == "downloaded" for g in games.values()),
                         "failed": sum(g["status"] in ("failed", "missing_source") for g in games.values())}
    report["download_failures"] = [{"igdb_id": g["igdb_id"], "name": g["name"], "error": g.get("error")} for g in games.values() if g["status"] in ("failed", "missing_source")]
    report["small_images"] = [g["igdb_id"] for g in games.values() if g.get("height", 1000) < 374]
    index = {s: {"igdb_id": entry["igdb_id"], "path": entry["path"]} for s, entry in plan["serials"].items()
             if not download or games[str(entry["igdb_id"])]["status"] == "downloaded"}
    atomic_json(output / "manifest.json", plan)
    atomic_json(output / "serials.json", index)
    atomic_json(output / "review.json", report)
    return report["summary"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=ROOT / "app/src/main/assets/catalog/games.db")
    parser.add_argument("--titles", type=Path, default=ROOT / "app/src/main/assets/catalog/psp_titles.json")
    parser.add_argument("--overrides", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", choices=("cover_big_2x", "720p", "1080p"), default="1080p")
    parser.add_argument("--download", action="store_true", help="Without this flag only a review plan is produced")
    parser.add_argument("--workers", type=int, choices=range(1, 5), default=3)
    parser.add_argument("--attempts", type=int, choices=range(1, 6), default=3)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    lock = output / ".export.lock"
    try:
        lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        parser.error(f"Another export may be running: {lock}. Remove only after confirming it stopped.")
    os.close(lock_fd)
    try:
        plan, report = build_plan(args.database, args.titles, args.overrides, args.size)
        previous_path = output / "manifest.json"
        previous = json.loads(previous_path.read_text(encoding="utf-8")).get("games", {}) if previous_path.is_file() else {}
        if args.download:
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                pending = {pool.submit(fetch_cover, output, game, previous.get(key), args.attempts): key for key, game in plan["games"].items()}
                for count, future in enumerate(as_completed(pending), 1):
                    key = pending[future]
                    plan["games"][key] = future.result()
                    if count % 50 == 0:
                        summary = save_outputs(output, plan, report, True)
                        print(f"{count}/{len(pending)} {summary}", flush=True)
        summary = save_outputs(output, plan, report, args.download)
        print(json.dumps(summary, indent=2), flush=True)
        return 1 if args.download and summary["failed"] else 0
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
