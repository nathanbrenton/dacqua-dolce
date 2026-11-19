// Props shared by the customer account sections (account/sections/*).
// The page shows one alert and one toast; sections report into them.

export type AccountNoticeProps = {
  /** Page-level alert (null clears it). */
  onError: (text: string | null) => void;
  /** Success toast (null clears the last notice). */
  onNotice: (text: string | null) => void;
};

/** One busy flag for the whole page, so a save anywhere disables other saves. */
export type AccountSavingProps = {
  saving: boolean;
  onSavingChange: (saving: boolean) => void;
};
