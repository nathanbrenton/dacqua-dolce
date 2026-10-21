import {
  useEffect,
  useState,
} from "react";

import { DEVELOPER_MODE } from "../../config/environment";
import {
  getCatalogProducts,
  type CatalogProduct,
  type CatalogImage,
} from "../../api/catalog";
import { PreviewProductImage } from "./PreviewProductImage";
import { getProductPresentation } from "./productPresentation";
import { CONFIGURATION_FAMILIES } from "./productConfigurations";

type CatalogSectionProps = {
  imagePreviewEnabled: boolean;
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



/**
 * Temporary storefront family imagery, reused from the pre-PT41 catalog.
 * Never attach these historical photos to new SKUs as verified product images.
 * The earlier Harmony photo does NOT depict a verified Pureline Duo assembly.
 * Remove each fallback when its current default SKU has approved imagery.
 */
const FAMILY_CARD_IMAGE_FALLBACKS: Readonly<Record<string, CatalogImage>> = {
  Refine: {
    path: "/products/media/refine-1-5-cf.jpeg",
    alt_text: "Earlier Refine water-softener system with brine tank; representative image",
  },
  Harmony: {
    path: "/products/media/1-5cf-pass-through-with-prefilter-dimensions.webp",
    alt_text: "Earlier Harmony water conditioner with prefilter; illustrative, not the Pureline Duo configuration",
  },
};

export function CatalogSection({
  imagePreviewEnabled,
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

  // Preserve the backend's configurable family ordering, while rendering one
  // card per family. A card's destination always belongs to a real SKU.
  const groupedProducts: CatalogProduct[] = [];
  const shownFamilies = new Set<string>();
  for (const item of products) {
    const family = CONFIGURATION_FAMILIES.find(
      (entry) => entry.name === item.product_family);
    if (family === undefined) {
      groupedProducts.push(item);
      continue;
    }
    if (shownFamilies.has(family.name)) continue;
    shownFamilies.add(family.name);
    const candidates = products.filter((product) =>
      family.configurations.some((configuration) => configuration.sku === product.sku));
    // Before the PT41 database rollout, show the existing family card; after
    // rollout, prefer the explicitly configured SKU for each family.
    groupedProducts.push(
      candidates.find((product) => product.sku === family.defaultSku)
      ?? candidates[0]
      ?? item,
    );
  }

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
          {groupedProducts.map((product) => {
            const presentation = getProductPresentation(product);
            const family = CONFIGURATION_FAMILIES.find((entry) =>
              entry.configurations.some((configuration) => configuration.sku === product.sku));
            // The API image always takes precedence. Fallbacks are for cards only;
            // no unverified media is attached to a new product-detail record.
            const illustrativeImage = product.primary_image === null
              ? FAMILY_CARD_IMAGE_FALLBACKS[family?.name ?? ""] ?? null
              : null;
            const cardImage = product.primary_image ?? illustrativeImage;

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
                <PreviewProductImage
                  sku={product.sku}
                  original={cardImage}
                  enabled={imagePreviewEnabled}
                  presentation="landing"
                />
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
                  {family?.summary ?? presentation.catalogSummary ?? product.description}
                </p>

                {illustrativeImage !== null ? (
                  <p className="product-image-note">
                    Representative image; selected configuration may differ.
                  </p>
                ) : null}

                {family !== undefined ? (
                  <p className="product-configuration-count">
                    {family.configurations.length} configurations available
                  </p>
                ) : null}

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
