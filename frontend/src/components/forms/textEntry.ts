/**
 * Mobile keyboard settings for typed fields. Spread one of these onto every
 * text `<input>` and `<textarea>` (tests/text-entry-autocorrect.test.mjs
 * checks that none is missed).
 *
 * iPhone autocorrect rewrites names, street addresses, codes and emails as
 * they're typed, so it is off everywhere. `autoCapitalize` is left to the
 * browser; set it per field only where a field needs it.
 */

/**
 * Names, addresses, emails, phones, ZIPs, codes, IDs, numbers, URLs and
 * searches: no autocorrect and no spell-check underline.
 */
export const exactEntryProps = {
  autoCorrect: "off",
  spellCheck: false,
} as const;

/**
 * Free-text messages and notes: no autocorrect, but misspellings are still
 * underlined.
 */
export const proseEntryProps = {
  autoCorrect: "off",
} as const;
