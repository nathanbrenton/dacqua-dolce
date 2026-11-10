import {
  useEffect,
  useRef,
  type MouseEvent,
  type PointerEvent,
  type ReactNode,
} from "react";

import "./ProductImageLightbox.css";

type ProductImageLightboxProps = {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
};

/** Never magnify less than this, even when the photograph is small. */
const MIN_HOVER_ZOOM = 2;
/** Never magnify more than this; beyond it the photograph only gets blurrier. */
const MAX_HOVER_ZOOM = 3;

/**
 * Full-viewport enlarged product image. Uses the native modal dialog so
 * Escape, focus containment, and focus return to the gallery are handled by
 * the browser.
 *
 * With a mouse, hovering the photograph magnifies the area under the cursor
 * and clicking the photograph does nothing, so exploring it cannot close the
 * viewer by accident. The backdrop, the close button and Escape close it.
 * On touch screens there is no hover, and a tap anywhere closes the viewer.
 */
export function ProductImageLightbox({
  open,
  onClose,
  children,
}: ProductImageLightboxProps) {
  const dialogRef = useRef<HTMLDialogElement | null>(null);
  const stageRef = useRef<HTMLDivElement | null>(null);
  const mouseOverStageRef = useRef(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog === null) return;

    if (open && !dialog.open) {
      dialog.showModal();
    }

    if (!open && dialog.open) {
      dialog.close();
    }

    if (!open) {
      mouseOverStageRef.current = false;
    }
  }, [open]);

  function stopHoverZoom() {
    mouseOverStageRef.current = false;
    stageRef.current?.classList.remove("is-zooming");
  }

  function handlePointerMove(event: PointerEvent<HTMLDivElement>) {
    if (event.pointerType !== "mouse") return;

    const stage = event.currentTarget;
    const image = stage.querySelector("img");
    if (image === null || image.clientWidth === 0) return;

    // The stage hugs the photograph and is never transformed, so its box
    // gives the cursor position in the photograph's own coordinates.
    const bounds = stage.getBoundingClientRect();
    const x = ((event.clientX - bounds.left) / bounds.width) * 100;
    const y = ((event.clientY - bounds.top) / bounds.height) * 100;

    if (!mouseOverStageRef.current) {
      const nativeScale = image.naturalWidth / image.clientWidth;
      const zoom = Math.min(
        MAX_HOVER_ZOOM,
        Math.max(MIN_HOVER_ZOOM, nativeScale),
      );
      stage.style.setProperty("--hover-zoom", zoom.toFixed(2));
      mouseOverStageRef.current = true;
    }

    stage.style.setProperty("--hover-x", `${Math.min(100, Math.max(0, x))}%`);
    stage.style.setProperty("--hover-y", `${Math.min(100, Math.max(0, y))}%`);
    stage.classList.add("is-zooming");
  }

  function handleStageClick(event: MouseEvent<HTMLDivElement>) {
    // While a mouse is exploring the photograph, a click must not close it.
    if (mouseOverStageRef.current) {
      event.stopPropagation();
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className="product-lightbox"
      aria-label="Enlarged product image"
      onClose={onClose}
      onClick={onClose}
    >
      <button
        type="button"
        className="product-lightbox-close"
        aria-label="Close enlarged image"
        onClick={(event) => {
          event.stopPropagation();
          onClose();
        }}
      >
        <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
          <path
            d="M5 5l14 14M19 5L5 19"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>
      </button>

      {open ? (
        <div
          ref={stageRef}
          className="product-lightbox-stage"
          onPointerMove={handlePointerMove}
          onPointerLeave={stopHoverZoom}
          onClick={handleStageClick}
        >
          {children}
        </div>
      ) : null}
    </dialog>
  );
}
