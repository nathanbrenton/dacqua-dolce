import { useEffect, useState } from "react";
import type { GalleryPhoto, MediaAsset } from "./productMediaRegistry";

/** Never show the browser broken-image icon when an optional media path is unavailable. */
export function ApprovedMediaImage({ photo, thumbnail = false, fallbackAlt = "", loading = "lazy" }: {
  photo: GalleryPhoto; thumbnail?: boolean; fallbackAlt?: string; loading?: "eager" | "lazy";
}) {
  const [failed, setFailed] = useState<string[]>([]);
  useEffect(() => { setFailed([]); }, [photo.media.src, photo.media.thumbnail]);
  const candidates: MediaAsset[] = [photo.media, ...(photo.fallback ? [photo.fallback] : [])];
  const source = candidates.map((asset) => thumbnail ? asset.thumbnail : asset.src)
    .find((path) => !failed.includes(path));
  return source ? <img src={source} alt={thumbnail ? "" : photo.alt || fallbackAlt}
    loading={loading} decoding="async" onError={() => setFailed((current) => [...current, source])} />
    : <span className="product-media-placeholder product-media-missing" role="img"
        aria-label={photo.alt || fallbackAlt || "Image unavailable"}>
        Photograph unavailable
      </span>;
}
