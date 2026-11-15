import { useId } from "react";

import {
  CONTACT_METHOD_OPTIONS,
  type ContactMethod,
  contactMethodHint,
} from "../../utils/contactMethod";

/** "Preferred contact method" dropdown shared by the site's contact forms. */
export function ContactMethodSelect({
  value,
  onChange,
  hint = true,
}: {
  value: ContactMethod;
  onChange: (method: ContactMethod) => void;
  hint?: boolean;
}) {
  const hintId = useId();

  return (
    <label>
      <span>Preferred contact method</span>
      <select
        value={value}
        aria-describedby={hint ? hintId : undefined}
        onChange={(event) => {
          onChange(event.target.value as ContactMethod);
        }}
      >
        {CONTACT_METHOD_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {hint ? (
        <small id={hintId} className="field-helper">
          {contactMethodHint(value)}
        </small>
      ) : null}
    </label>
  );
}
