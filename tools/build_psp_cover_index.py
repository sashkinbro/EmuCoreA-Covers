"""Build a compact client index from verified flat and 3D manifests."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
from export_psp_covers import atomic_json, normalize_title, digest


def build(root):
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    three = json.loads((root / "3d-manifest.json").read_text(encoding="utf-8"))
    games, titles = {}, defaultdict(set)
    for key, game in manifest["games"].items():
        if game["status"] != "downloaded":
            continue
        if digest(root / game["path"]) != game["sha256"]:
            raise ValueError(f"Invalid flat cover: {key}")
        record = {name: game[name] for name in ("path", "source_url", "sha256")}
        if key in three:
            image = three[key]
            if image["source_sha256"] != game["sha256"] or digest(root / image["path"]) != image["sha256"]:
                raise ValueError(f"Invalid 3D cover: {key}")
            record.update(path_3d=image["path"], sha256_3d=image["sha256"])
        games[key] = record
        titles[normalize_title(game["name"])].add(key)
    return {"schema_version": 1, "games": games,
            "serials": {s: str(v["igdb_id"]) for s, v in manifest["serials"].items() if str(v["igdb_id"]) in games},
            "titles": {name: next(iter(ids)) for name, ids in titles.items() if len(ids) == 1}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    atomic_json(args.output, build(args.repository))
