import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getCatalogProduct,
  subscribeStockNotification,
  type CatalogProductDetail,
} from "../../api/catalog";
import type { AuthenticationStatus } from "../../api/authentication";
import {
  addCartItem,
} from "../../api/cart";
import { QuoteDialog } from "../quotes/QuoteDialog";
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
  return value === "accessory" ? "Accessory" : "Option";
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
  const [quoteOpen, setQuoteOpen] =
    useState(false);
  const [commerceError, setCommerceError] =
    useState<string | null>(null);
  const [addingToCart, setAddingToCart] =
    useState(false);
  const [notificationEmail, setNotificationEmail] =
    useState(account?.email ?? "");
  const [notificationState, setNotificationState] =
    useState<"idle" | "saving" | "saved">("idle");
  const [notificationMessage, setNotificationMessage] =
    useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setSelectedImageIndex(0);
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

  const selectedImage = useMemo(
    () => (
      product?.images[
        selectedImageIndex
      ] ?? product?.primary_image ?? null
    ),
    [
      product,
      selectedImageIndex,
    ],
  );

  if (loading) {
    return (
      <main className="detail-shell">
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
      <main className="detail-shell">
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

  const pricing = product.pricing;
  const availability = product.availability;
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

  async function handlePrimaryAction() {
    setCommerceError(null);

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
        productName={product.name}
        inquiryContext="product"
        initialEmail={
          account?.email ?? null
        }
        recommendationContext={null}
        onClose={() => {
          setQuoteOpen(false);
        }}
      />

      <main className="detail-shell">
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
              {product.category}
            </p>

            <div className="product-detail-identity">
              <h1>{presentation.familyName}</h1>

              {presentation.systemType !== null ? (
                <p className="product-detail-system-type">
                  {presentation.systemType}
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

                {availability.estimated_lead_time !== null ? (
                  <p>
                    Estimated lead time: {availability.estimated_lead_time}
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
                    <button
                      type="button"
                      className="primary-button"
                      disabled={notificationState === "saving"}
                      onClick={() => void handleStockNotification()}
                    >
                      {notificationState === "saving"
                        ? "Saving…"
                        : notificationState === "saved"
                          ? "Notification requested ✓"
                          : "Notify When in Stock"}
                    </button>
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
                disabled={addingToCart}
                onClick={() => {
                  void handlePrimaryAction();
                }}
              >
                {addingToCart
                  ? "Adding…"
                  : pricing.action_label}
              </button>
            </div>

            {product.variants.length > 0 ? (
              <section
                className="product-configurations"
                aria-labelledby="product-configurations-heading"
              >
                <p className="eyebrow">Configurations</p>
                <h2
                  id="product-configurations-heading"
                  className="product-detail-section-title"
                >
                  Available sizes &amp; capacities
                </h2>

                <div className="product-configuration-grid">
                  {product.variants.map((variant) => (
                    <article
                      className="product-configuration-card"
                      key={variant.id}
                    >
                      <h3>{variant.display_name}</h3>

                      {Object.keys(variant.option_values).length > 0 ? (
                        <dl className="product-configuration-values">
                          {Object.entries(variant.option_values).map(
                            ([key, value]) => (
                              <div key={key}>
                                <dt>{humanizeOptionKey(key)}</dt>
                                <dd>{value}</dd>
                              </div>
                            ),
                          )}
                        </dl>
                      ) : null}

                      <p className="product-configuration-sku">
                        SKU {variant.sku}
                      </p>
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

            {product.specifications.length > 0 ? (
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
                  {product.specifications.map(
                    (specification) => (
                      <div key={specification.spec_key}>
                        <dt>{specification.label}</dt>
                        <dd>
                          {specification.value_text}
                          {specification.unit !== null
                            ? ` ${specification.unit}`
                            : ""}
                        </dd>
                      </div>
                    ),
                  )}
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
                  <dd>{product.sku}</dd>
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
          </div>
        </section>
      </main>
    </>
  );
}
