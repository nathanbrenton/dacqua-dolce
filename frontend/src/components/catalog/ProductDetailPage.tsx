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
} from "../../api/catalog";
import type { AuthenticationStatus } from "../../api/authentication";
import {
  addCartItem,
} from "../../api/cart";
import { QuoteDialog } from "../quotes/QuoteDialog";
import { SupportRequestForm } from "../support/SupportRequestForm";
import { ResponsiveProductImage } from "./ResponsiveProductImage";
import { getProductPresentation } from "./productPresentation";

type ProductDetailPageProps = {
  slug: string;
  account: AuthenticationStatus | null;
  onNavigate: (path: string) => void;
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
  const [selectedVariantId, setSelectedVariantId] =
    useState<string | null>(null);
  const [quoteOpen, setQuoteOpen] =
    useState(false);
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
    setLoading(true);
    setError(null);
    setSelectedImageIndex(0);
    setSelectedVariantId(null);
    setNotificationEmail(account?.email ?? "");
    setNotificationState("idle");
    setNotificationMessage(null);

    void getCatalogProduct(slug)
      .then((result) => {
        setProduct(result);
      })
      .catch((caught) => {
        setError(
          caught instanceof Error
            ? caught.message
            : "System unavailable.",
        );
      })
      .finally(() => {
        setLoading(false);
      });
  }, [slug, account]);

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
        productName={
          selectedVariant !== null
            ? `${product.name} — ${selectedVariant.display_name}`
            : product.name
        }
        inquiryContext="product"
        initialEmail={
          account?.email ?? null
        }
        recommendationContext={null}
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
              {selectedImage !== null ? (
                <ResponsiveProductImage
                  image={selectedImage}
                  loading="eager"
                />
              ) : (
                <div
                  className="product-media-placeholder"
                  aria-hidden="true"
                />
              )}
            </div>

            {product.images.length > 1 ? (
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
                {presentation.catalogSummary ?? product.description}
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
                  productName={
                    selectedVariant !== null
                      ? `${product.name} — ${selectedVariant.display_name}`
                      : product.name
                  }
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
