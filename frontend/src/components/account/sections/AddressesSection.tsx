// Saved delivery and billing addresses on the account page: list, remove, and
// the add-address form. The newest address is highlighted after adding.
//
// API: createAddress, deleteAddress, getProfile in api/account.ts
//   -> /api/account/addresses (addresses come back on the profile)

import {
  type Dispatch,
  type FormEvent,
  type SetStateAction,
  useRef,
  useState,
} from "react";
import {
  type AddressCreate,
  createAddress,
  type CustomerProfile,
  deleteAddress,
  getProfile,
} from "../../../api/account";
import { type AccountNoticeProps, type AccountSavingProps } from "../accountShared";

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

type AddressesSectionProps = {
  profile: CustomerProfile;
  onProfileChange: Dispatch<SetStateAction<CustomerProfile | null>>;
  /** Last success notice; "Address added." highlights the new address. */
  saveNotice: string | null;
} & AccountSavingProps & AccountNoticeProps;

export function AddressesSection({
  profile,
  onProfileChange: setProfile,
  saveNotice,
  saving,
  onSavingChange: setSaving,
  onError: setError,
  onNotice: setSaveNotice,
}: AddressesSectionProps) {
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

  return (
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
  );
}
