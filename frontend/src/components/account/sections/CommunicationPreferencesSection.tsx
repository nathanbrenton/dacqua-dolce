// Reminder and update email preferences on the account page.
//
// API: updateCommunicationPreferences in api/account.ts
//   -> PUT /api/account/communication-preferences

import { type Dispatch, type SetStateAction } from "react";
import {
  type CommunicationPreferences,
  updateCommunicationPreferences,
} from "../../../api/account";
import { type AccountNoticeProps, type AccountSavingProps } from "../accountShared";

type CommunicationPreferencesSectionProps = {
  preferences: CommunicationPreferences | null;
  onPreferencesChange: Dispatch<SetStateAction<CommunicationPreferences | null>>;
} & AccountSavingProps & AccountNoticeProps;

export function CommunicationPreferencesSection({
  preferences: communicationPreferences,
  onPreferencesChange: setCommunicationPreferences,
  saving,
  onSavingChange: setSaving,
  onError: setError,
  onNotice: setSaveNotice,
}: CommunicationPreferencesSectionProps) {
  async function saveCommunicationPreferences() {
    if (communicationPreferences === null) {
      return;
    }

    setSaving(true);
    setError(null);
    setSaveNotice(null);

    try {
      const updated = await updateCommunicationPreferences(
        communicationPreferences,
      );
      setCommunicationPreferences(updated);
      setSaveNotice("Communication preferences updated.");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Communication preference update failed.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="account-panel account-preferences-panel">
      <p className="eyebrow">Communication</p>
      <h2>Choose your reminders.</h2>
      <p className="account-muted">
        Optional maintenance and follow-up messages stay off until you choose them. Security, account, order, and other required transactional messages are separate from these preferences.
      </p>

      {communicationPreferences !== null ? (
        <div className="account-preference-list">
          {[
            ["filter_replacement_reminders", "Filter replacement reminders", "Helpful when a replaceable cartridge is part of your system."],
            ["softener_check_reminders", "Softener salt / check reminders", "Periodic reminders to inspect salt and routine softener settings."],
            ["uv_service_reminders", "UV lamp / service reminders", "Service reminders when UV treatment is part of your installed configuration."],
            ["annual_system_check_reminders", "Annual system check reminders", "A yearly prompt to review the condition and operation of your system."],
            ["product_specific_reminders", "Product-specific maintenance reminders", "Maintenance guidance tied to the equipment recorded for your account."],
            ["post_purchase_followup", "Post-purchase follow-up", "One useful follow-up after an equipment purchase."],
            ["post_installation_followup", "Post-installation follow-up", "One useful follow-up after installation information is recorded."],
          ].map(([key, label, description]) => (
            <label key={key} className="account-preference-option">
              <input
                type="checkbox"
                checked={communicationPreferences[key as keyof CommunicationPreferences]}
                onChange={(event) => {
                  setCommunicationPreferences({
                    ...communicationPreferences,
                    [key]: event.target.checked,
                  });
                }}
              />
              <span>
                <strong>{label}</strong>
                <small>{description}</small>
              </span>
            </label>
          ))}

          <button
            type="button"
            className="account-action"
            disabled={saving}
            onClick={() => {
              void saveCommunicationPreferences();
            }}
          >
            Save Communication Preferences
          </button>
        </div>
      ) : (
        <p className="account-muted">Loading communication preferences…</p>
      )}
    </section>
  );
}
