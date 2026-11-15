import {
  BUSINESS_PHONE_DISPLAY,
  BUSINESS_PHONE_HREF,
  SUPPORT_EMAIL,
  SUPPORT_EMAIL_HREF,
} from "../../config/businessContact";

/** "Prefer to reach us directly? Call … or email …" for support areas. */
export function BusinessContactLine() {
  return (
    <>
      Prefer to reach us directly? Call{" "}
      <a href={BUSINESS_PHONE_HREF}>{BUSINESS_PHONE_DISPLAY}</a>
      {" "}or email{" "}
      <a href={SUPPORT_EMAIL_HREF}>{SUPPORT_EMAIL}</a>.
    </>
  );
}

/** Phone and email in the site footer. */
export function FooterContact() {
  return (
    <address className="footer-contact" aria-label="Contact D'Acqua Dolce">
      <a href={BUSINESS_PHONE_HREF}>{BUSINESS_PHONE_DISPLAY}</a>
      <a href={SUPPORT_EMAIL_HREF}>{SUPPORT_EMAIL}</a>
    </address>
  );
}
