import { useEffect, useState } from "react";
import type { CatalogImage } from "../../api/catalog";
import { ResponsiveProductImage } from "./ResponsiveProductImage";

/** Opt-in AI imagery; no image here is an approved catalog asset. */
const HARMONY_PREVIEW: Readonly<Record<string, string>> = {
  DD15CLEARPTV: "/__dd_image_preview/DD15CLEARPTV.png",
  DD15CLEARPL1: "/__dd_image_preview/DD15CLEARPL1.png",
  DD15CLEARPL2: "/__dd_image_preview/DD15CLEARPL2.png",
  DD15CLEARPL3: "/__dd_image_preview/DD15CLEARPL3.png",
};

/** Origin Standard and Alkaline Plus: clean local-only landing-page previews. */
const ORIGIN_PREVIEW: Readonly<Record<string, string>> = {
  DD5RO: "/__dd_image_preview/origin/DD5RO-hero.png",
  DD6ROAE: "/__dd_image_preview/origin/DD6ROAE-hero.png",
};

/** Refine system concepts: both sizes; clean and unmeasured for landing cards. */
const REFINE_PREVIEW: Readonly<Record<string, string>> = {
  DD15SOFT: "/__dd_image_preview/refine/DD15SOFT-bare.png",
  DD20SOFT: "/__dd_image_preview/refine/DD20SOFT-bare.png",
};

/** Owner-photo composites for Essence: local prototypes only, never approved catalog media. */
const ESSENCE_PREVIEW: Readonly<Record<string, string>> = {
  DD15CATRV: "/__dd_image_preview/essence/DD15CATRV-bare.png",
  DD20CATRV: "/__dd_image_preview/essence/DD20CATRV-bare.png",
};

export type AdditionalPreviewImage = {
  id: string;
  path: string;
  label: string;
  alt: string;
};

/** The same opt-in draft imagery is available from versioned static release assets. */
const FOLDED_JACKET: AdditionalPreviewImage = {
  id: "jacket-folded-15",
  path: "/__dd_image_preview/shared/neoprene-jacket-15-folded.png",
  label: "Neoprene jacket",
  alt: "AI concept of folded black neoprene tank jacket for a 1.5 cubic-foot tank",
};

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
    if (sku === "DD15CATRV") result.push(FOLDED_JACKET);
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
  result.push(FOLDED_JACKET);
  // The installed jacket mockup shows Harmony's pass-through top, so using
  // it as a Refine/Essence tank photo would misrepresent their valve heads.
  if (isHarmony) result.push(HARMONY_JACKET_INSTALLED);
  return result;
}

export const CAN_PREVIEW_PRODUCT_IMAGERY = true;

type PreviewProductImageProps = {
  sku: string;
  original: CatalogImage | null;
  enabled: boolean;
  loading?: "eager" | "lazy";
  presentation?: "landing" | "detail";
  override?: AdditionalPreviewImage | null;
};

export function PreviewProductImage({
  sku, original, enabled, loading = "lazy", presentation = "detail", override = null,
}: PreviewProductImageProps) {
  const previewPath = enabled && CAN_PREVIEW_PRODUCT_IMAGERY
    ? (override?.path ?? (HARMONY_PREVIEW[sku] !== undefined
      ? presentation === "landing"
        ? HARMONY_PREVIEW[sku].replace(/\.png$/, "-hero.png")
        : HARMONY_PREVIEW[sku]
      : ORIGIN_PREVIEW[sku] ?? REFINE_PREVIEW[sku] ?? ESSENCE_PREVIEW[sku] ?? null))
    : null;
  const [readyPath, setReadyPath] = useState<string | null>(null);
  const [failedPath, setFailedPath] = useState<string | null>(null);

  useEffect(() => {
    if (previewPath === null) return;
    let cancelled = false;
    const check = new Image();
    check.onload = () => {
      if (!cancelled) setReadyPath(previewPath);
    };
    check.onerror = () => {
      if (!cancelled) setFailedPath(previewPath);
    };
    check.src = previewPath;
    return () => { cancelled = true; };
  }, [previewPath]);

  // Require a successful preload for the current SKU. Missing prototypes
  // fall back to the original image, including after switching configurations.
  if (previewPath !== null && readyPath === previewPath && failedPath !== previewPath) {
    return (
      <>
        <img
          src={previewPath}
          alt={override?.alt ?? `AI concept preview for ${sku}; visual layout unapproved`}
          loading={loading}
          decoding="async"
          onError={() => { setFailedPath(previewPath); }}
        />
        <span className="product-image-demo-label" aria-hidden="true">
          AI concept · not approved
        </span>
      </>
    );
  }
  return original !== null
    ? <ResponsiveProductImage image={original} loading={loading} />
    : <span className="product-media-placeholder" aria-hidden="true" />;
}
