import { useEffect, useState } from "react";
import { useToast } from "../toast/ToastProvider";
import { getProductFamilyOrder, saveProductFamilyOrder, type ProductFamilyOrder } from "../../api/operations";

const defaults = ["Refine", "Essence", "Origin", "Harmony"];

export function ProductFamilyOrderPanel() {
  const [server, setServer] = useState<ProductFamilyOrder | null>(null);
  const [draft, setDraft] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  const refresh = () => {
    void getProductFamilyOrder().then((data) => {
      setServer(data);
      setDraft([...data.families]);
      setError(null);
    }).catch((caught: unknown) => setError(caught instanceof Error ? caught.message : "Cannot load ordering."));
  };
  useEffect(refresh, []);
  const dirty = Boolean(server && draft.join("\u0000") !== server.families.join("\u0000"));
  const move = (index: number, delta: number) => {
    const target = index + delta;
    if (target < 0 || target >= draft.length || busy) return;
    setDraft((current) => {
      const copy = [...current];
      [copy[index], copy[target]] = [copy[target], copy[index]];
      return copy;
    });

  };
  const save = async () => {
    if (!server || !dirty) return;
    setBusy(true); setError(null);
    try {
      const data = await saveProductFamilyOrder({ families: draft, revision: server.revision });
      setServer(data); setDraft([...data.families]); toast.success("Order saved. The public catalog now uses this order.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save order.");
    } finally { setBusy(false); }
  };
  return (
    <section aria-label="Product family display order" className="operations-availability-demand">
      <header><div><p className="operations-subsection-label">Merchandising</p><h3>Product display order</h3></div></header>
      <p>Arrange product families in the public catalog. Only administrators and developers may save changes. Variants remain grouped with their product.</p>
      {error && <p role="alert">{error} <button type="button" onClick={refresh}>Reload</button></p>}

      {!server ? <p>Loading product order…</p> : (
        <>
          <ol style={{ listStyle: "none", padding: 0 }}>
            {draft.map((name, index) => (
              <li key={name} style={{ display: "flex", alignItems: "center", gap: "1rem", margin: "0.5rem 0" }}>
                <strong style={{ flex: 1 }}>{index + 1}. {name}</strong>
                <button type="button" disabled={busy || index === 0} aria-label={`Move ${name} up`} onClick={() => move(index, -1)}>↑ Up</button>
                <button type="button" disabled={busy || index === draft.length - 1} aria-label={`Move ${name} down`} onClick={() => move(index, 1)}>↓ Down</button>
              </li>
            ))}
          </ol>
          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
            <button type="button" disabled={busy || !dirty} onClick={() => { setDraft([...server.families]); setError(null); }}>Cancel</button>
            <button type="button" disabled={busy || !dirty} onClick={() => void save()}>{busy ? "Saving…" : "Save order"}</button>
            <button type="button" disabled={busy} onClick={() => { setDraft([...defaults.filter((x) => draft.includes(x)), ...draft.filter((x) => !defaults.includes(x))]); }}>Restore default</button>
          </div>
        </>
      )}
    </section>
  );
}
