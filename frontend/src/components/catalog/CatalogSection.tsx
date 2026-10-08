import {
  useEffect,
  useState,
} from "react";

import { DEVELOPER_MODE } from "../../config/environment";
import {
  getCatalogProducts,
  type CatalogProduct,
} from "../../api/catalog";
import { ResponsiveProductImage } from "./ResponsiveProductImage";
import { getProductPresentation } from "./productPresentation";

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

  const developerMode = DEVELOPER_MODE;

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
          Better water, designed around your life.
        </h2>

        <p>
          Explore our water treatment systems and pricing below.
        </p>
      </div>

      <aside
        className="catalog-purchase-boundary"
        aria-label="Purchase and installation boundary"
      >
        <strong>Installation &amp; Services</strong>
        <p>
          Equipment is currently offered without installation. Installation services
          and installer referrals may be available in the future. Please contact us
          to discuss your needs.
        </p>
      </aside>

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
          {products.map((product) => {
            const presentation =
              getProductPresentation(product);

            return (
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
                  {presentation.categoryName}
                </p>

                <div className="product-identity">
                  <h3>{presentation.familyName}</h3>

                  {presentation.variantLabel !== null ? (
                    <p className="product-system-type">
                      {presentation.variantLabel}
                    </p>
                  ) : null}

                  {presentation.technologyLabel !== null ? (
                    <p className="product-technology">
                      {presentation.technologyLabel}
                    </p>
                  ) : null}
                </div>

                <p className="product-description">
                  {presentation.catalogSummary ?? product.description}
                </p>

                {product.availability.lifecycle_status === "soon_discontinued" ? (
                  <p className="product-lifecycle-label">Soon to be discontinued</p>
                ) : null}

                <div className="product-commerce">
                  {product.availability.lifecycle_status === "discontinued" ? (
                    <span className="product-policy product-stock-status">
                      Discontinued
                    </span>
                  ) : product.availability.status === "out_of_stock" ? (
                    <span className="product-policy product-stock-status">
                      Out of stock
                      {product.availability.expected_available_on !== null
                        ? ` · expected ${new Date(`${product.availability.expected_available_on}T00:00:00`).toLocaleDateString()}`
                        : product.availability.estimated_lead_time !== null
                          ? ` · ${product.availability.estimated_lead_time}`
                          : ""}
                    </span>
                  ) : product.pricing
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
            );
          })}
        </div>
      ) : null}
    </section>
  );
}
