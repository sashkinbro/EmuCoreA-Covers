import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from export_psp_covers import build_plan, image_url, normalize_serial, inspect_image, fetch_cover


class CoverTests(unittest.TestCase):
    def test_regional_serials_share_exact_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = root / "catalog.json"
            titles = root / "titles.json"
            catalog.write_text(json.dumps({"games": [{"igdb_id": 1, "name": "Example", "cover_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/co1.jpg"}]}))
            titles.write_text(json.dumps({"ULUS-12345": "Example", "ULES12345": "Example", "ULJM12345": "Other"}))
            plan, report = build_plan(catalog, titles, None, "1080p")
            self.assertEqual(set(plan["serials"]), {"ULUS12345", "ULES12345"})
            self.assertEqual(len(plan["games"]["1"]["serials"]), 2)
            self.assertEqual(report["unresolved_serials"][0]["serial"], "ULJM12345")
            data = json.loads(catalog.read_text())
            data["games"].append(dict(data["games"][0], igdb_id=2))
            catalog.write_text(json.dumps(data))
            plan, report = build_plan(catalog, titles, None, "1080p")
            self.assertFalse(plan["serials"])
            self.assertEqual(sum(r["reason"] == "ambiguous" for r in report["unresolved_serials"]), 2)

    def test_source_validation(self):
        for url in ("http://images.igdb.com/igdb/image/upload/t_cover_big/co1.jpg", "https://evil.example/co1.jpg", "https://images.igdb.com/../co1.jpg"):
            with self.assertRaises(ValueError):
                image_url(url, "1080p")
        self.assertEqual(normalize_serial("ules-12345"), "ULES12345")
        with self.assertRaises(ValueError):
            normalize_serial("../../escape")

    def test_resume_requires_valid_image_and_matching_checksum(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "cover.jpg"
            Image.new("RGB", (20, 30), "blue").save(target)
            metadata = inspect_image(target)
            game = {"status": "pending", "path": "cover.jpg", "source_url": "unused"}
            previous = dict(game, **metadata, status="downloaded")
            self.assertEqual(fetch_cover(root, game, previous, 0)["status"], "downloaded")
            target.write_bytes(b"invalid")
            self.assertEqual(fetch_cover(root, game, previous, 0)["status"], "failed")


if __name__ == "__main__":
    unittest.main()
