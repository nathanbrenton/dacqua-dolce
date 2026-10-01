import {
  type InputHTMLAttributes,
  useId,
  useState,
} from "react";

type PasswordInputProps = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "type" | "id"
> & {
  label: string;
  visibilityLabel?: string;
};

export function PasswordInput({
  label,
  visibilityLabel = label.toLowerCase(),
  ...inputProps
}: PasswordInputProps) {
  const inputId = useId();
  const [visible, setVisible] =
    useState(false);

  const action = visible ? "Hide" : "Show";

  return (
    <div className="password-field">
      <label htmlFor={inputId}>
        <span>{label}</span>
      </label>

      <div className="password-input-control">
        <input
          {...inputProps}
          id={inputId}
          type={visible ? "text" : "password"}
        />

        <button
          type="button"
          className="password-visibility-toggle"
          aria-label={`${action} ${visibilityLabel}`}
          aria-pressed={visible}
          onClick={() => {
            setVisible((current) => !current);
          }}
        >
          {visible ? (
            <svg
              viewBox="0 0 24 24"
              aria-hidden="true"
              focusable="false"
            >
              <path
                d="M3 3 21 21M10.6 10.7a2 2 0 0 0 2.7 2.7M9.9 4.2A10.7 10.7 0 0 1 12 4c5.5 0 9 5.5 9 8a10.8 10.8 0 0 1-2.2 3.7M6.2 6.2C4.1 7.7 3 10.2 3 12c0 2.5 3.5 8 9 8 1.4 0 2.7-.4 3.8-1"
              />
            </svg>
          ) : (
            <svg
              viewBox="0 0 24 24"
              aria-hidden="true"
              focusable="false"
            >
              <path
                d="M3 12c0-2.5 3.5-8 9-8s9 5.5 9 8-3.5 8-9 8-9-5.5-9-8Z"
              />
              <circle cx="12" cy="12" r="2.6" />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
}
