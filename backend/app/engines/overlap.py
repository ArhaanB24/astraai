from typing import List, Dict, Any


def calculate_portfolio_overlap(
    funds_holdings: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Computes stock level overlap and sector concentration across multiple mutual funds.
    Input format:
    {
       "fund_1_code": {
           "scheme_name": "Parag Parikh Flexi Cap Fund",
           "allocation_in_portfolio_pct": 60.0,
           "holdings": [
               {"company_name": "HDFC Bank Ltd.", "sector": "Financial Services", "allocation_percentage": 8.0},
               ...
           ]
       },
       "fund_2_code": { ... }
    }
    """
    if not funds_holdings or len(funds_holdings) < 1:
        return {
            "success": False,
            "error_code": "INSUFFICIENT_FUNDS",
            "message": "At least one fund with holdings is required to compute portfolio overlap."
        }

    fund_codes = list(funds_holdings.keys())

    # Map stock -> total portfolio weight % & fund breakdown
    stock_weights: Dict[str, Dict[str, Any]] = {}
    sector_weights: Dict[str, float] = {}

    for code, fund in funds_holdings.items():
        scheme_name = fund.get("scheme_name", code)
        fund_port_weight = fund.get("allocation_in_portfolio_pct", 100.0) / 100.0
        holdings = fund.get("holdings", [])

        for h in holdings:
            company = h.get("company_name", "Unknown Company")
            sector = h.get("sector", "Other")
            fund_stock_alloc = float(h.get("allocation_percentage", 0.0))
            effective_port_weight = fund_stock_alloc * fund_port_weight

            # Sector accumulation
            sector_weights[sector] = sector_weights.get(sector, 0.0) + effective_port_weight

            # Stock accumulation
            if company not in stock_weights:
                stock_weights[company] = {
                    "company_name": company,
                    "sector": sector,
                    "effective_portfolio_weight_pct": 0.0,
                    "held_by_funds": []
                }
            stock_weights[company]["effective_portfolio_weight_pct"] += effective_port_weight
            stock_weights[company]["held_by_funds"].append({
                "scheme_code": code,
                "scheme_name": scheme_name,
                "fund_allocation_pct": fund_stock_alloc
            })

    # Sort stocks by weight
    sorted_stocks = sorted(stock_weights.values(), key=lambda x: x["effective_portfolio_weight_pct"], reverse=True)
    for s in sorted_stocks:
        s["effective_portfolio_weight_pct"] = round(s["effective_portfolio_weight_pct"], 2)

    # Filter overlapping stocks (held by > 1 fund)
    overlapping_stocks = [s for s in sorted_stocks if len(s["held_by_funds"]) > 1]

    # Calculate overall stock overlap percentage (sum of min allocation for common stocks across fund pairs)
    pairwise_overlap = []
    if len(fund_codes) >= 2:
        for i in range(len(fund_codes)):
            for j in range(i + 1, len(fund_codes)):
                c1, c2 = fund_codes[i], fund_codes[j]
                f1_h = {h["company_name"]: float(h.get("allocation_percentage", 0.0)) for h in funds_holdings[c1].get("holdings", [])}
                f2_h = {h["company_name"]: float(h.get("allocation_percentage", 0.0)) for h in funds_holdings[c2].get("holdings", [])}

                common_keys = set(f1_h.keys()).intersection(set(f2_h.keys()))
                overlap_pct = sum(min(f1_h[k], f2_h[k]) for k in common_keys)

                pairwise_overlap.append({
                    "fund_1": funds_holdings[c1].get("scheme_name", c1),
                    "fund_2": funds_holdings[c2].get("scheme_name", c2),
                    "overlap_percentage": round(overlap_pct, 2),
                    "common_stocks_count": len(common_keys)
                })

    # Format sector weights
    formatted_sectors = [
        {"sector": sec, "portfolio_weight_pct": round(weight, 2)}
        for sec, weight in sorted(sector_weights.items(), key=lambda x: x[1], reverse=True)
    ]

    return {
        "success": True,
        "top_portfolio_stocks": sorted_stocks[:15],
        "overlapping_stocks": overlapping_stocks,
        "pairwise_overlap": pairwise_overlap,
        "sector_concentration": formatted_sectors
    }
