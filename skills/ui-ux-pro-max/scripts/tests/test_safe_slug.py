#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for safe_slug and the persisted-file writer in design_system.py."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import design_system  # noqa: E402
from design_system import safe_slug  # noqa: E402


class SafeSlugTests(unittest.TestCase):
    def test_ascii_names_are_lowercased_and_dashed(self):
        self.assertEqual("my-project", safe_slug("My Project"))
        self.assertEqual("ops_console-2", safe_slug("Ops_Console 2"))

    def test_non_latin_names_are_kept(self):
        self.assertEqual("नेपाल", safe_slug("नेपाल"))  # Devanagari with vowel signs
        self.assertEqual("東京-カフェ", safe_slug("東京 カフェ"))
        self.assertEqual("café-ünï", safe_slug("Café Ünï"))

    def test_different_non_latin_names_do_not_collide(self):
        self.assertNotEqual(safe_slug("नेपाल"), safe_slug("काठमाडौं"))

    def test_symbol_only_names_get_a_stable_hash_not_a_shared_default(self):
        a, b = safe_slug("///"), safe_slug("!!!")
        self.assertTrue(a.startswith("default-"))
        self.assertNotEqual(a, b)
        self.assertEqual(a, safe_slug("///"))

    def test_empty_and_none_use_fallback(self):
        self.assertEqual("default", safe_slug(""))
        self.assertEqual("default", safe_slug(None))
        self.assertEqual("page", safe_slug("", "page"))

    def test_path_traversal_is_impossible(self):
        for name in ("../../etc/passwd", "..\\..\\x", "a/b", "/abs", "."):
            slug = safe_slug(name)
            self.assertNotIn("/", slug)
            self.assertNotIn("\\", slug)
            self.assertNotIn(".", slug)


class WritePersistedFileTests(unittest.TestCase):
    def test_falls_back_when_hard_links_are_unsupported(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "MASTER.md"
            with mock.patch.object(os, "link", side_effect=PermissionError("no hard links")):
                design_system._write_persisted_file(target, "hello", force=False)
            self.assertEqual("hello", target.read_text(encoding="utf-8"))
            self.assertEqual([target.name], os.listdir(tmp))  # temp file cleaned up

    def test_existing_file_is_not_overwritten_even_without_hard_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "MASTER.md"
            target.write_text("original", encoding="utf-8")
            with mock.patch.object(os, "link", side_effect=PermissionError("no hard links")):
                with self.assertRaises(FileExistsError):
                    design_system._write_persisted_file(target, "new", force=False)
            self.assertEqual("original", target.read_text(encoding="utf-8"))

    def test_default_path_still_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "MASTER.md"
            design_system._write_persisted_file(target, "one", force=False)
            with self.assertRaises(FileExistsError):
                design_system._write_persisted_file(target, "two", force=False)
            design_system._write_persisted_file(target, "two", force=True)
            self.assertEqual("two", target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
