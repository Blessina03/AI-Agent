import json
import re
from pathlib import Path
from typing import Any


ORDERS_PATH = Path("data/orders.json")


def load_orders() -> dict[str, Any]:
    """Load the operational order snapshot."""
    with ORDERS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_order_id(order_id: str) -> str:
    """
    Normalize harmless differences in an order ID.

    Examples:
        ord-1001       -> ORD-1001
        ORD-1001       -> ORD-1001
        " ORD-1001 "   -> ORD-1001

    We do not guess substantially different IDs.
    """
    if not isinstance(order_id, str):
        return ""

    normalized = order_id.strip().upper()

    # Remove ordinary surrounding punctuation.
    normalized = normalized.strip(".,!?;:'\"()[]{}")

    return normalized


def find_order(order_id: str) -> dict[str, Any] | None:
    """Find an order using exact normalized order ID matching."""
    normalized_id = normalize_order_id(order_id)

    if not normalized_id:
        return None

    data = load_orders()

    for order in data.get("orders", []):
        if order.get("order_id") == normalized_id:
            return order

    return None


def _safe_items(order: dict[str, Any]) -> list[dict[str, Any]]:
    """Return only customer-safe item fields."""
    return [
        {
            "name": item.get("name"),
            "quantity": item.get("quantity"),
            "final_sale": item.get("final_sale"),
        }
        for item in order.get("items", [])
    ]


def lookup_order(order_id: str) -> dict[str, Any]:
    """
    Customer-safe order lookup.

    IMPORTANT:
    - Never returns customer name/email/address.
    - Never returns anything from the internal object.
    - Uses status as the authoritative operational state.
    - Never invents an ETA.
    - Never exposes stale ETA/tracking information for cancelled/returned orders.
    """

    order = find_order(order_id)

    if order is None:
        return {
            "found": False,
            "order_id": normalize_order_id(order_id),
            "message": (
                "No order was found for that order ID. "
                "Do not guess or substitute another order ID."
            ),
        }

    status = order.get("status")

    result = {
        "found": True,
        "order_id": order.get("order_id"),
        "membership_tier": order.get("membership_tier"),
        "items": _safe_items(order),
        "placed_at": order.get("placed_at"),
        "status": status,
        "status_updated_at": order.get("status_updated_at"),
        "customer_safe_message": order.get("customer_safe_message"),
    }

    # Only expose shipping-related fields when appropriate.
    if status == "shipped":
        result["shipped_at"] = order.get("shipped_at")
        result["carrier"] = order.get("carrier")
        result["tracking_number"] = order.get("tracking_number")

        # Do NOT calculate an ETA if one is unavailable.
        if order.get("estimated_delivery") is not None:
            result["estimated_delivery"] = order.get(
                "estimated_delivery"
            )
        else:
            result["estimated_delivery"] = None

    elif status == "delivered":
        result["shipped_at"] = order.get("shipped_at")
        result["delivered_at"] = order.get("delivered_at")

    elif status in {"cancelled", "returned"}:
        # Do not expose stale shipping/tracking/ETA information.
        result["operational_note"] = (
            f"The authoritative order status is '{status}'. "
            "Older shipping or estimated-delivery information must "
            "not be used to say that the order is still arriving."
        )

    elif status == "exception":
        result["operational_note"] = (
            "This order requires support review. "
            "Recommend a human handoff."
        )

    return result


if __name__ == "__main__":
    test_order = "ORD-1001"

    result = lookup_order(test_order)

    print(json.dumps(result, indent=2))