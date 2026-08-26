from app.tools.orders import lookup_order


def test_existing_pending_order():
    result = lookup_order("ORD-1001")

    assert result["found"] is True
    assert result["order_id"] == "ORD-1001"
    assert result["status"] == "pending"


def test_unknown_order():
    result = lookup_order("ORD-9999")

    assert result["found"] is False
    assert result["order_id"] == "ORD-9999"


def test_order_id_normalization():
    result = lookup_order(" ord-1001 ")

    assert result["found"] is True
    assert result["order_id"] == "ORD-1001"


def test_cancelled_order_hides_stale_shipping_data():
    result = lookup_order("ORD-1004")

    assert result["found"] is True
    assert result["status"] == "cancelled"

    assert "tracking_number" not in result
    assert "carrier" not in result
    assert "estimated_delivery" not in result


def test_delayed_order_returns_eta():
    result = lookup_order("ORD-1005")

    assert result["found"] is True
    assert result["status"] == "delayed"

    # Delayed orders should still provide the customer-safe information.
    assert "customer_safe_message" in result
    assert "August 20, 2026" in result["customer_safe_message"]


def test_shipped_order_returns_shipping_information():
    result = lookup_order("ORD-1003")

    assert result["found"] is True
    assert result["status"] == "shipped"

    assert result["carrier"] == "USPS"
    assert result["tracking_number"] == "94001118995600001003"
    assert result["estimated_delivery"] == "2026-08-18"


def test_shipped_order_without_eta_does_not_invent_eta():
    result = lookup_order("ORD-1011")

    assert result["found"] is True
    assert result["status"] == "shipped"

    assert result["estimated_delivery"] is None


def test_exception_order_requires_human_handoff():
    result = lookup_order("ORD-1010")

    assert result["found"] is True
    assert result["status"] == "exception"

    assert "operational_note" in result
    assert "human handoff" in result["operational_note"].lower()


def test_returned_order_hides_stale_shipping_data():
    result = lookup_order("ORD-1008")

    assert result["found"] is True
    assert result["status"] == "returned"

    assert "tracking_number" not in result
    assert "carrier" not in result
    assert "estimated_delivery" not in result


def test_internal_information_is_not_exposed():
    result = lookup_order("ORD-1007")

    assert "customer" not in result
    assert "name" not in result
    assert "email" not in result
    assert "shipping_address" not in result
    assert "internal" not in result
    assert "risk_score" not in result
    assert "warehouse_note" not in result
    assert "support_tags" not in result