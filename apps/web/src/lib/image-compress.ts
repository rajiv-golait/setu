/** Client-side image compression for low-bandwidth rural uploads. */
export async function compressImage(file: File, maxEdge = 1280, quality = 0.7): Promise<File> {
  if (!file.type.startsWith("image/")) return file;
  if (file.size < 400_000) return file;

  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, maxEdge / Math.max(bitmap.width, bitmap.height));
  const w = Math.round(bitmap.width * scale);
  const h = Math.round(bitmap.height * scale);

  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  if (!ctx) return file;
  ctx.drawImage(bitmap, 0, 0, w, h);
  bitmap.close();

  const blob = await new Promise<Blob | null>((resolve) =>
    canvas.toBlob(resolve, "image/jpeg", quality),
  );
  if (!blob || blob.size >= file.size) return file;

  const base = file.name.replace(/\.[^.]+$/, "") || "document";
  return new File([blob], `${base}.jpg`, { type: "image/jpeg" });
}

export function wasCompressed(original: File, result: File): boolean {
  return result !== original && result.size < original.size;
}
