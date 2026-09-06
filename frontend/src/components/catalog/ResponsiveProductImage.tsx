import type { CatalogImage } from "../../api/catalog";

type ResponsiveProductImageProps = {
  image: CatalogImage;
  loading?: "eager" | "lazy";
  className?: string;
};

function jpegFallback(
  path: string,
): string {
  return path.endsWith(".webp")
    ? path.replace(/\.webp$/i, ".jpg")
    : path;
}

export function ResponsiveProductImage({
  image,
  loading = "lazy",
  className,
}: ResponsiveProductImageProps) {
  return (
    <picture>
      {image.path.endsWith(".webp") ? (
        <source
          srcSet={image.path}
          type="image/webp"
        />
      ) : null}

      <img
        className={className}
        src={jpegFallback(image.path)}
        alt={image.alt_text}
        loading={loading}
        decoding="async"
      />
    </picture>
  );
}
