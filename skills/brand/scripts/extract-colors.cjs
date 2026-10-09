#!/usr/bin/env node
/**
 * extract-colors.cjs
 *
 * Extract dominant colors from an image and compare them against the brand
 * palette in the brand guidelines. Pure Node.js, no dependencies.
 *
 * What it can read:
 *   .svg  every hex colour in the file (#RGB / #RRGGBB), counted
 *   .png  8-bit, non-interlaced PNGs (greyscale, RGB, palette, +alpha);
 *         pixels are bucketed and the most frequent colours reported
 *   other (JPEG, WebP, ...) are NOT decoded - the script prints an ImageMagick
 *         command you can run instead.
 *
 * Usage:
 *   node extract-colors.cjs <image-path>
 *   node extract-colors.cjs <image-path> --brand-file <path>
 *   node extract-colors.cjs <image-path> --json
 *   node extract-colors.cjs --palette  # Show brand palette from guidelines
 */

const fs = require("fs");
const path = require("path");
const zlib = require("zlib");

// Default brand guidelines path
const DEFAULT_GUIDELINES_PATH = "docs/brand-guidelines.md";

/**
 * Extract hex colors from markdown content
 */
function extractHexColors(text) {
  const hexPattern = /#[0-9A-Fa-f]{6}\b/g;
  return [...new Set(text.match(hexPattern) || [])];
}

/**
 * Parse brand guidelines for color palette
 */
function parseBrandColors(guidelinesPath) {
  const resolvedPath = path.isAbsolute(guidelinesPath)
    ? guidelinesPath
    : path.join(process.cwd(), guidelinesPath);

  if (!fs.existsSync(resolvedPath)) {
    return null;
  }

  const content = fs.readFileSync(resolvedPath, "utf-8");

  const palette = {
    primary: [],
    secondary: [],
    neutral: [],
    semantic: [],
    all: [],
  };

  // Extract colors from different sections
  const sections = [
    { name: "primary", regex: /### Primary[\s\S]*?(?=###|##|$)/i },
    { name: "secondary", regex: /### Secondary[\s\S]*?(?=###|##|$)/i },
    { name: "neutral", regex: /### Neutral[\s\S]*?(?=###|##|$)/i },
    { name: "semantic", regex: /### Semantic[\s\S]*?(?=###|##|$)/i },
  ];

  sections.forEach(({ name, regex }) => {
    const match = content.match(regex);
    if (match) {
      const colors = extractHexColors(match[0]);
      palette[name] = colors;
      palette.all.push(...colors);
    }
  });

  // Dedupe all
  palette.all = [...new Set(palette.all)];

  return palette;
}

/**
 * Convert hex to RGB
 */
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null;
}

/**
 * Convert RGB to hex
 */
function rgbToHex(r, g, b) {
  return (
    "#" +
    [r, g, b]
      .map((x) => {
        const hex = Math.round(x).toString(16);
        return hex.length === 1 ? "0" + hex : hex;
      })
      .join("")
      .toUpperCase()
  );
}

/**
 * Calculate color distance (Euclidean in RGB space)
 */
function colorDistance(color1, color2) {
  const rgb1 = typeof color1 === "string" ? hexToRgb(color1) : color1;
  const rgb2 = typeof color2 === "string" ? hexToRgb(color2) : color2;

  if (!rgb1 || !rgb2) return Infinity;

  return Math.sqrt(
    Math.pow(rgb1.r - rgb2.r, 2) +
      Math.pow(rgb1.g - rgb2.g, 2) +
      Math.pow(rgb1.b - rgb2.b, 2)
  );
}

/**
 * Find nearest brand color
 */
function findNearestBrandColor(color, brandColors) {
  let nearest = null;
  let minDistance = Infinity;

  brandColors.forEach((brandColor) => {
    const distance = colorDistance(color, brandColor);
    if (distance < minDistance) {
      minDistance = distance;
      nearest = brandColor;
    }
  });

  return { color: nearest, distance: minDistance };
}

/**
 * Calculate brand compliance percentage
 * Distance threshold: 50 (out of max ~441 for RGB)
 */
function calculateCompliance(extractedColors, brandColors, threshold = 50) {
  if (!extractedColors || extractedColors.length === 0) return 100;
  if (!brandColors || brandColors.length === 0) return 0;

  let matchCount = 0;

  extractedColors.forEach((color) => {
    const nearest = findNearestBrandColor(color, brandColors);
    if (nearest.distance <= threshold) {
      matchCount++;
    }
  });

  return Math.round((matchCount / extractedColors.length) * 100);
}

/**
 * Generate ImageMagick command for color extraction
 */
function generateImageMagickCommand(imagePath, numColors = 10) {
  return `magick "${imagePath}" -colors ${numColors} -depth 8 -format "%c" histogram:info:`;
}

/**
 * Parse ImageMagick histogram output to extract colors
 */
function parseImageMagickOutput(output) {
  const colors = [];
  const lines = output.trim().split("\n");

  lines.forEach((line) => {
    // Match pattern like: 12345: (255,128,64) #FF8040 srgb(255,128,64)
    const hexMatch = line.match(/#([0-9A-Fa-f]{6})/);
    const countMatch = line.match(/^\s*(\d+):/);

    if (hexMatch) {
      colors.push({
        hex: "#" + hexMatch[1].toUpperCase(),
        count: countMatch ? parseInt(countMatch[1]) : 0,
      });
    }
  });

  // Sort by count (most common first)
  colors.sort((a, b) => b.count - a.count);

  return colors;
}

/**
 * Expand #RGB to #RRGGBB and upper-case.
 */
function normalizeHex(hex) {
  let h = hex.replace("#", "");
  if (h.length === 3) h = h.split("").map((c) => c + c).join("");
  return "#" + h.toUpperCase();
}

/**
 * Count hex colours written in an SVG (or any text) file.
 */
function extractColorsFromSvg(text) {
  const counts = new Map();
  for (const m of text.matchAll(/#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b/g)) {
    const hex = normalizeHex(m[0]);
    counts.set(hex, (counts.get(hex) || 0) + 1);
  }
  return [...counts.entries()]
    .map(([hex, count]) => ({ hex, count }))
    .sort((a, b) => b.count - a.count);
}

/**
 * Decode an 8-bit, non-interlaced PNG into { width, height, channels, data }.
 * Returns { error } for anything unsupported.
 */
function decodePng(buf) {
  const SIG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  if (buf.length < 33 || !buf.subarray(0, 8).equals(SIG)) return { error: "not a PNG file" };

  let width = 0, height = 0, bitDepth = 0, colorType = 0, interlace = 0;
  let palette = null;
  const idat = [];
  let pos = 8;
  while (pos + 8 <= buf.length) {
    const len = buf.readUInt32BE(pos);
    const type = buf.toString("ascii", pos + 4, pos + 8);
    const body = buf.subarray(pos + 8, pos + 8 + len);
    if (type === "IHDR") {
      width = body.readUInt32BE(0);
      height = body.readUInt32BE(4);
      bitDepth = body[8];
      colorType = body[9];
      interlace = body[12];
    } else if (type === "PLTE") palette = body;
    else if (type === "IDAT") idat.push(body);
    else if (type === "IEND") break;
    pos += 12 + len;
  }

  if (bitDepth !== 8) return { error: "only 8-bit PNGs are supported" };
  if (interlace) return { error: "interlaced PNGs are not supported" };
  const channelsByType = { 0: 1, 2: 3, 3: 1, 4: 2, 6: 4 };
  const channels = channelsByType[colorType];
  if (!channels) return { error: "unsupported PNG colour type" };
  if (colorType === 3 && !palette) return { error: "palette PNG without PLTE chunk" };
  if (width * height > 50_000_000) return { error: "image too large" };

  let raw;
  try {
    raw = zlib.inflateSync(Buffer.concat(idat));
  } catch (e) {
    return { error: `corrupt PNG data (${e.message})` };
  }

  const stride = width * channels;
  if (raw.length < (stride + 1) * height) return { error: "truncated PNG data" };
  const out = Buffer.alloc(stride * height);
  for (let y = 0; y < height; y++) {
    const filter = raw[y * (stride + 1)];
    const src = y * (stride + 1) + 1;
    const dst = y * stride;
    for (let x = 0; x < stride; x++) {
      const a = x >= channels ? out[dst + x - channels] : 0;
      const b = y > 0 ? out[dst - stride + x] : 0;
      const c = x >= channels && y > 0 ? out[dst - stride + x - channels] : 0;
      let v = raw[src + x];
      if (filter === 1) v += a;
      else if (filter === 2) v += b;
      else if (filter === 3) v += (a + b) >> 1;
      else if (filter === 4) {
        const p = a + b - c;
        const pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
        v += pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
      } else if (filter > 4) return { error: "bad PNG filter" };
      out[dst + x] = v & 0xff;
    }
  }
  return { width, height, channels, colorType, palette, data: out };
}

/**
 * Most frequent colours of a decoded PNG (16 levels per channel buckets,
 * mostly-transparent pixels ignored).
 */
function dominantColorsFromPng(png, limit = 10) {
  const { width, height, channels, colorType, palette, data } = png;
  const buckets = new Map();
  for (let i = 0; i < width * height; i++) {
    const o = i * channels;
    let r, g, b, a = 255;
    if (colorType === 0) { r = g = b = data[o]; }
    else if (colorType === 4) { r = g = b = data[o]; a = data[o + 1]; }
    else if (colorType === 3) { const k = data[o] * 3; r = palette[k]; g = palette[k + 1]; b = palette[k + 2]; }
    else { r = data[o]; g = data[o + 1]; b = data[o + 2]; if (channels === 4) a = data[o + 3]; }
    if (a < 128) continue;
    const key = ((r >> 4) << 8) | ((g >> 4) << 4) | (b >> 4);
    const bucket = buckets.get(key) || { count: 0, r: 0, g: 0, b: 0 };
    bucket.count++; bucket.r += r; bucket.g += g; bucket.b += b;
    buckets.set(key, bucket);
  }
  return [...buckets.values()]
    .sort((x, y) => y.count - x.count)
    .slice(0, limit)
    .map((k) => ({ hex: rgbToHex(k.r / k.count, k.g / k.count, k.b / k.count), count: k.count }));
}

/**
 * Extract colours from an image file. Returns { colors } or { unsupported, reason }.
 */
function extractImageColors(filePath, limit = 10) {
  const ext = path.extname(filePath).toLowerCase();
  if (ext === ".svg") {
    return { colors: extractColorsFromSvg(fs.readFileSync(filePath, "utf-8")).slice(0, limit) };
  }
  if (ext === ".png") {
    const png = decodePng(fs.readFileSync(filePath));
    if (png.error) return { unsupported: true, reason: png.error };
    return { colors: dominantColorsFromPng(png, limit) };
  }
  return { unsupported: true, reason: `${ext || "this"} format is not decoded by this script` };
}

/**
 * Display brand palette
 */
function displayPalette(palette) {
  console.log("\n" + "=".repeat(50));
  console.log("BRAND COLOR PALETTE");
  console.log("=".repeat(50));

  if (palette.primary.length > 0) {
    console.log("\nPrimary Colors:");
    palette.primary.forEach((c) => console.log(`  ${c}`));
  }

  if (palette.secondary.length > 0) {
    console.log("\nSecondary Colors:");
    palette.secondary.forEach((c) => console.log(`  ${c}`));
  }

  if (palette.neutral.length > 0) {
    console.log("\nNeutral Colors:");
    palette.neutral.forEach((c) => console.log(`  ${c}`));
  }

  if (palette.semantic.length > 0) {
    console.log("\nSemantic Colors:");
    palette.semantic.forEach((c) => console.log(`  ${c}`));
  }

  console.log("\n" + "=".repeat(50));
  console.log(`Total: ${palette.all.length} colors in brand palette`);
  console.log("=".repeat(50) + "\n");
}

/**
 * Parse CLI arguments. Throws on a flag that is missing its value.
 */
function parseArgs(argv) {
  const opts = { json: false, palette: false, brandFile: DEFAULT_GUIDELINES_PATH, imagePath: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--json") opts.json = true;
    else if (a === "--palette") opts.palette = true;
    else if (a === "--brand-file") {
      const value = argv[i + 1];
      if (!value || value.startsWith("--")) throw new Error("--brand-file requires a path");
      opts.brandFile = value;
      i++;
    } else if (a.startsWith("--")) throw new Error(`Unknown option: ${a}`);
    else if (!opts.imagePath) opts.imagePath = a;
    else throw new Error(`Unexpected argument: ${a}`);
  }
  return opts;
}

/**
 * Main function
 */
function main() {
  let opts;
  try {
    opts = parseArgs(process.argv.slice(2));
  } catch (e) {
    console.error(e.message);
    console.error("Usage: node extract-colors.cjs [<image-path>] [--brand-file <path>] [--palette] [--json]");
    process.exit(2);
  }
  const { json: jsonOutput, palette: showPalette, brandFile, imagePath } = opts;

  // Load brand palette
  const brandPalette = parseBrandColors(brandFile);

  if (!brandPalette) {
    console.error(`Brand guidelines not found at: ${brandFile}`);
    console.error(`Create brand guidelines or specify path with --brand-file`);
    process.exit(1);
  }

  // Show palette mode
  if (showPalette || !imagePath) {
    if (jsonOutput) {
      console.log(JSON.stringify(brandPalette, null, 2));
    } else {
      displayPalette(brandPalette);
      if (!imagePath) {
        console.log("To compare an image (SVG or 8-bit PNG) against this palette:");
        console.log("  node extract-colors.cjs <image-path>\n");
      }
    }
    return;
  }

  // Resolve image path
  const resolvedPath = path.isAbsolute(imagePath)
    ? imagePath
    : path.join(process.cwd(), imagePath);

  if (!fs.existsSync(resolvedPath)) {
    console.error(`Image not found: ${resolvedPath}`);
    process.exit(1);
  }

  const extraction = extractImageColors(resolvedPath);
  const threshold = 50;

  if (extraction.unsupported) {
    const result = {
      image: resolvedPath,
      supported: false,
      reason: extraction.reason,
      suggestion: generateImageMagickCommand(resolvedPath),
      brandColors: brandPalette.all,
    };
    if (jsonOutput) console.log(JSON.stringify(result, null, 2));
    else {
      console.error(`Cannot extract colours: ${extraction.reason}.`);
      console.error("This script reads SVG and 8-bit PNG files only. For other formats run ImageMagick:");
      console.error(`  ${result.suggestion}`);
    }
    process.exit(3);
  }

  const colors = extraction.colors.map((c) => {
    const nearest = findNearestBrandColor(c.hex, brandPalette.all);
    return {
      hex: c.hex,
      count: c.count,
      nearestBrandColor: nearest.color,
      distance: Math.round(nearest.distance),
      onBrand: nearest.distance <= threshold,
    };
  });
  const compliance = calculateCompliance(colors.map((c) => c.hex), brandPalette.all, threshold);

  if (jsonOutput) {
    console.log(JSON.stringify({ image: resolvedPath, colors, compliance, threshold, brandColors: brandPalette.all }, null, 2));
    return;
  }

  console.log("\n" + "=".repeat(60));
  console.log("IMAGE COLORS vs BRAND PALETTE");
  console.log("=".repeat(60));
  console.log(`Image: ${resolvedPath}`);
  console.log(`Brand colors loaded: ${brandPalette.all.length}\n`);
  if (colors.length === 0) console.log("No opaque colours found.");
  colors.forEach((c) => {
    const status = c.onBrand ? "on-brand " : "off-brand";
    console.log(`  ${c.hex}  x${c.count}  ${status}  nearest ${c.nearestBrandColor || "none"} (distance ${c.distance})`);
  });
  console.log(`\nBrand compliance: ${compliance}% of dominant colours within distance ${threshold} of a brand colour`);
  console.log("=".repeat(60) + "\n");
}

// Export functions for use as module
module.exports = {
  parseBrandColors,
  hexToRgb,
  rgbToHex,
  colorDistance,
  findNearestBrandColor,
  calculateCompliance,
  parseImageMagickOutput,
  parseArgs,
  extractColorsFromSvg,
  decodePng,
  dominantColorsFromPng,
  extractImageColors,
};

// Run if called directly
if (require.main === module) {
  main();
}
