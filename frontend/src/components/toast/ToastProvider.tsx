import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import "./toast.css";

type ToastKind = "success" | "info" | "warning" | "error";
type Toast = { id: number; message: string; kind: ToastKind; duration: number | null };
type ToastApi = {
  show: (message: string, kind?: ToastKind, duration?: number | null) => void;
  success: (message: string) => void;
  info: (message: string) => void;
  warning: (message: string) => void;
  error: (message: string) => void;
};
const ToastContext = createContext<ToastApi | null>(null);
let nextToastId = 0;
const DEFAULT_DURATION: Record<ToastKind, number | null> = {
  success: 4000, info: 5000, warning: 7000, error: null,
};

function ToastItem({ toast, dismiss }: { toast: Toast; dismiss: (id: number) => void }) {
  useEffect(() => {
    if (toast.duration === null) return;
    const timer = window.setTimeout(() => dismiss(toast.id), toast.duration);
    return () => window.clearTimeout(timer);
  }, [toast.id, toast.duration, dismiss]);
  return (
    <div className={`dd-toast dd-toast--${toast.kind}`} role={toast.kind === "error" ? "alert" : "status"}>
      <span className="dd-toast__symbol" aria-hidden="true">{toast.kind === "success" ? "✓" : toast.kind === "error" ? "!" : toast.kind === "warning" ? "!" : "i"}</span>
      <span className="dd-toast__message">{toast.message}</span>
      <button type="button" className="dd-toast__dismiss" aria-label="Dismiss notification" onClick={() => dismiss(toast.id)}>×</button>
    </div>
  );
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const dismiss = useCallback((id: number) => setItems((current) => current.filter((item) => item.id !== id)), []);
  const show = useCallback((message: string, kind: ToastKind = "info", duration: number | null = DEFAULT_DURATION[kind]) => {
    const id = ++nextToastId;
    setItems((current) => [...current.slice(-3), { id, message, kind, duration }]);
  }, []);
  const api = useMemo<ToastApi>(() => ({
    show,
    success: (message) => show(message, "success"),
    info: (message) => show(message, "info"),
    warning: (message) => show(message, "warning"),
    error: (message) => show(message, "error"),
  }), [show]);
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setItems((current) => current.slice(0, -1));
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);
  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="dd-toast-stack" aria-label="Notifications">
        {items.map((item) => <ToastItem key={item.id} toast={item} dismiss={dismiss} />)}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastApi {
  const api = useContext(ToastContext);
  if (!api) throw new Error("useToast must be used inside ToastProvider");
  return api;
}
