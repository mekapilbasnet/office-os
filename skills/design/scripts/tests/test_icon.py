import unittest

from _loader import load_module

icon = load_module("icon_generate", "icon/generate.py")


class ApplyViewboxSizeTests(unittest.TestCase):
    SVG = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" '
        'height="24" fill="none" stroke="currentColor" stroke-width="2">'
        '<path stroke-width="2" d="M1 1"/><rect width="10" height="10"/></svg>'
    )

    def test_stroke_width_is_preserved(self):
        out = icon.apply_viewbox_size(self.SVG, 48)
        self.assertIn('stroke-width="2"', out)
        self.assertNotIn('stroke-width="48"', out)
        self.assertIn('width="48"', out.split(">")[0])
        self.assertIn('height="48"', out.split(">")[0])

    def test_child_elements_are_untouched(self):
        out = icon.apply_viewbox_size(self.SVG, 48)
        self.assertIn('<rect width="10" height="10"/>', out)

    def test_width_height_added_when_missing(self):
        out = icon.apply_viewbox_size('<svg viewBox="0 0 24 24"><path stroke-width="2"/></svg>', 16)
        root = out.split(">")[0]
        self.assertIn('width="16"', root)
        self.assertIn('height="16"', root)
        self.assertIn('stroke-width="2"', out)

    def test_viewbox_added_for_numeric_size_so_it_can_scale(self):
        out = icon.apply_viewbox_size('<svg width="32" height="32"><path/></svg>', 64)
        self.assertIn('viewBox="0 0 32 32"', out)
        self.assertIn('width="64"', out)


class SanitizeTests(unittest.TestCase):
    XL = 'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"'

    def assertRejected(self, svg):
        with self.assertRaises(ValueError, msg=svg):
            icon.sanitize_svg(svg)

    def test_script_elements_are_removed(self):
        out = icon.sanitize_svg('<svg><script>alert(1)</script><path d="M0 0"/></svg>')
        self.assertNotIn("script", out.lower())
        self.assertIn('<path d="M0 0"', out)

    def test_event_handler_attributes_are_removed(self):
        out = icon.sanitize_svg('<svg onload="x()"><rect onclick=\'y()\' width="1"/></svg>')
        self.assertNotIn("onload", out)
        self.assertNotIn("onclick", out)
        self.assertIn('width="1"', out)

    def test_event_handlers_case_insensitive(self):
        out = icon.sanitize_svg('<svg OnLoad="x()"><rect ONCLICK="y()" width="1"/></svg>')
        self.assertNotIn("onload", out.lower())
        self.assertNotIn("onclick", out.lower())

    def test_javascript_hrefs_are_removed(self):
        out = icon.sanitize_svg(
            f'<svg {self.XL}><a href="javascript:alert(1)"><a xlink:href=" java&#x73;cript:alert(2)">'
            '<a href="#ok"></a></a></a></svg>'
        )
        self.assertNotIn("javascript", out.lower())
        self.assertNotIn("alert", out)
        self.assertIn('href="#ok"', out)

    def test_control_chars_in_scheme_are_removed(self):
        out = icon.sanitize_svg('<svg><a href="jav&#x09;ascript:alert(1)"/></svg>')
        self.assertNotIn("alert", out)

    def test_malformed_attribute_tricks_are_rejected(self):
        self.assertRejected("<svg/onload=alert(1)>")
        self.assertRejected('<svg viewBox="0 0 24 24"onload="x"></svg>')
        self.assertRejected('<svg><a/href="javascript:alert(1)">x</a></svg>')

    def test_nested_reassembly_is_rejected(self):
        self.assertRejected("<svg><scr<script></script>ipt>x</scr<script></script>ipt></svg>")

    def test_smil_href_animation_is_removed(self):
        out = icon.sanitize_svg(
            '<svg><a href="#x"><set attributeName="href" to="javascript:alert(1)"/>'
            '<animate attributeName="href" values="javascript:alert(2)"/></a></svg>'
        )
        self.assertNotIn("javascript", out.lower())
        self.assertNotIn("<set", out)
        self.assertNotIn("<animate", out)

    def test_smil_javascript_value_on_other_attribute_is_removed(self):
        out = icon.sanitize_svg(
            '<svg><a><animate attributeName="x" from="0" to="javascript:alert(1)"/></a></svg>'
        )
        self.assertNotIn("javascript", out.lower())

    def test_benign_animation_is_kept(self):
        svg = '<svg><circle r="1"><animate attributeName="r" values="1;2;1" dur="1s"/></circle></svg>'
        self.assertEqual(svg, icon.sanitize_svg(svg))

    def test_use_with_data_or_external_href_is_removed(self):
        out = icon.sanitize_svg(
            f'<svg {self.XL}><use href="data:image/svg+xml,&lt;svg/&gt;"/>'
            '<use xlink:href="http://evil.example/x.svg#a"/><use href="#local"/></svg>'
        )
        self.assertNotIn("data:", out)
        self.assertNotIn("evil.example", out)
        self.assertIn('href="#local"', out)

    def test_style_import_and_external_url_removed(self):
        out = icon.sanitize_svg(
            "<svg><style>@import url(http://evil.example/a.css);</style>"
            "<style>.a{fill:url(http://evil.example/f)}</style>"
            "<style>.b{fill:url(#grad)}</style><path d=\"M0 0\"/></svg>"
        )
        self.assertNotIn("evil.example", out)
        self.assertNotIn("@import", out)
        self.assertIn(".b{fill:url(#grad)}", out)

    def test_style_attribute_external_url_removed(self):
        out = icon.sanitize_svg('<svg><rect style="fill:url(http://evil.example/x)" width="1"/></svg>')
        self.assertNotIn("evil.example", out)
        self.assertIn('width="1"', out)

    def test_foreign_object_removed(self):
        out = icon.sanitize_svg(
            f'<svg {self.XL}><foreignObject><div/></foreignObject><path d="M0 0"/></svg>'
        )
        self.assertNotIn("foreignObject", out)
        self.assertIn("<path", out)

    def test_doctype_and_entities_are_rejected(self):
        self.assertRejected('<!DOCTYPE svg [<!ENTITY x "y">]><svg>&x;</svg>')
        self.assertRejected('<!DOCTYPE svg><svg/>')

    def test_non_svg_root_is_rejected(self):
        self.assertRejected("<html><body/></html>")

    def test_sanitised_output_is_well_formed_svg(self):
        out = icon.sanitize_svg(
            f'<svg {self.XL} viewBox="0 0 24 24" onload="x()"><path d="M1 1"/></svg>'
        )
        import xml.etree.ElementTree as ET
        root = ET.fromstring(out)
        self.assertTrue(root.tag.endswith("svg"))
        self.assertNotIn("onload", out)

    def test_clean_svg_is_unchanged(self):
        svg = '<svg viewBox="0 0 24 24"><title>Gear</title><path d="M1 1" fill="currentColor"/></svg>'
        self.assertEqual(svg, icon.sanitize_svg(svg))


class ColorValidationTests(unittest.TestCase):
    def test_valid_colors(self):
        for value in ("#fff", "#6366F1", "#6366F180", "red", "RebeccaPurple"):
            self.assertEqual(value, icon.validate_color(value))

    def test_invalid_colors(self):
        for value in ('red"/><script>', "javascript:1", "#12", "#GGGGGG", "rgb(1,2,3)", "not-a-color", ""):
            with self.assertRaises(ValueError, msg=value):
                icon.validate_color(value)

    def test_apply_color_rejects_markup(self):
        with self.assertRaises(ValueError):
            icon.apply_color("<svg/>", 'red" onload="x')


class ImportTests(unittest.TestCase):
    def test_module_imports_without_the_gemini_sdk(self):
        # load_module above already imported it; --list-styles data must exist.
        self.assertIn("outlined", icon.ICON_STYLES)


if __name__ == "__main__":
    unittest.main()
