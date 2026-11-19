// Installed systems recorded for this customer (entered by staff in
// Operations > Customers), with one-click reorder of replacement items.
//
// API: addCartItem in api/cart.ts; equipment comes from getCustomerEquipment

import { type CustomerEquipment } from "../../../api/account";
import { addCartItem, type Cart } from "../../../api/cart";
import { type AccountNoticeProps, type AccountSavingProps } from "../accountShared";

type EquipmentSectionProps = {
  equipment: CustomerEquipment[];
  onCartChange: (cart: Cart) => void;
  onNavigate: (path: string) => void;
} & AccountSavingProps & AccountNoticeProps;

export function EquipmentSection({
  equipment: customerEquipment,
  onCartChange: setCart,
  onNavigate,
  saving,
  onSavingChange: setSaving,
  onError: setError,
  onNotice: setSaveNotice,
}: EquipmentSectionProps) {
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

  return (
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
  );
}
