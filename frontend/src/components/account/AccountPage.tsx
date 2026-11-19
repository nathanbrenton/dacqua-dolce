import {
  useEffect,
  useState,
} from "react";

import "./AccountAppearance.css";
import { useToast } from "../toast/ToastProvider";
import { AppearancePanel } from "./AppearancePanel";
import { SecurityPanel } from "./SecurityPanel";
import { AddressesSection } from "./sections/AddressesSection";
import { CartSection } from "./sections/CartSection";
import { CommunicationPreferencesSection } from "./sections/CommunicationPreferencesSection";
import { ConsultationHistorySection } from "./sections/ConsultationHistorySection";
import { EquipmentSection } from "./sections/EquipmentSection";
import { FormalQuotesSection } from "./sections/FormalQuotesSection";
import { MaintenanceChecksSection } from "./sections/MaintenanceChecksSection";
import { OrdersSection } from "./sections/OrdersSection";
import { ProfileSection } from "./sections/ProfileSection";

import {
  getCommunicationPreferences,
  getCustomerEquipment,
  getCustomerFormalQuotes,
  getCustomerRequests,
  getProfile,
  type CommunicationPreferences,
  type CustomerEquipment,
  type CustomerFormalQuote,
  type CustomerProfile,
  type CustomerRequestSummary,
} from "../../api/account";
import {
  type AuthenticationStatus,
} from "../../api/authentication";
import {
  getCart,
  type Cart,
} from "../../api/cart";
import {
  getOrders,
  type Order,
} from "../../api/orders";
import {
  getSalesArea,
  type SalesArea,
} from "../../api/salesArea";
import {
  type AppearanceMode,
} from "../../theme/appearance";
import {
  type ThemeId,
} from "../../theme/themes";

type AccountPageProps = {
  onNavigate: (path: string) => void;
  onRequestSignIn: () => void;
  account: AuthenticationStatus | null;
  theme: ThemeId;
  onThemeChange: (theme: ThemeId) => void;
  appearance: AppearanceMode;
  onAppearanceChange: (
    appearance: AppearanceMode,
  ) => void;
  onMfaReconfigurationStarted: (
    account: AuthenticationStatus,
  ) => void;
};


export function AccountPage({
  onNavigate,
  onRequestSignIn,
  account,
  theme,
  onThemeChange,
  appearance,
  onAppearanceChange,
  onMfaReconfigurationStarted,
}: AccountPageProps) {
  const authenticated =
    account?.authenticated ?? false;

  const isCustomer =
    account?.roles.includes(
      "customer",
    ) ?? false;
  const [profile, setProfile] =
    useState<CustomerProfile | null>(null);
  const [cart, setCart] =
    useState<Cart | null>(null);
  const [orders, setOrders] =
    useState<Order[]>([]);
  const [communicationPreferences, setCommunicationPreferences] =
    useState<CommunicationPreferences | null>(null);
  const [customerRequests, setCustomerRequests] =
    useState<CustomerRequestSummary[]>([]);
  const [formalQuotes, setFormalQuotes] =
    useState<CustomerFormalQuote[]>([]);
  const [salesArea, setSalesArea] =
    useState<SalesArea | null>(null);
  const [customerEquipment, setCustomerEquipment] =
    useState<CustomerEquipment[]>([]);
  const [error, setError] =
    useState<string | null>(null);
  const [saving, setSaving] =
    useState(false);
  // Profile form problems show inside the form, next to Save, rather than
  // in the page-level alert far above it.
  const [saveNotice, setSaveNotice] =
    useState<string | null>(null);

  const toast = useToast();
  useEffect(() => {
    if (saveNotice !== null) {
      toast.success(saveNotice);
    }
  }, [saveNotice, toast]);

  useEffect(() => {
    if (
      !authenticated
      || !isCustomer
    ) {
      return;
    }

    void Promise.all([
      getProfile(),
      getCart(),
      getOrders(),
      getCommunicationPreferences(),
      getCustomerRequests(),
      getCustomerFormalQuotes(),
      getCustomerEquipment(),
      getSalesArea(),
    ])
      .then(
        ([
          profileResult,
          cartResult,
          orderResult,
          preferenceResult,
          requestResult,
          formalQuoteResult,
          equipmentResult,
          salesAreaResult,
        ]) => {
          setProfile(profileResult);
          setCart(cartResult);
          setOrders(orderResult);
          setCommunicationPreferences(preferenceResult);
          setCustomerRequests(requestResult);
          setFormalQuotes(formalQuoteResult);
          setCustomerEquipment(equipmentResult);
          setSalesArea(salesAreaResult);
          setError(null);
        },
      )
      .catch((caught) => {
        setError(
          caught instanceof Error
            ? caught.message
            : "Account unavailable.",
        );
      });
  }, [
    authenticated,
    isCustomer,
  ]);

  if (
    account === null
    || !authenticated
  ) {
    return (
      <main
        id="main-content"
        tabIndex={-1}
        className="account-shell"
        data-appearance={appearance}
      >
        <button
          type="button"
          className="text-button"
          onClick={() => {
            onNavigate("/");
          }}
        >
          ← Home
        </button>

        <section className="account-signin">
          <p className="eyebrow">
            Customer Account
          </p>

          <h1>Sign in to continue.</h1>

          <button
            type="button"
            className="detail-primary-action"
            onClick={onRequestSignIn}
          >
            Sign In
          </button>
        </section>
      </main>
    );
  }

  if (!isCustomer) {
    return (
      <main
        id="main-content"
        tabIndex={-1}
        className="account-shell"
        data-appearance={appearance}
      >
        <button
          type="button"
          className="text-button"
          onClick={() => {
            onNavigate("/");
          }}
        >
          ← Home
        </button>

        <header className="account-heading">
          <p className="eyebrow">
            Account
          </p>

          <h1>Account &amp; security.</h1>

          <p>{account.email}</p>
        </header>

        <div className="account-grid">
          <SecurityPanel
            account={account}
            onMfaReconfigurationStarted={
              onMfaReconfigurationStarted
            }
          />

          <AppearancePanel
            theme={theme}
            onThemeChange={onThemeChange}
            appearance={appearance}
            onAppearanceChange={onAppearanceChange}
          />
        </div>
      </main>
    );
  }

  if (profile === null) {
    return (
      <main
        id="main-content"
        tabIndex={-1}
        className="account-shell"
        data-appearance={appearance}
      >
        <p role="status">
          Loading account…
        </p>

        {error !== null ? (
          <p role="alert">{error}</p>
        ) : null}
      </main>
    );
  }


  return (
    <main
      id="main-content"
      tabIndex={-1}
      className="account-shell"
      data-appearance={appearance}
    >
      <button
        type="button"
        className="text-button"
        onClick={() => {
          onNavigate("/");
        }}
      >
        ← Home
      </button>

      <header className="account-heading">
        <p className="eyebrow">
          Account
        </p>

        <h1>Your water, organized.</h1>

        <p>{account.email}</p>
      </header>

      {error !== null ? (
        <p
          className="account-error"
          role="alert"
        >
          {error}
        </p>
      ) : null}


      <div className="account-grid">
        <SecurityPanel
          account={account}
          onMfaReconfigurationStarted={
            onMfaReconfigurationStarted
          }
        />

        <AppearancePanel
          theme={theme}
          onThemeChange={onThemeChange}
          appearance={appearance}
          onAppearanceChange={onAppearanceChange}
        />

        <ProfileSection
          profile={profile}
          onProfileChange={setProfile}
          saving={saving}
          onSavingChange={setSaving}
          onNotice={setSaveNotice}
        />

        <AddressesSection
          profile={profile}
          onProfileChange={setProfile}
          saveNotice={saveNotice}
          saving={saving}
          onSavingChange={setSaving}
          onError={setError}
          onNotice={setSaveNotice}
        />

        <CommunicationPreferencesSection
          preferences={communicationPreferences}
          onPreferencesChange={setCommunicationPreferences}
          saving={saving}
          onSavingChange={setSaving}
          onError={setError}
          onNotice={setSaveNotice}
        />

        <EquipmentSection
          equipment={customerEquipment}
          onCartChange={setCart}
          onNavigate={onNavigate}
          saving={saving}
          onSavingChange={setSaving}
          onError={setError}
          onNotice={setSaveNotice}
        />

        <MaintenanceChecksSection />

        <ConsultationHistorySection requests={customerRequests} />

        <FormalQuotesSection
          formalQuotes={formalQuotes}
          onFormalQuotesChange={setFormalQuotes}
          orders={orders}
          onOrdersChange={setOrders}
          salesArea={salesArea}
          onError={setError}
          onNotice={setSaveNotice}
        />

        <CartSection cart={cart} onCartChange={setCart} />

        <OrdersSection
          orders={orders}
          onOrdersChange={setOrders}
          onError={setError}
          onNotice={setSaveNotice}
        />
      </div>
    </main>
  );
}
