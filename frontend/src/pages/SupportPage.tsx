import type { AuthenticationStatus } from "../api/authentication";
import { SupportRequestForm } from "../components/support/SupportRequestForm";

type SupportPageProps = {
  account: AuthenticationStatus | null;
  onNavigate: (path: string) => void;
};

export function SupportPage({ account, onNavigate }: SupportPageProps) {
  return (
    <main className="support-page-shell">
      <button type="button" className="text-button" onClick={() => onNavigate("/")}>
        ← Home
      </button>

      <header className="support-page-heading">
        <p className="eyebrow">Warranty &amp; support</p>
        <h1>Support for your system.</h1>
        <p>
          Send a warranty, product, or general support request. Website requests
          stay with the support conversation so our team can continue from the same
          record.
        </p>
        <p>
          Prefer email? <a href="mailto:support@dacquadolce.com">support@dacquadolce.com</a>
        </p>
      </header>

      <section className="support-page-form-panel" aria-labelledby="support-request-heading">
        <h2 id="support-request-heading">Send a support request</h2>
        <SupportRequestForm account={account} />
      </section>
    </main>
  );
}
