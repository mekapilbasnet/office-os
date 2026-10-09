"""Tests for the brand scripts (unittest; no pytest needed).

- sync-brand-to-tokens.cjs must run on its documented happy path (bundled
  starter guidelines), create assets/ when missing, generate the CSS itself and
  not overwrite tokens.brand with a hard-coded name.
- extract-colors.cjs must reject `--brand-file` with no value instead of
  crashing with a TypeError.
- validate-asset.cjs must read image dimensions without dependencies.

Skipped automatically when `node` is not installed.
"""

import json
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
BRAND_DIR = SCRIPTS.parent
SYNC = SCRIPTS / "sync-brand-to-tokens.cjs"
EXTRACT = SCRIPTS / "extract-colors.cjs"
VALIDATE = SCRIPTS / "validate-asset.cjs"
BRAND_STARTER = BRAND_DIR / "templates" / "brand-guidelines-starter.md"
NODE = shutil.which("node")


def run_node(script, cwd, *args):
    # The scripts print emoji; decode as UTF-8 explicitly so a non-UTF-8
    # locale cannot break the harness.
    return subprocess.run(
        [NODE, str(script), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def make_png(width, height, rgb):
    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    rows = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows))
        + chunk(b"IEND", b"")
    )


@unittest.skipUnless(NODE, "node not available")
class SyncBrandToTokensTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.project = Path(self._tmp.name)

    def write_guidelines(self, text=None):
        (self.project / "docs").mkdir()
        target = self.project / "docs" / "brand-guidelines.md"
        if text is None:
            shutil.copy(BRAND_STARTER, target)
        else:
            target.write_text(text, encoding="utf-8")

    def test_parses_bundled_starter_template_and_writes_css(self):
        self.write_guidelines()  # note: no assets/ directory exists yet

        result = run_node(SYNC, self.project)

        self.assertNotIn("TypeError", result.stderr, result.stderr)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)

        tokens = json.loads((self.project / "assets" / "design-tokens.json").read_text())
        primitive = tokens["primitive"]["color"]
        self.assertEqual("#2563EB", primitive["primary"]["500"]["$value"])
        self.assertEqual("#8B5CF6", primitive["secondary"]["500"]["$value"])
        self.assertEqual("#10B981", primitive["accent"]["500"]["$value"])
        # The starter guideline has no brand title: nothing hard-coded is written.
        self.assertNotIn("ClaudeKit", json.dumps(tokens))

        css = (self.project / "assets" / "design-tokens.css").read_text()
        self.assertIn(":root {", css)
        self.assertIn("--primitive-color-primary-500: #2563EB;", css)
        self.assertIn("--color-primary: var(--primitive-color-primary-500);", css)
        self.assertIn('[data-theme="dark"]', css)

    def test_brand_name_comes_from_guideline_title(self):
        starter = BRAND_STARTER.read_text(encoding="utf-8")
        self.write_guidelines(starter.replace("# Brand Guidelines v1.0", "# Acme Brand Guidelines v1.0", 1))

        result = run_node(SYNC, self.project)

        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        tokens = json.loads((self.project / "assets" / "design-tokens.json").read_text())
        self.assertEqual("Acme", tokens["brand"])

    def test_digits_inside_brand_name_are_kept(self):
        starter = BRAND_STARTER.read_text(encoding="utf-8")
        for title, expected in (
            ("# V8 Motors Brand Guide", "V8 Motors"),
            ("# Acme Brand Guidelines v2", "Acme"),
            ("# Studio 54 Brand Guidelines 1.0", "Studio 54"),
        ):
            with self.subTest(title=title):
                project = Path(tempfile.mkdtemp(dir=self._tmp.name))
                (project / "docs").mkdir()
                (project / "docs" / "brand-guidelines.md").write_text(
                    starter.replace("# Brand Guidelines v1.0", title, 1), encoding="utf-8"
                )
                result = run_node(SYNC, project)
                self.assertEqual(0, result.returncode, result.stderr + result.stdout)
                tokens = json.loads((project / "assets" / "design-tokens.json").read_text())
                self.assertEqual(expected, tokens["brand"])

    def test_status_colors_never_reference_missing_shades(self):
        self.write_guidelines()

        result = run_node(SYNC, self.project)

        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        tokens = json.loads((self.project / "assets" / "design-tokens.json").read_text())
        prim = tokens["primitive"]["color"]
        sem = tokens["semantic"]["color"]
        for key in ("success", "success-light", "error", "error-light"):
            value = sem[key]["$value"]
            if value.startswith("{"):
                _, _, hue, shade = value.strip("{}").split(".")
                self.assertIn(shade, prim[hue], f"{key} -> {value}")
        css = (self.project / "assets" / "design-tokens.css").read_text()
        self.assertNotIn("primitive-color-green-300", css)
        self.assertNotIn("primitive-color-red-300", css)

    def test_existing_brand_name_is_kept_when_guideline_is_untitled(self):
        self.write_guidelines()
        (self.project / "assets").mkdir()
        (self.project / "assets" / "design-tokens.json").write_text(
            json.dumps({"brand": "My Existing Brand", "primitive": {}}), encoding="utf-8"
        )

        result = run_node(SYNC, self.project)

        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        tokens = json.loads((self.project / "assets" / "design-tokens.json").read_text())
        self.assertEqual("My Existing Brand", tokens["brand"])

    def test_reports_missing_guidelines(self):
        result = run_node(SYNC, self.project)

        self.assertEqual(1, result.returncode)
        self.assertIn("Brand guidelines not found", result.stderr)


@unittest.skipUnless(NODE, "node not available")
class ExtractColorsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.project = Path(self._tmp.name)
        (self.project / "docs").mkdir()
        shutil.copy(BRAND_STARTER, self.project / "docs" / "brand-guidelines.md")

    def test_brand_file_without_value_is_a_clean_error(self):
        result = run_node(EXTRACT, self.project, "--brand-file")

        self.assertEqual(2, result.returncode)
        self.assertNotIn("TypeError", result.stderr)
        self.assertIn("--brand-file requires a path", result.stderr)

    def test_png_colors_are_compared_with_the_palette(self):
        (self.project / "logo.png").write_bytes(make_png(4, 4, (37, 99, 235)))

        result = run_node(EXTRACT, self.project, "logo.png", "--json")

        self.assertEqual(0, result.returncode, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual("#2563EB", data["colors"][0]["hex"])
        self.assertTrue(data["colors"][0]["onBrand"])
        self.assertEqual(100, data["compliance"])

    def test_unsupported_format_is_reported_not_faked(self):
        (self.project / "photo.jpg").write_bytes(b"\xff\xd8\xff\xd9")

        result = run_node(EXTRACT, self.project, "photo.jpg")

        self.assertEqual(3, result.returncode)
        self.assertIn("magick", result.stderr)


@unittest.skipUnless(NODE, "node not available")
class ValidateAssetTests(unittest.TestCase):
    def test_png_dimensions_are_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset = Path(tmp) / "logo_brand_mark_20250101.png"
            asset.write_bytes(make_png(4, 4, (0, 0, 0)))

            result = run_node(VALIDATE, tmp, str(asset), "--json")

            self.assertEqual(1, result.returncode)
            data = json.loads(result.stdout)
            self.assertEqual(4, data["checks"]["dimensions"]["width"])
            self.assertTrue(any("below the minimum" in i for i in data["issues"]), data["issues"])

    def test_large_png_passes_dimension_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset = Path(tmp) / "logo_brand_mark_20250101.png"
            asset.write_bytes(make_png(120, 120, (0, 0, 0)))

            result = run_node(VALIDATE, tmp, str(asset), "--json")

            data = json.loads(result.stdout)
            self.assertEqual([], data["checks"]["dimensions"]["issues"])


if __name__ == "__main__":
    unittest.main()
