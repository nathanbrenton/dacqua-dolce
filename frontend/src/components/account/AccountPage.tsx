import {
  type FormEvent,
  useEffect,
  useState,
} from "react";

import {
  createAddress,
  deleteAddress,
  getProfile,
  updateProfile,
  type AddressCreate,
  type CustomerProfile,
} from "../../api/account";
import {
  getCart,
  removeCartItem,
  type Cart,
} from "../../api/cart";
import {
  getOrders,
  type Order,
} from "../../api/orders";

type AccountPageProps = {
  onNavigate: (path: string) => void;
  onRequestSignIn: () => void;
  authenticated: boolean;
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

export function AccountPage({
  onNavigate,
  onRequestSignIn,
  authenticated,
}: AccountPageProps) {
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
  const [addressDraft, setAddressDraft] =
    useState<AddressCreate>(
      EMPTY_ADDRESS,
    );

  useEffect(() => {
    if (!authenticated) {
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
  }, [authenticated]);

  if (!authenticated) {
    return (
      <main className="account-shell">
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

  if (profile === null) {
    return (
      <main className="account-shell">
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

    setSaving(true);
    setError(null);

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
    <main className="account-shell">
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
          Customer Account
        </p>

        <h1>Your water, organized.</h1>

        <p>{profile.email}</p>
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
                autoComplete="tel"
                value={
                  profile.phone ?? ""
                }
                onChange={(event) => {
                  setProfile({
                    ...profile,
                    phone:
                      event.target.value
                      || null,
                  });
                }}
              />
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
                    <strong>
                      {address.label}
                    </strong>

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
                        void deleteAddress(
                          address.id,
                        ).then(
                          async () => {
                            setProfile(
                              await getProfile(),
                            );
                          },
                        );
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
