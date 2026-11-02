from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.mutual_fund import MutualFund, FundHolding
from app.providers.mutual_funds.mfapi import MFAPIProvider


AVAILABLE_FUNDS_CATALOG: List[Dict[str, Any]] = [
    {
        "scheme_code": "122639",
        "scheme_name": "Parag Parikh Flexi Cap Fund - Direct Plan - Growth",
        "fund_house": "PPFAS Mutual Fund",
        "category": "Equity - Flexi Cap",
        "plan": "Direct",
        "growth_type": "Growth",
        "risk_level": "Very High",
        "expense_ratio": 0.63,
        "suitable_for": ["Aggressive", "Moderate"],
        "min_horizon_years": 5,
        "description": "Consistent multi-cap equity fund with international exposure and long-term value compounding."
    },
    {
        "scheme_code": "119063",
        "scheme_name": "HDFC Nifty 50 Index Fund - Direct Plan - Growth",
        "fund_house": "HDFC Mutual Fund",
        "category": "Equity - Index Fund (Large Cap)",
        "plan": "Direct",
        "growth_type": "Growth",
        "risk_level": "Very High",
        "expense_ratio": 0.20,
        "suitable_for": ["Conservative", "Moderate", "Aggressive"],
        "min_horizon_years": 3,
        "description": "Low-cost passive index tracking India's top 50 blue-chip companies across sectors."
    },
    {
        "scheme_code": "118989",
        "scheme_name": "HDFC Balanced Advantage Fund - Direct Plan - Growth",
        "fund_house": "HDFC Mutual Fund",
        "category": "Hybrid - Dynamic Asset Allocation",
        "plan": "Direct",
        "growth_type": "Growth",
        "risk_level": "High",
        "expense_ratio": 0.82,
        "suitable_for": ["Conservative", "Moderate"],
        "min_horizon_years": 3,
        "description": "Dynamic equity and debt allocation designed to provide downside cushion and stable capital appreciation."
    },
    {
        "scheme_code": "119062",
        "scheme_name": "HDFC Flexi Cap Fund - Direct Plan - Growth",
        "fund_house": "HDFC Mutual Fund",
        "category": "Equity - Flexi Cap",
        "plan": "Direct",
        "growth_type": "Growth",
        "risk_level": "Very High",
        "expense_ratio": 0.85,
        "suitable_for": ["Moderate", "Aggressive"],
        "min_horizon_years": 5,
        "description": "Diversified fund investing across large, mid, and small cap equities for long-term alpha."
    },
    {
        "scheme_code": "120503",
        "scheme_name": "Axis ELSS Tax Saver Fund - Direct Plan - Growth Option",
        "fund_house": "Axis Mutual Fund",
        "category": "Equity - ELSS (Tax Saving)",
        "plan": "Direct",
        "growth_type": "Growth",
        "risk_level": "Very High",
        "expense_ratio": 0.76,
        "suitable_for": ["Moderate", "Aggressive"],
        "min_horizon_years": 3,
        "description": "Section 80C tax-saving equity fund with a 3-year statutory lock-in period and quality growth focus."
    },
    {
        "scheme_code": "118834",
        "scheme_name": "Mirae Asset Large Cap Fund - Direct Plan - Growth",
        "fund_house": "Mirae Asset Mutual Fund",
        "category": "Equity - Large Cap",
        "plan": "Direct",
        "growth_type": "Growth",
        "risk_level": "Very High",
        "expense_ratio": 0.54,
        "suitable_for": ["Moderate", "Aggressive"],
        "min_horizon_years": 4,
        "description": "Premier large-cap fund focusing on top market leaders with strong corporate governance and steady cash flows."
    },
    {
        "scheme_code": "125497",
        "scheme_name": "SBI Small Cap Fund - Direct Plan - Growth",
        "fund_house": "SBI Mutual Fund",
        "category": "Equity - Small Cap",
        "plan": "Direct",
        "growth_type": "Growth",
        "risk_level": "Very High",
        "expense_ratio": 0.69,
        "suitable_for": ["Aggressive"],
        "min_horizon_years": 7,
        "description": "High-growth high-volatility fund identifying emerging market champions in the small-cap segment."
    },
    {
        "scheme_code": "120716",
        "scheme_name": "ICICI Prudential Bluechip Fund - Direct Plan - Growth",
        "fund_house": "ICICI Prudential Mutual Fund",
        "category": "Equity - Large Cap",
        "plan": "Direct",
        "growth_type": "Growth",
        "risk_level": "Very High",
        "expense_ratio": 0.90,
        "suitable_for": ["Conservative", "Moderate", "Aggressive"],
        "min_horizon_years": 3,
        "description": "Large-cap portfolio investing in India's top 100 benchmark leaders with disciplined sector limits."
    },
    {
        "scheme_code": "120847",
        "scheme_name": "Nippon India Small Cap Fund - Direct Plan - Growth",
        "fund_house": "Nippon India Mutual Fund",
        "category": "Equity - Small Cap",
        "plan": "Direct",
        "growth_type": "Growth",
        "risk_level": "Very High",
        "expense_ratio": 0.70,
        "suitable_for": ["Aggressive"],
        "min_horizon_years": 7,
        "description": "Extensively diversified small-cap strategy capturing domestic cyclical expansion."
    },
    {
        "scheme_code": "120465",
        "scheme_name": "Kotak Emerging Equity Fund - Direct Plan - Growth",
        "fund_house": "Kotak Mahindra Mutual Fund",
        "category": "Equity - Mid Cap",
        "plan": "Direct",
        "growth_type": "Growth",
        "risk_level": "Very High",
        "expense_ratio": 0.81,
        "suitable_for": ["Aggressive", "Moderate"],
        "min_horizon_years": 5,
        "description": "Mid-cap specialist fund targeting established companies with scalable business models."
    },
    {
        "scheme_code": "120703",
        "scheme_name": "UTI Nifty 50 Index Fund - Direct Plan - Growth",
        "fund_house": "UTI Mutual Fund",
        "category": "Equity - Index Fund",
        "plan": "Direct",
        "growth_type": "Growth",
        "risk_level": "Very High",
        "expense_ratio": 0.18,
        "suitable_for": ["Conservative", "Moderate", "Aggressive"],
        "min_horizon_years": 3,
        "description": "Ultra low-cost passive index tracking standard benchmark performance."
    },
    {
        "scheme_code": "145552",
        "scheme_name": "Quant Flexi Cap Fund - Direct Plan - Growth",
        "fund_house": "Quant Mutual Fund",
        "category": "Equity - Flexi Cap",
        "plan": "Direct",
        "growth_type": "Growth",
        "risk_level": "Very High",
        "expense_ratio": 0.77,
        "suitable_for": ["Aggressive"],
        "min_horizon_years": 5,
        "description": "Momentum and quantitative multi-asset strategy adjusting asset allocations based on predictive algorithms."
    }
]


class MutualFundService:

    def __init__(self):
        self.provider = MFAPIProvider()

    def get_available_catalog(self) -> List[Dict[str, Any]]:
        """Returns the curated master catalog of available mutual funds in ArthaAI."""
        return AVAILABLE_FUNDS_CATALOG

    def search_funds(self, query: str) -> List[Dict[str, Any]]:
        """
        Fast multi-tier fund search:
        1. Instant match against curated catalog (handles 1-char queries like 'h', 'p', 'pa', 'flex').
        2. Fallback / supplement with provider if query length >= 2.
        """
        q = (query or "").strip().lower()
        if not q:
            return AVAILABLE_FUNDS_CATALOG[:10]

        matches: List[Dict[str, Any]] = []
        matched_codes = set()

        # Tier 1: Local Curated Catalog match (scheme_name, fund_house, category, code)
        for fund in AVAILABLE_FUNDS_CATALOG:
            name = fund["scheme_name"].lower()
            house = fund.get("fund_house", "").lower()
            category = fund.get("category", "").lower()
            code = fund["scheme_code"]

            if q in name or q in house or q in category or q == code:
                matches.append({
                    "scheme_code": code,
                    "scheme_name": fund["scheme_name"],
                    "fund_house": fund.get("fund_house", "Mutual Fund"),
                    "category": fund.get("category", "Equity"),
                    "plan": fund.get("plan", "Direct"),
                    "growth_type": fund.get("growth_type", "Growth"),
                })
                matched_codes.add(code)

        # Tier 2: Search Provider if query >= 2 chars to find extra AMFI schemes
        if len(q) >= 2:
            try:
                provider_results = self.provider.search_funds(q)
                for item in provider_results:
                    code = str(item.get("scheme_code"))
                    if code not in matched_codes:
                        matches.append({
                            "scheme_code": code,
                            "scheme_name": item.get("scheme_name"),
                            "fund_house": item.get("fund_house", "Mutual Fund"),
                            "category": item.get("category", "Equity"),
                            "plan": "Direct",
                            "growth_type": "Growth"
                        })
                        matched_codes.add(code)
            except Exception as e:
                print(f"Provider search fallback error: {e}")

        return matches[:20]

    def get_fund_details(self, db: Session, scheme_code: str) -> Optional[Dict[str, Any]]:
        # Check Catalog first
        for f in AVAILABLE_FUNDS_CATALOG:
            if f["scheme_code"] == str(scheme_code):
                db_fund = db.query(MutualFund).filter(MutualFund.scheme_code == str(scheme_code)).first()
                if not db_fund:
                    db_fund = MutualFund(
                        scheme_code=f["scheme_code"],
                        scheme_name=f["scheme_name"],
                        fund_house=f.get("fund_house"),
                        category=f.get("category"),
                        current_nav=55.0
                    )
                    db.add(db_fund)
                    db.commit()
                    db.refresh(db_fund)
                return {
                    "scheme_code": f["scheme_code"],
                    "scheme_name": f["scheme_name"],
                    "fund_house": f.get("fund_house"),
                    "category": f.get("category"),
                    "current_nav": db_fund.current_nav or 55.0,
                    "expense_ratio": f.get("expense_ratio", 0.75),
                    "risk_level": f.get("risk_level", "Very High"),
                    "description": f.get("description", "")
                }

        # Check DB
        db_fund = db.query(MutualFund).filter(MutualFund.scheme_code == str(scheme_code)).first()
        details = self.provider.get_fund_details(scheme_code)

        if not details:
            if db_fund:
                return {
                    "scheme_code": db_fund.scheme_code,
                    "scheme_name": db_fund.scheme_name,
                    "fund_house": db_fund.fund_house,
                    "category": db_fund.category,
                    "current_nav": db_fund.current_nav,
                    "nav_date": str(db_fund.nav_date) if db_fund.nav_date else None
                }
            return None

        # Upsert in DB
        if not db_fund:
            db_fund = MutualFund(
                scheme_code=str(scheme_code),
                scheme_name=details["scheme_name"],
                fund_house=details.get("fund_house"),
                category=details.get("category"),
                current_nav=details.get("current_nav")
            )
            db.add(db_fund)
        else:
            db_fund.scheme_name = details["scheme_name"]
            db_fund.current_nav = details.get("current_nav")
            if details.get("fund_house"):
                db_fund.fund_house = details.get("fund_house")
            if details.get("category"):
                db_fund.category = details.get("category")

        db.commit()
        db.refresh(db_fund)
        return details

    def get_latest_nav(self, scheme_code: str) -> Optional[Dict[str, Any]]:
        return self.provider.get_latest_nav(scheme_code)

    def get_nav_history(self, scheme_code: str, limit: int = 365) -> List[Dict[str, Any]]:
        return self.provider.get_nav_history(scheme_code, limit=limit)

    def get_holdings(self, scheme_code: str) -> List[Dict[str, Any]]:
        return self.provider.get_holdings(scheme_code)
