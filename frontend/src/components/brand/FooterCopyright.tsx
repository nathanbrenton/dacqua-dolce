export function FooterCopyright() {
  const year = new Date().getFullYear();

  return (
    <small>
      © {year} D&apos;Acqua Dolce.
      {" "}
      All rights reserved.
    </small>
  );
}
