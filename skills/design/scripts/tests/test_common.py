import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _loader import load_module

common = load_module("design_common", "_common.py")


class TokenizerTests(unittest.TestCase):
    def test_short_tokens_are_kept(self):
        self.assertEqual(["ai", "ui"], common.BM25().tokenize("AI UI"))
        self.assertEqual(["3d", "ux"], common.BM25().tokenize("3D, UX!"))

    def test_single_characters_are_dropped(self):
        self.assertEqual(["go"], common.BM25().tokenize("a go x"))

    def test_two_letter_query_finds_two_letter_term(self):
        index = common.BM25()
        index.fit(["ai assistant chat", "garden tools", "ui kit design"])
        ranked = index.score("AI UI")
        self.assertGreater(ranked[0][1], 0)
        self.assertIn(ranked[0][0], (0, 2))


class SearchCacheTests(unittest.TestCase):
    def test_csv_and_index_are_cached_per_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.csv"
            path.write_text("Name,Keywords\nAI chatbot,ai chat\nPlant,garden\n", encoding="utf-8")
            first = common.search_csv(path, ["Name", "Keywords"], ["Name"], "ai", 3)
            self.assertEqual([{"Name": "AI chatbot"}], first)

            with mock.patch.object(common.BM25, "fit", side_effect=AssertionError("rebuilt")):
                second = common.search_csv(path, ["Name", "Keywords"], ["Name"], "ai", 3)
            self.assertEqual(first, second)


class LoadEnvTests(unittest.TestCase):
    def test_only_known_keys_are_loaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text(
                "# comment\n"
                "GEMINI_API_KEY='abc'\n"
                "export MUAPI_API_KEY=\"m-key\"\n"
                "AWS_SECRET_ACCESS_KEY=leak\n"
                "GITHUB_TOKEN=leak\n",
                encoding="utf-8",
            )
            clean = {k: v for k, v in os.environ.items()
                     if k not in common.KNOWN_ENV_KEYS + ("AWS_SECRET_ACCESS_KEY", "GITHUB_TOKEN")}
            with mock.patch.dict(os.environ, clean, clear=True):
                loaded = common.load_env([env_file])
                self.assertEqual("abc", os.environ["GEMINI_API_KEY"])
                self.assertEqual("m-key", os.environ["MUAPI_API_KEY"])
                self.assertNotIn("AWS_SECRET_ACCESS_KEY", os.environ)
                self.assertNotIn("GITHUB_TOKEN", os.environ)
                self.assertEqual(["GEMINI_API_KEY", "MUAPI_API_KEY"], sorted(loaded))

    def test_existing_environment_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text("GEMINI_API_KEY=from-file\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "from-env"}):
                common.load_env([env_file])
                self.assertEqual("from-env", os.environ["GEMINI_API_KEY"])


if __name__ == "__main__":
    unittest.main()
