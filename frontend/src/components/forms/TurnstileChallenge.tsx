import { useEffect, useRef, useState } from "react";

const SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY as string | undefined;
const SCRIPT_URL = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";

type TurnstileApi = {
  render: (element: HTMLElement, options: Record<string, unknown>) => string;
  reset: (widgetId: string) => void;
  remove: (widgetId: string) => void;
};
type TurnstileWindow = Window & { turnstile?: TurnstileApi };

export function TurnstileChallenge({ action, onToken, resetKey }: {
  action: "support" | "quote";
  onToken: (token: string | null) => void;
  resetKey: number;
}) {
  const container = useRef<HTMLDivElement>(null);
  const callback = useRef(onToken);
  const widget = useRef<string | null>(null);
  const [error, setError] = useState(false);
  callback.current = onToken;

  useEffect(() => {
    if (!SITE_KEY) return;
    let disposed = false;
    let widgetId: string | null = null;
    let poll: number | undefined;
    const mount = () => {
      if (disposed || widgetId || !container.current) return;
      const api = (window as TurnstileWindow).turnstile;
      if (!api) return;
      widgetId = api.render(container.current, {
        sitekey: SITE_KEY,
        action,
        callback: (token: string) => { setError(false); callback.current(token); },
        "expired-callback": () => callback.current(null),
        "error-callback": () => { setError(true); callback.current(null); },
      });
      widget.current = widgetId;
      window.clearInterval(poll);
    };
    const scriptId = "dacqua-turnstile-script";
    if (!document.getElementById(scriptId)) {
      const script = document.createElement("script");
      script.id = scriptId;
      script.src = SCRIPT_URL;
      script.async = true;
      script.addEventListener("load", mount);
      document.head.appendChild(script);
    }
    poll = window.setInterval(mount, 100);
    mount();
    return () => {
      disposed = true;
      window.clearInterval(poll);
      if (widgetId) (window as TurnstileWindow).turnstile?.remove(widgetId);
    };
  }, [action]);
  useEffect(() => {
    if (resetKey > 0 && widget.current) {
      (window as TurnstileWindow).turnstile?.reset(widget.current);
    }
  }, [resetKey]);
  if (!SITE_KEY) return null;
  return <div><div ref={container} aria-label="Bot verification" />
    {error ? <p role="alert">Verification unavailable. Refresh and try again.</p> : null}
  </div>;
}

export const turnstileConfigured = Boolean(SITE_KEY);
