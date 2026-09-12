import {
  useEffect,
  useState,
} from "react";

import {
  getCatalogProducts,
  type CatalogProduct,
} from "../../api/catalog";
import { ResponsiveProductImage } from "./ResponsiveProductImage";

type CatalogSectionProps = {
  onNavigate: (path: string) => void;
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

export function CatalogSection({
  onNavigate,
}: CatalogSectionProps) {
  const [products, setProducts] =
    useState<CatalogProduct[]>([]);
  const [loading, setLoading] =
    useState(true);
  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    void getCatalogProducts()
      .then((catalogProducts) => {
        setProducts(catalogProducts);
        setError(null);
      })
      .catch((caught) => {
        setError(
          caught instanceof Error
            ? caught.message
            : "Catalog unavailable.",
        );
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const developerMode =
    import.meta.env.VITE_DEVELOPER_MODE
    === "true";

  if (
    !loading
    && error === null
    && products.length === 0
    && !developerMode
  ) {
    return null;
  }

  return (
    <section
      id="systems"
      className="catalog-section"
      aria-labelledby="systems-heading"
    >
      <div className="section-heading">
        <p className="eyebrow">
          Systems
        </p>

        <h2 id="systems-heading">
          Designed around the water you live with.
        </h2>

        <p>
          Product specifications, availability,
          pricing visibility, and purchase actions
          come from the authoritative catalog.
        </p>
      </div>

      {loading ? (
        <p
          className="catalog-status"
          role="status"
        >
          Loading systems…
        </p>
      ) : null}

      {error !== null ? (
        <p
          className="catalog-status catalog-error"
          role="alert"
        >
          {error}
        </p>
      ) : null}

      {!loading
      && error === null
      && products.length === 0
      && developerMode ? (
        <div className="catalog-empty">
          <strong>
            Developer catalog is empty.
          </strong>

          <p>
            Add authoritative product records
            when manufacturer/business data
            is ready.
          </p>
        </div>
      ) : null}

      {products.length > 0 ? (
        <div className="product-grid">
          {products.map((product) => (
            <article
              className="product-card"
              key={product.id}
            >
              <button
                type="button"
                className="product-media product-media-button"
                aria-label={`View ${product.name}`}
                onClick={() => {
                  onNavigate(
                    product.public_path,
                  );
                }}
              >
                {product.primary_image
                  !== null ? (
                  <ResponsiveProductImage
                    image={
                      product.primary_image
                    }
                  />
                ) : (
                  <span
                    className="product-media-placeholder"
                    aria-hidden="true"
                  />
                )}
              </button>

              <div className="product-card-body">
                <p className="product-meta">
                  {product.category}
                </p>

                <h3>{product.name}</h3>

                <p className="product-description">
                  {product.description}
                </p>

                <div className="product-commerce">
                  {product.pricing
                    .display_price
                  && product.pricing
                    .amount_minor !== null
                  && product.pricing
                    .currency !== null ? (
                    <strong className="product-price">
                      {formatPrice(
                        product.pricing
                          .amount_minor,
                        product.pricing
                          .currency,
                      )}
                    </strong>
                  ) : (
                    <span className="product-policy">
                      {
                        product.pricing
                          .action_label
                      }
                    </span>
                  )}

                  <button
                    type="button"
                    className="product-action"
                    onClick={() => {
                      onNavigate(
                        product.public_path,
                      );
                    }}
                  >
                    View System
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
