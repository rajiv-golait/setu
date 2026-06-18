/** Generate PNG PWA icons from public/icon.svg (run: node scripts/generate-pwa-icons.mjs) */
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const src = path.join(root, "public", "icon.svg");
const iconsDir = path.join(root, "public", "icons");

await mkdir(iconsDir, { recursive: true });

for (const size of [192, 512]) {
  await sharp(src)
    .resize(size, size, { fit: "contain", background: "#0F766E" })
    .png()
    .toFile(path.join(iconsDir, `icon-${size}x${size}.png`));
}

await sharp(src)
  .resize(180, 180, { fit: "contain", background: "#0F766E" })
  .png()
  .toFile(path.join(root, "public", "apple-touch-icon.png"));

console.log("PWA icons written to public/icons/ and public/apple-touch-icon.png");
