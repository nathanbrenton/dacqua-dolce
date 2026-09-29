import {
  type ComponentPropsWithoutRef,
  type ChangeEvent,
  useEffect,
  useRef,
} from "react";

import {
  formatUsPhoneInput,
} from "../../utils/phone";

type UsPhoneInputProps = Omit<
  ComponentPropsWithoutRef<"input">,
  "type" | "value" | "onChange"
> & {
  value: string;
  onValueChange: (value: string) => void;
};

function digitCountBefore(
  value: string,
  position: number,
): number {
  return (
    value
      .slice(0, position)
      .match(/[0-9]/g)
      ?.length
    ?? 0
  );
}

function caretForDigitCount(
  formatted: string,
  digitCount: number,
): number {
  if (formatted.length === 0) {
    return 0;
  }

  if (digitCount <= 0) {
    return formatted.startsWith("(")
      ? 1
      : 0;
  }

  let seen = 0;

  for (
    let index = 0;
    index < formatted.length;
    index += 1
  ) {
    if (/[0-9]/.test(formatted[index])) {
      seen += 1;

      if (seen === digitCount) {
        return index + 1;
      }
    }
  }

  return formatted.length;
}

function digitsOnly(
  value: string,
): string {
  return value.replace(/[^0-9]/g, "");
}

export function UsPhoneInput({
  value,
  onValueChange,
  maxLength: _maxLength,
  ...inputProps
}: UsPhoneInputProps) {
  const inputRef =
    useRef<HTMLInputElement>(null);

  const displayedValue =
    formatUsPhoneInput(value);

  useEffect(() => {
    const inputElement = inputRef.current;

    if (inputElement === null) {
      return;
    }

    function handleBeforeInput(
      event: InputEvent,
    ) {
      const input = inputRef.current;

      if (input === null) {
        return;
      }

      /*
       * React's synthetic beforeinput event is not consistent enough across
       * browsers for this overwrite behavior, especially for type="tel" and
       * mobile virtual keyboards. Listen to the native InputEvent instead.
       *
       * The browser-level maxLength attribute is intentionally omitted below.
       * It can suppress the insertion event entirely when the formatted field
       * is already "full". The component itself remains the authoritative
       * 10-digit limit.
       */
      if (
        event.inputType !== "insertText"
        || event.data === null
        || !/^[0-9]$/.test(event.data)
      ) {
        return;
      }

      const selectionStart =
        input.selectionStart
        ?? input.value.length;
      const selectionEnd =
        input.selectionEnd
        ?? selectionStart;

      if (selectionStart !== selectionEnd) {
        return;
      }

      const currentDigits =
        digitsOnly(input.value);

      if (currentDigits.length !== 10) {
        return;
      }

      const digitIndex =
        digitCountBefore(
          input.value,
          selectionStart,
        );

      if (digitIndex >= 10) {
        return;
      }

      event.preventDefault();

      const nextDigits =
        currentDigits.slice(0, digitIndex)
        + event.data
        + currentDigits.slice(digitIndex + 1);

      const formatted =
        formatUsPhoneInput(nextDigits);

      onValueChange(formatted);

      const nextCaret =
        caretForDigitCount(
          formatted,
          digitIndex + 1,
        );

      requestAnimationFrame(() => {
        if (
          document.activeElement
          !== input
        ) {
          return;
        }

        input.setSelectionRange(
          nextCaret,
          nextCaret,
        );
      });
    }

    inputElement.addEventListener(
      "beforeinput",
      handleBeforeInput,
    );

    return () => {
      inputElement.removeEventListener(
        "beforeinput",
        handleBeforeInput,
      );
    };
  }, [onValueChange, value]);

  function handleChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const input = event.currentTarget;
    const rawValue = input.value;

    const selectionStart =
      input.selectionStart
      ?? rawValue.length;
    const selectionEnd =
      input.selectionEnd
      ?? selectionStart;

    /*
     * Preserve the edit location by tracking how many actual phone digits
     * existed before each side of the browser's selection. Raw character
     * offsets are unstable because formatting characters such as "(", ")",
     * spaces, and "-" are inserted automatically.
     */
    const startDigitCount =
      digitCountBefore(
        rawValue,
        selectionStart,
      );
    const endDigitCount =
      digitCountBefore(
        rawValue,
        selectionEnd,
      );

    const currentDigits =
      digitsOnly(displayedValue);
    const rawDigits =
      digitsOnly(rawValue);

    /*
     * Fallback for browsers/virtual keyboards that do not expose a usable
     * native beforeinput event. If a full 10-digit value becomes 11 digits
     * after a collapsed-caret insertion, treat the newly inserted digit as an
     * overwrite and remove the old digit immediately after it.
     */
    let valueToFormat = rawValue;

    if (
      currentDigits.length === 10
      && rawDigits.length === 11
      && selectionStart === selectionEnd
    ) {
      const caretDigitCount =
        digitCountBefore(
          rawValue,
          selectionStart,
        );
      const insertedIndex =
        Math.max(
          0,
          caretDigitCount - 1,
        );

      if (insertedIndex < 10) {
        valueToFormat =
          rawDigits.slice(0, insertedIndex + 1)
          + rawDigits.slice(insertedIndex + 2);
      }
    }

    const formatted =
      formatUsPhoneInput(valueToFormat);

    const nextSelectionStart =
      caretForDigitCount(
        formatted,
        startDigitCount,
      );
    const nextSelectionEnd =
      caretForDigitCount(
        formatted,
        endDigitCount,
      );

    onValueChange(formatted);

    /*
     * React may write the controlled value after this event completes.
     * Restore the caret/selection on the next animation frame so mid-field
     * deletes, replacements, paste operations, mouse selections, and mobile
     * touch edits stay at the user's edit location instead of jumping to end.
     */
    requestAnimationFrame(() => {
      if (
        document.activeElement
        !== input
      ) {
        return;
      }

      input.setSelectionRange(
        nextSelectionStart,
        nextSelectionEnd,
      );
    });
  }

  return (
    <input
      {...inputProps}
      ref={inputRef}
      type="tel"
      value={displayedValue}
      onChange={handleChange}
    />
  );
}
