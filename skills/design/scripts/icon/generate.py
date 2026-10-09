#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Icon Generation Script using Gemini 3.1 Pro Preview API
Generates SVG icons via text generation (SVG is XML text format)

Model: gemini-3.1-pro-preview - best thinking, token efficiency, factual consistency

Usage:
    python generate.py --prompt "settings gear icon" --style outlined
    python generate.py --prompt "shopping cart" --style filled --color "#6366F1"
    python generate.py --name "dashboard" --category navigation --style duotone
    python generate.py --prompt "cloud upload" --batch 4 --output-dir ./icons
    python generate.py --prompt "user profile" --sizes "16,24,32,48"
"""

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

# Shared helpers live one directory up (design/scripts/_common.py)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import load_env  # noqa: E402

# Only loads GEMINI_API_KEY, GOOGLE_API_KEY, ATLASCLOUD_API_KEY, MUAPI_API_KEY
load_env()


def _require_genai():
    """Import the Gemini SDK lazily so --help / --list-styles work without it."""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("Error: google-genai package not installed.")
        print("Install with: pip install google-genai")
        return None
    return genai, types


# ============ CONFIGURATION ============
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-3.1-pro-preview"

# Icon styles with SVG-specific instructions
ICON_STYLES = {
    "outlined": "outlined stroke icons, 2px stroke width, no fill, clean open paths",
    "filled": "solid filled icons, no stroke, flat color fills, bold shapes",
    "duotone": "duotone style with primary color at full opacity and secondary color at 30% opacity, layered shapes",
    "thin": "thin line icons, 1px or 1.5px stroke width, delicate minimalist lines",
    "bold": "bold thick line icons, 3px stroke width, heavy weight, impactful",
    "rounded": "rounded icons with round line caps and joins, soft corners, friendly feel",
    "sharp": "sharp angular icons, square line caps and mitered joins, precise edges",
    "flat": "flat design icons, solid fills, no gradients or shadows, geometric simplicity",
    "gradient": "linear or radial gradient fills, modern vibrant color transitions",
    "glassmorphism": "glassmorphism style with semi-transparent fills, blur backdrop effect simulation, frosted glass",
    "pixel": "pixel art style icons on a grid, retro 8-bit aesthetic, crisp edges",
    "hand-drawn": "hand-drawn sketch style, slightly irregular strokes, organic feel, imperfect lines",
    "isometric": "isometric 3D projection, 30-degree angles, dimensional depth",
    "glyph": "simple glyph style, single solid shape, minimal detail, pictogram",
    "animated-ready": "animated-ready SVG with named groups and IDs for CSS/JS animation targets",
}

ICON_CATEGORIES = {
    "navigation": "arrows, menus, hamburger, chevrons, home, back, forward, breadcrumb",
    "action": "edit, delete, save, download, upload, share, copy, paste, print, search",
    "communication": "email, chat, phone, video call, notification, bell, message bubble",
    "media": "play, pause, stop, skip, volume, microphone, camera, image, gallery",
    "file": "document, folder, archive, attachment, cloud, database, storage",
    "user": "person, group, avatar, profile, settings, lock, key, shield",
    "commerce": "cart, bag, wallet, credit card, receipt, tag, gift, store",
    "data": "chart, graph, analytics, dashboard, table, filter, sort, calendar",
    "development": "code, terminal, bug, git, API, server, database, deploy",
    "social": "heart, star, thumbs up, bookmark, flag, trophy, badge, crown",
    "weather": "sun, moon, cloud, rain, snow, wind, thunder, temperature",
    "map": "pin, location, compass, globe, route, directions, map marker",
}

# SVG generation prompt template
SVG_PROMPT_TEMPLATE = """Generate a clean, production-ready SVG icon.

Requirements:
- Output ONLY valid SVG code, nothing else
- ViewBox: "0 0 {viewbox} {viewbox}"
- Use currentColor for strokes/fills (inherits CSS color)
- No embedded fonts or text elements unless specifically requested
- No raster images or external references
- Optimized paths with minimal nodes
- Accessible: include <title> element with icon description
{style_instructions}
{color_instructions}
{size_instructions}

Icon to generate: {prompt}

Output the SVG code only, wrapped in ```svg``` code block."""

SVG_BATCH_PROMPT_TEMPLATE = """Generate {count} distinct SVG icon variations for: {prompt}

Requirements for EACH icon:
- Output ONLY valid SVG code
- ViewBox: "0 0 {viewbox} {viewbox}"
- Use currentColor for strokes/fills (inherits CSS color)
- No embedded fonts, raster images, or external references
- Optimized paths with minimal nodes
- Include <title> element with icon description
{style_instructions}
{color_instructions}

Generate {count} different visual interpretations. Output each SVG in a separate ```svg``` code block.
Label each variation (e.g., "Variation 1: [brief description]")."""


def extract_svgs(text):
    """Extract SVG code blocks from model response"""
    svgs = []

    # Try ```svg code blocks first
    pattern = r'```svg\s*\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        svgs.extend(matches)

    # Fallback: try ```xml code blocks
    if not svgs:
        pattern = r'```xml\s*\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        svgs.extend(matches)

    # Fallback: try bare <svg> tags
    if not svgs:
        pattern = r'(<svg[^>]*>.*?</svg>)'
        matches = re.findall(pattern, text, re.DOTALL)
        svgs.extend(matches)

    # Clean up extracted SVGs
    cleaned = []
    for svg in svgs:
        svg = svg.strip()
        if not svg.startswith('<svg'):
            # Try to find <svg> within the extracted text
            match = re.search(r'(<svg[^>]*>.*?</svg>)', svg, re.DOTALL)
            if match:
                svg = match.group(1)
            else:
                continue
        cleaned.append(svg)

    return cleaned


CSS_NAMED_COLORS = frozenset("""
aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue
blueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk
crimson cyan darkblue darkcyan darkgoldenrod darkgray darkgreen darkgrey darkkhaki
darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon darkseagreen
darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink deepskyblue
dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite
gold goldenrod gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki
lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan
lightgoldenrodyellow lightgray lightgreen lightgrey lightpink lightsalmon lightseagreen
lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime limegreen linen
magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen
mediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream
mistyrose moccasin navajowhite navy oldlace olive olivedrab orange orangered orchid
palegoldenrod palegreen paleturquoise palevioletred papayawhip peachpuff peru pink plum
powderblue purple rebeccapurple red rosybrown royalblue saddlebrown salmon sandybrown
seagreen seashell sienna silver skyblue slateblue slategray slategrey snow springgreen
steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow
yellowgreen transparent
""".split())

_HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


def validate_color(value):
    """Return `value` if it is a hex colour or CSS named colour, else raise
    ValueError. The value ends up inside SVG markup, so nothing else is allowed."""
    value = str(value).strip()
    if _HEX_COLOR.match(value) or value.lower() in CSS_NAMED_COLORS:
        return value
    raise ValueError(
        f"Invalid colour {value!r}: use a hex value like #6366F1 or a CSS colour name"
    )


def _color_arg(value):
    """argparse type wrapper for --color."""
    try:
        return validate_color(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc))


def apply_color(svg_code, color):
    """Replace currentColor with specific color if provided"""
    if color:
        color = validate_color(color)
        # Replace currentColor with the specified color
        svg_code = svg_code.replace('currentColor', color)
        # If no currentColor was present, add fill/stroke color
        if color not in svg_code:
            svg_code = svg_code.replace('<svg', f'<svg color="{color}"', 1)
    return svg_code


# ---- SVG sanitising (model output is untrusted) ----
# The SVG is parsed as XML; anything that is not well-formed is rejected
# instead of being regex-repaired (regex repair is what browsers' lenient
# HTML-style parsing defeats, e.g. "<svg/onload=x>").
_SVG_NS = "http://www.w3.org/2000/svg"
_XLINK_NS = "http://www.w3.org/1999/xlink"
_DANGEROUS_ELEMENTS = {"script", "foreignobject", "iframe", "object", "embed"}
_ANIMATION_ELEMENTS = {"set", "animate", "animatetransform", "animatemotion"}
_URL_ATTRS_EXTERNAL_BLOCKED = {"use", "image", "feimage"}
_UNSAFE_SCHEMES = ("javascript:", "vbscript:", "data:")
_EXTERNAL_PREFIXES = ("http:", "https:", "//", "ftp:", "file:")
_CSS_URL = re.compile(r"url\(\s*([^)]*)\)", re.I)
_DECL = re.compile(r"<!\s*(?:DOCTYPE|ENTITY)", re.I)


def _local(name):
    return name.rsplit("}", 1)[-1] if isinstance(name, str) else ""


def _norm_url(value):
    """Lowercase and drop whitespace/control chars browsers ignore."""
    return re.sub(r"[\x00-\x20\x7f]+", "", value or "").lower()


def _css_is_unsafe(css):
    """True if CSS text pulls external resources or runs script."""
    low = css.lower()
    if "@import" in low or "expression(" in low or "javascript:" in low or "\\" in css:
        return True
    for m in _CSS_URL.finditer(css):
        target = _norm_url(m.group(1).strip("\"'"))
        if not target.startswith("#"):
            return True
    return False


def _attr_is_unsafe(tag, name, value):
    lname = _local(name).lower()
    if lname.startswith("on"):
        return True
    if lname == "href":
        url = _norm_url(value)
        if url.startswith(_UNSAFE_SCHEMES):
            return True
        if tag in _URL_ATTRS_EXTERNAL_BLOCKED and url.startswith(_EXTERNAL_PREFIXES):
            return True
    if "url(" in value.lower() or "@import" in value.lower() or lname == "style":
        return _css_is_unsafe(value)
    return False


def _element_is_unsafe(el):
    tag = _local(el.tag).lower()
    if not isinstance(el.tag, str):
        return True
    if "}" in el.tag and el.tag.split("}", 1)[0][1:] != _SVG_NS:
        return True  # foreign namespace (xhtml, etc.)
    if tag in _DANGEROUS_ELEMENTS:
        return True
    if tag == "style":
        return _css_is_unsafe("".join(el.itertext()))
    if tag in _ANIMATION_ELEMENTS:
        target = _local(el.get("attributeName", "")).lower()
        if target == "href" or target.startswith("on") or target == "style":
            return True
        for key in ("to", "from", "by", "values"):
            if _norm_url(el.get(key)).startswith(_UNSAFE_SCHEMES + _EXTERNAL_PREFIXES):
                return True
            if "javascript:" in _norm_url(el.get(key)):
                return True
    return False


def _clean_tree(el):
    """Sanitise el in place. Returns True if anything was removed."""
    changed = False
    for name in list(el.attrib):
        if _attr_is_unsafe(_local(el.tag).lower(), name, el.attrib[name]):
            del el.attrib[name]
            changed = True
    for child in list(el):
        if _element_is_unsafe(child):
            el.remove(child)
            changed = True
        else:
            changed = _clean_tree(child) or changed
    return changed


def sanitize_svg(svg_code):
    """Return a safe copy of svg_code, or raise ValueError if it is unsafe.

    The input must be well-formed XML with an <svg> root and no DOCTYPE or
    ENTITY declarations. Removed: script/foreignObject/iframe/object/embed and
    foreign-namespace elements, <set>/<animate*> that target href/on*/style or
    carry javascript:/data:/external values, <style> with @import or external
    url(), all on* attributes, and href/xlink:href with javascript:, vbscript:
    or data: URLs (plus external URLs on use/image/feImage).
    A SVG that needs no changes is returned unmodified.
    """
    if _DECL.search(svg_code):
        raise ValueError("SVG with DOCTYPE/ENTITY declarations is rejected")
    try:
        root = ET.fromstring(svg_code.strip())
    except ET.ParseError as exc:
        raise ValueError(f"SVG is not well-formed XML: {exc}")
    if _local(root.tag).lower() != "svg":
        raise ValueError("SVG root element is not <svg>")
    if _element_is_unsafe(root):
        raise ValueError("SVG root element is unsafe")
    if not _clean_tree(root):
        return svg_code
    ET.register_namespace("", _SVG_NS)
    ET.register_namespace("xlink", _XLINK_NS)
    return ET.tostring(root, encoding="unicode")


_SVG_OPEN_TAG = re.compile(r"""<svg\b(?:"[^"]*"|'[^']*'|[^>"'])*>""", re.I)


def _get_attr(tag, name):
    m = re.search(rf"""(?<![\w:-]){name}\s*=\s*("([^"]*)"|'([^']*)')""", tag, re.I)
    return (m.group(2) if m.group(2) is not None else m.group(3)) if m else None


def _set_attr(tag, name, value):
    """Set/replace attribute `name` on a single opening tag string."""
    pattern = re.compile(rf"""(?<![\w:-]){name}\s*=\s*(?:"[^"]*"|'[^']*')""", re.I)
    if pattern.search(tag):
        return pattern.sub(lambda _m: f'{name}="{value}"', tag, count=1)
    return re.sub(r"<svg\b", f'<svg {name}="{value}"', tag, count=1, flags=re.I)


def apply_viewbox_size(svg_code, size):
    """Set the rendered width/height of the root <svg> element to `size`.

    Only the root opening tag is touched (never stroke-width, child elements,
    etc.). The viewBox is kept, so the artwork scales; if the root has no
    viewBox but numeric width/height, one is added first so scaling works.
    """
    if not size:
        return svg_code
    match = _SVG_OPEN_TAG.search(svg_code)
    if not match:
        return svg_code
    tag = match.group(0)

    if _get_attr(tag, "viewBox") is None:
        w, h = _get_attr(tag, "width"), _get_attr(tag, "height")
        try:
            tag = _set_attr(tag, "viewBox", f"0 0 {float(w):g} {float(h):g}")
        except (TypeError, ValueError):
            pass

    tag = _set_attr(tag, "width", size)
    tag = _set_attr(tag, "height", size)
    return svg_code[:match.start()] + tag + svg_code[match.end():]


def _response_text(response):
    text = response.text if hasattr(response, 'text') else ""
    if not text:
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                text += part.text
    return text


def _build_prompt(prompt, style=None, category=None, name=None, color=None,
                  size=24, viewbox=24):
    style_instructions = ""
    if style and style in ICON_STYLES:
        style_instructions = f"- Style: {ICON_STYLES[style]}"

    color_instructions = "- Use currentColor for all strokes and fills"
    if color:
        color_instructions = f"- Use color: {color} for primary elements, currentColor for secondary"

    size_instructions = f"- Design for {size}px display size, optimize detail level accordingly"

    icon_prompt = prompt
    if category and category in ICON_CATEGORIES:
        icon_prompt = f"{prompt} (category: {ICON_CATEGORIES[category]})"
    if name:
        icon_prompt = f"'{name}' icon: {icon_prompt}"

    return SVG_PROMPT_TEMPLATE.format(
        prompt=icon_prompt,
        viewbox=viewbox,
        style_instructions=style_instructions,
        color_instructions=color_instructions,
        size_instructions=size_instructions
    )


def _generate_svg(prompt, style=None, category=None, name=None, color=None,
                  size=24, viewbox=24):
    """Call the model once and return sanitised SVG text (colour applied), or None."""
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not set")
        print("Set it with: export GEMINI_API_KEY='your-key'")
        return None

    sdk = _require_genai()
    if not sdk:
        return None
    genai, types = sdk

    client = genai.Client(api_key=GEMINI_API_KEY)
    full_prompt = _build_prompt(prompt, style, category, name, color, size, viewbox)

    print(f"Generating icon with {MODEL}...")
    print(f"Prompt: {prompt}")
    if style:
        print(f"Style: {style}")
    print()

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=4096,
            )
        )
        response_text = _response_text(response)
        svgs = extract_svgs(response_text)

        if not svgs:
            print("No valid SVG generated. Model response:")
            print(response_text[:500])
            return None

        return apply_color(sanitize_svg(svgs[0]), color)

    except Exception as e:
        print(f"Error generating icon: {e}")
        return None


def generate_icon(prompt, style=None, category=None, name=None,
                  color=None, size=24, output_path=None, viewbox=24):
    """Generate a single SVG icon using Gemini 3.1 Pro Preview"""
    svg_code = _generate_svg(prompt, style, category, name, color, size, viewbox)
    if svg_code is None:
        return None

    # Apply size
    svg_code = apply_viewbox_size(svg_code, size)

    # Determine output path
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = name or (prompt.split()[0] if prompt else "icon")
        slug = re.sub(r'[^a-zA-Z0-9_-]', '_', slug.lower())
        style_suffix = f"_{style}" if style else ""
        output_path = f"{slug}{style_suffix}_{timestamp}.svg"

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg_code)
    except OSError as e:
        print(f"Error saving icon: {e}")
        return None

    print(f"Icon saved to: {output_path}")
    return output_path


def generate_batch(prompt, count, output_dir, style=None, color=None,
                   viewbox=24, name=None):
    """Generate multiple icon variations"""

    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not set")
        return []

    sdk = _require_genai()
    if not sdk:
        return []
    genai, types = sdk

    client = genai.Client(api_key=GEMINI_API_KEY)
    os.makedirs(output_dir, exist_ok=True)

    # Build instructions
    style_instructions = ""
    if style and style in ICON_STYLES:
        style_instructions = f"- Style: {ICON_STYLES[style]}"

    color_instructions = "- Use currentColor for all strokes and fills"
    if color:
        color_instructions = f"- Use color: {color} for primary elements"

    full_prompt = SVG_BATCH_PROMPT_TEMPLATE.format(
        prompt=prompt,
        count=count,
        viewbox=viewbox,
        style_instructions=style_instructions,
        color_instructions=color_instructions
    )

    print(f"\n{'='*60}")
    print("  BATCH ICON GENERATION")
    print(f"  Model: {MODEL}")
    print(f"  Prompt: {prompt}")
    print(f"  Variants: {count}")
    print(f"  Output: {output_dir}")
    print(f"{'='*60}\n")

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.9,
                max_output_tokens=16384,
            )
        )

        response_text = _response_text(response)
        svgs = extract_svgs(response_text)

        if not svgs:
            print("No valid SVGs generated.")
            print(response_text[:500])
            return []

        results = []
        slug = name or re.sub(r'[^a-zA-Z0-9_-]', '_', prompt.split()[0].lower())
        style_suffix = f"_{style}" if style else ""

        for i, svg_code in enumerate(svgs[:count]):
            try:
                svg_code = apply_color(sanitize_svg(svg_code), color)
            except ValueError as exc:
                print(f"  [{i+1}/{len(svgs[:count])}] Skipped unsafe SVG: {exc}")
                continue
            filename = f"{slug}{style_suffix}_{i+1:02d}.svg"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(svg_code)

            results.append(filepath)
            print(f"  [{i+1}/{len(svgs[:count])}] Saved: {filename}")

        print(f"\n{'='*60}")
        print(f"  BATCH COMPLETE: {len(results)}/{count} icons generated")
        print(f"{'='*60}\n")

        return results

    except Exception as e:
        print(f"Error generating icons: {e}")
        return []


def generate_sizes(prompt, sizes, style=None, color=None, output_dir=None,
                   name=None, viewbox=24):
    """Generate the icon ONCE, then write it at several sizes.

    The artwork is rescaled by changing the root width/height; the viewBox is
    kept, so no extra API calls are needed per size.
    """
    if output_dir is None:
        output_dir = "."
    os.makedirs(output_dir, exist_ok=True)

    svg_code = _generate_svg(prompt, style=style, name=None, color=color,
                             size=max(sizes), viewbox=viewbox)
    if svg_code is None:
        return []

    results = []
    slug = name or re.sub(r'[^a-zA-Z0-9_-]', '_', prompt.split()[0].lower())
    style_suffix = f"_{style}" if style else ""

    for size in sizes:
        filepath = os.path.join(output_dir, f"{slug}{style_suffix}_{size}px.svg")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(apply_viewbox_size(svg_code, size))
        print(f"Icon saved to: {filepath}")
        results.append(filepath)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Generate SVG icons using Gemini 3.1 Pro Preview"
    )
    parser.add_argument("--prompt", "-p", type=str, help="Icon description")
    parser.add_argument("--name", "-n", type=str, help="Icon name (for filename)")
    parser.add_argument("--style", "-s", choices=list(ICON_STYLES.keys()),
                        help="Icon style")
    parser.add_argument("--category", "-c", choices=list(ICON_CATEGORIES.keys()),
                        help="Icon category for context")
    parser.add_argument("--color", type=_color_arg,
                        help="Primary color: hex (e.g. #6366F1) or CSS color name. Default: currentColor")
    parser.add_argument("--size", type=int, default=24,
                        help="Icon size in px (default: 24)")
    parser.add_argument("--viewbox", type=int, default=24,
                        help="SVG viewBox size (default: 24)")
    parser.add_argument("--output", "-o", type=str, help="Output file path")
    parser.add_argument("--output-dir", type=str, help="Output directory for batch")
    parser.add_argument("--batch", type=int,
                        help="Number of icon variants to generate")
    parser.add_argument("--sizes", type=str,
                        help="Comma-separated sizes (e.g. '16,24,32,48')")
    parser.add_argument("--list-styles", action="store_true",
                        help="List available icon styles")
    parser.add_argument("--list-categories", action="store_true",
                        help="List available icon categories")

    args = parser.parse_args()

    if args.list_styles:
        print("Available icon styles:")
        for style, desc in ICON_STYLES.items():
            print(f"  {style}: {desc[:70]}...")
        return

    if args.list_categories:
        print("Available icon categories:")
        for cat, desc in ICON_CATEGORIES.items():
            print(f"  {cat}: {desc}")
        return

    if not args.prompt and not args.name:
        parser.error("Either --prompt or --name is required")

    prompt = args.prompt or args.name

    # Multi-size mode
    if args.sizes:
        try:
            sizes = [int(s.strip()) for s in args.sizes.split(",") if s.strip()]
        except ValueError:
            parser.error("--sizes must be comma-separated integers, e.g. 16,24,32")
        if not sizes or any(sz <= 0 for sz in sizes):
            parser.error("--sizes must contain positive integers")
        results = generate_sizes(
            prompt=prompt,
            sizes=sizes,
            style=args.style,
            color=args.color,
            output_dir=args.output_dir or "./icons",
            name=args.name,
            viewbox=args.viewbox
        )
        if len(results) < len(sizes):
            sys.exit(1)
    # Batch mode
    elif args.batch:
        output_dir = args.output_dir or "./icons"
        results = generate_batch(
            prompt=prompt,
            count=args.batch,
            output_dir=output_dir,
            style=args.style,
            color=args.color,
            viewbox=args.viewbox,
            name=args.name
        )
        if not results:
            sys.exit(1)
    # Single icon
    else:
        result = generate_icon(
            prompt=prompt,
            style=args.style,
            category=args.category,
            name=args.name,
            color=args.color,
            size=args.size,
            output_path=args.output,
            viewbox=args.viewbox
        )
        if not result:
            sys.exit(1)


if __name__ == "__main__":
    main()
