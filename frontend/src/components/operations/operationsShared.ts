/**
 * Small helpers shared by more than one Operations workspace.
 * Workspace-specific helpers live in that workspace's own file.
 */

/** Save progress for a row-level "Save" button. */
export type SaveState =
  | "idle"
  | "saving"
  | "saved";

/** Props every workspace gets for the page-level message banner. */
export type OperationsNoticeProps = {
  /** Shows a success message in the banner at the top of Operations. */
  onMessage: (text: string | null) => void;
  /** Shows an error in the banner at the top of Operations. */
  onError: (text: string | null) => void;
};

/** Value for an <input type="datetime-local"> in the browser's timezone. */
export function localDateTimeValue(date: Date): string {
  const local = new Date(
    date.getTime() - date.getTimezoneOffset() * 60_000,
  );

  return local.toISOString().slice(0, 16);
}
