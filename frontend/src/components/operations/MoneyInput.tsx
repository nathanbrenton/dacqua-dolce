import type { InputHTMLAttributes } from "react";

/**
 * A text input for dollar amounts with a fixed "$" in front of it. A typed or
 * pasted "$" is dropped as it's entered, since the prefix already shows one.
 */
export function MoneyInput(
  props: Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "inputMode">,
) {
  const { onChange, ...rest } = props;

  return (
    <span
      className={
        "operations-money-input" + (props.disabled === true ? " is-disabled" : "")
      }
    >
      <span className="operations-money-prefix" aria-hidden="true">$</span>
      <input
        {...rest}
        type="text"
        inputMode="decimal"
        onChange={(event) => {
          if (event.target.value.includes("$")) {
            event.target.value = event.target.value.replaceAll("$", "").trimStart();
          }
          onChange?.(event);
        }}
      />
    </span>
  );
}
