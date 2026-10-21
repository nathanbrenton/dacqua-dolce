/**
 * Owner-supplied Clack fittings for Refine and Essence only.
 * These are requested fitting choices, NOT priced catalog inventory.
 * Verify compatibility, availability and final cost with Clack before quoting.
 */
export type ClackInstallationFitting = {
  size: string;
  label: string;
  orderNo: string;
};

export const CLACK_INSTALLATION_FITTINGS: readonly ClackInstallationFitting[] = [
  { size: '3/4"', label: 'Brass Sweat (Solder) Assembly LF', orderNo: 'V3007-03LF' },
  { size: '3/4"', label: 'SharkBite® Assembly', orderNo: 'V3007-12LF' },
  { size: '3/4"', label: 'Plastic Male NPT', orderNo: 'V3007-18' },
  { size: '1"', label: 'Brass Sweat (Solder) Assembly LF', orderNo: 'V3007-02LF' },
  { size: '1"', label: 'SharkBite® Assembly', orderNo: 'V3007-13LF' },
  { size: '1"', label: 'Plastic Male NPT', orderNo: 'V3007-04' },
  { size: '1"', label: 'Plastic Male NPT Elbow Assembly', orderNo: 'V3007' },
  { size: '1"', label: 'Brass Press/Sweat Assembly LF', orderNo: 'V3007-22LF' },
  { size: '1.25" / 1.5"', label: 'Brass Sweat (Solder) Assembly LF', orderNo: 'V3007-09LF' },
  { size: '1.25"', label: 'Plastic Male NPT Assembly', orderNo: 'V3007-05' },
];

// Separate connection sizes avoid cramped labels and clarify the shared
// 1.25-inch / 1.5-inch brass fitting (V3007-09LF).
export const CLACK_CONNECTION_SIZES = ['3/4"', '1"', '1.25"', '1.5"'] as const;

export function clackFittingsForSize(size: string): readonly ClackInstallationFitting[] {
  return CLACK_INSTALLATION_FITTINGS.filter((fitting) =>
    fitting.size === size ||
    (fitting.size === '1.25" / 1.5"' && (size === '1.25"' || size === '1.5"'))
  );
}

/** Short customer-facing fitting names; the full model number is internal. */
export function shortClackFittingLabel(fitting: ClackInstallationFitting): string {
  if (fitting.label.startsWith('Brass Sweat')) return 'Brass sweat / solder';
  if (fitting.label.startsWith('Brass Press/Sweat')) return 'Brass press / sweat';
  if (fitting.label.startsWith('SharkBite')) return 'SharkBite®';
  if (fitting.label.includes('Elbow')) return 'Plastic NPT elbow';
  return 'Plastic male NPT';
}

const CLACK_FITTING_SYSTEM_SKUS = new Set([
  'DD15SOFT', 'DD20SOFT', 'DD15CATRV', 'DD20CATRV',
]);

export function offersClackInstallationFittings(sku: string): boolean {
  return CLACK_FITTING_SYSTEM_SKUS.has(sku.toUpperCase());
}
