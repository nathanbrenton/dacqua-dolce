import type { CatalogImage } from "../../api/catalog";
import { ResponsiveProductImage } from "./ResponsiveProductImage";
import { approvedLandingPhoto, type PhotoSource } from "./productMediaRegistry";
import { ApprovedMediaImage } from "./ApprovedMediaImage";

export type AdditionalPreviewImage = {
  id: string;
  path: string;
  label: string;
  alt: string;
};

/** The same opt-in draft imagery is available from versioned static release assets. */
const HARMONY_JACKET_INSTALLED: AdditionalPreviewImage = {
  id: "jacket-installed-15-harmony",
  path: "/__dd_image_preview/shared/neoprene-jacket-15-installed-harmony.png",
  label: "Jacket on Harmony",
  alt: "AI concept showing a black neoprene jacket installed on a Harmony tank with a red-topped pass-through fitting",
};

/** Additional product-detail previews; never add these to public catalog records. */
export function getAdditionalPreviewImages(sku: string): AdditionalPreviewImage[] {
  const isHarmony = sku === "DD15CLEARPTV" || /^DD15CLEARPL[123]$/.test(sku);
  const isOtherOneFive = sku === "DD15SOFT" || sku === "DD15CATRV";
  if (sku === "DD15CATRV" || sku === "DD20CATRV") {
    const size = sku === "DD15CATRV" ? "1.5" : "2.0";
    const result: AdditionalPreviewImage[] = [
      {
        id: "essence-dimensions",
        path: `/__dd_image_preview/essence/${sku}-dimensions.png`,
        label: `${size} cf measurements`,
        alt: `Owner-supplied ${size} cubic-foot Essence stainless tank dimension diagram`,
      },
      {
        id: "essence-jacket-installed",
        path: `/__dd_image_preview/essence/${sku}-jacket.png`,
        label: `${size} cf jacket fitted`,
        alt: `Unapproved visual composite of black neoprene jacket fitted over ${size} cubic-foot Essence tank with square control head`,
      },
    ];
    return result;
  }
  if (!isHarmony && !isOtherOneFive) return [];
  const result: AdditionalPreviewImage[] = [];
  if (/^DD15CLEARPL[123]$/.test(sku)) {
    const count = Number(sku.slice(-1));
    result.push({
      id: "pureline-frame",
      path: `/__dd_image_preview/${sku}-frame.png`,
      label: `Pureline ${count}-housing frame`,
      alt: `AI concept of Pureline support frame holding exactly ${count} blue 20-inch filter ${count === 1 ? "housing" : "housings"}, without conditioning tank`,
    });
  }
  // The installed jacket mockup shows Harmony's pass-through top, so using
  // it as a Refine/Essence tank photo would misrepresent their valve heads.
  if (isHarmony) result.push(HARMONY_JACKET_INSTALLED);
  return result;
}

/** G4: current AI galleries or original/legacy catalog image, with no
 * retired alternate-style image selection.
 */
type PreviewProductImageProps = {
  sku: string;
  original: CatalogImage | null;
  photoSource: PhotoSource;
  loading?: "eager" | "lazy";
};

export function PreviewProductImage({
  sku, original, photoSource, loading = "lazy",
}: PreviewProductImageProps) {
  const approved = approvedLandingPhoto(sku, photoSource);
  if (approved !== null) return <ApprovedMediaImage photo={approved} loading={loading} />;
  return original !== null
    ? <ResponsiveProductImage image={original} loading={loading} />
    : <span className="product-media-placeholder" aria-hidden="true" />;
}
