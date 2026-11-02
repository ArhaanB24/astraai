from datetime import datetime
from typing import List, Dict, Any
from decimal import Decimal, ROUND_HALF_UP
from app.engines.xirr import calculate_xirr


def _to_decimal(val: Any) -> Decimal:
    """Helper to convert float/int/str to Decimal cleanly."""
    return Decimal(str(val))


def _round_decimal(val: Decimal, places: int = 2) -> float:
    """Rounds Decimal to specified places and converts to float for final API output."""
    fmt = "0." + "0" * places if places > 0 else "0"
    return float(val.quantize(Decimal(fmt), rounding=ROUND_HALF_UP))


def calculate_portfolio_metrics(
    transactions: List[Dict[str, Any]],
    current_navs: Dict[str, float]  # {scheme_code: latest_nav}
) -> Dict[str, Any]:
    """
    Dynamically computes portfolio metrics from transactions and latest NAVs.
    Uses Decimal internally for all monetary amounts, NAVs, and unit calculations
    to eliminate intermediate floating-point rounding errors.
    """
    if not transactions:
        return {
            "success": True,
            "total_invested": 0.0,
            "current_value": 0.0,
            "total_profit_loss": 0.0,
            "profit_loss_percentage": 0.0,
            "xirr": None,
            "fund_breakdown": []
        }

    fund_summaries: Dict[str, Dict[str, Any]] = {}
    cash_flows_by_date: Dict[datetime, Decimal] = {}
    latest_tx_date: datetime = datetime.min

    for tx in transactions:
        scheme_code = str(tx.get("scheme_code"))
        scheme_name = tx.get("scheme_name", "Mutual Fund")
        tx_type = tx.get("transaction_type", "BUY").upper()
        units = _to_decimal(tx.get("units", 0.0))
        amount = _to_decimal(tx.get("amount", 0.0))

        # Parse exact transaction date
        tx_date = tx.get("transaction_date")
        if isinstance(tx_date, str):
            tx_date = datetime.fromisoformat(tx_date.replace("Z", "+00:00"))

        if tx_date > latest_tx_date:
            latest_tx_date = tx_date

        if scheme_code not in fund_summaries:
            fund_summaries[scheme_code] = {
                "scheme_code": scheme_code,
                "scheme_name": scheme_name,
                "total_units": Decimal("0.0"),
                "invested_amount": Decimal("0.0"),
                "latest_nav": _to_decimal(current_navs.get(scheme_code, 0.0)),
            }

        if tx_type in ["BUY", "SIP"]:
            fund_summaries[scheme_code]["total_units"] += units
            fund_summaries[scheme_code]["invested_amount"] += amount
            cash_flows_by_date[tx_date] = cash_flows_by_date.get(tx_date, Decimal("0.0")) - abs(amount)
        elif tx_type == "SELL":
            fund_summaries[scheme_code]["total_units"] -= units
            fund_summaries[scheme_code]["invested_amount"] -= amount
            cash_flows_by_date[tx_date] = cash_flows_by_date.get(tx_date, Decimal("0.0")) + abs(amount)
        elif tx_type == "DIVIDEND":
            cash_flows_by_date[tx_date] = cash_flows_by_date.get(tx_date, Decimal("0.0")) + abs(amount)

    total_invested_dec = Decimal("0.0")
    total_current_value_dec = Decimal("0.0")
    fund_list = []

    for scheme_code, fund in fund_summaries.items():
        latest_nav_dec = _to_decimal(current_navs.get(scheme_code, fund["latest_nav"]))
        fund_unrounded_val = fund["total_units"] * latest_nav_dec
        fund_rounded_val = fund_unrounded_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fund_invested = fund["invested_amount"].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        pl_dec = fund_unrounded_val - fund_invested
        pl_pct_dec = (pl_dec / fund_invested * Decimal("100.0")) if fund_invested > 0 else Decimal("0.0")

        total_invested_dec += fund_invested
        total_current_value_dec += fund_unrounded_val

        fund_list.append({
            "scheme_code": scheme_code,
            "scheme_name": fund["scheme_name"],
            "total_units": float(fund["total_units"]),
            "latest_nav": float(latest_nav_dec),
            "invested_amount": float(fund_invested),
            "current_value": float(fund_rounded_val),
            "current_value_dec": fund_unrounded_val,
            "profit_loss": _round_decimal(pl_dec, 2),
            "profit_loss_pct": _round_decimal(pl_pct_dec, 2),
        })

    total_current_val_rounded = total_current_value_dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_pl_dec = total_current_value_dec - total_invested_dec
    overall_pl_pct_dec = (total_pl_dec / total_invested_dec * Decimal("100.0")) if total_invested_dec > 0 else Decimal("0.0")

    # Allocation percentages using exact unrounded Decimal denominator
    for f in fund_list:
        alloc_dec = (f["current_value_dec"] / total_current_value_dec * Decimal("100.0")) if total_current_value_dec > 0 else Decimal("0.0")
        f["allocation_pct"] = _round_decimal(alloc_dec, 2)
        del f["current_value_dec"]

    # Terminal value for XIRR on exact valuation date
    valuation_date = latest_tx_date if latest_tx_date > datetime.min else datetime.utcnow()
    cash_flows_by_date[valuation_date] = cash_flows_by_date.get(valuation_date, Decimal("0.0")) + total_current_value_dec

    # Convert to float ONLY at scipy XIRR boundary
    xirr_cash_flows = sorted([(dt, float(amt)) for dt, amt in cash_flows_by_date.items()], key=lambda x: x[0])
    xirr_res = calculate_xirr(xirr_cash_flows)
    xirr_val = xirr_res.get("xirr_percentage") if xirr_res.get("success") else None

    return {
        "success": True,
        "total_invested": _round_decimal(total_invested_dec, 2),
        "current_value": _round_decimal(total_current_val_rounded, 2),
        "total_profit_loss": _round_decimal(total_pl_dec, 2),
        "profit_loss_percentage": _round_decimal(overall_pl_pct_dec, 2),
        "xirr": xirr_val,
        "fund_breakdown": fund_list
    }
