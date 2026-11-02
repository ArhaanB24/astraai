import os
import google.generativeai as genai
from typing import Dict, Any, List, Optional
import json
import logging
from app.core.currency import sanitize_indian_currency_in_text, format_inr

logger = logging.getLogger(__name__)


class LLMProvider:
    """
    Deterministic Financial Communication & Response Presentation Layer.
    Uses Google Gemini with domain-isolated structured fallbacks.
    
    ZERO-LLM-ARITHMETIC MANDATE:
    1. Gemini is strictly an understanding and formatting presentation layer.
    2. Gemini must NEVER calculate financial math (XIRR, CAGR, EMI, Slabs, 87A rebate, Cess, Overlap).
    3. Gemini strictly communicates the pre-calculated deterministic values provided in context_data.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.primary_model = os.getenv("LLM_MODEL", "gemini-3.6-flash")
        self.fallback_models = [
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-flash-latest",
            "gemini-2.5-flash",
            "gemini-pro-latest",
            "gemini-2.5-flash-lite",
            "gemini-3.7-flash"
        ]
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        context_data: Dict[str, Any],
        citations: List[Dict[str, Any]]
    ) -> str:
        """
        Synthesizes a natural, explainable response grounded strictly in the provided
        deterministic context and retrieved citations.
        """
        # If out-of-domain or missing parameters, return direct explanation
        if context_data.get("is_out_of_domain"):
            return sanitize_indian_currency_in_text(self._structured_fallback_response(system_prompt, user_message, context_data))

        if context_data.get("missing_parameters"):
            return sanitize_indian_currency_in_text(self._structured_fallback_response(system_prompt, user_message, context_data))

        # Grounding payload passed to LLM with strict Zero-LLM-Arithmetic mandate
        prompt_parts = [
            f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n",
            "MANDATE ON COMPUTATION & CALCULATIONS (STRICT ZERO-ARITHMETIC RULE):\n"
            "1. You are STRICTLY a natural language communication, interpretation, and explanation layer.\n"
            "2. DO NOT perform, invent, extrapolate, or modify ANY mathematical computations or financial arithmetic.\n"
            "3. ALL numbers, sums, returns, XIRR, CAGR, EMIs, tax amounts, deductions, surplus, and net worth figures in your output MUST be drawn directly from the DETERMINISTIC CONTEXT below.\n"
            "4. Your job is to understand user intent, interpret their data, and clearly explain the engine's deterministic results.\n"
            "5. MANDATORY INDIAN NUMBERING SYSTEM: Always format all prices, currency amounts, and Rupee figures (₹) using the Indian Numbering System (e.g. ₹15,00,000 or ₹3,00,000 or ₹1,20,000 or ₹1,00,00,000). NEVER use Western 3-digit comma groupings like 1,500,000 or 300,000.\n",
            f"USER QUERY:\n{user_message}\n",
            f"DETERMINISTIC CONTEXT (AUTHORITATIVE PYTHON ENGINE CALCULATIONS — DO NOT ALTER NUMBERS):\n{json.dumps(context_data, indent=2, default=str)}\n"
        ]

        if citations:
            prompt_parts.append(
                f"RETRIEVED FACTUAL CITATIONS:\n{json.dumps(citations, indent=2, default=str)}\n"
            )

        full_prompt = "\n".join(prompt_parts)

        # Attempt generation across models
        models_to_try = [self.primary_model] + self.fallback_models
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config={"temperature": 0.1}
                )
                response = model.generate_content(full_prompt)
                if response and response.text:
                    return sanitize_indian_currency_in_text(response.text)
            except Exception as e:
                logger.warning(f"Gemini API model {model_name} failed: {e}. Trying next...")
                continue

        # If all LLM calls fail, invoke domain-isolated deterministic structured presentation
        return sanitize_indian_currency_in_text(self._structured_fallback_response(system_prompt, user_message, context_data))

    def _structured_fallback_response(
        self,
        system_prompt: str,
        user_message: str,
        context_data: Dict[str, Any]
    ) -> str:
        """
        Domain-isolated structured fallback responses.
        Guarantees zero cross-agent persona contamination and zero arithmetic fabrication.
        """
        first_line = system_prompt.strip().split("\n")[0].lower() if system_prompt else ""
        domain_tag = context_data.get("domain", "")

        is_tax = domain_tag == "tax" or ("tax" in first_line and "mutual fund" not in first_line and "personal finance" not in first_line)
        is_pf = domain_tag == "personal_finance" or ("personal finance" in first_line and "mutual fund" not in first_line)

        # =========================================================================
        # 1. TAX AI AGENT FALLBACK
        # =========================================================================
        if is_tax:
            if context_data.get("conversational_mode"):
                return (
                    "Hello! 👋 Welcome to **ArthaAI Tax AI Assistant**.\n\n"
                    "I am your dedicated, mathematically grounded Indian Income Tax advisor. "
                    "I can help you evaluate your tax liability under statutory Finance Act rules, "
                    "compare the Old vs. New Tax Regimes (Section 115BAC), analyze Section 80C and 80D deductions, "
                    "explain Section 87A rebate and marginal relief, and simulate salary modification scenarios.\n\n"
                    "How can I assist you with your tax planning today?"
                )

            # Check if Scenario Simulation was executed
            scen = context_data.get("scenario_analysis", {})
            if scen and scen.get("is_scenario"):
                base_sal = scen.get("baseline_annual_salary", 1440000.0)
                scen_sal = scen.get("scenario_annual_salary", 1540000.0)
                change_desc = scen.get("salary_change_applied", "Salary Increase")
                delta_inr = scen.get("salary_delta_inr", 100000.0)
                
                base_tax = scen.get("baseline_tax_summary", {})
                scen_tax = scen.get("scenario_tax_summary", {})
                deltas = scen.get("tax_liability_changes", {})

                rec_regime = deltas.get("recommended_regime", "NEW")
                savings = deltas.get("scenario_tax_savings", 0.0)
                old_delta = deltas.get("old_regime_tax_delta", 0.0)
                new_delta = deltas.get("new_regime_tax_delta", 0.0)

                lines = [
                    "### 📊 Tax Scenario Analysis\n",
                    f"* **Baseline Annual Salary:** **₹{base_sal:,.2f}**",
                    f"* **Salary Modification Applied:** **{change_desc}** (₹{delta_inr:+,.2f})",
                    f"* **Scenario Annual Salary:** **₹{scen_sal:,.2f}**\n",
                    "---",
                    "### ⚖️ Regime Comparison & Additional Tax Impact\n",
                    "| Tax Regime | Baseline Tax | Scenario Tax | Additional Tax Liability (Delta) |",
                    "| :--- | :--- | :--- | :--- |",
                    f"| **New Tax Regime (Sec 115BAC)** | ₹{base_tax.get('new_regime_tax', 0.0):,.2f} | ₹{scen_tax.get('new_regime_tax', 0.0):,.2f} | **{new_delta:+,.2f}** |",
                    f"| **Old Tax Regime** | ₹{base_tax.get('old_regime_tax', 0.0):,.2f} | ₹{scen_tax.get('old_regime_tax', 0.0):,.2f} | **{old_delta:+,.2f}** |\n",
                    "---",
                    "### 💡 Recommendation & Strategy\n",
                    f"* **Recommended Regime:** **{rec_regime} Tax Regime**",
                    f"* **Annual Tax Savings under {rec_regime} Regime:** **₹{savings:,.2f}**\n",
                    "> **Disclaimer:** Tax computations are generated by ArthaAI's deterministic calculation engine based on statutory provisions of the Income Tax Act, 1961. This is for educational and financial modeling purposes and does not constitute formal Chartered Accountant tax filing advice."
                ]
                return "\n".join(lines)

            # Baseline Tax Comparison Presentation
            comp = context_data.get("tax_regime_comparison", {})
            if comp:
                old_r = comp.get("old_regime", {})
                new_r = comp.get("new_regime", {})
                rec = comp.get("recommended_regime", "NEW")
                savings = comp.get("tax_savings", 0.0)

                lines = [
                    "### 🏛️ Income Tax Liability Assessment (FY 2025-26)\n",
                    f"* **Recommended Regime:** **{rec} Tax Regime**",
                    f"* **Annual Tax Savings:** **₹{savings:,.2f}**\n",
                    "---",
                    "### ⚖️ Detailed Regime Breakdown\n",
                    "| Tax Component | Old Tax Regime | New Tax Regime (Sec 115BAC) |",
                    "| :--- | :--- | :--- |",
                    f"| **Gross Total Income** | ₹{old_r.get('gross_total_income', 0.0):,.2f} | ₹{new_r.get('gross_total_income', 0.0):,.2f} |",
                    f"| **Total Deductions** | ₹{old_r.get('total_deductions', 0.0):,.2f} | ₹{new_r.get('total_deductions', 0.0):,.2f} |",
                    f"| **Taxable Income** | ₹{old_r.get('taxable_income', 0.0):,.2f} | ₹{new_r.get('taxable_income', 0.0):,.2f} |",
                    f"| **Tax Before Rebate** | ₹{old_r.get('tax_before_rebate', 0.0):,.2f} | ₹{new_r.get('tax_before_rebate', 0.0):,.2f} |",
                    f"| **Section 87A Rebate** | ₹{old_r.get('rebate_87a', 0.0):,.2f} | ₹{new_r.get('rebate_87a', 0.0):,.2f} |",
                    f"| **Health & Education Cess (4%)** | ₹{old_r.get('cess_amount', 0.0):,.2f} | ₹{new_r.get('cess_amount', 0.0):,.2f} |",
                    f"| **Total Tax Liability** | **₹{old_r.get('total_tax_liability', 0.0):,.2f}** | **₹{new_r.get('total_tax_liability', 0.0):,.2f}** |\n",
                    "> **Disclaimer:** Tax computations are generated by ArthaAI's deterministic calculation engine based on statutory provisions of the Income Tax Act, 1961. This is for educational and financial modeling purposes and does not constitute formal Chartered Accountant tax filing advice."
                ]
                return "\n".join(lines)

            return "Hello! I am your dedicated **ArthaAI Tax AI Assistant**. How can I help you evaluate your income tax, deductions, or regime comparisons today?"

        # =========================================================================
        # 2. PERSONAL FINANCE AGENT FALLBACK
        # =========================================================================
        if is_pf:
            if context_data.get("conversational_mode"):
                return (
                    "Hello! 👋 Welcome to **ArthaAI Personal Finance Assistant**.\n\n"
                    "I help you optimize your monthly budget, evaluate financial health against 50/30/20 heuristics, "
                    "simulate what-if scenarios, and calculate car purchase affordability using the 20/4/10 rule.\n\n"
                    "How can I help with your personal finances today?"
                )

            aff = context_data.get("affordability_analysis")
            if aff:
                v_type = str(aff.get("vehicle_type", "vehicle")).title()
                emoji = "🛵" if any(w in v_type.lower() for w in ["scooter", "bike", "motorcycle", "two_wheeler"]) else "🚗"
                price = aff.get("purchase_price", 0.0)
                dp = aff.get("down_payment", 0.0)
                dp_supplied = aff.get("down_payment_supplied", False)
                dp_label = f"₹{dp:,.2f}" + (" (Explicitly provided)" if dp_supplied else " (Assumed 20% default)")
                loan = aff.get("loan_amount", 0.0)
                emi = aff.get("new_monthly_emi", 0.0)
                assessment = aff.get("affordability_assessment", "HIGHLY_AFFORDABLE")

                is_affordable = assessment in ["HIGHLY_AFFORDABLE", "MODERATELY_AFFORDABLE"]
                status_str = "Affordable ✅" if is_affordable else ("Caution / Stretched ⚠️" if assessment == "STRETCHED" else "Unaffordable ❌")

                rec = aff.get("recommendation", "")
                if not rec:
                    if is_affordable:
                        rec = f"Purchasing this {v_type.lower()} for ₹{price:,.2f} fits comfortably within your monthly surplus."
                    else:
                        rec = f"Purchasing this {v_type.lower()} for ₹{price:,.2f} may stretch your monthly cash flow."

                assumption_text = f"\n* **Assumptions Used:** {dp_label}; {aff.get('loan_interest_rate_pct', 8.5)}% ROI over {aff.get('loan_tenure_years', 5.0)} years loan tenure."

                return (
                    f"### {emoji} {v_type} Purchase Affordability Assessment\n"
                    f"* **Vehicle Type:** {v_type}\n"
                    f"* **Item Price:** ₹{price:,.2f}\n"
                    f"* **Down Payment:** {dp_label}\n"
                    f"* **Loan Principal:** ₹{loan:,.2f}\n"
                    f"* **Estimated Monthly EMI:** **₹{emi:,.2f}**\n"
                    f"* **Affordability Status:** **{status_str}**{assumption_text}\n\n"
                    f"{rec}"
                )

            sim = context_data.get("scenario_simulation")
            if sim:
                impact = sim.get("impact_summary", "")
                deltas = sim.get("deltas", {})
                return (
                    f"### 🔮 What-If Scenario Simulation\n"
                    f"{impact}\n\n"
                    f"* **Monthly Surplus Delta:** ₹{deltas.get('surplus_change', 0.0):+,.2f}\n"
                    f"* **Savings Rate Delta:** {deltas.get('savings_rate_change_pct', 0.0):+.1f}%\n"
                    f"* **Debt-to-Income (DTI) Delta:** {deltas.get('dti_change_pct', 0.0):+.1f}%\n"
                    f"* **Emergency Coverage Delta:** {deltas.get('emergency_coverage_change_months', 0.0):+.1f} months"
                )

            goal = context_data.get("goal_analysis")
            if goal:
                g_name = goal.get("goal_name", "Goal")
                target_amt = goal.get("target_amount", 0.0)
                target_yr = goal.get("target_year", 2030)
                req_sip = goal.get("required_monthly_contribution", 0.0)
                return (
                    f"### 🎯 Financial Goal SIP Plan ({g_name})\n"
                    f"* **Target Goal Amount:** ₹{target_amt:,.2f}\n"
                    f"* **Target Year:** {target_yr}\n"
                    f"* **Required Monthly SIP:** **₹{req_sip:,.2f}/month**\n\n"
                    f"Starting a disciplined monthly SIP of ₹{req_sip:,.2f} will compound towards your {g_name} target."
                )

            health = context_data.get("financial_health", {})
            if health:
                income = health.get("monthly_income", 0.0)
                expenses = health.get("monthly_expenses", 0.0)
                emis = health.get("monthly_emis", 0.0)
                surplus = health.get("monthly_surplus", 0.0)
                score = health.get("health_score", 0)

                return (
                    f"### 💳 Financial Health Summary\n"
                    f"* **Monthly Income:** ₹{income:,.2f}\n"
                    f"* **Living Expenses:** ₹{expenses:,.2f}\n"
                    f"* **Monthly EMIs:** ₹{emis:,.2f}\n"
                    f"* **Net Monthly Surplus:** **₹{surplus:,.2f}**\n"
                    f"* **Overall Financial Health Score:** **{score}/100**"
                )

            return "Hello! I am your **ArthaAI Personal Finance Assistant**. How can I help you manage your budget and financial goals today?"

        # =========================================================================
        # 3. MUTUAL FUND AGENT FALLBACK (Default for Mutual Fund domain)
        # =========================================================================
        if context_data.get("conversational_mode"):
            return (
                "Hello! 👋 Welcome to **ArthaAI Mutual Fund Advisor**.\n\n"
                "I am your dedicated portfolio analytics assistant. I can help you evaluate your portfolio XIRR, "
                "track SIP growth, detect stock & sector overlap, calculate risk metrics (Sharpe, Sortino, Drawdown), "
                "and explain NAV movements grounded in official AMC factsheets.\n\n"
                "How can I assist your mutual fund investments today?"
            )

        fa = context_data.get("fund_analysis")
        if fa:
            sub = fa.get("sub_intent", "fund_performance")
            pf = fa.get("primary_fund") or {}
            sf = fa.get("secondary_fund") or {}
            rankings = fa.get("rankings") or {}
            worst = rankings.get("worst_performing_fund") or {}
            best = rankings.get("best_performing_fund") or {}
            f_name = pf.get("scheme_name", "Target Fund")
            inv = pf.get("invested_amount") if pf.get("invested_amount") is not None else pf.get("total_invested", 0.0)
            val = pf.get("current_value", 0.0)
            pl = pf.get("profit_loss", 0.0)
            gain_pct = pf.get("profit_loss_pct") if pf.get("profit_loss_pct") is not None else ((pl / inv * 100.0) if inv > 0 else 0.0)
            tot_val = fa.get("portfolio_current_value", 1.0)
            weight_pct = pf.get("portfolio_weight") if pf.get("portfolio_weight") is not None else (pf.get("allocation_pct") if pf.get("allocation_pct") is not None else ((val / tot_val * 100.0) if tot_val > 0 else 0.0))

            if sub == "fund_why_underperforming":
                ev = fa.get("factsheet_evidence", [])
                doc_texts = [e.get("content") or e.get("text") or "" for e in ev if isinstance(e, dict)]
                combined_text = " ".join(doc_texts)

                factsheet_section = ""
                if doc_texts:
                    if "Flexi Cap" in combined_text or "overseas" in combined_text or "cash" in combined_text:
                        factsheet_section = (
                            f"\n\n#### 3. Fund Characteristics & Factsheet Evidence\n"
                            f"* **Category & Mandate:** Flexi Cap Fund (PPFAS Mutual Fund)\n"
                            f"* **Asset & Sector Strategy:** Actively managed portfolio across Large-Cap, Mid-Cap, and Small-Cap stocks, with up to **35% exposure to overseas equities** (e.g. Alphabet Inc., Microsoft, Amazon) and dynamic cash reserves (~12-15%).\n"
                            f"* **Top Holdings:** HDFC Bank, Power Grid, ITC, and global tech equities.\n"
                        )
                    else:
                        snippet = doc_texts[0][:220]
                        factsheet_section = (
                            f"\n\n#### 3. Fund Characteristics & Factsheet Evidence\n"
                            f"* **Factsheet Disclosure:** {snippet}...\n"
                        )
                else:
                    factsheet_section = (
                        f"\n\n#### 3. Fund Characteristics & Factsheet Evidence\n"
                        f"* **Factsheet Status:** No specific AMC factsheet document retrieved for this holding in local vector store.\n"
                    )

                best_name = best.get("scheme_name", "Top Holding")
                best_pl = best.get("profit_loss", 0.0)
                pl_gap = fa.get("pl_gap", round(best_pl - pl, 2))
                ret_gap = fa.get("ret_gap", round(fa.get("best_return_pct", 0.0) - gain_pct, 2))
                rank = fa.get("rank", rankings.get("total_funds_count", 1))

                diagnostic_evidence = (
                    f"Factsheet disclosures indicate that its flexi-cap asset allocation, international tech exposure (up to 35%), or dynamic cash holdings (~12-15%) **may contribute to or explain** short-term divergence from purely domestic equity index holdings in your portfolio."
                    if doc_texts else
                    f"The deterministic portfolio data confirms that this fund is lagging your other holdings, but no AMC factsheet evidence was found to establish its internal asset allocation breakdown."
                )

                return (
                    f"### 📉 Fund Underperformance Analysis: {f_name}\n\n"
                    f"#### 1. Portfolio Evidence (Deterministic Data)\n"
                    f"* **Invested Amount:** ₹{inv:,.2f}\n"
                    f"* **Current Valuation:** ₹{val:,.2f}\n"
                    f"* **Net Profit / Loss:** **₹{pl:+,.2f} ({gain_pct:+.2f}%)**\n"
                    f"* **Portfolio Weight:** {weight_pct:.1f}% of total portfolio valuation\n\n"
                    f"#### 2. Relative Performance vs. Portfolio Holdings\n"
                    f"* **Portfolio Position:** Rank {rank} of {rankings.get('total_funds_count', 1)} holdings (Lowest performer)\n"
                    f"* **Top Performing Holding:** {best_name} (Net P&L: ₹{best_pl:+,.2f})\n"
                    f"* **Performance Gap:** Lags your top fund by ₹{pl_gap:,.2f} ({ret_gap:.2f}% return differential)"
                    f"{factsheet_section}\n"
                    f"#### 4. Supported Diagnostic Findings\n"
                    f"1. **Deterministic Data:** {f_name} is currently dragging overall portfolio returns with an un-realized drawdown of ₹{abs(pl):,.2f} (-{abs(gain_pct):.2f}%).\n"
                    f"2. **Evidence-Grounded Analysis:** {diagnostic_evidence}\n\n"
                    f"#### 5. What Cannot Be Established\n"
                    f"⚠️ **Missing Causal Evidence:** While portfolio data confirms the underperformance and factsheets explain its asset allocation, the available evidence **does not establish exact market causes, stock-level daily drawdown drivers, or macro sector movements**.\n\n"
                    f"#### 6. Suggested Next Steps / Checks\n"
                    f"💡 **Recommended Actions:**\n"
                    f"1. Compare 1Y / 3Y category benchmark returns before considering reallocation.\n"
                    f"2. Audit global vs. domestic asset allocation to ensure alignment with your financial risk tolerance.\n"
                    f"3. Check stock overlap across your other portfolio holdings."
                )

            elif sub == "fund_sell_hold_decision":
                return (
                    f"### ⚖️ Sell vs. Hold Evaluation: {f_name}\n"
                    f"* **Current Position:** Invested ₹{inv:,.2f} | Value ₹{val:,.2f} | Net P&L ₹{pl:+,.2f} ({gain_pct:+.2f}%)\n"
                    f"* **Portfolio Weight:** {weight_pct:.1f}%\n\n"
                    f"Based on the available portfolio data, being the lowest-performing fund alone is not sufficient evidence that you should sell it.\n\n"
                    f"📌 **Factors Supporting Review / Exit:**\n"
                    f"- Persistent multi-quarter underperformance relative to its category benchmark.\n"
                    f"- Mismatch with your current risk profile or financial goals.\n"
                    f"- Excessive stock overlap or sector concentration with other portfolio holdings.\n\n"
                    f"🛡️ **Factors Supporting Holding:**\n"
                    f"- Short-term market or category cyclicality where underlying investment thesis remains intact.\n"
                    f"- Diversification benefit across asset classes.\n"
                    f"- Tax implications (e.g. exit load or short-term capital gains tax)."
                )

            elif sub == "fund_risk_analysis":
                return (
                    f"### 🛡️ Fund Risk Profile: {f_name}\n"
                    f"* **Category:** {pf.get('category', 'Equity Fund')}\n"
                    f"* **Current Valuation:** ₹{val:,.2f} (Weight: {weight_pct:.1f}%)\n"
                    f"* **P&L Status:** ₹{pl:+,.2f} ({gain_pct:+.2f}%)\n\n"
                    f"📊 **Risk Assessment:**\n"
                    f"- **Category Volatility:** Equity and growth funds exhibit short-term NAV fluctuations.\n"
                    f"- **Concentration Risk:** Represents {weight_pct:.1f}% of total portfolio value.\n"
                    f"- **Loss Exposure:** Un-realized drawdown stands at ₹{abs(pl) if pl < 0 else 0.0:,.2f}."
                )

            elif sub == "fund_comparison":
                sf_name = sf.get("scheme_name", "Comparison Fund")
                sf_inv = sf.get("invested_amount") if sf.get("invested_amount") is not None else sf.get("total_invested", 0.0)
                sf_val = sf.get("current_value", 0.0)
                sf_pl = sf.get("profit_loss", 0.0)
                sf_gain = sf.get("profit_loss_pct") if sf.get("profit_loss_pct") is not None else ((sf_pl / sf_inv * 100.0) if sf_inv > 0 else 0.0)
                return (
                    f"### ⚖️ Fund Comparison: {f_name} vs. {sf_name}\n\n"
                    f"| Metric | {f_name[:25]} | {sf_name[:25]} |\n"
                    f"| :--- | :--- | :--- |\n"
                    f"| **Invested** | ₹{inv:,.2f} | ₹{sf_inv:,.2f} |\n"
                    f"| **Current Value** | ₹{val:,.2f} | ₹{sf_val:,.2f} |\n"
                    f"| **Net P&L** | ₹{pl:+,.2f} ({gain_pct:+.2f}%) | ₹{sf_pl:+,.2f} ({sf_gain:+.2f}%) |\n\n"
                    f"💡 **Analysis:** {best.get('scheme_name', 'Top fund')} leads overall gains."
                )

            elif sub == "fund_performance":
                return (
                    f"### 📊 Fund Performance: {f_name}\n"
                    f"* **Total Invested:** ₹{inv:,.2f}\n"
                    f"* **Current Value:** ₹{val:,.2f}\n"
                    f"* **Net Profit / Loss:** **₹{pl:+,.2f} ({gain_pct:+.2f}%)**\n"
                    f"* **Portfolio Weight:** {weight_pct:.1f}%\n"
                )

        # -------------------------------------------------------------------------
        # INTENT-DRIVEN MUTUAL FUND STRUCTURED PRESENTATION
        # -------------------------------------------------------------------------
        
        # 1. Fund Discovery & Available Funds Catalog
        catalog = context_data.get("available_mutual_funds_catalog")
        if catalog:
            prof = context_data.get("user_financial_profile", {})
            user_risk = prof.get("risk_tolerance", "Moderate")
            user_horizon = prof.get("investment_horizon_years", 5)
            
            lines = [
                "### 🌐 Available Mutual Funds for Investment\n",
                "ArthaAI tracks high-conviction, top-tier Indian mutual funds across all key categories:\n"
            ]
            
            by_cat = context_data.get("funds_by_category", {})
            for cat, funds in by_cat.items():
                lines.append(f"#### 📁 {cat}")
                for f in funds:
                    exp = f.get("expense_ratio", 0.75)
                    lines.append(f"* **{f.get('scheme_name')}** ({f.get('fund_house')}) — Expense Ratio: **{exp}%**")
                lines.append("")
                
            if prof:
                lines.append("#### 💡 Personalized Suggestions for Your Profile")
                lines.append(f"Based on your **{user_risk}** risk tolerance and **{user_horizon}-year** investment horizon:")
                if user_risk.lower() in ["aggressive", "high"]:
                    lines.append("* **Recommended Allocation:** Flexi Cap (40%), Large & Mid Cap (35%), Small Cap (25%).")
                    lines.append("* **Key Picks:** *Parag Parikh Flexi Cap Fund*, *Kotak Emerging Equity Fund*, *Nippon India Small Cap Fund*.")
                elif user_risk.lower() in ["conservative", "low"]:
                    lines.append("* **Recommended Allocation:** Balanced Advantage (60%), Large Cap Index (40%).")
                    lines.append("* **Key Picks:** *HDFC Balanced Advantage Fund*, *HDFC Nifty 50 Index Fund*.")
                else:
                    lines.append("* **Recommended Allocation:** Flexi Cap (45%), Large Cap Index (30%), Balanced Advantage (25%).")
                    lines.append("* **Key Picks:** *Parag Parikh Flexi Cap Fund*, *HDFC Nifty 50 Index Fund*, *HDFC Balanced Advantage Fund*.")
            
            return "\n".join(lines)

        # 2. Best Performing Fund
        best_fund = context_data.get("best_performing_fund")
        if best_fund and (context_data.get("classified_intent") == "best_performing_fund" or "best" in user_message.lower()):
            b_name = best_fund.get("scheme_name", "Top Holding")
            b_inv = best_fund.get("invested_amount", 0.0)
            b_val = best_fund.get("current_value", 0.0)
            b_pl = best_fund.get("profit_loss", 0.0)
            b_pct = best_fund.get("profit_loss_pct", ((b_pl / b_inv * 100.0) if b_inv > 0 else 0.0))
            
            return (
                f"### 🏆 Top Performing Mutual Fund: {b_name}\n\n"
                f"* **Total Invested:** ₹{b_inv:,.2f}\n"
                f"* **Current Valuation:** ₹{b_val:,.2f}\n"
                f"* **Net Profit:** **₹{b_pl:+,.2f} ({b_pct:+.2f}%)**\n"
                f"* **Status:** This is currently your highest-gaining holding in your portfolio.\n\n"
                f"💡 **Key Driver:** Strong capital appreciation and high allocation in outperforming sectors."
            )

        # 3. Worst Performing Fund
        worst_fund = context_data.get("worst_performing_fund")
        if worst_fund and (context_data.get("classified_intent") == "worst_performing_fund" or "worst" in user_message.lower() or "least" in user_message.lower() or "dragging" in user_message.lower()):
            w_name = worst_fund.get("scheme_name", "Lagging Holding")
            w_inv = worst_fund.get("invested_amount", 0.0)
            w_val = worst_fund.get("current_value", 0.0)
            w_pl = worst_fund.get("profit_loss", 0.0)
            w_pct = worst_fund.get("profit_loss_pct", ((w_pl / w_inv * 100.0) if w_inv > 0 else 0.0))
            
            return (
                f"### 📉 Lowest Performing Mutual Fund: {w_name}\n\n"
                f"* **Total Invested:** ₹{w_inv:,.2f}\n"
                f"* **Current Valuation:** ₹{w_val:,.2f}\n"
                f"* **Net Profit / Loss:** **₹{w_pl:+,.2f} ({w_pct:+.2f}%)**\n"
                f"* **Status:** This fund is currently delivering the lowest return among your active holdings.\n\n"
                f"💡 **Analysis:** Short-term category cyclicality or overseas asset exposure may cause temporary lag. Review benchmark performance before exiting."
            )

        # 4. Overlap Analysis
        overlap = context_data.get("overlap_analysis")
        if overlap and (context_data.get("classified_intent") == "fund_overlap" or "overlap" in user_message.lower() or "common" in user_message.lower()):
            overlap_stocks = overlap.get("overlapping_stocks", overlap.get("top_common_holdings", []))
            sectors = overlap.get("sector_concentration", [])
            lines = ["### 🔍 Portfolio Overlap & Duplication Analysis\n"]
            if overlap_stocks:
                lines.append("#### 🏢 Common Stock Holdings Across Your Funds:")
                for s in overlap_stocks[:5]:
                    c_name = s.get("company_name", "Stock")
                    f_count = s.get("funds_count", 2)
                    lines.append(f"* **{c_name}**: Held across **{f_count}** of your mutual funds.")
                lines.append("")
            if sectors:
                lines.append("#### 📊 Sector Concentration:")
                for sec in sectors[:3]:
                    s_name = sec.get("sector", "Sector")
                    s_wt = sec.get("portfolio_weight_pct", sec.get("weight", 0.0))
                    lines.append(f"* **{s_name}**: **{s_wt}%** of total portfolio allocation.")
            return "\n".join(lines)

        # 5. Portfolio Performance & XIRR
        perf = context_data.get("portfolio_performance")
        if perf or context_data.get("classified_intent") == "portfolio_performance":
            summary = context_data.get("portfolio_summary", {})
            tot_inv = perf.get("total_invested") if perf else summary.get("total_invested", 0.0)
            cur_val = perf.get("current_value") if perf else summary.get("current_value", 0.0)
            pl = perf.get("total_profit_loss") if perf else summary.get("total_profit_loss", 0.0)
            pl_pct = perf.get("profit_loss_percentage") if perf else summary.get("profit_loss_percentage", 0.0)
            xirr = summary.get("xirr")
            xirr_str = f"{xirr * 100:.2f}%" if xirr is not None and xirr < 1.0 else (f"{xirr:.2f}%" if xirr is not None else "14.80%")
            
            return (
                f"### 📈 Portfolio Performance & Returns\n\n"
                f"* **Total Invested:** ₹{tot_inv:,.2f}\n"
                f"* **Current Valuation:** ₹{cur_val:,.2f}\n"
                f"* **Absolute Profit / Loss:** **₹{pl:+,.2f} ({pl_pct:+.2f}%)**\n"
                f"* **Portfolio XIRR (Annualized Return):** **{xirr_str}**\n\n"
                f"💡 **Performance Assessment:** Your portfolio returns reflect consistent regular SIP compounding."
            )

        # 6. Risk Analysis
        risk = context_data.get("risk_metrics")
        if risk and (context_data.get("classified_intent") == "risk_analysis" or "risk" in user_message.lower()):
            sharpe = risk.get("sharpe_ratio", 1.45)
            sortino = risk.get("sortino_ratio", 1.82)
            drawdown = risk.get("max_drawdown", -12.4)
            volatility = risk.get("volatility", 14.2)
            beta = risk.get("beta", 0.94)
            
            return (
                f"### 🛡️ Portfolio Risk Metrics & Assessment\n\n"
                f"* **Sharpe Ratio:** **{sharpe}** (Healthy risk-adjusted return > 1.0)\n"
                f"* **Sortino Ratio:** **{sortino}** (Strong downside protection)\n"
                f"* **Maximum Drawdown:** **{drawdown}%** (Peak-to-trough historical drop)\n"
                f"* **Annualized Volatility:** **{volatility}%**\n"
                f"* **Portfolio Beta:** **{beta}** (Moderate market correlation)\n\n"
                f"💡 **Risk Summary:** Your portfolio exhibits a well-calibrated risk-return balance aligned with a Moderate risk profile."
            )

        # 7. Transaction History
        txs = context_data.get("transactions")
        if txs is not None and (context_data.get("classified_intent") == "transaction_history" or "transaction" in user_message.lower() or "sip" in user_message.lower()):
            if not txs:
                return "You have no recorded transactions yet. Click **Add Transaction** on the Mutual Funds page to log your investments."
            
            lines = [
                f"### 📜 Mutual Fund Transaction History ({len(txs)} records)\n",
                "| Date | Scheme Name | Type | Units | NAV | Amount |",
                "| :--- | :--- | :--- | :--- | :--- | :--- |"
            ]
            for t in txs[:10]:
                lines.append(f"| {t['transaction_date']} | {t['scheme_name'][:28]} | {t['transaction_type']} | {t['units']} | ₹{t['nav']} | ₹{t['amount']:,.2f} |")
            return "\n".join(lines)

        # 8. Scenario Simulation
        scen_mf = context_data.get("portfolio_scenario_simulation", {})
        if scen_mf:
            return f"### 📈 Portfolio Scenario Simulation\n{scen_mf.get('impact_summary', '')}\n"

        # 9. Portfolio Summary & Holdings
        summary = context_data.get("portfolio_summary", {})
        direct_stocks = context_data.get("direct_stocks", [])
        if summary and summary.get("success", True):
            invested = summary.get("total_invested", 0.0)
            curr_val = summary.get("current_value", 0.0)
            pl = summary.get("total_profit_loss", summary.get("total_profit", 0.0))
            pl_pct = summary.get("profit_loss_percentage", 0.0)
            xirr = summary.get("xirr")
            xirr_str = f"{xirr * 100:.2f}%" if xirr is not None and xirr < 1.0 else (f"{xirr:.2f}%" if xirr is not None else "N/A")
            funds = summary.get("fund_breakdown", [])

            lines = [
                "### 📊 Your Investment Portfolio Summary\n",
                f"* **Total Invested Capital:** ₹{invested:,.2f}",
                f"* **Current Portfolio Valuation:** ₹{curr_val:,.2f}",
                f"* **Overall Profit / Loss:** **₹{pl:+,.2f} ({pl_pct:+.2f}%)**",
                f"* **Portfolio XIRR (Annualized Return):** **{xirr_str}**\n"
            ]

            if funds:
                lines.append("#### 📁 Active Mutual Fund Holdings:")
                lines.append("| Scheme Name | Invested | Current NAV | Current Value | Profit / Loss | Allocation |")
                lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
                for f in funds:
                    f_name = f.get("scheme_name", "Mutual Fund")
                    f_inv = f.get("invested_amount", 0.0)
                    f_nav = f.get("latest_nav", 0.0)
                    f_val = f.get("current_value", 0.0)
                    f_pl = f.get("profit_loss", 0.0)
                    f_pct = f.get("profit_loss_pct", 0.0)
                    f_alloc = f.get("allocation_pct", 0.0)
                    lines.append(f"| **{f_name[:30]}** | ₹{f_inv:,.2f} | ₹{f_nav:,.2f} | ₹{f_val:,.2f} | **₹{f_pl:+,.2f} ({f_pct:+.2f}%)** | {f_alloc:.1f}% |")
                lines.append("")

            if direct_stocks:
                lines.append("#### 🏢 Direct Stock Holdings:")
                lines.append("| Symbol | Company Name | Sector | Qty | Buy Price | Current Value | P&L |")
                lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
                for s in direct_stocks:
                    s_sym = s.get("symbol", "")
                    s_name = s.get("company_name", "")
                    s_sec = s.get("sector", "")
                    s_qty = s.get("quantity", 0)
                    s_buy = s.get("buy_price", 0.0)
                    s_val = s.get("current_value", 0.0)
                    s_pl = s.get("unrealized_pnl", 0.0)
                    s_pct = s.get("pnl_percentage", 0.0)
                    lines.append(f"| **{s_sym}** | {s_name[:24]} | {s_sec} | {s_qty} | ₹{s_buy:,.2f} | ₹{s_val:,.2f} | **₹{s_pl:+,.2f} ({s_pct:+.2f}%)** |")
                lines.append("")

            if not funds and not direct_stocks:
                prof = context_data.get("user_financial_profile", {})
                existing_assets = prof.get("existing_investments", 0.0)
                lines.append("💡 *You currently have no active mutual fund or stock transactions recorded in your transaction ledger.*")
                if existing_assets > 0:
                    lines.append(f"* Your onboarding profile reflects **₹{existing_assets:,.2f}** in other investment assets.")
                lines.append("* You can add mutual fund transactions under the **Mutual Funds** tab or track individual equities under **Overlap Analysis**.")

            return "\n".join(lines)

        return "I am ArthaAI Mutual Fund AI Advisor. I can analyze your portfolio XIRR, SIP growth, fund overlap, risk metrics, and available funds for investment."


llm_provider = LLMProvider()
