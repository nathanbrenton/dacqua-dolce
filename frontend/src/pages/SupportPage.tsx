import type { AuthenticationStatus } from "../api/authentication";
import { BusinessContactLine } from "../components/brand/BusinessContactLine";
import { SupportRequestForm } from "../components/support/SupportRequestForm";

type SupportPageProps = {
  account: AuthenticationStatus | null;
  onNavigate: (path: string) => void;
};

export function SupportPage({ account, onNavigate }: SupportPageProps) {
  return (
    <main
      id="main-content"
      tabIndex={-1}
      className="support-page-shell"
    >
      <button type="button" className="text-button" onClick={() => onNavigate("/")}>
        ← Home
      </button>

      <header className="support-page-heading">
        <p className="eyebrow">Warranty &amp; support</p>
        <h1>Support for your system.</h1>
        <p>
          Tell us what&apos;s happening with your system, whether it&apos;s a
          warranty question, a product question or anything else. Your request and
          our replies stay in one conversation, so you never have to start over.
        </p>
        <p>
          <BusinessContactLine />
        </p>
      </header>

      <section className="support-page-form-panel" aria-labelledby="support-request-heading">
        <h2 id="support-request-heading">Send a support request</h2>
        <SupportRequestForm account={account} />
      </section>
    </main>
  );
}
