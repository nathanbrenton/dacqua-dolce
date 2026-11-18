// Customers workspace of Operations: registered customer accounts with
// contact details and preferred contact method, saved addresses (read-only),
// linked orders, and installed-equipment records.
//
// The customer list is loaded by OperationsPage (Requests uses it too) and
// comes in as `customers`; equipment saves hand the updated customer back
// through onCustomerChange. `orders` and `products` feed the per-customer
// order count and the equipment product picker.
//
// API: createCustomerEquipment / updateCustomerEquipment in api/operations.ts
//   -> /api/operations/customers/{id}/equipment
// Contact-method labels: utils/contactMethod.ts. Styles: .operations-account-*

import { useMemo, useState } from "react";

import {
  createCustomerEquipment,
  updateCustomerEquipment,
  type OperationsCustomer,
  type OperationsOrder,
  type OperationsProduct,
} from "../../../api/operations";
import { contactMethodLabel } from "../../../utils/contactMethod";
import { formatUsPhoneInput } from "../../../utils/phone";
import { CopyEmailButton } from "../CopyEmailButton";
import type { OperationsNoticeProps } from "../operationsShared";

type EquipmentDraft = {
  productId: string;
  variantId: string;
  serialNumber: string;
  locationLabel: string;
  installedOn: string;
  lastServiceOn: string;
  nextServiceDueOn: string;
};

const EMPTY_EQUIPMENT_DRAFT: EquipmentDraft = {
  productId: "",
  variantId: "",
  serialNumber: "",
  locationLabel: "",
  installedOn: "",
  lastServiceOn: "",
  nextServiceDueOn: "",
};

type CustomersWorkspaceProps = {
  hidden: boolean;
  customers: OperationsCustomer[];
  orders: OperationsOrder[];
  products: OperationsProduct[];
  privileged: boolean;
  onCustomerChange: (customer: OperationsCustomer) => void;
} & OperationsNoticeProps;

export function CustomersWorkspace({
  hidden,
  customers,
  orders,
  products,
  privileged,
  onCustomerChange,
  onMessage: setMessage,
  onError: setError,
}: CustomersWorkspaceProps) {
  const [customerSearch, setCustomerSearch] =
    useState("");
  const [equipmentDraftCustomerId, setEquipmentDraftCustomerId] =
    useState<string | null>(null);
  const [equipmentDraft, setEquipmentDraft] =
    useState<EquipmentDraft>(EMPTY_EQUIPMENT_DRAFT);
  const [equipmentSaving, setEquipmentSaving] =
    useState(false);

  const filteredCustomers = useMemo(() => {
    const query =
      customerSearch.trim().toLowerCase();

    if (query.length === 0) {
      return customers;
    }

    return customers.filter((customer) => {
      const addressText =
        customer.addresses
          .flatMap((address) => [
            address.label,
            address.line1,
            address.line2 ?? "",
            address.city,
            address.region_code,
            address.postal_code,
            address.country_code,
          ])
          .join(" ");

      const searchable = [
        customer.email,
        customer.first_name ?? "",
        customer.last_name ?? "",
        customer.phone ?? "",
        customer.status,
        addressText,
      ]
        .join(" ")
        .toLowerCase();

      return searchable.includes(query);
    });
  }, [
    customers,
    customerSearch,
  ]);

  async function saveCustomerEquipment(customerId: string): Promise<void> {
    if (!equipmentDraft.productId) {
      setError("Choose a catalog product before recording equipment.");
      return;
    }
    setEquipmentSaving(true);
    setError(null);
    try {
      const updated = await createCustomerEquipment(customerId, {
        product_id: equipmentDraft.productId,
        variant_id: equipmentDraft.variantId || null,
        serial_number: equipmentDraft.serialNumber.trim() || null,
        location_label: equipmentDraft.locationLabel.trim() || null,
        installed_on: equipmentDraft.installedOn || null,
        last_service_on: equipmentDraft.lastServiceOn || null,
        next_service_due_on: equipmentDraft.nextServiceDueOn || null,
      });
      onCustomerChange(updated);
      setEquipmentDraftCustomerId(null);
      setEquipmentDraft(EMPTY_EQUIPMENT_DRAFT);
      setMessage("Installed equipment recorded.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to record equipment.");
    } finally {
      setEquipmentSaving(false);
    }
  }

  async function retireCustomerEquipment(customer: OperationsCustomer, equipmentId: string): Promise<void> {
    const equipment = customer.equipment.find((item) => item.id === equipmentId);
    if (!equipment) {
      return;
    }
    setError(null);
    try {
      const updated = await updateCustomerEquipment(customer.id, equipment.id, {
        serial_number: equipment.serial_number,
        location_label: equipment.location_label,
        installed_on: equipment.installed_on,
        last_service_on: equipment.last_service_on,
        next_service_due_on: equipment.next_service_due_on,
        active: false,
      });
      onCustomerChange(updated);
      setMessage("Equipment record marked inactive.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to update equipment.");
    }
  }

  return (
    <section
      id="operations-panel-customers"
      className="operations-workspace-panel"
      aria-label="Customer accounts"
      hidden={hidden}
    >
    <details
      id="customer-roster"
      className="operations-section operations-disclosure"
    >
      <summary className="operations-disclosure-summary">
        <span>
          <strong>Accounts & address book</strong>
          <small>Customer roster</small>
        </span>
      </summary>

      <div className="operations-disclosure-content">

      <div className="operations-section-heading">
        <p className="eyebrow">Customer Roster</p>
        <h2>Accounts &amp; address book</h2>
        <p>
          Registered customer accounts, saved addresses, and installed equipment.
          Profile and address information remains read-only here.
        </p>
      </div>

      <label
        className={
          "operations-field "
          + "operations-customer-search"
        }
      >
        <span>Search customers</span>
        <input
          type="search"
          placeholder="Name, email, phone, city, ZIP…"
          value={customerSearch}
          onChange={(event) => {
            setCustomerSearch(
              event.target.value,
            );
          }}
        />
      </label>

      {customers.length === 0 ? (
        <p className="account-muted">
          No registered customer accounts.
        </p>
      ) : filteredCustomers.length === 0 ? (
        <p className="account-muted">
          No customers match this search.
        </p>
      ) : (
        <div className="operations-customer-list">
          {filteredCustomers.map((customer) => {
            const fullName = [
              customer.first_name,
              customer.last_name,
            ]
              .filter(
                (value): value is string =>
                  value !== null,
              )
              .join(" ");

            const customerOrders = orders.filter(
              (order) => order.customer.id === customer.id,
            );
            const addressCount = customer.addresses.length;
            const orderCount = customerOrders.length;

            return (
              <article
                key={customer.id}
                className="operations-customer operations-account-workspace"
              >
                <section className="operations-account-identity">
                  <div className="operations-account-heading">
                    <div>
                      <p className="product-meta">
                        Customer account
                      </p>

                      <h3>
                        {fullName || customer.email}
                      </h3>
                    </div>

                    <span className="operations-account-status">
                      {customer.status}
                    </span>
                  </div>

                  <div className="operations-account-contact">
                    <div>
                      <span>Email</span>
                      <CopyEmailButton email={customer.email} />
                    </div>

                    <div>
                      <span>Phone</span>
                      {customer.phone !== null ? (
                        <a href={`tel:${customer.phone}`}>
                          {formatUsPhoneInput(
                            customer.phone,
                          )}
                        </a>
                      ) : (
                        <strong>Not provided</strong>
                      )}
                    </div>

                    <div>
                      <span>Prefers</span>
                      <strong>
                        {contactMethodLabel(customer.preferred_contact_method)
                          ?? "Not set"}
                      </strong>
                    </div>
                  </div>

                  <div className="operations-account-facts">
                    <div>
                      <span>Saved addresses</span>
                      <strong>{addressCount}</strong>
                    </div>
                    <div>
                      <span>Recorded orders</span>
                      <strong>{orderCount}</strong>
                    </div>
                    <div>
                      <span>Installed equipment</span>
                      <strong>{customer.equipment.filter((item) => item.active).length}</strong>
                    </div>
                    <div>
                      <span>Customer since</span>
                      <strong>
                        {new Date(
                          customer.created_at,
                        ).toLocaleDateString()}
                      </strong>
                    </div>
                  </div>

                  <p className="operations-account-boundary">
                    Orders are linked by the registered customer
                    account. Customer Requests are kept separate
                    unless a durable account relationship is stored.
                  </p>
                </section>

                <section className="operations-account-addresses">
                  <div className="operations-account-section-heading">
                    <div>
                      <p className="product-meta">Address book</p>
                      <h4>Saved customer addresses</h4>
                    </div>
                    <small>Read-only</small>
                  </div>

                  <div className="operations-address-list">
                    {customer.addresses.length === 0 ? (
                      <div className="operations-address operations-address-empty">
                        <strong>No saved addresses</strong>
                        <p className="account-muted">
                          This customer has not saved a shipping or
                          billing address yet.
                        </p>
                      </div>
                    ) : (
                      customer.addresses.map(
                        (address) => (
                          <div
                            key={address.id}
                            className="operations-address"
                          >
                            <div className="operations-address-heading">
                              <strong>{address.label}</strong>
                              {(
                                address.is_default_shipping
                                || address.is_default_billing
                              ) ? (
                                <div className="operations-address-badges">
                                  {address.is_default_shipping ? (
                                    <span>Default shipping</span>
                                  ) : null}
                                  {address.is_default_billing ? (
                                    <span>Default billing</span>
                                  ) : null}
                                </div>
                              ) : null}
                            </div>

                            <address>
                              {address.line1}

                              {address.line2 !== null ? (
                                <>
                                  <br />
                                  {address.line2}
                                </>
                              ) : null}

                              <br />
                              {address.city},{" "}
                              {address.region_code}{" "}
                              {address.postal_code}
                              <br />
                              {address.country_code}
                            </address>
                          </div>
                        )
                      )
                    )}
                  </div>
                </section>

                <section className="operations-account-equipment">
                  <div className="operations-account-section-heading">
                    <div>
                      <p className="product-meta">Installed equipment</p>
                      <h4>Ownership &amp; service record</h4>
                    </div>
                    <small>{privileged ? "Managed" : "Read-only"}</small>
                  </div>

                  <div className="operations-equipment-list">
                    {customer.equipment.filter((item) => item.active).length === 0 ? (
                      <p className="account-muted">No active installed equipment is recorded.</p>
                    ) : customer.equipment.filter((item) => item.active).map((equipment) => (
                      <article key={equipment.id} className="operations-equipment-row">
                        <div>
                          <strong>{equipment.product_name}</strong>
                          <p>{equipment.variant_name ?? equipment.sku}{equipment.location_label ? ` · ${equipment.location_label}` : ""}</p>
                        </div>
                        <div className="operations-equipment-dates">
                          <span>Installed: {equipment.installed_on ?? "Not recorded"}</span>
                          <span>Last service: {equipment.last_service_on ?? "Not recorded"}</span>
                          <span>Next service: {equipment.next_service_due_on ?? "Not scheduled"}</span>
                        </div>
                        {privileged ? (
                          <button type="button" className="text-button compact" onClick={() => void retireCustomerEquipment(customer, equipment.id)}>Mark inactive</button>
                        ) : null}
                      </article>
                    ))}
                  </div>

                  {privileged ? (
                    equipmentDraftCustomerId === customer.id ? (
                      <div className="operations-equipment-form">
                        <label className="operations-field">
                          <span>Catalog product</span>
                          <select value={equipmentDraft.productId} onChange={(event) => setEquipmentDraft({ ...equipmentDraft, productId: event.target.value, variantId: "" })}>
                            <option value="">Choose product…</option>
                            {products.filter((product) => product.active).map((product) => (
                              <option key={product.id} value={product.id}>{product.product_family ? `${product.product_family} — ` : ""}{product.name}</option>
                            ))}
                          </select>
                        </label>
                        {(() => {
                          const selectedProduct = products.find((product) => product.id === equipmentDraft.productId);
                          if (!selectedProduct || selectedProduct.variants.length === 0) {
                            return null;
                          }
                          return (
                            <label className="operations-field">
                              <span>Size / configuration</span>
                              <select value={equipmentDraft.variantId} onChange={(event) => setEquipmentDraft({ ...equipmentDraft, variantId: event.target.value })}>
                                <option value="">Not specified</option>
                                {selectedProduct.variants.map((variant) => (
                                  <option key={variant.id} value={variant.id}>{variant.display_name} · {variant.sku}</option>
                                ))}
                              </select>
                            </label>
                          );
                        })()}
                        <label className="operations-field"><span>Location</span><input value={equipmentDraft.locationLabel} onChange={(event) => setEquipmentDraft({ ...equipmentDraft, locationLabel: event.target.value })} placeholder="Kitchen, garage, utility room…" /></label>
                        <label className="operations-field"><span>Serial number</span><input value={equipmentDraft.serialNumber} onChange={(event) => setEquipmentDraft({ ...equipmentDraft, serialNumber: event.target.value })} /></label>
                        <div className="operations-equipment-date-grid">
                          <label className="operations-field"><span>Installed</span><input type="date" value={equipmentDraft.installedOn} onChange={(event) => setEquipmentDraft({ ...equipmentDraft, installedOn: event.target.value })} /></label>
                          <label className="operations-field"><span>Last service</span><input type="date" value={equipmentDraft.lastServiceOn} onChange={(event) => setEquipmentDraft({ ...equipmentDraft, lastServiceOn: event.target.value })} /></label>
                          <label className="operations-field"><span>Next service</span><input type="date" value={equipmentDraft.nextServiceDueOn} onChange={(event) => setEquipmentDraft({ ...equipmentDraft, nextServiceDueOn: event.target.value })} /></label>
                        </div>
                        <div className="operations-inline-actions">
                          <button type="button" className="operations-action" disabled={equipmentSaving} onClick={() => void saveCustomerEquipment(customer.id)}>{equipmentSaving ? "Saving…" : "Record equipment"}</button>
                          <button type="button" className="text-button compact" disabled={equipmentSaving} onClick={() => { setEquipmentDraftCustomerId(null); setEquipmentDraft(EMPTY_EQUIPMENT_DRAFT); }}>Cancel</button>
                        </div>
                      </div>
                    ) : (
                      <button type="button" className="operations-action secondary" onClick={() => { setEquipmentDraftCustomerId(customer.id); setEquipmentDraft(EMPTY_EQUIPMENT_DRAFT); }}>Record installed equipment</button>
                    )
                  ) : null}
                </section>
              </article>
            );
          })}
        </div>
      )}

      </div>
    </details>

    </section>
  );
}
