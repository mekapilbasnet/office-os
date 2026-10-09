import tempfile
import unittest
from pathlib import Path

from _loader import load_module

cip_core = load_module("cip_core", "cip/core.py")
render = load_module("cip_render_html", "cip/render-html.py")


def names(rows):
    return [r["Deliverable"] for r in rows]


class DeliverableParsingTests(unittest.TestCase):
    def test_multiword_deliverable_is_matched_as_a_whole(self):
        self.assertEqual(["Business Card"], names(cip_core.parse_key_deliverables("Business cards")))
        self.assertEqual(["ID Badge"], names(cip_core.parse_key_deliverables("ID badges")))

    def test_comma_and_semicolon_separated_lists(self):
        got = names(cip_core.parse_key_deliverables("business card, letterhead; polo shirt"))
        self.assertEqual(["Business Card", "Letterhead", "Polo Shirt"], got)

    def test_unseparated_industry_text_does_not_split_by_word(self):
        got = names(cip_core.parse_key_deliverables("Business cards office signage digital templates vehicle"))
        self.assertEqual("Business Card", got[0])
        self.assertIn("Document Template", got)
        # "business" alone must not have produced a second Business Card row
        self.assertEqual(len(got), len(set(got)))

    def test_generic_adjectives_alone_do_not_match(self):
        self.assertEqual([], cip_core.parse_key_deliverables("Premium stationery"))
        self.assertEqual([], cip_core.parse_key_deliverables("digital, custom, corporate"))

    def test_generic_adjective_is_ignored_next_to_a_real_noun(self):
        self.assertEqual(["Packaging Box"], names(cip_core.parse_key_deliverables("Premium packaging")))

    def test_vehicle_maps_to_the_van_deliverable(self):
        self.assertEqual(["Van"], names(cip_core.parse_key_deliverables("vehicle")))
        self.assertIn("Van", names(cip_core.parse_key_deliverables("Business cards office signage digital templates vehicle")))

    def test_limit_and_empty_input(self):
        self.assertEqual([], cip_core.parse_key_deliverables(""))
        self.assertEqual([], cip_core.parse_key_deliverables(None))
        self.assertLessEqual(len(cip_core.parse_key_deliverables("letterhead, envelope, folder, notebook, pen, mug", limit=3)), 3)

    def test_brief_uses_parsed_deliverables(self):
        brief = cip_core.get_cip_brief("Acme", "technology")
        self.assertEqual("Business Card", brief["recommended_deliverables"][0]["Deliverable"])


class RenderHtmlTests(unittest.TestCase):
    def test_word_boundary_filename_matching(self):
        # "car" must not match the brand "Carlos"
        self.assertNotEqual("Car Branding", render.get_deliverable_info("carlos-letterhead-20260101")["title"])
        self.assertEqual("Letterhead", render.get_deliverable_info("carlos-letterhead-20260101")["title"])
        self.assertEqual("Car Branding", render.get_deliverable_info("acme-car-20260101")["title"])
        self.assertEqual("Polo Shirt", render.get_deliverable_info("acme_polo_shirt_1")["title"])

    def test_longest_match_wins(self):
        # "office signage" must beat any single-word key inside it
        self.assertEqual("Office Signage", render.get_deliverable_info("x-office-signage-1")["title"])

    def test_unknown_filename_falls_back_to_title_case(self):
        self.assertEqual("Mystery Item", render.get_deliverable_info("mystery-item")["title"])

    def test_generated_html_escapes_user_text(self):
        png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
            b"\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xcf\xc0\xf0\x1f\x00\x05\x00\x01\xff"
            b"\x89\x99=\x1d\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        with tempfile.TemporaryDirectory() as tmp:
            images = Path(tmp)
            (images / "x<img src=a onerror=1>-letterhead-1.png").write_bytes(png)
            out = images / "out.html"
            render.generate_html("<script>alert(1)</script>", "technology", images, out)
            page = out.read_text(encoding="utf-8")
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)
        self.assertNotIn("<img src=a", page)
        self.assertNotIn('loading="lazy"', page)  # data URIs are never lazy-loaded


if __name__ == "__main__":
    unittest.main()
