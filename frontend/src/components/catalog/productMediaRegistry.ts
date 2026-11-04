import publishedPhotoIndex from "./publishedPhotoIndex.json" with { type: "json" };
import photoCaptionOverrides from "./photoCaptionOverrides.json" with { type: "json" };
import photoSetIndex from "./photoSetIndex.json" with { type: "json" };

export type TankFinish = "stainless" | "neoprene";
export type PhotoSource = "ai-placeholder" | "legacy-original" | "product-photo";
/** PT54-G1: the first active gallery set is AI placeholders. Actual photography is not supplied yet. */
export const DEFAULT_PHOTO_SOURCE: PhotoSource = "ai-placeholder";
export const AVAILABLE_PHOTO_SOURCES: Readonly<Record<PhotoSource, boolean>> = {
  "legacy-original": true,
  "ai-placeholder": photoSetIndex.sets["ai-placeholder"].active,
  "product-photo": photoSetIndex.sets["product-photo"].active,
};
export type MediaAsset = { src: string; thumbnail: string };
export type GalleryPhoto = { id: string; label: string; alt: string; media: MediaAsset; fallback?: MediaAsset };
const ORIGIN_GALLERIES: Readonly<Record<"DD5RO" | "DD6ROAE", GalleryPhoto[]>> = {
  DD5RO: [
    {"id": "system", "label": "Complete five-stage system", "alt": "Origin five-stage complete five-stage system", "media": {"src": "/products/media/origin/DD5RO-hero.png", "thumbnail": "/products/media/origin/thumbnails/DD5RO-hero-thumb.webp"}},
    {"id": "filter", "label": "Filter assembly", "alt": "Origin five-stage filter assembly", "media": {"src": "/products/media/origin/DD5RO-filter.png", "thumbnail": "/products/media/origin/thumbnails/DD5RO-filter-thumb.webp"}},
    {"id": "storage", "label": "Storage tank", "alt": "Origin five-stage storage tank", "media": {"src": "/products/media/origin/storage-tank.png", "thumbnail": "/products/media/origin/thumbnails/storage-tank-thumb.webp"}},
    {"id": "dimensions", "label": "Illustrative measurement view", "alt": "Origin five-stage illustrative measurement view", "media": {"src": "/products/media/origin/DD5RO-dimensions.png", "thumbnail": "/products/media/origin/thumbnails/DD5RO-dimensions-thumb.webp"}},
    {"id": "catalog-dimensions", "label": "Original catalog measurement image", "alt": "Origin five-stage original catalog measurement image", "media": {"src": "/products/media/reverse-osmosis-without-remineralizer-dimensions.webp", "thumbnail": "/products/media/reverse-osmosis-without-remineralizer-dimensions.webp"}},
    {"id": "catalog-spec", "label": "Original specification diagram", "alt": "Origin five-stage original specification diagram", "media": {"src": "/products/media/dd5ro-spec-dimensions.webp", "thumbnail": "/products/media/dd5ro-spec-dimensions.webp"}},
  ],
  DD6ROAE: [
    {"id": "system", "label": "Complete six-stage system", "alt": "Origin six-stage complete six-stage system", "media": {"src": "/products/media/origin/DD6ROAE-hero.png", "thumbnail": "/products/media/origin/thumbnails/DD6ROAE-hero-thumb.webp"}},
    {"id": "filter", "label": "Filter assembly", "alt": "Origin six-stage filter assembly", "media": {"src": "/products/media/origin/DD6ROAE-filter.png", "thumbnail": "/products/media/origin/thumbnails/DD6ROAE-filter-thumb.webp"}},
    {"id": "storage", "label": "Storage tank", "alt": "Origin six-stage storage tank", "media": {"src": "/products/media/origin/storage-tank.png", "thumbnail": "/products/media/origin/thumbnails/storage-tank-thumb.webp"}},
    {"id": "alkaline", "label": "Remineralization stage", "alt": "Origin six-stage remineralization stage", "media": {"src": "/products/media/origin/DD6ROAE-alkaline-detail.png", "thumbnail": "/products/media/origin/thumbnails/DD6ROAE-alkaline-detail-thumb.webp"}},
    {"id": "dimensions", "label": "Illustrative measurement view", "alt": "Origin six-stage illustrative measurement view", "media": {"src": "/products/media/origin/DD6ROAE-dimensions.png", "thumbnail": "/products/media/origin/thumbnails/DD6ROAE-dimensions-thumb.webp"}},
    {"id": "catalog-dimensions", "label": "Original catalog measurement image", "alt": "Origin six-stage original catalog measurement image", "media": {"src": "/products/media/reverse-osmosis-with-remineralizer-dimensions.webp", "thumbnail": "/products/media/reverse-osmosis-with-remineralizer-dimensions.webp"}},
  ],
};

/** PT54-F3: opt-in, reviewed published photos overlay. Existing PT53 assets remain the
 * fallback until a local review batch is explicitly published and committed.
 * No filename inference or customer-facing valve selection occurs here.
 */
type PublishedPhotoEntry = {
  configuration: string;
  role: string;
  sequence: number;
  version: number;
  photographed_valve?: string;
  src: string;
  thumbnail: string;
};
const PUBLISHED_PHOTOS = publishedPhotoIndex.entries as PublishedPhotoEntry[];
const PHOTO_ROLE_LABELS: Readonly<Record<string, string>> = {
  system: "Complete system", tank: "Tank detail", valve: "Control valve detail",
  brine: "Brine tank", pureline: "Pureline assembly", cartridge: "Replacement cartridge",
  detail: "Product detail", angle: "Additional view", hookup: "Connection fitting",
  membrane: "RO membrane", faucet: "RO faucet",
};
function mergePublishedPhotos(existing: GalleryPhoto[], configuration: string): GalleryPhoto[] {
  // Old photo roles and selected fitting images remain intact unless a new
  // explicitly-approved image targets that exact role and sequence 01.
  const selected = new Map<string, PublishedPhotoEntry>();
  for (const entry of PUBLISHED_PHOTOS) {
    if (entry.configuration !== configuration) continue;
    const slot = `${entry.role}:${entry.sequence}`;
    const previous = selected.get(slot);
    if (!previous || entry.version > previous.version) selected.set(slot, entry);
  }
  if (!selected.size) return existing;
  const output = existing.map((photo) => ({ ...photo }));
  const newPhotos: Array<{ role: string; sequence: number; photo: GalleryPhoto }> = [];
  for (const entry of selected.values()) {
    const label = PHOTO_ROLE_LABELS[entry.role] ?? "Additional product photograph";
    const replaceId = entry.sequence === 1
      ? ({ system: "system", tank: "tank", brine: "brine", pureline: "pureline" } as Record<string, string>)[entry.role]
      : undefined;
    const index = replaceId ? output.findIndex((item) => item.id === replaceId) : -1;
    const media = { src: entry.src, thumbnail: entry.thumbnail };
    if (index >= 0) {
      // Preserve the current image as an optional loading fallback.
      output[index] = { ...output[index], media, fallback: output[index].fallback ?? output[index].media };
    } else {
      const id = `published-${entry.role}-${String(entry.sequence).padStart(2, "0")}`;
      newPhotos.push({ role: entry.role, sequence: entry.sequence, photo: {
        id, label: entry.sequence === 1 ? label : `${label} ${entry.sequence}`,
        alt: `${configuration.replaceAll(":", " ")}, ${label.toLowerCase()} ${entry.sequence}`,
        media,
      } });
    }
  }
  newPhotos.sort((a, b) => a.role.localeCompare(b.role) || a.sequence - b.sequence);
  // Insert before the special per-customer selected fitting image.
  const fittingIndex = output.findIndex((item) => item.id === "hookup");
  output.splice(fittingIndex < 0 ? output.length : fittingIndex, 0, ...newPhotos.map((item) => item.photo));
  return output;
}

/** PT54-F6: captions are editorial metadata, never part of photo filenames or quotes. */
type CaptionOverrides = {
  schema_version: number;
  families: Record<string, Record<string, string>>;
  configurations: Record<string, Record<string, string>>;
};
const CAPTIONS = photoCaptionOverrides as CaptionOverrides;
function withCaptionOverrides(photos: GalleryPhoto[], key: string): GalleryPhoto[] {
  const family = key.split(":")[0];
  return photos.map((photo) => {
    const revised = CAPTIONS.configurations[key]?.[photo.id] ?? CAPTIONS.families[family]?.[photo.id];
    return revised ? { ...photo, label: revised } : photo;
  });
}

/** The historical alternate-style registry was retired in PT54-G4.
 * The original/legacy source uses existing product catalog photos and fallback
 * assets in the page components. This registry owns AI and future real-photo
 * galleries only; it never substitutes a retired system image.
 */
function indexedGallery(
  family: "refine" | "essence" | "harmony", size: "1.5" | "2.0",
  finish: TankFinish, pureline: number,
  photoSource: Exclude<PhotoSource, "legacy-original">, fittingPhoto?: string | null,
): GalleryPhoto[] | null {
  const selected = photoSetIndex.sets[photoSource];
  if (!selected.active) return null;
  const key = family === "harmony"
    ? `harmony:${size}:${finish}:pass-through:${pureline}`
    : `${family}:${size}:${finish}`;
  const entries = selected.entries as Record<string, GalleryPhoto[]>;
  const gallery = entries[key];
  if (!gallery?.length) return null;
  const photos = gallery.map((photo) => ({ ...photo, media: { ...photo.media } }));
  if (family !== "harmony" && fittingPhoto) photos.push({
    id: "hookup", label: "Selected connection fitting",
    alt: "Individual selected installation fitting",
    media: { src: fittingPhoto, thumbnail: fittingPhoto },
  });
  return withCaptionOverrides(photos, key);
}

/** Original/legacy source deliberately returns null: the product page uses the
 * catalog's original images and its established family fallback. Origin keeps
 * its verified independent gallery regardless of the selected source.
 */
export function resolveApprovedGallery(
  sku: string, finish: TankFinish = "stainless", fittingPhoto?: string | null,
  harmonySize: "1.5" | "2.0" = "1.5",
  photoSource: PhotoSource = DEFAULT_PHOTO_SOURCE,
): GalleryPhoto[] | null {
  if (sku === "DD5RO" || sku === "DD6ROAE")
    return withCaptionOverrides(mergePublishedPhotos(ORIGIN_GALLERIES[sku], `origin:${sku}`), `origin:${sku}`);
  if (photoSource === "legacy-original") return null;
  let family: "refine" | "essence" | "harmony";
  let size: "1.5" | "2.0";
  let pureline = 0;
  if (sku === "DD15SOFT" || sku === "DD20SOFT") {
    family = "refine"; size = sku === "DD15SOFT" ? "1.5" : "2.0";
  } else if (sku === "DD15CATRV" || sku === "DD20CATRV") {
    family = "essence"; size = sku === "DD15CATRV" ? "1.5" : "2.0";
  } else if (sku === "DD15CLEARPTV" || /^DD15CLEARPL[123]$/.test(sku)) {
    family = "harmony"; size = harmonySize;
    pureline = sku === "DD15CLEARPTV" ? 0 : Number(sku.slice(-1));
  } else return null;
  return indexedGallery(family, size, finish, pureline, photoSource, fittingPhoto);
}

export function isPhotographyIntegratedSku(sku: string): boolean {
  return resolveApprovedGallery(sku) !== null;
}

export function approvedLandingPhoto(
  sku: string, photoSource: PhotoSource = DEFAULT_PHOTO_SOURCE,
): GalleryPhoto | null {
  if (sku === "DD5RO" || sku === "DD6ROAE") return null;
  return resolveApprovedGallery(sku, "stainless", null, "1.5", photoSource)?.[0] ?? null;
}
