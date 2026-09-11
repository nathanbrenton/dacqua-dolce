function nationalDigits(
  value: string,
): string {
  let digits = value.replace(
    /[^0-9]/g,
    "",
  );

  const trimmed =
    value.trim();

  const hasExplicitCountryCode =
    trimmed.startsWith("+1");

  if (
    digits.startsWith("1")
    && (
      digits.length === 11
      || hasExplicitCountryCode
    )
  ) {
    digits = digits.slice(1);
  }

  return digits.slice(0, 10);
}


export function formatUsPhoneInput(
  value: string,
): string {
  const digits =
    nationalDigits(value);

  if (digits.length === 0) {
    return "";
  }

  if (digits.length <= 3) {
    return `(${digits}`;
  }

  if (digits.length <= 6) {
    return (
      `(${digits.slice(0, 3)}) `
      + digits.slice(3)
    );
  }

  return (
    `(${digits.slice(0, 3)}) `
    + `${digits.slice(3, 6)}-`
    + digits.slice(6)
  );
}


export function isCompleteUsPhone(
  value: string,
): boolean {
  return (
    nationalDigits(value).length
    === 10
  );
}
