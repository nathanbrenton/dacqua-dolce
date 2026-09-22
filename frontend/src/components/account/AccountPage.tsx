import {
  type FormEvent,
  useEffect,
  useState,
} from "react";

import "./AccountAppearance.css";

import {
  createAddress,
  deleteAddress,
  getProfile,
  updateProfile,
  type AddressCreate,
  type CustomerProfile,
} from "../../api/account";
import {
  reconfigureMfa,
  requestEmailVerification,
  type AuthenticationStatus,
} from "../../api/authentication";
import {
  getCart,
  removeCartItem,
  type Cart,
} from "../../api/cart";
import {
  getOrders,
  type Order,
} from "../../api/orders";
import {
  AppearanceToggle,
} from "../theme/AppearanceToggle";
import {
  getInitialAccountAppearance,
  saveAccountAppearance,
  type AppearanceMode,
} from "../../theme/appearance";
import {
  DEFAULT_THEME,
  isThemeId,
  THEMES,
  type ThemeId,
} from "../../theme/themes";
import {
  formatUsPhoneInput,
  isCompleteUsPhone,
} from "../../utils/phone";

type AccountPageProps = {
  onNavigate: (path: string) => void;
  onRequestSignIn: () => void;
  account: AuthenticationStatus | null;
  theme: ThemeId;
  onThemeChange: (theme: ThemeId) => void;
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
              <label>
                <span>
                  Current password
                </span>

                <input
                  type="password"
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
              </label>

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
  const [error, setError] =
    useState<string | null>(null);
  const [saving, setSaving] =
    useState(false);
  const [saveNotice, setSaveNotice] =
    useState<string | null>(null);
  const [appearance, setAppearance] =
    useState<AppearanceMode>(
      getInitialAccountAppearance,
    );
  const [addressDraft, setAddressDraft] =
    useState<AddressCreate>(
      EMPTY_ADDRESS,
    );

  useEffect(() => {
    saveAccountAppearance(appearance);
  }, [appearance]);

  useEffect(() => {
    if (saveNotice === null) {
      return;
    }

    const timeout = window.setTimeout(
      () => {
        setSaveNotice(null);
      },
      3500,
    );

    return () => {
      window.clearTimeout(timeout);
    };
  }, [saveNotice]);

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
    ])
      .then(
        ([
          profileResult,
          cartResult,
          orderResult,
        ]) => {
          setProfile(profileResult);
          setCart(cartResult);
          setOrders(orderResult);
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
            onAppearanceChange={setAppearance}
          />
        </div>
      </main>
    );
  }

  if (profile === null) {
    return (
      <main
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
      await createAddress(
        addressDraft,
      );

      setProfile(
        await getProfile(),
      );

      setAddressDraft(
        EMPTY_ADDRESS,
      );
      setSaveNotice("Address added.");
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

  return (
    <main
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

      {saveNotice !== null ? (
        <div
          className="account-toast"
          role="status"
          aria-live="polite"
        >
          {saveNotice}
        </div>
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
          onAppearanceChange={setAppearance}
        />

        <section className="account-panel">
          <h2>Profile</h2>

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
              <input
                type="tel"
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
                  formatUsPhoneInput(
                    profile.phone ?? "",
                  )
                }
                onChange={(event) => {
                  const formatted =
                    formatUsPhoneInput(
                      event.target.value,
                    );

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

        <section className="account-panel">
          <h2>Addresses</h2>

          {profile.addresses.length
            > 0 ? (
            <div className="address-list">
              {profile.addresses.map(
                (address) => (
                  <article
                    key={address.id}
                    className="address-card"
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

          <form
            className="account-form address-form"
            onSubmit={(event) => {
              void submitAddress(
                event,
              );
            }}
          >
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

            <button
              type="submit"
              className="account-action"
              disabled={saving}
            >
              Add Address
            </button>
          </form>
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
                      {order.status.replaceAll(
                        "_",
                        " ",
                      )}
                    </strong>
                    <p>
                      {new Date(
                        order.created_at,
                      ).toLocaleDateString()}
                    </p>
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
