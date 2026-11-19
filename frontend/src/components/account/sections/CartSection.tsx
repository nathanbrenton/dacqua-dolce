// The customer's cart on the account page.
//
// API: removeCartItem in api/cart.ts

import { type Cart, removeCartItem } from "../../../api/cart";
import { money } from "../accountFormat";

type CartSectionProps = {
  cart: Cart | null;
  onCartChange: (cart: Cart) => void;
};

export function CartSection({
  cart,
  onCartChange: setCart,
}: CartSectionProps) {
  return (
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
  );
}
