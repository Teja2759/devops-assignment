"""Deterministic bill arithmetic; never rely on the LLM to calculate totals."""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def _decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, str):
        value = value.replace(",", "").replace("$", "").strip()
        if not value:
            return None
    try:
        return Decimal(str(value)).quantize(CENT, ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return None


def _float(value: Decimal | None) -> float | None:
    return None if value is None else float(value)


def compute_bill_totals(data: dict[str, Any]) -> dict[str, Any]:
    """Sum line items and calculate each total as subtotal minus discount plus tax."""
    warnings: list[str] = []
    bills_out: list[dict[str, Any]] = []
    grand_total = ZERO
    total_items = 0
    currencies: set[str] = set()

    for index, bill in enumerate(data.get("bills") or [], start=1):
        label = bill.get("bill_number") or f"#{index}"
        items_out: list[dict[str, Any]] = []
        items_total = ZERO
        for item in bill.get("items") or []:
            amount = _decimal(item.get("amount"))
            if amount is None:
                warnings.append(
                    f"bill {label}: item '{item.get('description')}' has no readable amount"
                )
            else:
                items_total += amount
            items_out.append(
                {
                    "date": item.get("date"),
                    "description": item.get("description"),
                    "quantity": item.get("quantity"),
                    "unit_rate": item.get("unit_rate"),
                    "amount": _float(amount),
                }
            )

        discount = abs(_decimal(bill.get("discount")) or ZERO)
        tax = abs(_decimal(bill.get("tax")) or ZERO)
        stated_subtotal = _decimal(bill.get("subtotal"))
        stated_total = _decimal(bill.get("total_amount_stated"))
        calculated_total = items_total - discount + tax
        subtotal_matches = (
            None if stated_subtotal is None else abs(stated_subtotal - items_total) < CENT
        )
        total_matches = (
            None if stated_total is None else abs(stated_total - calculated_total) < CENT
        )
        if subtotal_matches is False:
            warnings.append(
                f"bill {label}: items add up to {items_total} but the bill states subtotal {stated_subtotal}"
            )
        if total_matches is False:
            warnings.append(
                f"bill {label}: calculated total {calculated_total} differs from stated total {stated_total}"
            )

        currency = bill.get("currency")
        if currency:
            currencies.add(str(currency))
        grand_total += calculated_total
        total_items += len(items_out)
        bills_out.append(
            {
                "bill_number": bill.get("bill_number"),
                "provider_name": bill.get("provider_name"),
                "bill_date": bill.get("bill_date"),
                "patient_name": bill.get("patient_name"),
                "currency": currency,
                "item_count": len(items_out),
                "items": items_out,
                "items_subtotal": _float(items_total),
                "discount": _float(discount),
                "tax": _float(tax),
                "calculated_total": _float(calculated_total),
                "stated_subtotal": _float(stated_subtotal),
                "stated_total": _float(stated_total),
                "subtotal_matches_items": subtotal_matches,
                "total_matches_stated": total_matches,
            }
        )

    total: float | None = _float(grand_total)
    if len(currencies) > 1:
        warnings.append(
            f"bills use different currencies {sorted(currencies)}; grand total not computed"
        )
        total = None

    return {
        "bill_count": len(bills_out),
        "total_item_count": total_items,
        "currency": next(iter(currencies)) if len(currencies) == 1 else None,
        "total_amount": total,
        "bills": bills_out,
        "items": [item for bill in bills_out for item in bill["items"]],
        "warnings": warnings,
    }
