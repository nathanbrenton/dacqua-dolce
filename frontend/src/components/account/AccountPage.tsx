import {
  type FormEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import "./AccountAppearance.css";
import { useToast } from "../toast/ToastProvider";

import {
  createAddress,
  deleteAddress,
  getCommunicationPreferences,
  approveCustomerFormalQuote,
  getCustomerEquipment,
  getCustomerFormalQuotes,
  getCustomerRequests,
  getProfile,
  recordShippingInsuranceDecision,
  updateCommunicationPreferences,
  updateProfile,
  type AddressCreate,
  type CommunicationPreferences,
  type CustomerEquipment,
  type CustomerFormalQuote,
  type CustomerProfile,
  type CustomerRequestSummary,
} from "../../api/account";
import {
  reconfigureMfa,
  requestEmailVerification,
  type AuthenticationStatus,
} from "../../api/authentication";
import type { CommercialAddress } from "../../api/commercial";
import {
  addCartItem,
  getCart,
  removeCartItem,
  type Cart,
} from "../../api/cart";
import {
  getOrders,
  requestOrderCancellation,
  type Order,
} from "../../api/orders";
import {
  getSalesArea,
  salesAreaAllowsAddress,
  type SalesArea,
} from "../../api/salesArea";
import {
  AppearanceToggle,
} from "../theme/AppearanceToggle";
import {
  type AppearanceMode,
} from "../../theme/appearance";
import {
  DEFAULT_THEME,
  isThemeId,
  THEMES,
  type ThemeId,
} from "../../theme/themes";
import {
  isCompleteUsPhone,
} from "../../utils/phone";
import {
  PasswordInput,
} from "../forms/PasswordInput";
import {
  UsPhoneInput,
} from "../forms/UsPhoneInput";

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

const EMPTY_ADDRESS: AddressCreate = {
  label: "Home",
  line1: "",
  line2: null,
  city: "",
  region_code: "",
  postal_code: "",
  country_code: "US",
  is_default_shipping: false,
  is_default_billing: false,
};

function money(
  amountMinor: number,
  currency: string,
): string {
  return new Intl.NumberFormat(
    undefined,
    {
      style: "currency",
      currency,
    },
  ).format(amountMinor / 100);
}

function formalQuoteExpired(quote: CustomerFormalQuote): boolean {
  return quote.expires_at !== null
    && new Date(quote.expires_at).getTime() <= Date.now();
}

function commercialAddressLines(address: CommercialAddress): string[] {
  return [
    address.recipient_name,
    address.line1,
    address.line2,
    `${address.city}, ${address.region_code} ${address.postal_code}`,
    address.country_code,
    address.phone,
  ].filter((value): value is string => value !== null && value !== "");
}


const ORDER_STAGE_LABELS: Record<string, string> = {
  received: "Received",
  processing: "Processing",
  supplier_confirmed: "Supplier Confirmed",
  awaiting_shipment: "Awaiting Shipment",
  shipped: "Shipped",
  completed: "Completed",
  cancelled: "Cancelled",
  refunded: "Refunded",
};

function orderStageLabel(value: string): string {
  return ORDER_STAGE_LABELS[value] ?? value.replaceAll("_", " ");
}


const PRIVILEGED_MFA_ROLES = new Set([
  "manager",
  "administrator",
  "developer",
]);

function hasPrivilegedMfaRole(
  account: AuthenticationStatus,
): boolean {
  return account.roles.some((role) =>
    PRIVILEGED_MFA_ROLES.has(role),
  );
}

type SecurityPanelProps = {
  account: AuthenticationStatus;
  onMfaReconfigurationStarted: (
    account: AuthenticationStatus,
  ) => void;
};

function SecurityPanel({
  account,
  onMfaReconfigurationStarted,
}: SecurityPanelProps) {
  const [password, setPassword] =
    useState("");

  const [reconfiguring, setReconfiguring] =
    useState(false);

  const [securityError, setSecurityError] =
    useState<string | null>(null);

  const [
    verificationSending,
    setVerificationSending,
  ] = useState(false);

  const [
    verificationMessage,
    setVerificationMessage,
  ] = useState<string | null>(null);

  const privileged =
    hasPrivilegedMfaRole(account);

  async function resendVerification() {
    setSecurityError(null);
    setVerificationMessage(null);
    setVerificationSending(true);

    try {
      const message =
        await requestEmailVerification();

      setVerificationMessage(
        message,
      );
    } catch (caught) {
      setSecurityError(
        caught instanceof Error
          ? caught.message
          : (
              "Unable to request "
              + "verification email."
            ),
      );
    } finally {
      setVerificationSending(false);
    }
  }

  async function replaceAuthenticator(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setSecurityError(null);
    setReconfiguring(true);

    try {
      const pendingAccount =
        await reconfigureMfa(
          password,
        );

      setPassword("");

      onMfaReconfigurationStarted(
        pendingAccount,
      );
    } catch (caught) {
      setSecurityError(
        caught instanceof Error
          ? caught.message
          : (
              "Unable to replace "
              + "authenticator."
            ),
      );
    } finally {
      setReconfiguring(false);
    }
  }

  return (
    <section className="account-panel">
      <h2>Security</h2>

      <div className="account-security-status">
        <div>
          <strong>Email address</strong>

          <p className="account-security-email">
            {account.email}
          </p>
        </div>

        <span
          className={
            account.email_verified
              ? "account-security-verified"
              : "account-security-unverified"
          }
        >
          {account.email_verified
            ? "Verified"
            : "Not verified"}
        </span>
      </div>

      {!account.email_verified ? (
        <div
          className={
            "account-email-verification-actions"
          }
        >
          <p className="account-muted">
            Verify this email before
            production account access is
            granted.
          </p>

          <button
            type="button"
            className="account-action"
            disabled={verificationSending}
            onClick={() => {
              void resendVerification();
            }}
          >
            {verificationSending
              ? "Sending..."
              : "Resend Verification Email"}
          </button>

          {verificationMessage !== null ? (
            <p
              className="account-success-inline"
              role="status"
            >
              {verificationMessage}
            </p>
          ) : null}
        </div>
      ) : null}

      <div className="account-security-status">
        <div className="account-security-authenticator">
          <div
            className={
              "authenticator-generic-icon "
              + "account-authenticator-icon"
            }
            aria-hidden="true"
          >
            <span
              className="authenticator-phone"
            />
            <span
              className="authenticator-shield"
            >
              ✓
            </span>
          </div>

          <div>
            <strong>
              Authenticator MFA
            </strong>

            {privileged ? (
              <div
                className={
                  "authenticator-compatibility-meta"
                }
              >
                <span
                  className={
                    "authenticator-compatibility-badge"
                  }
                >
                  Microsoft Authenticator
                  compatible
                </span>

                <span>
                  Standard TOTP
                </span>
              </div>
            ) : null}
          </div>
        </div>

        <span>
          {privileged
            ? "Enabled"
            : account.roles.includes(
                "customer",
              )
              ? "Optional"
              : "Not required"}
        </span>
      </div>

      {privileged ? (
        <>
          <p className="account-muted">
            Protects privileged Operations
            access. Works with Microsoft
            Authenticator and other
            standards-compatible TOTP
            authenticator apps.
          </p>

          <details
            className="account-security-replace"
          >
            <summary>
              Replace authenticator
            </summary>

            <p className="account-muted">
              Replacing the authenticator
              immediately invalidates the
              existing setup and recovery
              codes, signs out other
              sessions, and requires a
              new enrollment.
            </p>

            <form
              className="account-form"
              onSubmit={(event) => {
                void replaceAuthenticator(
                  event,
                );
              }}
            >
              <PasswordInput
                label="Current password"
                autoComplete="current-password"
                required
                maxLength={256}
                value={password}
                onChange={(event) => {
                  setPassword(
                    event.target.value,
                  );
                }}
              />

              {securityError !== null ? (
                <p
                  className="account-error-inline"
                  role="alert"
                >
                  {securityError}
                </p>
              ) : null}

              <button
                type="submit"
                className="account-action"
                disabled={reconfiguring}
              >
                {reconfiguring
                  ? "Replacing..."
                  : "Replace Authenticator"}
              </button>
            </form>
          </details>
        </>
      ) : account.roles.includes(
        "customer",
      ) ? (
        <p className="account-muted">
          Authenticator MFA is optional
          for customer accounts. Enable
          it for additional account
          security.
        </p>
      ) : (
        <p className="account-muted">
          Authenticator MFA is not
          required for this account.
        </p>
      )}
    </section>
  );
}

type AppearancePanelProps = {
  theme: ThemeId;
  onThemeChange: (theme: ThemeId) => void;
  appearance: AppearanceMode;
  onAppearanceChange: (
    appearance: AppearanceMode,
  ) => void;
};

function AppearancePanel({
  theme,
  onThemeChange,
  appearance,
  onAppearanceChange,
}: AppearancePanelProps) {
  return (
    <section className="account-panel">
      <h2>Appearance</h2>

      <div className="account-appearance-controls">
        <label
          className="account-appearance-field"
          htmlFor="account-theme"
        >
          <span>Visual theme</span>

          <select
            id="account-theme"
            value={theme}
            onChange={(event) => {
              const value = event.target.value;

              onThemeChange(
                isThemeId(value)
                  ? value
                  : DEFAULT_THEME,
              );
            }}
          >
            {THEMES.map((option) => (
              <option
                key={option.id}
                value={option.id}
              >
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <div className="account-appearance-mode">
          <div>
            <strong>Page appearance</strong>
            <p className="account-muted">
              Choose light or dark mode for
              your account workspace.
            </p>
          </div>

          <AppearanceToggle
            appearance={appearance}
            onAppearanceChange={
              onAppearanceChange
            }
          />
        </div>
      </div>
    </section>
  );
}

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
  const [cancellationReasons, setCancellationReasons] =
    useState<Record<string, string>>({});
  const [cancellationBusyOrderId, setCancellationBusyOrderId] =
    useState<string | null>(null);
  const [communicationPreferences, setCommunicationPreferences] =
    useState<CommunicationPreferences | null>(null);
  const [customerRequests, setCustomerRequests] =
    useState<CustomerRequestSummary[]>([]);
  const [formalQuotes, setFormalQuotes] =
    useState<CustomerFormalQuote[]>([]);
  const [salesArea, setSalesArea] =
    useState<SalesArea | null>(null);
  const [policyAcknowledgments, setPolicyAcknowledgments] =
    useState<Record<string, boolean>>({});
  const [insuranceDecisionBusyQuoteId, setInsuranceDecisionBusyQuoteId] =
    useState<string | null>(null);
  const [customerEquipment, setCustomerEquipment] =
    useState<CustomerEquipment[]>([]);
  const [error, setError] =
    useState<string | null>(null);
  const [saving, setSaving] =
    useState(false);
  const [saveNotice, setSaveNotice] =
    useState<string | null>(null);
  const [addressDraft, setAddressDraft] =
    useState<AddressCreate>(
      EMPTY_ADDRESS,
    );
  const [addressFormOpen, setAddressFormOpen] =
    useState(false);
  const [recentAddressId, setRecentAddressId] =
    useState<string | null>(null);
  const addressSectionRef =
    useRef<HTMLElement | null>(null);

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

  async function setShippingInsuranceDecision(
    quote: CustomerFormalQuote,
    decision: "accepted" | "declined",
  ): Promise<void> {
    setError(null);
    setSaveNotice(null);
    setInsuranceDecisionBusyQuoteId(quote.id);
    try {
      const updated = await recordShippingInsuranceDecision(
        quote.id,
        decision,
      );
      setFormalQuotes((current) => current.map((candidate) => (
        candidate.id === updated.id ? updated : candidate
      )));
      setSaveNotice(
        decision === "accepted"
          ? "Shipping insurance accepted for this quote revision."
          : "Shipping insurance declined. D’Acqua Dolce can prepare a revised quote without the insurance charge.",
      );
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Shipping insurance choice could not be recorded.",
      );
    } finally {
      setInsuranceDecisionBusyQuoteId(null);
    }
  }

  async function approveFormalQuote(quote: CustomerFormalQuote): Promise<void> {
    if (policyAcknowledgments[quote.id] !== true) {
      setError("Review and acknowledge the policy versions attached to this quote.");
      return;
    }

    if (
      quote.shipping_insurance_offered
      && quote.shipping_insurance_decision !== "accepted"
    ) {
      setError(
        quote.shipping_insurance_decision === "declined"
          ? "Shipping insurance was declined. Contact D’Acqua Dolce for a revised quote without the insurance charge."
          : "Accept or decline shipping insurance before approving this quote.",
      );
      return;
    }

    const confirmed = window.confirm(
      `Approve quote revision ${quote.revision_number} for ${money(
        quote.total_amount_minor,
        quote.currency,
      )}?`,
    );
    if (!confirmed) {
      return;
    }

    setError(null);
    setSaveNotice(null);
    try {
      const updated = await approveCustomerFormalQuote(
        quote.id,
        quote.policy_snapshots.map((snapshot) => snapshot.id),
      );
      const refreshedOrders = await getOrders();
      setFormalQuotes((current) => current.map((candidate) => (
        candidate.id === updated.id ? updated : candidate
      )));
      setOrders(refreshedOrders);
      setSaveNotice(
        `Quote revision ${updated.revision_number} approved and order prepared.`,
      );
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Quote approval failed.",
      );
    }
  }

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

  async function submitProfile(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const currentProfile = profile;

    if (currentProfile === null) {
      return;
    }

    if (
      currentProfile.phone !== null
      && !isCompleteUsPhone(
        currentProfile.phone,
      )
    ) {
      setError(
        "Enter a complete "
        + "10-digit phone number.",
      );
      return;
    }

    setSaving(true);
    setError(null);
    setSaveNotice(null);

    try {
      const updated =
        await updateProfile({
          first_name:
            currentProfile.first_name,
          last_name:
            currentProfile.last_name,
          phone: currentProfile.phone,
        });

      setProfile(updated);
      setSaveNotice("Profile updated.");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Profile update failed.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function submitAddress(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSaveNotice(null);

    try {
      const createdAddress =
        await createAddress(
          addressDraft,
        );

      setProfile(
        await getProfile(),
      );

      setAddressDraft(
        EMPTY_ADDRESS,
      );
      setAddressFormOpen(false);
      setRecentAddressId(
        createdAddress.id,
      );
      setSaveNotice("Address added.");

      window.requestAnimationFrame(() => {
        addressSectionRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      });
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Address update failed.",
      );
    } finally {
      setSaving(false);
    }
  }


  async function saveCommunicationPreferences() {
    if (communicationPreferences === null) {
      return;
    }

    setSaving(true);
    setError(null);
    setSaveNotice(null);

    try {
      const updated = await updateCommunicationPreferences(
        communicationPreferences,
      );
      setCommunicationPreferences(updated);
      setSaveNotice("Communication preferences updated.");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Communication preference update failed.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function reorderConsumable(
    productId: string,
    name: string,
  ) {
    setSaving(true);
    setError(null);
    setSaveNotice(null);

    try {
      const updatedCart = await addCartItem(productId);
      setCart(updatedCart);
      setSaveNotice(`${name} added to your cart.`);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to add replacement item to cart.",
      );
    } finally {
      setSaving(false);
    }
  }


  async function submitOrderCancellation(
    order: Order,
  ): Promise<void> {
    setCancellationBusyOrderId(order.id);
    setError(null);
    setSaveNotice(null);

    try {
      const reason = cancellationReasons[order.id]?.trim() || null;
      const cancellation = await requestOrderCancellation(
        order.id,
        reason,
      );

      setOrders((current) =>
        current.map((candidate) =>
          candidate.id === order.id
            ? {
                ...candidate,
                cancellation,
              }
            : candidate,
        ),
      );
      setCancellationReasons((current) => {
        const next = { ...current };
        delete next[order.id];
        return next;
      });
      setSaveNotice(
        cancellation.status === "approved"
          ? "Cancellation accepted. Our team will complete any required payment or administrative steps."
          : "Cancellation review requested.",
      );
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Cancellation request failed.",
      );
    } finally {
      setCancellationBusyOrderId(null);
    }
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

        <section className="account-panel">
          <h2>Client Profile</h2>

          <form
            className="account-form"
            onSubmit={(event) => {
              void submitProfile(
                event,
              );
            }}
          >
            <label>
              <span>First name</span>
              <input
                value={
                  profile.first_name
                  ?? ""
                }
                onChange={(event) => {
                  setProfile({
                    ...profile,
                    first_name:
                      event.target
                        .value
                      || null,
                  });
                }}
              />
            </label>

            <label>
              <span>Last name</span>
              <input
                value={
                  profile.last_name
                  ?? ""
                }
                onChange={(event) => {
                  setProfile({
                    ...profile,
                    last_name:
                      event.target
                        .value
                      || null,
                  });
                }}
              />
            </label>

            <label>
              <span>Phone</span>
              <UsPhoneInput
                inputMode="tel"
                autoComplete="tel"
                maxLength={14}
                pattern={
                  "[(][0-9]{3}[)] "
                  + "[0-9]{3}-"
                  + "[0-9]{4}"
                }
                title={
                  "Enter a 10-digit "
                  + "US phone number."
                }
                placeholder={
                  "(949) 555-1234"
                }
                value={
                  profile.phone ?? ""
                }
                onValueChange={(formatted) => {
                  setProfile({
                    ...profile,
                    phone:
                      formatted
                      || null,
                  });
                }}
              />

              <small className="field-helper">
                Type the 10 digits;
                formatting is added
                automatically.
              </small>
            </label>

            <button
              type="submit"
              className="account-action"
              disabled={saving}
            >
              Save Profile
            </button>
          </form>
        </section>

        <section
          ref={addressSectionRef}
          className="account-panel account-address-panel"
        >
          <h2>Addresses</h2>

          {saveNotice === "Address added." ? (
            <p
              className="account-address-status"
              role="status"
            >
              Address added. Your saved address is shown below.
            </p>
          ) : null}

          {profile.addresses.length
            > 0 ? (
            <div className="address-list">
              {profile.addresses.map(
                (address) => (
                  <article
                    key={address.id}
                    className={
                      address.id === recentAddressId
                        ? "address-card is-recent"
                        : "address-card"
                    }
                  >
                    <div
                      className="address-card-heading"
                    >
                      <strong>
                        {address.label}
                      </strong>

                      <div
                        className="address-badges"
                      >
                        {address
                          .is_default_shipping ? (
                          <span
                            className="address-badge"
                          >
                            Default shipping
                          </span>
                        ) : null}

                        {address
                          .is_default_billing ? (
                          <span
                            className="address-badge"
                          >
                            Default billing
                          </span>
                        ) : null}
                      </div>
                    </div>

                    <p>
                      {address.line1}
                      {address.line2
                        !== null
                        ? (
                          <>
                            <br />
                            {
                              address.line2
                            }
                          </>
                        )
                        : null}
                      <br />
                      {address.city},{" "}
                      {
                        address.region_code
                      }{" "}
                      {
                        address.postal_code
                      }
                    </p>

                    <button
                      type="button"
                      className="text-button compact"
                      onClick={() => {
                        setError(null);
                        setSaveNotice(null);

                        void deleteAddress(
                          address.id,
                        )
                          .then(
                            async () => {
                              setProfile(
                                await getProfile(),
                              );
                              setSaveNotice(
                                "Address removed.",
                              );
                            },
                          )
                          .catch((caught) => {
                            setError(
                              caught instanceof Error
                                ? caught.message
                                : "Address removal failed.",
                            );
                          });
                      }}
                    >
                      Remove
                    </button>
                  </article>
                ),
              )}
            </div>
          ) : (
            <p className="account-muted">
              No saved addresses.
            </p>
          )}

          {!addressFormOpen ? (
            <button
              type="button"
              className="account-action account-add-address-action"
              onClick={() => {
                setAddressDraft(EMPTY_ADDRESS);
                setAddressFormOpen(true);
                setError(null);
                setSaveNotice(null);
              }}
            >
              {profile.addresses.length > 0
                ? "Add Additional Address"
                : "Add Address"}
            </button>
          ) : (
          <form
            className="account-form address-form"
            onSubmit={(event) => {
              void submitAddress(
                event,
              );
            }}
          >
            <h3>
              {profile.addresses.length > 0
                ? "Add another address"
                : "Add your address"}
            </h3>
            <label>
              <span>Label</span>
              <input
                required
                value={
                  addressDraft.label
                }
                onChange={(event) => {
                  setAddressDraft({
                    ...addressDraft,
                    label:
                      event.target.value,
                  });
                }}
              />
            </label>

            <label>
              <span>Address</span>
              <input
                required
                autoComplete="address-line1"
                value={
                  addressDraft.line1
                }
                onChange={(event) => {
                  setAddressDraft({
                    ...addressDraft,
                    line1:
                      event.target.value,
                  });
                }}
              />
            </label>

            <label>
              <span>Address line 2</span>
              <input
                autoComplete="address-line2"
                value={
                  addressDraft.line2
                  ?? ""
                }
                onChange={(event) => {
                  setAddressDraft({
                    ...addressDraft,
                    line2:
                      event.target.value
                      || null,
                  });
                }}
              />
            </label>

            <div className="account-form-row">
              <label>
                <span>City</span>
                <input
                  required
                  autoComplete="address-level2"
                  value={
                    addressDraft.city
                  }
                  onChange={(event) => {
                    setAddressDraft({
                      ...addressDraft,
                      city:
                        event.target
                          .value,
                    });
                  }}
                />
              </label>

              <label>
                <span>State / region</span>
                <input
                  required
                  autoComplete="address-level1"
                  value={
                    addressDraft
                      .region_code
                  }
                  onChange={(event) => {
                    setAddressDraft({
                      ...addressDraft,
                      region_code:
                        event.target
                          .value,
                    });
                  }}
                />
              </label>
            </div>

            <div className="account-form-row">
              <label>
                <span>Postal code</span>
                <input
                  required
                  autoComplete="postal-code"
                  value={
                    addressDraft
                      .postal_code
                  }
                  onChange={(event) => {
                    setAddressDraft({
                      ...addressDraft,
                      postal_code:
                        event.target
                          .value,
                    });
                  }}
                />
              </label>

              <label>
                <span>Country</span>
                <input
                  required
                  maxLength={2}
                  autoComplete="country"
                  value={
                    addressDraft
                      .country_code
                  }
                  onChange={(event) => {
                    setAddressDraft({
                      ...addressDraft,
                      country_code:
                        event.target
                          .value
                          .toUpperCase(),
                    });
                  }}
                />
              </label>
            </div>

            <label className="account-checkbox">
              <input
                type="checkbox"
                checked={
                  addressDraft
                    .is_default_shipping
                }
                onChange={(event) => {
                  setAddressDraft({
                    ...addressDraft,
                    is_default_shipping:
                      event.target
                        .checked,
                  });
                }}
              />
              <span>
                Default shipping address
              </span>
            </label>

            <label className="account-checkbox">
              <input
                type="checkbox"
                checked={
                  addressDraft
                    .is_default_billing
                }
                onChange={(event) => {
                  setAddressDraft({
                    ...addressDraft,
                    is_default_billing:
                      event.target
                        .checked,
                  });
                }}
              />
              <span>
                Default billing address
              </span>
            </label>

            <div className="address-form-actions">
              <button
                type="submit"
                className="account-action"
                disabled={saving}
              >
                {saving
                  ? "Saving..."
                  : "Save Address"}
              </button>

              <button
                type="button"
                className="text-button compact"
                disabled={saving}
                onClick={() => {
                  setAddressDraft(EMPTY_ADDRESS);
                  setAddressFormOpen(false);
                }}
              >
                Cancel
              </button>
            </div>
          </form>
          )}
        </section>

        <section className="account-panel account-preferences-panel">
          <p className="eyebrow">Communication</p>
          <h2>Choose your reminders.</h2>
          <p className="account-muted">
            Optional maintenance and follow-up messages stay off until you choose them. Security, account, order, and other required transactional messages are separate from these preferences.
          </p>

          {communicationPreferences !== null ? (
            <div className="account-preference-list">
              {[
                ["filter_replacement_reminders", "Filter replacement reminders", "Helpful when a replaceable cartridge is part of your system."],
                ["softener_check_reminders", "Softener salt / check reminders", "Periodic reminders to inspect salt and routine softener settings."],
                ["uv_service_reminders", "UV lamp / service reminders", "Service reminders when UV treatment is part of your installed configuration."],
                ["annual_system_check_reminders", "Annual system check reminders", "A yearly prompt to review the condition and operation of your system."],
                ["product_specific_reminders", "Product-specific maintenance reminders", "Maintenance guidance tied to the equipment recorded for your account."],
                ["post_purchase_followup", "Post-purchase follow-up", "One useful follow-up after an equipment purchase."],
                ["post_installation_followup", "Post-installation follow-up", "One useful follow-up after installation information is recorded."],
              ].map(([key, label, description]) => (
                <label key={key} className="account-preference-option">
                  <input
                    type="checkbox"
                    checked={communicationPreferences[key as keyof CommunicationPreferences]}
                    onChange={(event) => {
                      setCommunicationPreferences({
                        ...communicationPreferences,
                        [key]: event.target.checked,
                      });
                    }}
                  />
                  <span>
                    <strong>{label}</strong>
                    <small>{description}</small>
                  </span>
                </label>
              ))}

              <button
                type="button"
                className="account-action"
                disabled={saving}
                onClick={() => {
                  void saveCommunicationPreferences();
                }}
              >
                Save Communication Preferences
              </button>
            </div>
          ) : (
            <p className="account-muted">Loading communication preferences…</p>
          )}
        </section>


        <section className="account-panel account-equipment-panel">
          <p className="eyebrow">Your equipment</p>
          <h2>Installed systems.</h2>
          {customerEquipment.length === 0 ? (
            <p className="account-muted">No installed equipment has been recorded for this account yet. Equipment appears here when installation information is confirmed.</p>
          ) : (
            <div className="account-equipment-list">
              {customerEquipment.map((equipment) => (
                <article key={equipment.id} className="account-equipment-row">
                  <div>
                    <p className="product-meta">{[equipment.product_family, equipment.system_type].filter(Boolean).join(" · ") || "Water treatment equipment"}</p>
                    <h3>{equipment.product_name}</h3>
                    <p className="account-muted">{equipment.variant_name ?? equipment.sku}{equipment.location_label ? ` · ${equipment.location_label}` : ""}</p>
                  </div>
                  <dl className="account-equipment-facts">
                    <div><dt>Installed</dt><dd>{equipment.installed_on ? new Date(`${equipment.installed_on}T00:00:00`).toLocaleDateString() : "Not recorded"}</dd></div>
                    <div><dt>Last service</dt><dd>{equipment.last_service_on ? new Date(`${equipment.last_service_on}T00:00:00`).toLocaleDateString() : "Not recorded"}</dd></div>
                    <div><dt>Next service</dt><dd>{equipment.next_service_due_on ? new Date(`${equipment.next_service_due_on}T00:00:00`).toLocaleDateString() : "Not scheduled"}</dd></div>
                  </dl>
                  {equipment.service_calendar_path !== null ? (
                    <a
                      className="text-button compact"
                      href={equipment.service_calendar_path}
                      download
                    >
                      Add service target to calendar
                    </a>
                  ) : null}
                  {equipment.consumables.length > 0 ? (
                    <div className="account-equipment-consumables">
                      <strong>Replacement items</strong>
                      {equipment.consumables.map((consumable) => (
                        <div
                          key={consumable.product_id}
                          className="account-equipment-consumable"
                        >
                          <div>
                            <span>{consumable.name}</span>
                            <small>
                              {consumable.next_replacement_due_on !== null
                                ? `Next replacement target: ${new Date(`${consumable.next_replacement_due_on}T00:00:00`).toLocaleDateString()}`
                                : consumable.replacement_interval_days !== null
                                  ? `Replacement interval: ${consumable.replacement_interval_days} days; service baseline not recorded.`
                                  : "Replacement interval has not been configured."}
                            </small>
                          </div>
                          <div className="account-equipment-consumable-actions">
                            {consumable.calendar_path !== null ? (
                              <a
                                className="text-button compact"
                                href={consumable.calendar_path}
                                download
                              >
                                Add to calendar
                              </a>
                            ) : null}
                            {consumable.online_reorder_available ? (
                              <button
                                type="button"
                                className="account-action compact"
                                disabled={saving}
                                onClick={() => {
                                  void reorderConsumable(
                                    consumable.product_id,
                                    consumable.name,
                                  );
                                }}
                              >
                                Add to Cart
                              </button>
                            ) : (
                              <button
                                type="button"
                                className="text-button compact"
                                onClick={() => {
                                  onNavigate(consumable.public_path);
                                }}
                              >
                                View Item
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : null}
                  {equipment.documents.length > 0 ? (
                    <div className="account-equipment-documents">
                      <strong>Documents</strong>
                      {equipment.documents.map((document) => (
                        <a key={`${document.path}-${document.version}`} href={document.path}>{document.title}</a>
                      ))}
                    </div>
                  ) : null}
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="account-panel account-maintenance-panel">
          <p className="eyebrow">Maintenance &amp; support</p>
          <h2>Useful ownership checks.</h2>
          <div className="account-maintenance-list">
            <article>
              <strong>Exterior water routing</strong>
              <p>Exterior irrigation, hose-bib, and pool-fill lines should generally bypass whole-property treatment when practical. Large pool-fill volumes can shorten filtration-media service life. Final routing still depends on the property and installation.</p>
            </article>
            <article>
              <strong>Softener salt</strong>
              <p>Inspect brine-tank salt about monthly and replenish it as needed. Follow the applicable manufacturer instructions; numeric minimum-fill guidance remains subject to manufacturer confirmation.</p>
            </article>
            <article>
              <strong>After a power interruption</strong>
              <p>Where applicable, verify the valve time-of-day on conventional softeners and backwashing carbon filters.</p>
            </article>
            <article>
              <strong>Replaceable cartridges</strong>
              <p>Plan on replacement about every six months where applicable, with actual life affected by water quality, use, micron rating, and system conditions. Follow a pressure or clog gauge when equipped.</p>
            </article>
          </div>
        </section>

        <section className="account-panel account-requests-panel">
          <p className="eyebrow">Requests</p>
          <h2>Your consultation history.</h2>
          {customerRequests.length === 0 ? (
            <p className="account-muted">No signed-in requests are attached to this account yet.</p>
          ) : (
            <div className="account-request-list">
              {customerRequests.map((request) => (
                <article key={request.id} className="account-request-row">
                  <div>
                    <strong>{request.product_name ?? request.recommendation_title ?? "Water treatment consultation"}</strong>
                    <p>{new Date(request.created_at).toLocaleDateString()} · {request.status.replaceAll("_", " ")}</p>
                  </div>
                  <div className="account-request-badges">
                    {request.requires_third_party_lab ? <span>Lab testing</span> : null}
                    {request.human_review ? <span>Human review</span> : null}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="account-panel account-formal-quotes-panel">
          <p className="eyebrow">Quotes</p>
          <h2>Review and approve formal quotes.</h2>
          {formalQuotes.length === 0 ? (
            <p className="account-muted">No formal quotes are ready for this account yet.</p>
          ) : (
            <div className="account-formal-quote-list">
              {formalQuotes.map((quote) => (
                <article key={quote.id} className="account-formal-quote">
                  <header>
                    <div>
                      <strong>Quote revision {quote.revision_number}</strong>
                      <p>{quote.status.replaceAll("_", " ")}</p>
                      {quote.expires_at !== null ? (
                        <small>
                          Valid through {new Date(quote.expires_at).toLocaleDateString()}
                        </small>
                      ) : null}
                    </div>
                    <strong>{money(quote.total_amount_minor, quote.currency)}</strong>
                  </header>

                  <div className="account-formal-quote-lines">
                    {quote.items.map((item) => (
                      <div key={`${quote.id}-${item.sku}-${item.name}`}>
                        <span>{item.quantity} × {item.name}</span>
                        <strong>{money(item.line_total_minor, item.currency)}</strong>
                        {item.estimated_lead_time !== null ? (
                          <small>Estimated lead time: {item.estimated_lead_time}</small>
                        ) : null}
                      </div>
                    ))}
                    <div>
                      <span>Product / other costs</span>
                      <strong>
                        {money(
                          quote.cost_breakdown.product_other_amount_minor,
                          quote.currency,
                        )}
                      </strong>
                    </div>
                    <div>
                      <span>Shipping / delivery</span>
                      <strong>
                        {money(
                          quote.cost_breakdown.shipping_delivery_amount_minor,
                          quote.currency,
                        )}
                      </strong>
                    </div>
                    <div>
                      <span>Shipping insurance</span>
                      <strong>
                        {money(
                          quote.cost_breakdown.shipping_insurance_amount_minor,
                          quote.currency,
                        )}
                      </strong>
                    </div>
                    <div>
                      <span>Tax</span>
                      <strong>
                        {money(quote.cost_breakdown.tax_amount_minor, quote.currency)}
                      </strong>
                    </div>
                    <div>
                      <span>Total cost</span>
                      <strong>
                        {money(quote.cost_breakdown.total_amount_minor, quote.currency)}
                      </strong>
                    </div>
                    {quote.charges.length > 0 ? (
                      <small className="account-muted">
                        Adjustments: {quote.charges
                          .map(
                            (charge) =>
                              `${charge.label} ${money(charge.amount_minor, quote.currency)}`,
                          )
                          .join(" · ")}
                      </small>
                    ) : null}
                  </div>

                  <div className="account-formal-quote-addresses">
                    {quote.delivery_address !== null ? (
                      <div>
                        <strong>Delivery / service address</strong>
                        <address>
                          {commercialAddressLines(quote.delivery_address).map((line) => (
                            <span key={line}>{line}<br /></span>
                          ))}
                        </address>
                        {salesArea?.enforcement_enabled ? (
                          <p className="account-muted">
                            {salesAreaAllowsAddress(
                              salesArea,
                              quote.delivery_address,
                            )
                              ? `Delivery eligible within ${salesArea.label}.`
                              : `This delivery address is outside ${salesArea.label}. Contact D’Acqua Dolce for assistance.`}
                          </p>
                        ) : null}
                      </div>
                    ) : null}
                    {quote.billing_address !== null ? (
                      <div>
                        <strong>Billing address</strong>
                        <address>
                          {commercialAddressLines(quote.billing_address).map((line) => (
                            <span key={line}>{line}<br /></span>
                          ))}
                        </address>
                      </div>
                    ) : null}
                  </div>

                  {quote.customer_note !== null ? (
                    <p className="account-formal-quote-note">{quote.customer_note}</p>
                  ) : null}

                  {quote.warranty_snapshots.length > 0 ? (
                    <div className="account-formal-quote-policies">
                      <strong>Manufacturer warranty documents attached to this quote</strong>
                      {quote.warranty_snapshots.map((snapshot) => (
                        <div key={snapshot.id} className="account-warranty-snapshot">
                          <a href={snapshot.path}>
                            {snapshot.product_name}: {snapshot.title}
                          </a>
                          <small>
                            {snapshot.manufacturer_name} · version {snapshot.version} · verified {new Date(snapshot.verified_at).toLocaleDateString()}
                          </small>
                        </div>
                      ))}
                      <p className="account-muted">
                        D’Acqua Dolce is your primary contact for warranty assistance.
                      </p>
                    </div>
                  ) : null}

                  <div className="account-formal-quote-policies">
                    <strong>Policy versions attached to this quote</strong>
                    {quote.policy_snapshots.map((snapshot) => (
                      <details key={snapshot.id}>
                        <summary>
                          {snapshot.title} · version {snapshot.version}
                        </summary>
                        <div className="account-policy-snapshot-body">
                          {snapshot.body}
                        </div>
                      </details>
                    ))}
                  </div>

                  {quote.status === "presented" ? (
                    <>
                      {quote.shipping_insurance_offered ? (
                        <fieldset className="account-policy-acknowledgment">
                          <legend>Shipping insurance choice</legend>
                          <label>
                            <input
                              type="radio"
                              name={`shipping-insurance-${quote.id}`}
                              value="accepted"
                              checked={quote.shipping_insurance_decision === "accepted"}
                              disabled={insuranceDecisionBusyQuoteId === quote.id}
                              onChange={() => {
                                void setShippingInsuranceDecision(quote, "accepted");
                              }}
                            />
                            <span>
                              Accept shipping insurance for this quote revision.
                            </span>
                          </label>
                          <label>
                            <input
                              type="radio"
                              name={`shipping-insurance-${quote.id}`}
                              value="declined"
                              checked={quote.shipping_insurance_decision === "declined"}
                              disabled={insuranceDecisionBusyQuoteId === quote.id}
                              onChange={() => {
                                void setShippingInsuranceDecision(quote, "declined");
                              }}
                            />
                            <span>
                              Decline shipping insurance for this quote revision.
                            </span>
                          </label>
                          {quote.shipping_insurance_decision === "declined" ? (
                            <small className="account-muted">
                              This quote includes a shipping insurance charge. D’Acqua Dolce must prepare a revised quote without that charge before approval.
                            </small>
                          ) : null}
                        </fieldset>
                      ) : (
                        <p className="account-muted">
                          Shipping insurance is not included in this quote revision.
                        </p>
                      )}
                      <label className="account-policy-acknowledgment">
                        <input
                          type="checkbox"
                          checked={policyAcknowledgments[quote.id] === true}
                          onChange={(event) => {
                            setPolicyAcknowledgments((current) => ({
                              ...current,
                              [quote.id]: event.target.checked,
                            }));
                          }}
                        />
                        <span>
                          I reviewed the policy versions attached to this quote.
                        </span>
                      </label>
                    {formalQuoteExpired(quote) ? (
                      <p className="account-muted">
                        This quote has expired. Contact D’Acqua Dolce for a current revision.
                      </p>
                    ) : null}
                    {salesArea?.enforcement_enabled
                      && !salesAreaAllowsAddress(
                        salesArea,
                        quote.delivery_address,
                      ) ? (
                        <p className="account-muted">
                          This quote cannot be approved for the current delivery address.
                        </p>
                      ) : null}
                    <button
                      type="button"
                      className="account-action"
                      disabled={
                        formalQuoteExpired(quote)
                        || (
                          quote.shipping_insurance_offered
                          && quote.shipping_insurance_decision !== "accepted"
                        )
                        || (
                          salesArea?.enforcement_enabled === true
                          && !salesAreaAllowsAddress(
                            salesArea,
                            quote.delivery_address,
                          )
                        )
                      }
                      onClick={() => {
                        void approveFormalQuote(quote);
                      }}
                    >
                      {formalQuoteExpired(quote) ? "Quote Expired" : "Approve This Quote"}
                    </button>
                    </>
                  ) : quote.status === "approved" ? (
                    <div>
                      <p className="account-formal-quote-approved">
                        Approved {quote.approved_at !== null
                          ? new Date(quote.approved_at).toLocaleString()
                          : ""}
                      </p>
                      {quote.shipping_insurance_offered ? (
                        <p className="account-muted">
                          Shipping insurance: {quote.shipping_insurance_decision ?? "not recorded"}
                          {quote.shipping_insurance_decided_at !== null
                            ? ` · recorded ${new Date(quote.shipping_insurance_decided_at).toLocaleString()}`
                            : ""}
                        </p>
                      ) : null}
                      {orders.find((order) => order.formal_quote_id === quote.id) !== undefined ? (
                        <p className="account-muted">
                          Order prepared · awaiting secure payment.
                        </p>
                      ) : null}
                    </div>
                  ) : (
                    <p className="account-muted">This revision has been superseded.</p>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="account-panel">
          <h2>Cart</h2>

          {cart === null
          || cart.items.length === 0 ? (
            <p className="account-muted">
              Your cart is empty.
            </p>
          ) : (
            <>
              <div className="cart-list">
                {cart.items.map(
                  (item) => (
                    <article
                      key={item.id}
                      className="cart-row"
                    >
                      <div>
                        <strong>
                          {item.name}
                        </strong>
                        <p>
                          {item.sku}
                          {" · Qty "}
                          {item.quantity}
                        </p>
                      </div>

                      <div>
                        <strong>
                          {money(
                            item.line_total_minor,
                            item.currency,
                          )}
                        </strong>

                        <button
                          type="button"
                          className="text-button compact"
                          onClick={() => {
                            void removeCartItem(
                              item.id,
                            ).then(
                              setCart,
                            );
                          }}
                        >
                          Remove
                        </button>
                      </div>
                    </article>
                  ),
                )}
              </div>

              {cart.currency
                !== null ? (
                <p className="cart-total">
                  Total{" "}
                  <strong>
                    {money(
                      cart.total_amount_minor,
                      cart.currency,
                    )}
                  </strong>
                </p>
              ) : null}

              <p className="account-muted">
                Checkout activates only
                through the contracted
                PCI-compliant provider.
              </p>
            </>
          )}
        </section>

        <section className="account-panel">
          <h2>Orders</h2>

          {orders.length === 0 ? (
            <p className="account-muted">
              No orders yet.
            </p>
          ) : (
            <div className="order-list">
              {orders.map((order) => (
                <article
                  key={order.id}
                  className="order-row"
                >
                  <div>
                    <strong>
                      {orderStageLabel(order.customer_status)}
                    </strong>
                    <p>
                      {new Date(
                        order.created_at,
                      ).toLocaleDateString()}
                    </p>

                    <p className="account-muted">
                      {order.customer_status === "received"
                        ? "Your order has been received."
                        : order.customer_status === "processing"
                          ? "We are preparing the order and confirming supplier availability."
                          : order.customer_status === "supplier_confirmed"
                            ? "D’Acqua Dolce has confirmed the supplier stage for this order."
                            : order.customer_status === "awaiting_shipment"
                              ? "Your order is being prepared for shipment."
                              : order.customer_status === "shipped"
                                ? "Your order is on the way."
                                : order.customer_status === "completed"
                                  ? "This order is complete."
                                  : null}
                    </p>

                    {order.items.some(
                      (item) =>
                        item.estimated_lead_time !== null,
                    ) ? (
                      <p className="account-muted">
                        Estimated lead time:{" "}
                        {order.items
                          .map(
                            (item) =>
                              item.estimated_lead_time,
                          )
                          .filter(
                            (value): value is string =>
                              value !== null,
                          )
                          .join(" · ")}
                      </p>
                    ) : null}

                    {order.shipment !== null ? (
                      <p className="account-muted">
                        Tracking:{" "}
                        {order.shipment.carrier}{" "}
                        {order.shipment.tracking_number}
                        {order.shipment.tracking_url !== null ? (
                          <>
                            {" · "}
                            <a
                              href={order.shipment.tracking_url}
                              target="_blank"
                              rel="noreferrer"
                            >
                              Track shipment
                            </a>
                          </>
                        ) : null}
                      </p>
                    ) : null}

                    {order.cancellation !== null ? (
                      <div className="account-order-cancellation">
                        <strong>Cancellation</strong>
                        <p className="account-muted">
                          {order.cancellation.status === "requested"
                            ? "Cancellation review requested. Our team will review the supplier/order status."
                            : order.cancellation.status === "approved"
                              ? "Cancellation accepted. Any required payment reversal or administrative completion is handled separately."
                              : order.cancellation.status === "declined"
                                ? "Cancellation was reviewed and not approved. Contact us if you need help."
                                : "Cancellation workflow completed."}
                        </p>
                        {order.cancellation.reason !== null ? (
                          <p className="account-muted">
                            Reason: {order.cancellation.reason}
                          </p>
                        ) : null}
                      </div>
                    ) : (
                      order.status !== "cancelled"
                      && order.status !== "refunded"
                    ) ? (
                      <div className="account-order-cancellation">
                        <p className="account-muted">
                          {order.cancellation_mode === "unrestricted"
                            ? "Online cancellation is available until D’Acqua Dolce marks the order Supplier Confirmed."
                            : "Online cancellation is closed after Supplier Confirmed. Contact D’Acqua Dolce if exceptional review is needed."}
                        </p>
                        {order.cancellation_mode === "unrestricted" ? (
                          <>
                            <label className="account-order-cancellation-field">
                              <span>Reason (optional)</span>
                              <textarea
                                rows={2}
                                maxLength={2000}
                                value={cancellationReasons[order.id] ?? ""}
                                onChange={(event) => {
                                  setCancellationReasons((current) => ({
                                    ...current,
                                    [order.id]: event.target.value,
                                  }));
                                }}
                              />
                            </label>
                            <button
                              type="button"
                              className="account-action"
                              disabled={cancellationBusyOrderId === order.id}
                              onClick={() => {
                                void submitOrderCancellation(order);
                              }}
                            >
                              {cancellationBusyOrderId === order.id
                                ? "Submitting…"
                                : "Cancel order"}
                            </button>
                          </>
                        ) : null}
                      </div>
                    ) : null}

                    {order.charges.length > 0 ? (
                      <p className="account-muted">
                        Products {money(order.subtotal_amount_minor, order.currency)}
                        {order.charges.map((charge) => (
                          ` · ${charge.label} ${money(charge.amount_minor, order.currency)}`
                        )).join("")}
                      </p>
                    ) : null}

                    {order.delivery_address !== null ? (
                      <address className="account-order-address">
                        <strong>Delivery / service address</strong><br />
                        {commercialAddressLines(order.delivery_address).map((line) => (
                          <span key={line}>{line}<br /></span>
                        ))}
                      </address>
                    ) : null}
                  </div>

                  <strong>
                    {money(
                      order.total_amount_minor,
                      order.currency,
                    )}
                  </strong>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
