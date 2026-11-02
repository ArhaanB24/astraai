import pytest
from decimal import Decimal
from app.engines.portfolio import calculate_portfolio_metrics


def test_portfolio_exact_reconciliation_zero_discrepancy():
    """
    Regression Test: Guarantees 0.00 discrepancy between portfolio-level totals and fund position sums:
    - SUM(position.current_value) == portfolio.current_value
    - SUM(position.invested) == portfolio.total_invested
    - SUM(position.profit_loss) == portfolio.total_profit_loss
    - portfolio.current_value - portfolio.total_invested == portfolio.total_profit_loss
    Specifically guards against any ₹400 or ₹335.44 aggregation discrepancy.
    """
    transactions = [
        {
            "scheme_code": "122639",
            "scheme_name": "Parag Parikh Flexi Cap Fund - Direct Plan - Growth",
            "transaction_type": "SIP",
            "transaction_date": "2025-08-14",
            "units": 1302.6884772389976,
            "nav": 92.1172,
            "amount": 120000.0
        },
        {
            "scheme_code": "119063",
            "scheme_name": "HDFC Nifty 50 Index Fund - Direct Plan",
            "transaction_type": "SIP",
            "transaction_date": "2025-08-14",
            "units": 249.61000651080235,
            "nav": 240.3750,
            "amount": 60000.0
        },
        {
            "scheme_code": "120503",
            "scheme_name": "Axis ELSS Tax Saver Fund - Direct Plan - Growth Option",
            "transaction_type": "SIP",
            "transaction_date": "2025-08-14",
            "units": 557.219189851867,
            "nav": 107.6775,
            "amount": 60000.0
        }
    ]

    current_navs = {
        "122639": 90.7427,
        "119063": 237.1753,
        "120503": 112.2447
    }

    metrics = calculate_portfolio_metrics(transactions, current_navs)
    assert metrics["success"] is True

    # 1. SUM(position.current_value) == portfolio.current_value
    sum_current_val = round(sum(f["current_value"] for f in metrics["fund_breakdown"]), 2)
    diff_val = round(abs(metrics["current_value"] - sum_current_val), 2)
    assert diff_val == 0.00, f"Discrepancy detected: Portfolio Current Value ({metrics['current_value']}) != Sum of positions ({sum_current_val})"

    # 2. SUM(position.invested) == portfolio.total_invested
    sum_invested = round(sum(f["invested_amount"] for f in metrics["fund_breakdown"]), 2)
    diff_inv = round(abs(metrics["total_invested"] - sum_invested), 2)
    assert diff_inv == 0.00, f"Discrepancy detected: Portfolio Total Invested ({metrics['total_invested']}) != Sum of invested ({sum_invested})"

    # 3. SUM(position.pnl) == portfolio.total_profit_loss
    sum_pnl = round(sum(f["profit_loss"] for f in metrics["fund_breakdown"]), 2)
    diff_pnl = round(abs(metrics["total_profit_loss"] - sum_pnl), 2)
    assert diff_pnl == 0.00, f"Discrepancy detected: Portfolio PnL ({metrics['total_profit_loss']}) != Sum of position PnLs ({sum_pnl})"

    # 4. portfolio.current_value - portfolio.total_invested == portfolio.total_profit_loss
    calculated_pnl = round(metrics["current_value"] - metrics["total_invested"], 2)
    assert metrics["total_profit_loss"] == calculated_pnl, f"PnL equation failed: {metrics['current_value']} - {metrics['total_invested']} = {calculated_pnl} != {metrics['total_profit_loss']}"
