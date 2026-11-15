import { getProfile } from "../../api/account";
import { type ContactMethod, isContactMethod } from "../../utils/contactMethod";
import { formatUsPhoneInput } from "../../utils/phone";

export type AccountContactDefaults = {
  name: string;
  phone: string;
  method: ContactMethod | null;
};

/**
 * A signed-in customer's saved name, phone and preferred contact method, used
 * to prefill the site's contact forms. Resolves null when signed out or when
 * the profile can't be read; the forms then simply start blank.
 */
export async function loadAccountContactDefaults(): Promise<AccountContactDefaults | null> {
  try {
    const profile = await getProfile();
    const name = [profile.first_name, profile.last_name]
      .filter((part): part is string => part !== null && part.trim() !== "")
      .join(" ");
    return {
      name,
      phone: formatUsPhoneInput(profile.phone ?? ""),
      method: isContactMethod(profile.preferred_contact_method)
        ? profile.preferred_contact_method
        : null,
    };
  } catch {
    return null;
  }
}
