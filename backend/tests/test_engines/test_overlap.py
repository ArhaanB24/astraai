import pytest
from app.engines.overlap import calculate_portfolio_overlap


def test_portfolio_overlap_calculation():
    funds_holdings = {
        "122639": {
            "scheme_name": "Parag Parikh Flexi Cap Fund",
            "allocation_in_portfolio_pct": 50.0,
            "holdings": [
                {"company_name": "HDFC Bank Ltd.", "sector": "Financial Services", "allocation_percentage": 8.0},
                {"company_name": "ITC Ltd.", "sector": "Consumer Goods", "allocation_percentage": 6.0}
            ]
        },
        "119063": {
            "scheme_name": "Axis Bluechip Fund",
            "allocation_in_portfolio_pct": 50.0,
            "holdings": [
                {"company_name": "HDFC Bank Ltd.", "sector": "Financial Services", "allocation_percentage": 9.0},
                {"company_name": "Infosys Ltd.", "sector": "Technology", "allocation_percentage": 7.0}
            ]
        }
    }

    res = calculate_portfolio_overlap(funds_holdings)

    assert res["success"] is True
    assert len(res["overlapping_stocks"]) == 1
    assert res["overlapping_stocks"][0]["company_name"] == "HDFC Bank Ltd."
    assert res["pairwise_overlap"][0]["overlap_percentage"] == 8.0  # min(8, 9) = 8
