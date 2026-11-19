// Client profile form on the account page: name, phone and preferred contact
// method (utils/contactMethod.ts). The form edits the profile directly; problems
// show inline next to Save.
//
// API: updateProfile in api/account.ts -> PUT /api/account/profile

import {
  type Dispatch,
  type FormEvent,
  type SetStateAction,
  useState,
} from "react";
import { type CustomerProfile, updateProfile } from "../../../api/account";
import {
  CONTACT_METHOD_OPTIONS,
  type ContactMethod,
  contactMethodNeedsPhone,
  DEFAULT_CONTACT_METHOD,
  isContactMethod,
  PHONE_REQUIRED_MESSAGE,
} from "../../../utils/contactMethod";
import { isCompleteUsPhone } from "../../../utils/phone";
import { type AccountNoticeProps, type AccountSavingProps } from "../accountShared";
import { UsPhoneInput } from "../../forms/UsPhoneInput";
import { exactEntryProps } from "../../forms/textEntry";

type ProfileSectionProps = {
  profile: CustomerProfile;
  onProfileChange: Dispatch<SetStateAction<CustomerProfile | null>>;
} & AccountSavingProps & Pick<AccountNoticeProps, "onNotice">;

export function ProfileSection({
  profile,
  onProfileChange: setProfile,
  saving,
  onSavingChange: setSaving,
  onNotice: setSaveNotice,
}: ProfileSectionProps) {
  const [profileError, setProfileError] =
    useState<string | null>(null);

  async function submitProfile(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const currentProfile = profile;

    if (currentProfile === null) {
      return;
    }

    const preferredContactMethod = isContactMethod(
      currentProfile.preferred_contact_method,
    )
      ? currentProfile.preferred_contact_method
      : DEFAULT_CONTACT_METHOD;

    if (
      contactMethodNeedsPhone(preferredContactMethod)
      && (currentProfile.phone ?? "") === ""
    ) {
      setProfileError(PHONE_REQUIRED_MESSAGE);
      return;
    }

    if (
      currentProfile.phone !== null
      && !isCompleteUsPhone(
        currentProfile.phone,
      )
    ) {
      setProfileError(
        "Enter a complete "
        + "10-digit phone number.",
      );
      return;
    }

    setSaving(true);
    setProfileError(null);
    setSaveNotice(null);

    try {
      const updated =
        await updateProfile({
          first_name:
            currentProfile.first_name,
          last_name:
            currentProfile.last_name,
          phone: currentProfile.phone,
          preferred_contact_method: preferredContactMethod,
        });

      setProfile(updated);
      setSaveNotice("Profile updated.");
    } catch (caught) {
      setProfileError(
        caught instanceof Error
          ? caught.message
          : "Profile update failed.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="account-panel">
      <h2>Client Profile</h2>

      <form
        className="account-form"
        onSubmit={(event) => {
          void submitProfile(
            event,
          );
        }}
      >
        <label>
          <span>First name</span>
          <input
            {...exactEntryProps}
            value={
              profile.first_name
              ?? ""
            }
            onChange={(event) => {
              setProfile({
                ...profile,
                first_name:
                  event.target
                    .value
                  || null,
              });
            }}
          />
        </label>

        <label>
          <span>Last name</span>
          <input
            {...exactEntryProps}
            value={
              profile.last_name
              ?? ""
            }
            onChange={(event) => {
              setProfile({
                ...profile,
                last_name:
                  event.target
                    .value
                  || null,
              });
            }}
          />
        </label>

        <label>
          <span>Phone</span>
          <UsPhoneInput
            inputMode="tel"
            autoComplete="tel"
            maxLength={14}
            pattern={
              "[(][0-9]{3}[)] "
              + "[0-9]{3}-"
              + "[0-9]{4}"
            }
            title={
              "Enter a 10-digit "
              + "US phone number."
            }
            placeholder={
              "(951) 555-0142"
            }
            required={
              isContactMethod(profile.preferred_contact_method)
              && contactMethodNeedsPhone(profile.preferred_contact_method)
            }
            value={
              profile.phone ?? ""
            }
            onValueChange={(formatted) => {
              setProfile({
                ...profile,
                phone:
                  formatted
                  || null,
              });
            }}
          />

          <small className="field-helper">
            Type the 10 digits;
            formatting is added
            automatically.
          </small>
        </label>

        <label>
          <span>Preferred contact method</span>
          <select
            value={
              isContactMethod(profile.preferred_contact_method)
                ? profile.preferred_contact_method
                : DEFAULT_CONTACT_METHOD
            }
            onChange={(event) => {
              setProfile({
                ...profile,
                preferred_contact_method:
                  event.target.value as ContactMethod,
              });
            }}
          >
            {CONTACT_METHOD_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <small className="field-helper">
            How we contact you about requests and orders. Used to fill
            in our contact forms when you're signed in. Calls and texts
            go to the phone number above.
          </small>
        </label>

        {profileError !== null ? (
          <p
            className="account-error-inline"
            role="alert"
          >
            {profileError}
          </p>
        ) : null}

        <button
          type="submit"
          className="account-action"
          disabled={saving}
        >
          Save Profile
        </button>
      </form>
    </section>
  );
}
