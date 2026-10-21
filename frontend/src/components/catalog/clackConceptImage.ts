/**
 * Static URL lookup for unapproved Clack fitting photo concepts.
 * Used only by opt-in Aesthetic Lab previews; this module deliberately
 * contains no interactive preview card, React hooks, or environment gate.
 * The caller controls visibility; fitting selections and catalog data
 * never change when a preview image is missing.
 */
const ASSET_BY_ORDER_NO: Readonly<Record<string, string>> = {
  "V3007-03LF": "V3007-03LF.png",
  "V3007-12LF": "V3007-12LF.png",
  "V3007-18": "V3007-18.png",
  "V3007-02LF": "V3007-02LF.png",
  "V3007-13LF": "V3007-13LF.png",
  "V3007-04": "V3007-04.png",
  "V3007": "V3007.png",
  "V3007-22LF": "V3007-22LF.png",
  "V3007-09LF": "V3007-09LF.png",
  "V3007-05": "V3007-05.png",
};
const PREFIX = "/__dd_image_preview/clack/";

/** Shared public-preview URL resolver; no catalog or pricing side effects. */
export function clackConceptImageForOrderNo(orderNo: string | null): string | null {
  if (orderNo === null) return null;
  const file = ASSET_BY_ORDER_NO[orderNo];
  return file === undefined ? null : PREFIX + file;
}
