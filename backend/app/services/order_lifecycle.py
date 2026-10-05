from __future__ import annotations

from enum import StrEnum

from app.models.commerce import FulfillmentStatus, Order, OrderStatus


class CustomerOrderStage(StrEnum):
    received = "received"
    processing = "processing"
    supplier_confirmed = "supplier_confirmed"
    awaiting_shipment = "awaiting_shipment"
    shipped = "shipped"
    completed = "completed"
    cancelled = "cancelled"
    refunded = "refunded"


def customer_order_stage(order: Order) -> CustomerOrderStage:
    """Return the stable customer-facing order lifecycle stage.

    Payment state and fulfillment state remain separate internal concerns. This
    view intentionally presents the moderate lifecycle approved for launch.
    """

    if order.status == OrderStatus.cancelled:
        return CustomerOrderStage.cancelled
    if order.status == OrderStatus.refunded:
        return CustomerOrderStage.refunded

    if order.fulfillment_status == FulfillmentStatus.delivered:
        return CustomerOrderStage.completed
    if order.fulfillment_status == FulfillmentStatus.shipped:
        return CustomerOrderStage.shipped
    if order.fulfillment_status == FulfillmentStatus.received_ready:
        return CustomerOrderStage.awaiting_shipment
    if order.fulfillment_status == FulfillmentStatus.supplier_ordered:
        return CustomerOrderStage.supplier_confirmed

    if order.status in {
        OrderStatus.paid,
        OrderStatus.processing,
        OrderStatus.shipped,
        OrderStatus.delivered,
    }:
        return CustomerOrderStage.processing

    return CustomerOrderStage.received


def supplier_confirmation_recorded(order: Order) -> bool:
    """Return whether D'Acqua Dolce has crossed the customer cancellation boundary."""

    return (
        order.supplier_ordered_at is not None
        or order.fulfillment_status != FulfillmentStatus.not_started
    )
