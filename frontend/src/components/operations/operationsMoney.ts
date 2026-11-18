/**
 * Dollar amounts typed by operators. Inputs show a "$" prefix, and a typed
 * "$", thousands commas or spaces are accepted and ignored.
 */

export const DOLLAR_AMOUNT_ERROR =
  "Enter amounts as dollars and cents, for example 2499.00.";

/** "$2,499.00" -> "2499.00"; anything else is returned trimmed. */
export function normalizeDollarInput(value: string): string {
  return value.trim().replace(/^\$\s*/, "").replace(/[,\s]/g, "");
}

/** Dollars to cents; null when blank. Throws on anything but dollars and cents. */
export function parseDollarsToMinor(value: string): number | null {
  const cleaned = normalizeDollarInput(value);
  if (cleaned === "") {
    return null;
  }
  if (!/^\d+(?:\.\d{1,2})?$/.test(cleaned)) {
    throw new Error(DOLLAR_AMOUNT_ERROR);
  }
  return Math.round(Number(cleaned) * 100);
}

const CONFIGURATION_HEADING = "Customer-requested configuration";

/**
 * Product inquiries store the server-rendered configuration summary ahead of
 * the customer's own words, separated by a blank line. Split them so the
 * summary can be folded away.
 */
export function splitRequestMessage(message: string | null): {
  configuration: string | null;
  customerMessage: string | null;
} {
  if (message === null || !message.startsWith(CONFIGURATION_HEADING)) {
    return { configuration: null, customerMessage: message };
  }
  const breakAt = message.indexOf("\n\n");
  if (breakAt === -1) {
    return { configuration: message, customerMessage: null };
  }
  const customerMessage = message.slice(breakAt + 2).trim();
  return {
    configuration: message.slice(0, breakAt),
    customerMessage: customerMessage === "" ? null : customerMessage,
  };
}

/** Minor units (cents) to a plain "12.34" string for an input; "" for none. */
export function minorToDollars(amountMinor: number | null): string {
  if (amountMinor === null) {
    return "";
  }

  return (amountMinor / 100).toFixed(2);
}

/** Minor units (cents) formatted as currency in the browser's locale. */
export function formatMoney(
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
