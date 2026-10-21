import { useEffect, useRef } from "react";
import type { ClackInstallationFitting } from "./clackInstallationFittings";
import { shortClackFittingLabel } from "./clackInstallationFittings";
import { clackConceptImageForOrderNo } from "./clackConceptImage";

/** Local Aesthetic Lab only: image-backed picker shared by Essence and Refine.
 * A native <select> remains in the product page whenever previews are OFF.
 * The summary and each option are keyboard-focusable, with native disclosure
 * behavior and standard buttons (no inaccessible image elements inside <option>).
 */
type Props = {
  options: readonly ClackInstallationFitting[];
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
};

export function ClackFittingThumbnailSelect({ options, value, disabled, onChange }: Props) {
  const detailsRef = useRef<HTMLDetailsElement>(null);
  const selected = options.find((item) => item.label === value) ?? null;
  useEffect(() => {
    if (disabled && detailsRef.current) detailsRef.current.open = false;
  }, [disabled]);
  useEffect(() => {
    const closeOnOutsideClick = (event: PointerEvent) => {
      if (detailsRef.current && !detailsRef.current.contains(event.target as Node)) {
        detailsRef.current.open = false;
      }
    };
    document.addEventListener("pointerdown", closeOnOutsideClick);
    return () => document.removeEventListener("pointerdown", closeOnOutsideClick);
  }, []);

  const choice = (nextValue: string) => {
    onChange(nextValue);
    if (detailsRef.current) detailsRef.current.open = false;
  };
  const thumb = (fitting: ClackInstallationFitting, thumbnailClass: string) => {
    const path = clackConceptImageForOrderNo(fitting.orderNo);
    return path ? (
      <img className={thumbnailClass} src={path} alt="" loading="lazy" width={44} height={44} />
    ) : <span className={thumbnailClass} aria-hidden="true">—</span>;
  };

  return (
    <details ref={detailsRef} className="clack-thumbnail-select" aria-disabled={disabled}>
      <summary
        tabIndex={disabled ? -1 : undefined}
        onClick={disabled ? (event) => event.preventDefault() : undefined}
        className="clack-thumbnail-select-trigger"
      >
        {selected ? thumb(selected, "clack-thumbnail-select-image") : (
          <span className="clack-thumbnail-select-image clack-thumbnail-empty" aria-hidden="true">—</span>
        )}
        <span className="clack-thumbnail-select-trigger-copy">
          <strong>{disabled ? "Choose connection size first" : selected ? shortClackFittingLabel(selected) : "Choose fitting type"}</strong>
          {selected ? <small>{selected.orderNo}</small> : null}
        </span>
        <span className="clack-thumbnail-caret" aria-hidden="true">⌄</span>
      </summary>
      {!disabled ? (
        <div className="clack-thumbnail-menu" role="group" aria-label="Fitting type options with image thumbnails">
          {options.map((fitting) => (
            <button
              type="button"
              key={fitting.orderNo}
              className={fitting.label === value ? "clack-thumbnail-menu-option is-selected" : "clack-thumbnail-menu-option"}
              aria-pressed={fitting.label === value}
              onClick={() => choice(fitting.label)}
            >
              {thumb(fitting, "clack-thumbnail-menu-image")}
              <span className="clack-thumbnail-menu-label">
                <strong>{shortClackFittingLabel(fitting)}</strong>
                <small>{fitting.orderNo}</small>
              </span>
            </button>
          ))}
          <button type="button" className="clack-thumbnail-menu-option" onClick={() => choice("")}>
            <span className="clack-thumbnail-menu-image clack-thumbnail-empty" aria-hidden="true">—</span>
            <span className="clack-thumbnail-menu-label"><strong>No fitting selected</strong><small>Ask for advice</small></span>
          </button>
        </div>
      ) : null}
    </details>
  );
}
