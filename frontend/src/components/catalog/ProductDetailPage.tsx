import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getCatalogProduct,
  type CatalogProductDetail,
} from "../../api/catalog";
import type { AuthenticationStatus } from "../../api/authentication";
import {
  addCartItem,
} from "../../api/cart";
import { QuoteDialog } from "../quotes/QuoteDialog";
import { ResponsiveProductImage } from "./ResponsiveProductImage";

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

  useEffect(() => {
    setLoading(true);
    setError(null);
    setSelectedImageIndex(0);

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
  const productId = product.id;

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
        initialEmail={
          account?.email ?? null
        }
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
              {product.manufacturer}
              {" · "}
              {product.category}
            </p>

            <h1>{product.name}</h1>

            <p className="product-detail-description">
              {product.description}
            </p>

            <dl className="product-facts">
              <div>
                <dt>SKU</dt>
                <dd>{product.sku}</dd>
              </div>

              {product.product_family
                !== null ? (
                <div>
                  <dt>Family</dt>
                  <dd>
                    {
                      product.product_family
                    }
                  </dd>
                </div>
              ) : null}

              {product.variants.length
                > 0 ? (
                <div>
                  <dt>Variants</dt>
                  <dd>
                    {
                      product.variants
                        .length
                    }
                  </dd>
                </div>
              ) : null}
            </dl>

            {product.specifications.length > 0 ? (
              <section
                className="product-specifications"
                aria-labelledby="product-specifications-heading"
              >
                <h2 id="product-specifications-heading">
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
