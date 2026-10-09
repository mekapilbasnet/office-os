#!/usr/bin/env node
/**
 * validate-asset.cjs
 *
 * Validates marketing assets against brand guidelines.
 * Checks: file naming, format, file size, pixel dimensions (PNG, JPEG, GIF,
 * WebP; SVG is vector so its size is reported but not enforced; video
 * dimensions are not read), and registration in .assets/manifest.json.
 * It only reports problems and suggests a filename; it never renames or edits files.
 *
 * Usage:
 *   node validate-asset.cjs <asset-path>
 *   node validate-asset.cjs <asset-path> --json
 *
 * For color validation of images, use with extract-colors.cjs
 */

const fs = require("fs");
const path = require("path");

// Validation rules
const RULES = {
  naming: {
    pattern: /^[a-z]+_[a-z0-9-]+_[a-z0-9-]+_\d{8}(_[a-z0-9-]+)?\.[a-z]+$/,
    description:
      "{type}_{campaign}_{description}_{timestamp}_{variant}.{ext}",
    examples: [
      "banner_claude-launch_hero-image_20251209.png",
      "logo_brand-refresh_horizontal_20251209_dark.svg",
    ],
  },
  dimensions: {
    banner: { minWidth: 600, minHeight: 300 },
    logo: { minWidth: 100, minHeight: 100 },
    design: { minWidth: 800, minHeight: 600 },
    video: { minWidth: 640, minHeight: 480 },
    default: { minWidth: 100, minHeight: 100 },
  },
  fileSize: {
    image: { max: 5 * 1024 * 1024, recommended: 1 * 1024 * 1024 },
    video: { max: 100 * 1024 * 1024, recommended: 50 * 1024 * 1024 },
    svg: { max: 500 * 1024, recommended: 100 * 1024 },
  },
  formats: {
    image: ["png", "jpg", "jpeg", "webp", "gif"],
    vector: ["svg"],
    video: ["mp4", "mov", "webm"],
    document: ["pdf", "psd", "ai", "fig"],
  },
};

/**
 * Parse asset filename
 */
function parseFilename(filename) {
  const parts = filename.replace(/\.[^.]+$/, "").split("_");

  if (parts.length < 4) {
    return null;
  }

  return {
    type: parts[0],
    campaign: parts[1],
    description: parts[2],
    timestamp: parts[3],
    variant: parts.length > 4 ? parts[4] : null,
    extension: path.extname(filename).slice(1).toLowerCase(),
  };
}

/**
 * Validate filename convention
 */
function validateFilename(filename) {
  const issues = [];
  const suggestions = [];

  // Check pattern match
  if (!RULES.naming.pattern.test(filename)) {
    issues.push("Filename does not match naming convention");
    suggestions.push(`Expected format: ${RULES.naming.description}`);
    suggestions.push(`Examples: ${RULES.naming.examples.join(", ")}`);
  }

  // Parse and check components
  const parsed = parseFilename(filename);
  if (parsed) {
    // Check timestamp format
    if (!/^\d{8}$/.test(parsed.timestamp)) {
      issues.push("Timestamp should be YYYYMMDD format");
    }

    // Check kebab-case for campaign and description
    if (parsed.campaign && !/^[a-z0-9-]+$/.test(parsed.campaign)) {
      issues.push("Campaign name should be kebab-case");
    }

    if (parsed.description && !/^[a-z0-9-]+$/.test(parsed.description)) {
      issues.push("Description should be kebab-case");
    }

    // Check valid type
    const validTypes = [
      "banner",
      "logo",
      "design",
      "video",
      "infographic",
      "icon",
      "photo",
    ];
    if (!validTypes.includes(parsed.type)) {
      suggestions.push(`Consider using type: ${validTypes.join(", ")}`);
    }
  }

  return { valid: issues.length === 0, issues, suggestions, parsed };
}

/**
 * Validate file size
 */
function validateFileSize(filepath, extension) {
  const issues = [];
  const warnings = [];

  const stats = fs.statSync(filepath);
  const size = stats.size;

  let limits;
  if (RULES.formats.video.includes(extension)) {
    limits = RULES.fileSize.video;
  } else if (extension === "svg") {
    limits = RULES.fileSize.svg;
  } else {
    limits = RULES.fileSize.image;
  }

  if (size > limits.max) {
    issues.push(
      `File size (${formatBytes(size)}) exceeds maximum (${formatBytes(
        limits.max
      )})`
    );
  } else if (size > limits.recommended) {
    warnings.push(
      `File size (${formatBytes(size)}) exceeds recommended (${formatBytes(
        limits.recommended
      )})`
    );
  }

  return { valid: issues.length === 0, issues, warnings, size };
}

/**
 * Validate file format
 */
function validateFormat(extension) {
  const issues = [];
  const info = { category: null };

  const allFormats = [
    ...RULES.formats.image,
    ...RULES.formats.vector,
    ...RULES.formats.video,
    ...RULES.formats.document,
  ];

  if (!allFormats.includes(extension)) {
    issues.push(`Unsupported file format: .${extension}`);
    return { valid: false, issues, info };
  }

  // Determine category
  if (RULES.formats.image.includes(extension)) info.category = "image";
  else if (RULES.formats.vector.includes(extension)) info.category = "vector";
  else if (RULES.formats.video.includes(extension)) info.category = "video";
  else if (RULES.formats.document.includes(extension))
    info.category = "document";

  return { valid: true, issues, info };
}

/**
 * Read pixel dimensions from an image file header (no dependencies).
 * Returns { width, height } or null if the format is unsupported/unreadable.
 */
function readImageDimensions(filepath, extension) {
  let buf;
  try {
    buf = fs.readFileSync(filepath);
  } catch {
    return null;
  }

  if (extension === "png") {
    // 8-byte signature, then IHDR: width @16, height @20 (big-endian)
    if (buf.length >= 24 && buf.toString("ascii", 12, 16) === "IHDR") {
      return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
    }
    return null;
  }

  if (extension === "gif") {
    if (buf.length >= 10 && buf.toString("ascii", 0, 3) === "GIF") {
      return { width: buf.readUInt16LE(6), height: buf.readUInt16LE(8) };
    }
    return null;
  }

  if (extension === "jpg" || extension === "jpeg") {
    if (buf.length < 4 || buf[0] !== 0xff || buf[1] !== 0xd8) return null;
    let pos = 2;
    while (pos + 9 < buf.length) {
      if (buf[pos] !== 0xff) { pos++; continue; }
      const marker = buf[pos + 1];
      if (marker === 0xff) { pos++; continue; }
      // Standalone markers carry no length
      if (marker === 0xd8 || (marker >= 0xd0 && marker <= 0xd7) || marker === 0x01) { pos += 2; continue; }
      const len = buf.readUInt16BE(pos + 2);
      // SOF0..SOF15 except DHT(C4), JPG(C8), DAC(CC)
      if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) {
        return { height: buf.readUInt16BE(pos + 5), width: buf.readUInt16BE(pos + 7) };
      }
      pos += 2 + len;
    }
    return null;
  }

  if (extension === "webp") {
    if (buf.length < 30 || buf.toString("ascii", 0, 4) !== "RIFF" || buf.toString("ascii", 8, 12) !== "WEBP") return null;
    const fourcc = buf.toString("ascii", 12, 16);
    if (fourcc === "VP8X") {
      return { width: 1 + buf.readUIntLE(24, 3), height: 1 + buf.readUIntLE(27, 3) };
    }
    if (fourcc === "VP8L") {
      const bits = buf.readUInt32LE(21);
      return { width: (bits & 0x3fff) + 1, height: ((bits >> 14) & 0x3fff) + 1 };
    }
    if (fourcc === "VP8 ") {
      return { width: buf.readUInt16LE(26) & 0x3fff, height: buf.readUInt16LE(28) & 0x3fff };
    }
    return null;
  }

  if (extension === "svg") {
    const text = buf.toString("utf-8", 0, Math.min(buf.length, 4096));
    const tag = text.match(/<svg\b[^>]*>/i);
    if (!tag) return null;
    const num = (name) => {
      const m = tag[0].match(new RegExp(`(?:^|\\s)${name}\\s*=\\s*["']\\s*([0-9.]+)(?:px)?\\s*["']`, "i"));
      return m ? parseFloat(m[1]) : null;
    };
    let width = num("width");
    let height = num("height");
    if (width == null || height == null) {
      const vb = tag[0].match(/viewBox\s*=\s*["']\s*[-0-9.]+[\s,]+[-0-9.]+[\s,]+([0-9.]+)[\s,]+([0-9.]+)\s*["']/i);
      if (vb) { width = parseFloat(vb[1]); height = parseFloat(vb[2]); }
    }
    return width != null && height != null ? { width, height } : null;
  }

  return null;
}

/**
 * Validate pixel dimensions against RULES.dimensions for the asset type
 * (the first "_" part of the filename; unknown types use "default").
 */
function validateDimensions(filepath, extension, assetType) {
  const issues = [];
  const warnings = [];
  const isVideo = RULES.formats.video.includes(extension);
  const isDocument = RULES.formats.document.includes(extension);
  if (isVideo || isDocument) {
    return { checked: false, valid: true, issues, warnings, reason: "dimensions are not read for this format" };
  }

  const dims = readImageDimensions(filepath, extension);
  if (!dims) {
    warnings.push("Could not read image dimensions");
    return { checked: false, valid: true, issues, warnings };
  }

  // SVG is resolution independent: report only.
  if (extension === "svg") {
    return { checked: true, valid: true, issues, warnings, ...dims, enforced: false };
  }

  const rule = RULES.dimensions[assetType] || RULES.dimensions.default;
  if (dims.width < rule.minWidth || dims.height < rule.minHeight) {
    issues.push(
      `Dimensions ${dims.width}x${dims.height} are below the minimum ${rule.minWidth}x${rule.minHeight} for "${RULES.dimensions[assetType] ? assetType : "default"}" assets`
    );
  }
  return { checked: true, valid: issues.length === 0, issues, warnings, ...dims, rule };
}

/**
 * Check if asset exists in manifest
 */
function checkManifest(filepath) {
  const manifestPath = path.join(process.cwd(), ".assets", "manifest.json");

  if (!fs.existsSync(manifestPath)) {
    return { registered: false, message: "Manifest not found" };
  }

  try {
    const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf-8"));
    const relativePath = path.relative(process.cwd(), filepath);
    const found = manifest.assets?.find(
      (a) => a.path === relativePath || a.path === filepath
    );

    return {
      registered: !!found,
      message: found ? "Asset registered in manifest" : "Asset not in manifest",
      asset: found,
    };
  } catch {
    return { registered: false, message: "Error reading manifest" };
  }
}

/**
 * Generate suggested filename
 */
function suggestFilename(original, parsed) {
  if (!parsed) return null;

  const today = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  const type = parsed.type || "asset";
  const campaign = parsed.campaign || "general";
  const description = parsed.description || "untitled";
  const ext = parsed.extension || "png";

  return `${type}_${campaign}_${description}_${today}.${ext}`;
}

/**
 * Format bytes to human readable
 */
function formatBytes(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

/**
 * Main validation function
 */
function validateAsset(assetPath) {
  const results = {
    path: assetPath,
    filename: path.basename(assetPath),
    valid: true,
    issues: [],
    warnings: [],
    suggestions: [],
    checks: {},
  };

  // Check file exists
  if (!fs.existsSync(assetPath)) {
    results.valid = false;
    results.issues.push(`File not found: ${assetPath}`);
    return results;
  }

  const filename = path.basename(assetPath);
  const extension = path.extname(filename).slice(1).toLowerCase();

  // 1. Validate filename
  const filenameResult = validateFilename(filename);
  results.checks.filename = filenameResult;
  if (!filenameResult.valid) {
    results.issues.push(...filenameResult.issues);
    results.suggestions.push(...filenameResult.suggestions);
  }

  // 2. Validate format
  const formatResult = validateFormat(extension);
  results.checks.format = formatResult;
  if (!formatResult.valid) {
    results.issues.push(...formatResult.issues);
  }

  // 3. Validate file size
  const sizeResult = validateFileSize(assetPath, extension);
  results.checks.fileSize = sizeResult;
  if (!sizeResult.valid) {
    results.issues.push(...sizeResult.issues);
  }
  results.warnings.push(...sizeResult.warnings);

  // 4. Validate pixel dimensions
  const assetType = (filenameResult.parsed && filenameResult.parsed.type) || filename.split("_")[0];
  const dimResult = validateDimensions(assetPath, extension, assetType);
  results.checks.dimensions = dimResult;
  results.issues.push(...dimResult.issues);
  results.warnings.push(...dimResult.warnings);

  // 5. Check manifest registration
  const manifestResult = checkManifest(assetPath);
  results.checks.manifest = manifestResult;
  if (!manifestResult.registered) {
    results.warnings.push("Asset not registered in manifest.json");
    results.suggestions.push(
      "Register asset in .assets/manifest.json for tracking"
    );
  }

  // 6. Suggest corrected filename if needed
  if (!filenameResult.valid && filenameResult.parsed) {
    const suggested = suggestFilename(filename, filenameResult.parsed);
    if (suggested) {
      results.suggestions.push(`Suggested filename: ${suggested}`);
    }
  }

  // Overall validity
  results.valid = results.issues.length === 0;

  return results;
}

/**
 * Format output for console
 */
function formatOutput(results) {
  const lines = [];

  lines.push("\n" + "=".repeat(60));
  lines.push(`ASSET VALIDATION: ${results.filename}`);
  lines.push("=".repeat(60));

  lines.push(`\nStatus: ${results.valid ? "PASS" : "FAIL"}`);
  lines.push(`Path: ${results.path}`);

  if (results.issues.length > 0) {
    lines.push("\nISSUES:");
    results.issues.forEach((issue) => lines.push(`  - ${issue}`));
  }

  if (results.warnings.length > 0) {
    lines.push("\nWARNINGS:");
    results.warnings.forEach((warning) => lines.push(`  - ${warning}`));
  }

  if (results.suggestions.length > 0) {
    lines.push("\nSUGGESTIONS:");
    results.suggestions.forEach((suggestion) =>
      lines.push(`  - ${suggestion}`)
    );
  }

  // File size info
  if (results.checks.fileSize?.size) {
    lines.push(`\nFile Size: ${formatBytes(results.checks.fileSize.size)}`);
  }

  if (results.checks.dimensions?.width) {
    const d = results.checks.dimensions;
    lines.push(`Dimensions: ${d.width}x${d.height}px`);
  }

  lines.push("\n" + "=".repeat(60));

  return lines.join("\n");
}

/**
 * Main
 */
function main() {
  const args = process.argv.slice(2);
  const jsonOutput = args.includes("--json");
  const assetPath = args.find((a) => !a.startsWith("--"));

  if (!assetPath) {
    console.error("Usage: node validate-asset.cjs <asset-path> [--json]");
    console.error("\nExamples:");
    console.error(
      "  node validate-asset.cjs assets/banners/social-media/banner_launch_hero_20251209.png"
    );
    console.error(
      "  node validate-asset.cjs assets/logos/icon-only/logo-icon.svg --json"
    );
    process.exit(1);
  }

  // Resolve path
  const resolvedPath = path.isAbsolute(assetPath)
    ? assetPath
    : path.join(process.cwd(), assetPath);

  // Validate
  const results = validateAsset(resolvedPath);

  // Output
  if (jsonOutput) {
    console.log(JSON.stringify(results, null, 2));
  } else {
    console.log(formatOutput(results));
  }

  // Exit with appropriate code
  process.exit(results.valid ? 0 : 1);
}

if (require.main === module) {
  main();
}

module.exports = { validateAsset, validateFilename, readImageDimensions, validateDimensions };
