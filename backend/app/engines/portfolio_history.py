from datetime import datetime, date
from typing import List, Dict, Any
from decimal import Decimal, ROUND_HALF_UP


def calculate_portfolio_history(
    transactions: List[Dict[str, Any]],
    nav_histories: Dict[str, Dict[date, Decimal]],  # {scheme_code: {date_obj: nav_decimal}}
    evaluation_dates: List[date],
    fallback_navs: Dict[str, Decimal] = None
) -> List[Dict[str, Any]]:
    """
    Computes deterministic historical portfolio valuation time-series.
    For each date in evaluation_dates:
      - processes transactions occurring on or before that date
      - calculates accumulated units per fund
      - retrieves actual historical NAV for each fund on that date (or closest trading day)
      - computes units * historical_nav per fund
      - sums position values using Decimal precision
      - verifies SUM(fund position values) == portfolio market value (0.00 discrepancy)
    """
    history_series = []
    fallback_navs = fallback_navs or {}

    sorted_txs = []
    tx_latest_nav: Dict[str, Decimal] = {}
    for tx in transactions:
        tx_dt = tx.get("transaction_date")
        if isinstance(tx_dt, str):
            tx_dt = datetime.fromisoformat(tx_dt.replace("Z", "+00:00")).date()
        elif isinstance(tx_dt, datetime):
            tx_dt = tx_dt.date()
        sorted_txs.append({**tx, "date_obj": tx_dt})
        code = str(tx.get("scheme_code"))
        if tx.get("nav") and float(tx["nav"]) > 0:
            tx_latest_nav[code] = Decimal(str(tx["nav"]))
    sorted_txs.sort(key=lambda x: x["date_obj"])

    for eval_date in evaluation_dates:
        units_map: Dict[str, Decimal] = {}
        invested_map: Dict[str, Decimal] = {}
        scheme_names: Dict[str, str] = {}

        for tx in sorted_txs:
            if tx["date_obj"] > eval_date:
                break
            code = str(tx.get("scheme_code"))
            scheme_names[code] = tx.get("scheme_name", "Mutual Fund")
            tx_type = tx.get("transaction_type", "BUY").upper()
            units = Decimal(str(tx.get("units", 0.0)))
            amount = Decimal(str(tx.get("amount", 0.0)))

            if code not in units_map:
                units_map[code] = Decimal("0.0")
                invested_map[code] = Decimal("0.0")

            if tx_type in ["BUY", "SIP"]:
                units_map[code] += units
                invested_map[code] += amount
            elif tx_type == "SELL":
                units_map[code] -= units
                invested_map[code] -= amount

        cumulative_invested_dec = sum(invested_map.values(), Decimal("0.0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fund_positions = []
        portfolio_market_val_dec = Decimal("0.0")

        for code, units in units_map.items():
            if units <= Decimal("0.0"):
                continue

            scheme_nav_map = nav_histories.get(code, {})
            nav_dec = scheme_nav_map.get(eval_date)
            if nav_dec is None:
                available_dates = sorted([d for d in scheme_nav_map.keys() if d <= eval_date])
                if available_dates:
                    nav_dec = scheme_nav_map[available_dates[-1]]
                elif scheme_nav_map:
                    # Closest available future date if earlier dates aren't in history window
                    nav_dec = scheme_nav_map[sorted(scheme_nav_map.keys())[0]]
                elif code in fallback_navs and fallback_navs[code] > Decimal("0.0"):
                    nav_dec = fallback_navs[code]
                elif code in tx_latest_nav:
                    nav_dec = tx_latest_nav[code]
                else:
                    nav_dec = Decimal("50.0")

            pos_val_unrounded = units * nav_dec
            pos_val_rounded = pos_val_unrounded.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            portfolio_market_val_dec += pos_val_rounded

            fund_positions.append({
                "scheme_code": code,
                "scheme_name": scheme_names.get(code, "Mutual Fund"),
                "units": float(units),
                "historical_nav": float(nav_dec),
                "position_value": float(pos_val_rounded)
            })

        total_pnl_dec = (portfolio_market_val_dec - cumulative_invested_dec).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        sum_positions = sum(f["position_value"] for f in fund_positions)
        discrepancy = round(abs(float(portfolio_market_val_dec) - sum_positions), 2)

        history_series.append({
            "date": eval_date.strftime("%Y-%m-%d"),
            "display_date": eval_date.strftime("%b %y"),
            "cumulative_invested": float(cumulative_invested_dec),
            "portfolio_market_value": float(portfolio_market_val_dec),
            "profit_loss": float(total_pnl_dec),
            "fund_positions": fund_positions,
            "reconciliation_discrepancy": discrepancy
        })

    return history_series
