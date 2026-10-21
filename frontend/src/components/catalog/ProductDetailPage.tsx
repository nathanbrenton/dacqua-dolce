import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  cancelStockNotification,
  getCatalogProduct,
  subscribeStockNotification,
  type CatalogProductDetail,
  type CatalogImage,
} from "../../api/catalog";
import type { AuthenticationStatus } from "../../api/authentication";
import {
  addCartItem,
} from "../../api/cart";
import { QuoteDialog } from "../quotes/QuoteDialog";
import { InstallationServicesNotice } from "./InstallationServicesNotice";
import { SupportRequestForm } from "../support/SupportRequestForm";
import { ResponsiveProductImage } from "./ResponsiveProductImage";
import { PreviewProductImage, CAN_PREVIEW_PRODUCT_IMAGERY, getAdditionalPreviewImages } from "./PreviewProductImage";
import { getProductPresentation } from "./productPresentation";
import { ClackFittingThumbnailSelect } from "./ClackFittingThumbnailSelect";
import { getConfigurablePreviewGallery } from "./ConfigurablePreviewGallery";
import { getConfigurationFamily } from "./productConfigurations";
import { CLACK_CONNECTION_SIZES, clackFittingsForSize, shortClackFittingLabel, offersClackInstallationFittings } from "./clackInstallationFittings";

// These are the same temporary, representative photos used on the landing
// cards. They are NOT approved SKU-specific product images. Verified catalog
// images always take precedence. Replace with approved photos when available.
const DETAIL_IMAGE_FALLBACKS: Readonly<Record<string, CatalogImage>> = {
  Refine: {
    path: "/products/media/refine-1-5-cf.jpeg",
    alt_text: "Earlier Refine softener with brine tank; representative image",
  },
  Harmony: {
    path: "/products/media/1-5cf-pass-through-with-prefilter-dimensions.webp",
    alt_text: "Earlier Harmony conditioner with prefilter; representative image, not a verified Pureline assembly",
  },
};

type ProductDetailPageProps = {
  imagePreviewEnabled: boolean;
  slug: string;
  account: AuthenticationStatus | null;
  onNavigate: (path: string, preserveScroll?: boolean) => void;
  onRequestSignIn: () => void;
};

function formatPrice(
  amountMinor: number,
  currency: string,
): string {
  return new Intl.NumberFormat(
    undefined,
    {
      style: "currency",
      currency,
    },
  ).format(amountMinor / 100);
}

function humanizeOptionKey(value: string): string {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function relationshipLabel(value: string): string {
  if (value === "accessory") {
    return "Accessory";
  }
  if (value === "replacement") {
    return "Replacement";
  }
  return "Option";
}

export function ProductDetailPage({
  imagePreviewEnabled,
  slug,
  account,
  onNavigate,
  onRequestSignIn,
}: ProductDetailPageProps) {
  const [product, setProduct] =
    useState<CatalogProductDetail | null>(
      null,
    );
  const [loading, setLoading] =
    useState(true);
  const [error, setError] =
    useState<string | null>(null);
  const [selectedImageIndex, setSelectedImageIndex] =
    useState(0);
  const [selectedDemoImageId, setSelectedDemoImageId] = useState<string | null>(null);
  const [originalThumbnailSelected, setOriginalThumbnailSelected] = useState(false);
  const [selectedVariantId, setSelectedVariantId] =
    useState<string | null>(null);
  const [quoteOpen, setQuoteOpen] =
    useState(false);
  const [selectedFittingSize, setSelectedFittingSize] = useState("");
  const [selectedFittingType, setSelectedFittingType] = useState("");
  // Aesthetic Lab preselection is visual only; never silently include an
  // unpriced part in a quote/cart until a visitor explicitly picks its type.
  const [fittingExplicitlyChosen, setFittingExplicitlyChosen] = useState(false);
  const [commerceError, setCommerceError] =
    useState<string | null>(null);
  const [addingToCart, setAddingToCart] =
    useState(false);
  const [notificationEmail, setNotificationEmail] =
    useState(account?.email ?? "");
  const [notificationState, setNotificationState] =
    useState<"idle" | "saving" | "saved" | "cancelling" | "cancelled">("idle");
  const [notificationMessage, setNotificationMessage] =
    useState<string | null>(null);

  useEffect(() => {
    // Preserve layout and scroll position across selections within a family.
    const family = product === null ? null : getConfigurationFamily(product.sku);
    const sameFamilySwitch = family !== null && family.configurations.some(
      (configuration) => configuration.sku.toLowerCase() === slug.toLowerCase());
    let active = true;
    if (!sameFamilySwitch) {
      setLoading(true);
    }
    setError(null);

    void getCatalogProduct(slug)
      .then((result) => {
        if (!active) return;
        setProduct(result);
        setSelectedImageIndex(0);
        setSelectedDemoImageId(null);
        setOriginalThumbnailSelected(false);
        setSelectedVariantId(null);
        setSelectedFittingSize("");
        setSelectedFittingType("");
        setFittingExplicitlyChosen(false);
        setNotificationEmail(account?.email ?? "");
        setNotificationState("idle");
        setNotificationMessage(null);
        setCommerceError(null);
        setQuoteOpen(false);
      })
      .catch((caught) => {
        if (!active) return;
        setError(
          caught instanceof Error
            ? caught.message
            : "System unavailable.",
        );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    // Stale requests must not overwrite a newer selection.
    return () => { active = false; };
    // product is intentionally excluded: refetch only for route/account changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, account]);

  useEffect(() => {
    // No gallery selection can persist after opting out of AI previews.
    setSelectedDemoImageId(null);
    setOriginalThumbnailSelected(false);
  }, [imagePreviewEnabled]);

  useEffect(() => {
    if (product === null || !offersClackInstallationFittings(product.sku)) return;
    if (imagePreviewEnabled && CAN_PREVIEW_PRODUCT_IMAGERY) {
      // Optional, display-only premium brass default in local dev preview.
      setSelectedFittingSize('1"');
      setSelectedFittingType("Brass Press/Sweat Assembly LF");
    } else {
      // Outside the visual lab, preserve the site's original blank selectors.
      setSelectedFittingSize("");
      setSelectedFittingType("");
    }
    setFittingExplicitlyChosen(false);
  }, [imagePreviewEnabled, product?.sku]);

  const selectedVariant = useMemo(() => {
    if (product === null || product.variants.length === 0) {
      return null;
    }
    return product.variants.find((variant) => variant.id === selectedVariantId)
      ?? product.variants[0];
  }, [product, selectedVariantId]);

  const selectedImage = useMemo(
    () => (
      selectedVariant?.primary_image
      ?? product?.images[selectedImageIndex]
      ?? product?.primary_image
      ?? null
    ),
    [product, selectedImageIndex, selectedVariant],
  );

  const illustrativeImage = selectedImage === null && product !== null
    ? DETAIL_IMAGE_FALLBACKS[getConfigurationFamily(product.sku)?.name ?? ""] ?? null
    : null;
  const demoImages = product !== null && imagePreviewEnabled && CAN_PREVIEW_PRODUCT_IMAGERY
    ? getAdditionalPreviewImages(product.sku)
    : [];
  const demoGalleryEnabled = demoImages.length > 0;
  const selectedDemoImage = demoImages.find((image) => image.id === selectedDemoImageId) ?? null;

  if (loading) {
    return (
      <main
        id="main-content"
        tabIndex={-1}
        className="detail-shell"
      >
        <p role="status">
          Loading system…
        </p>
      </main>
    );
  }

  if (
    error !== null
    || product === null
  ) {
    return (
      <main
        id="main-content"
        tabIndex={-1}
        className="detail-shell"
      >
        <button
          type="button"
          className="text-button"
          onClick={() => {
            onNavigate("/");
          }}
        >
          ← Back to systems
        </button>

        <h1 className="detail-error-title">
          System unavailable.
        </h1>

        <p>{error}</p>
      </main>
    );
  }

  const pricing = selectedVariant?.pricing ?? product.pricing;
  const availability = selectedVariant?.availability ?? product.availability;
  const productId = product.id;
  const presentation = getProductPresentation(product);
  const configurationLoading = product.slug.toLowerCase() !== slug.toLowerCase();
  const configurationFamily = getConfigurationFamily(product.sku);
  const fittingEligible = offersClackInstallationFittings(product.sku);
  const fittingOptions = selectedFittingSize === "" ? [] : clackFittingsForSize(selectedFittingSize);
  const matchingFitting = fittingEligible
    ? fittingOptions.find((fitting) => fitting.label === selectedFittingType)
    : undefined;
  // Preserve the user's actual connection size in the internal quote note,
  // including the Clack fitting shared between 1.25-inch and 1.5-inch systems.
  const selectedFitting = matchingFitting === undefined
    ? null : { ...matchingFitting, size: selectedFittingSize };
  const fittingForInquiry = fittingExplicitlyChosen ? selectedFitting : null;
  const configurableGallery = imagePreviewEnabled && CAN_PREVIEW_PRODUCT_IMAGERY
    ? getConfigurablePreviewGallery(product.sku, selectedFitting?.orderNo ?? null)
    : [];
  const configurableActive = configurableGallery.find((tile) => tile.id === selectedDemoImageId)
    ?? configurableGallery[0] ?? null;
  // Cart and quote requests use the selected product record, never a family ID.
  const contactProductName = selectedVariant !== null
    ? `${product.name} — ${selectedVariant.display_name}`
    : product.name;

  async function handleStockNotification() {
    if (notificationEmail.trim() === "") {
      setNotificationMessage("Enter an email address for the availability notice.");
      return;
    }

    setNotificationState("saving");
    setNotificationMessage(null);

    try {
      const result = await subscribeStockNotification(
        slug,
        notificationEmail,
      );
      setNotificationState("saved");
      setNotificationMessage(result.message);
    } catch (caught) {
      setNotificationState("idle");
      setNotificationMessage(
        caught instanceof Error
          ? caught.message
          : "The availability request could not be saved.",
      );
    }
  }

  async function handleStockNotificationCancellation() {
    if (notificationEmail.trim() === "") {
      setNotificationMessage("Enter the email address used for the availability notice.");
      return;
    }

    setNotificationState("cancelling");
    setNotificationMessage(null);

    try {
      const result = await cancelStockNotification(
        slug,
        notificationEmail,
      );
      setNotificationState("cancelled");
      setNotificationMessage(result.message);
    } catch (caught) {
      setNotificationState("idle");
      setNotificationMessage(
        caught instanceof Error
          ? caught.message
          : "The availability request could not be cancelled.",
      );
    }
  }

  async function handlePrimaryAction() {
    if (configurationLoading) return;
    setCommerceError(null);

    if (
      availability.status === "out_of_stock"
      || availability.status === "discontinued"
    ) {
      if (availability.can_inquire) {
        setQuoteOpen(true);
      } else {
        setCommerceError("This system is not accepting inquiries while unavailable.");
      }
      return;
    }

    if (
      pricing.action === "SIGN_IN"
    ) {
      onRequestSignIn();
      return;
    }

    if (
      pricing.action
      === "REQUEST_QUOTE"
    ) {
      setQuoteOpen(true);
      return;
    }

    if (
      pricing.action
      === "ADD_TO_CART"
    ) {
      // Fittings are not priced cart line items yet; never silently add an
      // unpriced selected fitting to a base-product purchase.
      if (fittingForInquiry !== null) {
        setQuoteOpen(true);
        return;
      }
      if (account === null) {
        onRequestSignIn();
        return;
      }

      setAddingToCart(true);

      try {
        await addCartItem(
          productId,
          selectedVariant?.id ?? null,
        );
        onNavigate("/account");
      } catch (caught) {
        setCommerceError(
          caught instanceof Error
            ? caught.message
            : "The system could not be added to the cart.",
        );
      } finally {
        setAddingToCart(false);
      }
    }
  }

  return (
    <>
      <QuoteDialog
        open={quoteOpen}
        productId={product.id}
        productName={contactProductName}
        inquiryContext="product"
        initialEmail={
          account?.email ?? null
        }
        recommendationContext={null}
        installationFitting={fittingForInquiry}
        onClose={() => {
          setQuoteOpen(false);
        }}
      />

      <main
        id="main-content"
        tabIndex={-1}
        className="detail-shell"
      >
        <button
          type="button"
          className="text-button"
          onClick={() => {
            onNavigate("/");
          }}
        >
          ← All systems
        </button>

        <section className="product-detail">
          <div className="product-detail-gallery">
            <div className="product-detail-main-image">
              {configurableActive !== null ? (
                configurableActive.path !== null ? (
                  <PreviewProductImage
                    sku={product.sku}
                    original={selectedImage ?? illustrativeImage}
                    enabled={imagePreviewEnabled}
                    override={{
                      id: configurableActive.id,
                      path: configurableActive.path,
                      label: configurableActive.label,
                      alt: configurableActive.alt,
                    }}
                    loading="eager"
                  />
                ) : (
                  <div className="product-fitting-preview-empty" role="status">
                    <strong>Choose a hookup fitting</strong>
                    <span>Select connection size and fitting type to display its individual hardware image.</span>
                  </div>
                )
              ) : demoGalleryEnabled && originalThumbnailSelected && product.images.length > 0 ? (
                <ResponsiveProductImage
                  image={product.images[selectedImageIndex] ?? product.images[0]}
                  loading="eager"
                />
              ) : (
                <PreviewProductImage
                  sku={product.sku}
                  original={selectedImage ?? illustrativeImage}
                  enabled={imagePreviewEnabled}
                  override={selectedDemoImage}
                  loading="eager"
                />
              )}
            </div>
            {illustrativeImage !== null ? (
              <p className="product-image-note">
                Representative image; selected configuration may differ.
              </p>
            ) : null}

            {configurableGallery.length > 0 ? (
              <div className="product-thumbnails product-preview-thumbnails" aria-label={`${configurationFamily?.name ?? "Product"} AI preview gallery`}>
                {configurableGallery.map((tile) => (
                  <button
                    key={tile.id}
                    type="button"
                    className={configurableActive?.id === tile.id ? "is-active" : undefined}
                    aria-label={`Show ${tile.label}`}
                    aria-pressed={configurableActive?.id === tile.id}
                    onClick={() => {
                      setSelectedDemoImageId(tile.id);
                      setOriginalThumbnailSelected(false);
                    }}
                  >
                    {tile.path !== null ? (
                      <img src={tile.path} alt={tile.alt} loading="lazy" />
                    ) : (
                      <span className="product-fitting-thumb-empty" aria-hidden="true">
                        Select fitting
                      </span>
                    )}
                    <span className="product-preview-thumb-caption">{tile.label}</span>
                  </button>
                ))}
              </div>
            ) : demoGalleryEnabled ? (
              <div className="product-thumbnails product-preview-thumbnails" aria-label="AI concept gallery and existing photographs">
                <button
                  type="button"
                  className={selectedDemoImage === null && !originalThumbnailSelected ? "is-active" : undefined}
                  aria-label="Show main system image"
                  aria-pressed={selectedDemoImage === null && !originalThumbnailSelected}
                  onClick={() => {
                    setSelectedDemoImageId(null);
                    setOriginalThumbnailSelected(false);
                  }}
                >
                  <PreviewProductImage
                    sku={product.sku}
                    original={selectedImage ?? illustrativeImage}
                    enabled={imagePreviewEnabled}
                    loading="lazy"
                  />
                  <span className="product-preview-thumb-caption">System</span>
                </button>
                {demoImages.map((image) => (
                  <button
                    key={image.id}
                    type="button"
                    className={selectedDemoImage?.id === image.id ? "is-active" : undefined}
                    aria-label={`Show ${image.label}`}
                    aria-pressed={selectedDemoImage?.id === image.id}
                    onClick={() => {
                      setSelectedDemoImageId(image.id);
                      setOriginalThumbnailSelected(false);
                    }}
                  >
                    <img src={image.path} alt={image.alt} loading="lazy" />
                    <span className="product-preview-thumb-caption">{image.label}</span>
                  </button>
                ))}
                {product.images.map((image, index) => (
                  <button
                    key={`catalog-${image.path}`}
                    type="button"
                    className={originalThumbnailSelected && selectedImageIndex === index ? "is-active" : undefined}
                    aria-label={`Show original catalog image ${index + 1}`}
                    aria-pressed={originalThumbnailSelected && selectedImageIndex === index}
                    onClick={() => {
                      setSelectedDemoImageId(null);
                      setOriginalThumbnailSelected(true);
                      setSelectedImageIndex(index);
                    }}
                  >
                    <ResponsiveProductImage image={image} />
                    <span className="product-preview-thumb-caption">Original {index + 1}</span>
                  </button>
                ))}
              </div>
            ) : product.images.length > 1 ? (
              <div
                className="product-thumbnails"
                aria-label="Product images"
              >
                {product.images.map(
                  (image, index) => (
                    <button
                      type="button"
                      key={image.path}
                      className={
                        index
                        === selectedImageIndex
                          ? "is-active"
                          : undefined
                      }
                      aria-label={
                        `Show image ${index + 1}`
                      }
                      aria-pressed={
                        index
                        === selectedImageIndex
                      }
                      onClick={() => {
                        setSelectedImageIndex(
                          index,
                        );
                      }}
                    >
                      <ResponsiveProductImage
                        image={image}
                      />
                    </button>
                  ),
                )}
              </div>
            ) : null}
          </div>

          <div className="product-detail-copy">
            <p className="product-meta">
              {presentation.categoryName}
            </p>

            <div className="product-detail-identity">
              <h1>{presentation.familyName}</h1>

              {presentation.variantLabel !== null ? (
                <p className="product-detail-system-type">
                  {presentation.variantLabel}
                </p>
              ) : null}

              {presentation.technologyLabel !== null ? (
                <p className="product-technology">
                  {presentation.technologyLabel}
                </p>
              ) : null}
            </div>

            <section
              className="product-detail-overview"
              aria-labelledby="product-overview-heading"
            >
              <p className="eyebrow">Overview</p>
              <h2
                id="product-overview-heading"
                className="product-detail-section-title"
              >
                System overview
              </h2>
              <p className="product-detail-description">
                {product.sku === "DD5RO"
                  ? (presentation.catalogSummary ?? product.description).replace(
                      " For everyday drinking water, consider Origin Alkaline Plus.",
                      "",
                    )
                  : (presentation.catalogSummary ?? product.description)}
              </p>
            </section>

            {presentation.education !== null ? (
              <aside
                className="product-technology-note"
                aria-label="About CLEAR Technology"
              >
                <p className="eyebrow">
                  CLEAR Technology
                </p>
                <p className="product-technology-explanation">
                  {presentation.education}
                </p>

                {presentation.technologyFacts.length > 0 ? (
                  <div className="product-technology-terms">
                    <p className="product-technology-terms-title">
                      CLEAR terminology
                    </p>
                    <dl>
                      {presentation.technologyFacts.map((fact) => (
                        <div key={fact.label}>
                          <dt>{fact.label}</dt>
                          <dd>{fact.value}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                ) : null}

                {presentation.technologyGuidance !== null ? (
                  <p className="product-technology-guidance">
                    {presentation.technologyGuidance}
                  </p>
                ) : null}
              </aside>
            ) : null}

            {presentation.installationFacts.length > 0 ? (
              <section
                className="product-installation"
                aria-labelledby="product-installation-heading"
              >
                <p className="eyebrow">
                  Installation &amp; ownership
                </p>
                <h2
                  id="product-installation-heading"
                  className="product-detail-section-title"
                >
                  Designed for straightforward ownership.
                </h2>

                <dl className="product-facts">
                  {presentation.installationFacts.map((fact) => (
                    <div key={fact.label}>
                      <dt>{fact.label}</dt>
                      <dd>{fact.value}</dd>
                    </div>
                  ))}
                </dl>

                {presentation.ownershipGuidance !== null ? (
                  <p className="product-ownership-guidance">
                    {presentation.ownershipGuidance}
                  </p>
                ) : null}
              </section>
            ) : null}

            <InstallationServicesNotice />

            {configurationFamily !== null ? (
              <section
                className="product-variant-selector"
                aria-labelledby="family-configuration-heading"
              >
                <p className="eyebrow">Configuration</p>
                <h2 id="family-configuration-heading" className="product-detail-section-title">
                  Choose your {configurationFamily.name} system
                </h2>
                <label>
                  <span>AVAILABLE CONFIGURATIONS</span>
                  <select
                    value={product.sku}
                    onChange={(event) => {
                      const path = `/systems/${event.target.value.toLowerCase()}`;
                      if (path !== product.public_path) onNavigate(path, true);
                    }}
                  >
                    {configurationFamily.configurations.map((configuration) => (
                      <option key={configuration.sku} value={configuration.sku}>
                        {configuration.label}
                      </option>
                    ))}
                  </select>
                </label>
                {configurationLoading ? (
                  <p role="status">Updating configuration…</p>
                ) : null}
                <p className="product-ownership-guidance">
                  {configurationFamily.configurations.find(
                    (configuration) => configuration.sku === product.sku)?.details}
                </p>
              </section>
            ) : null}


            {fittingEligible ? (
              <section
                className="product-variant-selector product-installation-fittings"
                aria-labelledby="clack-installation-fittings-heading"
              >
                <p className="eyebrow">Installation connection</p>
                <h2 id="clack-installation-fittings-heading" className="product-detail-section-title">
                  Select your connection fitting
                </h2>
                <label>
                  <span>CONNECTION SIZE (OPTIONAL)</span>
                  <select
                    value={selectedFittingSize}
                    onChange={(event) => {
                      const nextSize = event.target.value;
                      setSelectedFittingSize(nextSize);
                      const possible = clackFittingsForSize(nextSize);
                      const suggested = possible.find((item) => item.orderNo === "V3007-22LF")
                        ?? possible.find((item) => item.label.startsWith("Brass Sweat"));
                      setSelectedFittingType(imagePreviewEnabled && CAN_PREVIEW_PRODUCT_IMAGERY
                        ? (suggested?.label ?? "") : "");
                      setFittingExplicitlyChosen(false);
                      if (configurableGallery.length > 0) setSelectedDemoImageId("system");
                    }}
                  >
                    <option value="">Choose connection size</option>
                    {CLACK_CONNECTION_SIZES.map((size) => (
                      <option key={size} value={size}>{size}</option>
                    ))}
                  </select>
                </label>
                <div className="product-fitting-type-field">
                  <span id="clack-fitting-type-label">FITTING TYPE (OPTIONAL)</span>
                  {imagePreviewEnabled && CAN_PREVIEW_PRODUCT_IMAGERY ? (
                    <ClackFittingThumbnailSelect
                      options={fittingOptions}
                      value={selectedFittingType}
                      disabled={selectedFittingSize === ""}
                      onChange={(nextType) => {
                        setSelectedFittingType(nextType);
                        setFittingExplicitlyChosen(nextType !== "");
                        if (configurableGallery.length > 0) {
                          setSelectedDemoImageId(nextType === "" ? "system" : "hookup");
                          setOriginalThumbnailSelected(false);
                        }
                      }}
                    />
                  ) : (
                    <select
                      aria-labelledby="clack-fitting-type-label"
                      value={selectedFittingType}
                      onChange={(event) => {
                        setSelectedFittingType(event.target.value);
                        setFittingExplicitlyChosen(event.target.value !== "");
                      }}
                      disabled={selectedFittingSize === ""}
                    >
                      <option value="">{selectedFittingSize === "" ? "Choose size first" : "Choose fitting type"}</option>
                      {fittingOptions.map((fitting) => (
                        <option key={fitting.orderNo} value={fitting.label}>
                          {shortClackFittingLabel(fitting)}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
                {selectedFitting !== null ? (
                  <p className="product-ownership-guidance">
                    {fittingExplicitlyChosen ? "Selected" : "Visual preview default"}: {selectedFitting.size} — {shortClackFittingLabel(selectedFitting)}.
                  </p>
                ) : null}
                {imagePreviewEnabled && CAN_PREVIEW_PRODUCT_IMAGERY && !fittingExplicitlyChosen ? (
                  <p className="product-ownership-guidance">
                    This brass fitting is a visual preview suggestion, not a universal compatibility or quality claim.
                    Choose a fitting explicitly to include it in a quote request.
                  </p>
                ) : null}
                <p className="product-ownership-guidance">
                  Not sure which fitting you need? Leave either field blank and our team
                  can help. Compatibility, availability and final cost require confirmation;
                  installation labor is not included.
                </p>
              </section>
            ) : null}

            {product.variants.length > 0 ? (
              <section
                className="product-variant-selector"
                aria-labelledby="product-variant-selector-heading"
              >
                <p className="eyebrow">Configuration</p>
                <h2
                  id="product-variant-selector-heading"
                  className="product-detail-section-title"
                >
                  Select system size
                </h2>
                <label>
                  <span>MEDIA VOLUME</span>
                  <select
                    value={selectedVariant?.id ?? product.variants[0].id}
                    onChange={(event) => {
                      setSelectedVariantId(event.target.value);
                      setSelectedImageIndex(0);
                    }}
                  >
                    {product.variants.map((variant) => (
                      <option key={variant.id} value={variant.id}>
                        {variant.option_values.media_volume ?? variant.display_name}
                      </option>
                    ))}
                  </select>
                </label>
              </section>
            ) : null}

            {availability.lifecycle_status === "soon_discontinued" ? (
              <aside className="product-availability product-lifecycle-notice">
                <p className="eyebrow">Product lifecycle</p>
                <h2 className="product-detail-section-title">Soon to be discontinued</h2>
                <p>Availability may be limited as this system approaches end of sale.</p>
              </aside>
            ) : availability.lifecycle_status === "discontinued" ? (
              <aside className="product-availability product-lifecycle-notice">
                <p className="eyebrow">Product lifecycle</p>
                <h2 className="product-detail-section-title">Discontinued</h2>
                <p>This system is no longer offered for normal purchase or formal quoting.</p>
              </aside>
            ) : null}

            {availability?.status === "out_of_stock" ? (
              <aside
                className="product-availability product-availability-out"
                aria-labelledby="product-availability-heading"
              >
                <p className="eyebrow">Availability</p>
                <h2
                  id="product-availability-heading"
                  className="product-detail-section-title"
                >
                  Out of stock
                </h2>

                {availability.expected_available_on !== null ? (
                  <p>
                    Expected availability: {new Date(`${availability.expected_available_on}T00:00:00`).toLocaleDateString()}
                  </p>
                ) : availability.estimated_lead_time !== null ? (
                  <p>
                    Estimated availability: {availability.estimated_lead_time}
                  </p>
                ) : (
                  <p>
                    Timing will be updated when a reliable fulfillment estimate is available.
                  </p>
                )}

                {availability.can_notify_when_in_stock ? (
                  <div className="stock-notification-form">
                    <label>
                      <span>Email for availability notice</span>
                      <input
                        type="email"
                        autoComplete="email"
                        value={notificationEmail}
                        onChange={(event) => {
                          setNotificationEmail(event.target.value);
                          setNotificationState("idle");
                          setNotificationMessage(null);
                        }}
                      />
                    </label>
                    <div className="stock-notification-actions">
                      <button
                        type="button"
                        className="primary-button"
                        disabled={
                          notificationState === "saving"
                          || notificationState === "cancelling"
                        }
                        onClick={() => void handleStockNotification()}
                      >
                        {notificationState === "saving"
                          ? "Saving…"
                          : notificationState === "saved"
                            ? "Notification requested ✓"
                            : "Notify When in Stock"}
                      </button>
                      <button
                        type="button"
                        className="text-button compact"
                        disabled={
                          notificationState === "saving"
                          || notificationState === "cancelling"
                        }
                        onClick={() => void handleStockNotificationCancellation()}
                      >
                        {notificationState === "cancelling"
                          ? "Cancelling…"
                          : notificationState === "cancelled"
                            ? "Request cancelled"
                            : "Cancel availability notice"}
                      </button>
                    </div>
                    <small>
                      Availability notices are one-time transactional messages,
                      sent only after staff confirms the system is available.
                    </small>
                    {notificationMessage !== null ? (
                      <p role="status">{notificationMessage}</p>
                    ) : null}
                  </div>
                ) : null}
              </aside>
            ) : null}

            <div className="detail-commerce">
              {pricing.display_price
              && pricing.amount_minor
                !== null
              && pricing.currency
                !== null ? (
                <strong className="detail-price">
                  {formatPrice(
                    pricing.amount_minor,
                    pricing.currency,
                  )}
                </strong>
              ) : (
                <p className="detail-policy">
                  {pricing.action_label}
                </p>
              )}

              <p className="detail-purchase-boundary">
                Equipment only at launch. Installation is arranged separately from
                D&apos;Acqua Dolce&apos;s equipment sale and is not included in this
                purchase or quote request.
              </p>

              {commerceError !== null ? (
                <p
                  className="commerce-error"
                  role="alert"
                >
                  {commerceError}
                </p>
              ) : null}

              <button
                type="button"
                className="detail-primary-action"
                disabled={
                  addingToCart
                  || configurationLoading
                  || ((availability.status === "out_of_stock" || availability.status === "discontinued")
                    && !availability.can_inquire)
                }
                onClick={() => {
                  void handlePrimaryAction();
                }}
              >
                {addingToCart
                  ? "Adding…"
                  : (availability.status === "out_of_stock" || availability.status === "discontinued")
                    ? (availability.can_inquire ? "Send inquiry" : "Unavailable")
                    : pricing.action === "ADD_TO_CART" && fittingForInquiry !== null
                      ? "Request fitting quote"
                      : pricing.action_label}
              </button>
            </div>

            {product.replacements.length > 0 ? (
              <section
                className="product-options"
                aria-labelledby="product-replacements-heading"
              >
                <p className="eyebrow">Current alternatives</p>
                <h2
                  id="product-replacements-heading"
                  className="product-detail-section-title"
                >
                  Recommended replacement
                </h2>
                <p className="product-options-intro">
                  These current products are shown only when staff has explicitly
                  approved the replacement relationship for public presentation.
                </p>

                <div className="product-option-list">
                  {product.replacements.map((replacement) => (
                    <article
                      className="product-option-row"
                      key={`replacement-${replacement.id}`}
                    >
                      <div>
                        <p className="product-option-type">Replacement</p>
                        <h3>{replacement.name}</h3>
                        {replacement.system_type !== null ? (
                          <p className="product-option-system-type">
                            {replacement.system_type}
                          </p>
                        ) : null}
                      </div>

                      <button
                        type="button"
                        className="text-button"
                        onClick={() => {
                          onNavigate(replacement.public_path);
                        }}
                      >
                        View replacement
                      </button>
                    </article>
                  ))}
                </div>
              </section>
            ) : null}

            {product.options_accessories.length > 0 ? (
              <section
                className="product-options"
                aria-labelledby="product-options-heading"
              >
                <p className="eyebrow">Options &amp; accessories</p>
                <h2
                  id="product-options-heading"
                  className="product-detail-section-title"
                >
                  Compatible additions
                </h2>
                <p className="product-options-intro">
                  These additions are shown only when their relationship to this system has been explicitly approved for public presentation.
                </p>

                <div className="product-option-list">
                  {product.options_accessories.map((option) => (
                    <article
                      className="product-option-row"
                      key={`${option.relationship_type}-${option.id}`}
                    >
                      <div>
                        <p className="product-option-type">
                          {relationshipLabel(option.relationship_type)}
                        </p>
                        <h3>{option.name}</h3>
                        {option.system_type !== null ? (
                          <p className="product-option-system-type">
                            {option.system_type}
                          </p>
                        ) : null}
                      </div>

                      <button
                        type="button"
                        className="text-button"
                        onClick={() => {
                          onNavigate(option.public_path);
                        }}
                      >
                        View {relationshipLabel(option.relationship_type).toLowerCase()}
                      </button>
                    </article>
                  ))}
                </div>
              </section>
            ) : null}

            {product.manufacturer_claims.length > 0 ? (
              <section
                className="product-manufacturer-claims"
                aria-labelledby="product-manufacturer-claims-heading"
              >
                <p className="eyebrow">Manufacturer provenance</p>
                <h2
                  id="product-manufacturer-claims-heading"
                  className="product-detail-section-title"
                >
                  Manufacturer-stated claims
                </h2>
                <p className="product-claims-intro">
                  These statements are presented as manufacturer-stated information,
                  with the recorded source shown alongside each claim.
                </p>
                <div className="product-claim-list">
                  {product.manufacturer_claims.map((claim) => (
                    <article className="product-claim-card" key={`${claim.claim_text}-${claim.source_reference}`}>
                      <span className="product-claim-provenance">{claim.provenance_label}</span>
                      <p>{claim.claim_text}</p>
                      <small>Source: {claim.source_reference}</small>
                    </article>
                  ))}
                </div>
              </section>
            ) : null}

            {product.specifications.length > 0 || selectedVariant !== null ? (
              <section
                className="product-specifications"
                aria-labelledby="product-specifications-heading"
              >
                <p className="eyebrow">System details</p>
                <h2
                  id="product-specifications-heading"
                  className="product-detail-section-title"
                >
                  Specifications
                </h2>

                <dl className="product-facts">
                  {(() => {
                    const variantValues = selectedVariant?.option_values ?? {};
                    const reservedKeys = new Set(["image_path", "image_alt"]);
                    const baseKeys = new Set(product.specifications.map((item) => item.spec_key));
                    const merged = product.specifications.map((specification) => ({
                      ...specification,
                      value_text: variantValues[specification.spec_key] ?? specification.value_text,
                      unit: variantValues[specification.spec_key] !== undefined ? null : specification.unit,
                    }));
                    for (const [key, value] of Object.entries(variantValues)) {
                      if (reservedKeys.has(key) || baseKeys.has(key)) {
                        continue;
                      }
                      merged.push({
                        spec_key: key,
                        label: humanizeOptionKey(key),
                        value_text: value,
                        unit: null,
                      });
                    }
                    return merged.map((specification) => (
                      <div key={specification.spec_key}>
                        <dt>{specification.label}</dt>
                        <dd>
                          {specification.value_text}
                          {specification.unit !== null ? ` ${specification.unit}` : ""}
                        </dd>
                      </div>
                    ));
                  })()}
                </dl>
              </section>
            ) : null}

            <section
              className="product-reference"
              aria-labelledby="product-reference-heading"
            >
              <p className="eyebrow">Reference</p>
              <h2
                id="product-reference-heading"
                className="product-detail-section-title"
              >
                Product record
              </h2>
              <dl className="product-facts">
                <div>
                  <dt>SKU</dt>
                  <dd>{selectedVariant?.sku ?? product.sku}</dd>
                </div>
              </dl>
            </section>

            {product.documents.length > 0 ? (
              <section className="product-documents">
                <h2>Documents</h2>

                <ul>
                  {product.documents.map(
                    (document) => (
                      <li
                        key={
                          document.path
                        }
                      >
                        <a
                          href={
                            document.path
                          }
                        >
                          {document.title}
                        </a>
                      </li>
                    ),
                  )}
                </ul>
              </section>
            ) : null}

            <section
              className="product-support"
              aria-labelledby="product-support-heading"
            >
              <p className="eyebrow">Warranty &amp; support</p>
              <h2
                id="product-support-heading"
                className="product-detail-section-title"
              >
                Support for your system.
              </h2>
              <p>
                Warranty coverage applies to residential use only. Product-specific
                warranty documents are shown only when the recorded manufacturer document
                has passed the existing verification boundary. D&apos;Acqua Dolce can help
                route warranty and product-support questions without adding or changing
                manufacturer warranty terms.
              </p>
              <details className="product-support-request">
                <summary>Start a warranty or support request</summary>
                <SupportRequestForm
                  account={account}
                  productId={product.id}
                  productName={contactProductName}
                  defaultKind="warranty"
                />
              </details>
              <p className="product-support-email">
                Prefer email? <a href="mailto:support@dacquadolce.com">support@dacquadolce.com</a>
              </p>
            </section>
          </div>
        </section>
      </main>
    </>
  );
}
