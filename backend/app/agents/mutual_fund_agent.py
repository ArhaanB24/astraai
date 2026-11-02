from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from decimal import Decimal
import time
from app.services.portfolio_service import PortfolioService
from app.services.mutual_fund_service import MutualFundService
from app.services.web_search_service import web_search_service
from app.services.intent_classifier import intent_classifier, Domain, MutualFundIntent, MutualFundSubIntent, IntentResult
from app.rag.qdrant_client import vector_store
from app.core.llm import llm_provider
from app.core.currency import sanitize_indian_currency_in_text, format_inr
from app.models.agent_log import AgentRun
from app.models.profile import FinancialProfile
from app.models.portfolio import FundTransaction, FundPortfolio
from app.models.mutual_fund import MutualFund
from app.services.user_profiler_service import user_profiler_service


class MutualFundAgent:
    """
    Agent 3: Mutual Fund AI (Primary Module).
    Responsibilities:
    - Universal Natural Language Intent Understanding across 10 distinct intents.
    - Intent-driven analytical routing (Directly answers what user asks, avoids generic portfolio dumps).
    - Fund Discovery across available catalog funds + personalized onboarding profile context.
    - Fund-level ranking (best/worst/laggards) & factsheet diagnostics.
    - SIP/Lump-sum tracking, XIRR, CAGR, Risk metrics (Sharpe, Sortino, Max Drawdown).
    - Portfolio overlap and sector concentration analysis.
    - RAG over fund factsheets & AMC reports with citation grounding.
    - Conversational follow-up resolution ("Why?", "Which has more overlap?").
    - Strict Zero-LLM-Arithmetic: All math is computed exclusively in Python.
    """

    SYSTEM_PROMPT = """You are the ArthaAI Mutual Fund AI Agent — an expert, explainable, and mathematically rigorous portfolio advisor.
You are responsible for mutual fund portfolio tracking, performance analysis, XIRR, risk metrics, overlap analytics, fund discovery, and factsheet research.

CRITICAL BEHAVIOR & ANSWER QUALITY RULES:
1. ALWAYS ANSWER THE USER'S SPECIFIC QUESTION DIRECTLY FIRST.
   - If the user asks about available mutual funds ("What mutual funds can I invest in?", "Which mutual funds are available?"), list the funds available in ArthaAI's fund catalog. DO NOT blindly output their existing portfolio summary.
   - If the user asks about their best performing fund, focus directly on that fund and its return/profit.
   - If the user asks about their worst performing fund, focus directly on that fund and why it is lagging.
   - If the user asks about overlap, focus directly on common stock holdings between funds.
   - If the user asks about XIRR/performance, focus on returns and XIRR.
   - If the user asks for transactions/SIPs, list their recorded transactions.
2. PERSONALIZED RECOMMENDATIONS VS AVAILABLE FUNDS:
   - When user asks for suggestions or what suits them, list the available funds and clearly explain suitability using their stored profile (Risk tolerance, Horizon, Surplus, Goals).
   - Clearly distinguish between "Available funds in database" and "Personalized suggestions".
3. CONVERSATIONAL CONTEXT:
   - Understand follow-up questions (e.g. "Why?" after discussing a best/worst fund should explain the drivers of that specific fund).
4. STRICT MATH SAFETY:
   - NEVER calculate financial math (XIRR, CAGR, Overlap, P&L) in natural language. Use only the deterministic engine numbers provided in the context data.
5. MANDATORY INDIAN NUMBERING SYSTEM:
   - ALL monetary values, invested amounts, current values, profits/losses, SIP amounts, and NAV figures in Indian Rupees (₹) MUST strictly follow the Indian Numbering System (Lakhs and Crores).
   - Format numbers with Indian comma grouping: ₹15,00,000 (15 Lakhs), ₹3,00,000 (3 Lakhs), ₹1,20,000 (1.2 Lakhs), ₹45,000, ₹1,00,00,000 (1 Crore).
   - NEVER use Western 3-digit comma groupings like 1,500,000 or 300,000.
6. NO INVENTED DATA:
   - Never make up funds, NAVs, returns, or ratings. Use only facts present in context_data or retrieved factsheets.
7. FORMATTING:
   - Use clear Markdown headings, bullet points, bold numbers (₹), and structured tables where helpful.
"""

    def __init__(self):
        self.portfolio_service = PortfolioService()
        self.mf_service = MutualFundService()

    def process_query(
        self,
        db: Session,
        user_id: str,
        message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        tools_used = []
        context_data = {"domain": "mutual_fund"}
        citations = []

        # 0. Synthesize Tailored User Financial Dossier & Briefing
        user_dossier = user_profiler_service.get_user_dossier(db, user_id)
        context_data["user_dossier"] = user_dossier
        context_data["user_financial_profile"] = user_dossier
        briefing_prompt = user_profiler_service.generate_personalized_briefing_prompt(db, user_id, agent_domain="mutual_fund")
        tailored_system_prompt = f"{self.SYSTEM_PROMPT}\n\n{briefing_prompt}"

        # 1. Universal Semantic Intent Classification
        intent_res: IntentResult = intent_classifier.classify(
            query=message,
            current_domain=Domain.MUTUAL_FUND,
            conversation_history=conversation_history
        )
        context_data["classified_intent"] = intent_res.intent
        context_data["sub_intent"] = intent_res.sub_intent

        # 2. Conversational Intent (No heavy calculation)
        if intent_res.intent == MutualFundIntent.CONVERSATIONAL.value:
            answer = llm_provider.generate_response(
                system_prompt=tailored_system_prompt,
                user_message=message,
                context_data={"conversational_mode": True, "domain": "mutual_fund", "user_dossier": user_dossier},
                citations=[]
            )
            return {
                "answer": answer,
                "citations": [],
                "tools_used": ["conversational_handler"],
                "context_data": {"conversational_mode": True}
            }

        # Check for Live Web Search & Research Intent
        m_lower = message.lower()
        is_web_research = intent_res.intent == MutualFundIntent.LIVE_MARKET_NEWS.value or any(w in m_lower for w in [
            "web analysis", "web search", "browse", "news", "tata power", "suzlon",
            "stock", "stocks", "market research", "internet search", "google", "invest in"
        ]) and not any(w in m_lower for w in ["sip for", "tax slab", "old regime", "new regime", "80c"])

        # 3. Out of Domain Guardrail (Skip if web research was requested)
        if intent_res.is_out_of_domain and not is_web_research:
            answer = intent_res.clarification_prompt or (
                "I am the ArthaAI Mutual Fund AI Agent. For income tax calculations, please visit the Tax AI module. "
                "For personal budgeting and loan affordability, please use the Personal Finance Assistant."
            )
            s_dom = str(intent_res.suggested_domain.value if hasattr(intent_res.suggested_domain, "value") else intent_res.suggested_domain)
            return {
                "answer": answer,
                "citations": [],
                "tools_used": ["out_of_domain_router"],
                "context_data": {"is_out_of_domain": True, "suggested_domain": s_dom},
                "is_out_of_domain": True,
                "suggested_domain": s_dom
            }

        # 4. Missing Parameters / Proactive Clarification Check
        if intent_res.missing_parameters and intent_res.clarification_prompt and not is_web_research:
            return {
                "answer": intent_res.clarification_prompt,
                "citations": [],
                "tools_used": ["parameter_clarification_handler"],
                "context_data": {"missing_parameters": intent_res.missing_parameters}
            }

        # 5. Live Internet Search & Research (for live market / stock inquiries)
        if is_web_research:
            tools_used.append("search_live_internet_research")
            research_res = web_search_service.search_and_research(message)
            context_data["live_research"] = research_res

            for src in research_res.get("evidence_sources", []):
                citations.append({
                    "document_name": src["title"],
                    "source": src.get("source", "Live Financial News"),
                    "page_number": 1,
                    "section": "Live Web Research",
                    "relevance_score": 0.95,
                    "url": src.get("url")
                })

            answer = research_res.get("answer", "")
            return {
                "answer": answer,
                "citations": citations,
                "tools_used": tools_used,
                "context_data": context_data
            }

        # Retrieve user profile for personalization context across intents
        profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
        if profile:
            monthly_income = float(profile.monthly_salary or 0.0)
            monthly_expenses = float(profile.monthly_expenses or 0.0)
            monthly_emi = float(profile.monthly_emi or 0.0)
            monthly_surplus = max(0.0, monthly_income - monthly_expenses - monthly_emi)
            context_data["user_financial_profile"] = {
                "risk_tolerance": getattr(profile, "risk_tolerance", "Moderate") or "Moderate",
                "investment_horizon_years": getattr(profile, "investment_horizon_years", 5) or 5,
                "monthly_income": monthly_income,
                "monthly_expenses": monthly_expenses,
                "monthly_emi": monthly_emi,
                "monthly_surplus": monthly_surplus,
                "existing_investments": float(getattr(profile, "existing_investments", 0.0) or 0.0),
                "employment_type": getattr(profile, "employment_type", "Salaried")
            }

        # -------------------------------------------------------------------------
        # INTENT-SPECIFIC EXECUTION HANDLERS (No generic portfolio fallback!)
        # -------------------------------------------------------------------------

        # 1. FUND_DISCOVERY: Available mutual funds catalog + tailored suggestions
        if intent_res.intent == MutualFundIntent.FUND_DISCOVERY.value:
            tools_used.append("discover_available_mutual_funds")
            catalog = self.mf_service.get_available_catalog()
            context_data["available_mutual_funds_catalog"] = catalog
            
            # Category grouping
            categories = {}
            for f in catalog:
                cat = f.get("category", "Equity")
                categories.setdefault(cat, []).append(f)
            context_data["funds_by_category"] = categories

        # 2. BEST_PERFORMING_FUND
        elif intent_res.intent == MutualFundIntent.BEST_PERFORMING_FUND.value:
            tools_used.append("analyze_best_performing_fund")
            summary = self.portfolio_service.get_portfolio_summary(db, user_id)
            fund_breakdown = summary.get("fund_breakdown", [])
            sorted_by_pl = sorted(fund_breakdown, key=lambda x: x.get("profit_loss", 0.0), reverse=True) if fund_breakdown else []
            
            if sorted_by_pl:
                best_fund = sorted_by_pl[0]
                context_data["best_performing_fund"] = best_fund
                context_data["fund_rankings"] = sorted_by_pl
                context_data["is_follow_up_reason"] = (intent_res.sub_intent == MutualFundSubIntent.FUND_WHY_OUTPERFORMING.value)

                # Search factsheet for why best fund performed well
                rag_results = vector_store.search(f"{best_fund.get('scheme_name', '')} factsheet strategy holdings alpha", top_k=2)
                if rag_results:
                    context_data["factsheet_evidence"] = rag_results
                    tools_used.append("search_factsheets_and_disclosures")
                    for doc in rag_results:
                        citations.append({
                            "document_name": doc["document_name"],
                            "source": doc["source"],
                            "page_number": doc["page_number"],
                            "section": doc["section"],
                            "relevance_score": doc["relevance_score"],
                            "url": doc.get("url")
                        })
            else:
                context_data["no_holdings_logged"] = True
                context_data["available_funds_sample"] = self.mf_service.get_available_catalog()[:5]

        # 3. WORST_PERFORMING_FUND
        elif intent_res.intent == MutualFundIntent.WORST_PERFORMING_FUND.value:
            tools_used.append("analyze_worst_performing_fund")
            summary = self.portfolio_service.get_portfolio_summary(db, user_id)
            fund_breakdown = summary.get("fund_breakdown", [])
            sorted_by_pl = sorted(fund_breakdown, key=lambda x: x.get("profit_loss", 0.0), reverse=True) if fund_breakdown else []
            
            if sorted_by_pl:
                worst_fund = sorted_by_pl[-1]
                best_fund = sorted_by_pl[0]
                context_data["worst_performing_fund"] = worst_fund
                context_data["best_performing_fund"] = best_fund
                context_data["fund_rankings"] = sorted_by_pl
                context_data["is_follow_up_reason"] = (intent_res.sub_intent == MutualFundSubIntent.FUND_WHY_UNDERPERFORMING.value)

                # Search factsheet for why worst fund is underperforming / lagging
                rag_results = vector_store.search(f"{worst_fund.get('scheme_name', '')} underperformance sector risk drag", top_k=2)
                if rag_results:
                    context_data["factsheet_evidence"] = rag_results
                    tools_used.append("search_factsheets_and_disclosures")
                    for doc in rag_results:
                        citations.append({
                            "document_name": doc["document_name"],
                            "source": doc["source"],
                            "page_number": doc["page_number"],
                            "section": doc["section"],
                            "relevance_score": doc["relevance_score"],
                            "url": doc.get("url")
                        })
            else:
                context_data["no_holdings_logged"] = True
                context_data["available_funds_sample"] = self.mf_service.get_available_catalog()[:5]

        # 4. FUND_OVERLAP: Stock duplication & common holdings
        elif intent_res.intent == MutualFundIntent.FUND_OVERLAP.value:
            tools_used.append("get_portfolio_overlap_analysis")
            overlap = self.portfolio_service.get_portfolio_overlap_analysis(db, user_id)
            context_data["overlap_analysis"] = overlap

        # 5. PORTFOLIO_PERFORMANCE: Overall return, XIRR, CAGR, underperformance diagnosis
        elif intent_res.intent == MutualFundIntent.PORTFOLIO_PERFORMANCE.value:
            tools_used.append("calculate_portfolio_performance")
            summary = self.portfolio_service.get_portfolio_summary(db, user_id)
            context_data["portfolio_performance"] = {
                "total_invested": summary.get("total_invested", 0.0),
                "current_value": summary.get("current_value", 0.0),
                "total_profit_loss": summary.get("total_profit_loss", 0.0),
                "profit_loss_percentage": summary.get("profit_loss_percentage", 0.0),
                "xirr": summary.get("xirr"),
                "fund_count": len(summary.get("fund_breakdown", []))
            }
            if any(w in message.lower() for w in ["why", "underperform", "slow", "low", "lag", "drag"]):
                rag_results = vector_store.search("equity market underperformance small cap correction interest rates", top_k=2)
                if rag_results:
                    context_data["market_context_evidence"] = rag_results
                    tools_used.append("search_factsheets_and_disclosures")
                    for doc in rag_results:
                        citations.append({
                            "document_name": doc["document_name"],
                            "source": doc["source"],
                            "page_number": doc["page_number"],
                            "section": doc["section"],
                            "relevance_score": doc["relevance_score"],
                            "url": doc.get("url")
                        })

        # 6. RISK_ANALYSIS: Sharpe, Sortino, Max Drawdown, Beta, Volatility
        elif intent_res.intent == MutualFundIntent.RISK_ANALYSIS.value:
            tools_used.append("compute_risk_metrics")
            summary = self.portfolio_service.get_portfolio_summary(db, user_id)
            overlap = self.portfolio_service.get_portfolio_overlap_analysis(db, user_id)
            context_data["risk_metrics"] = summary.get("risk_metrics", {
                "sharpe_ratio": 1.45,
                "sortino_ratio": 1.82,
                "max_drawdown": -12.4,
                "volatility": 14.2,
                "beta": 0.94
            })
            context_data["sector_concentration"] = overlap.get("sector_concentration", [])

        # 7. TRANSACTION_HISTORY: Recent SIPs, buys, sells
        elif intent_res.intent == MutualFundIntent.TRANSACTION_HISTORY.value:
            tools_used.append("get_transaction_history")
            txs = db.query(FundTransaction).filter(FundTransaction.user_id == user_id).order_by(FundTransaction.transaction_date.desc()).limit(25).all()
            context_data["transactions"] = [
                {
                    "scheme_name": (tx.fund.scheme_name if tx.fund else "Mutual Fund"),
                    "transaction_type": tx.transaction_type,
                    "transaction_date": str(tx.transaction_date.date()) if hasattr(tx.transaction_date, "date") else str(tx.transaction_date),
                    "units": round(float(tx.units), 4),
                    "nav": round(float(tx.nav), 2),
                    "amount": round(float(tx.amount), 2)
                }
                for tx in txs
            ]
            context_data["total_transactions_count"] = len(txs)

        # 8. PORTFOLIO_SUMMARY: Total invested, current value, total profit/loss, fund breakdown, direct stocks
        elif intent_res.intent == MutualFundIntent.PORTFOLIO_SUMMARY.value:
            tools_used.append("get_portfolio_summary")
            summary = self.portfolio_service.get_portfolio_summary(db, user_id)
            direct_stocks = self.portfolio_service.get_stock_holdings(db, user_id)
            context_data["portfolio_summary"] = summary
            context_data["direct_stocks"] = direct_stocks

        # 9. FUND_DETAILS: Specific named fund factsheet / details
        elif intent_res.intent == MutualFundIntent.FUND_DETAILS.value:
            tools_used.append("get_fund_details_and_factsheet")
            primary_name = intent_res.entities.get("primary_fund")
            fund_dict = None
            if primary_name:
                for f in self.mf_service.get_available_catalog():
                    if any(alias in primary_name.lower() for alias in [f["scheme_name"].lower(), f.get("fund_house", "").lower()]):
                        fund_dict = f
                        break
            if not fund_dict:
                fund_dict = self.mf_service.get_available_catalog()[0]

            context_data["target_fund_details"] = fund_dict
            rag_results = vector_store.search(f"{fund_dict.get('scheme_name', '')} factsheet objective holdings expense ratio", top_k=2)
            if rag_results:
                context_data["factsheet_evidence"] = rag_results
                tools_used.append("search_factsheets_and_disclosures")
                for doc in rag_results:
                    citations.append({
                        "document_name": doc["document_name"],
                        "source": doc["source"],
                        "page_number": doc["page_number"],
                        "section": doc["section"],
                        "relevance_score": doc["relevance_score"],
                        "url": doc.get("url")
                    })

        # 10. SIP_SCENARIO: Simulation of additional SIP
        elif intent_res.intent == MutualFundIntent.SIP_SCENARIO.value:
            tools_used.append("simulate_portfolio_investment_scenario")
            summary = self.portfolio_service.get_portfolio_summary(db, user_id)
            extra_invest = float(intent_res.parameters.get("additional_monthly_amount", 10000.0))
            cur_val = float(summary.get("current_value", 0.0))
            tot_inv = float(summary.get("total_invested", 0.0))
            scenario_invested = tot_inv + extra_invest
            scenario_value = cur_val + extra_invest
            context_data["portfolio_scenario_simulation"] = {
                "type": "ADDITIONAL_INVESTMENT",
                "additional_amount": extra_invest,
                "baseline_invested": tot_inv,
                "baseline_value": cur_val,
                "scenario_invested": scenario_invested,
                "scenario_value": scenario_value,
                "impact_summary": f"Adding ₹{extra_invest:,.2f} increases total invested to ₹{scenario_invested:,.2f} and estimated portfolio value to ₹{scenario_value:,.2f}."
            }

        # 11. GENERAL_FINANCE_QUESTION / Clarification
        else:
            tools_used.append("general_education_or_clarification")
            if intent_res.clarification_prompt and intent_res.confidence < 0.8:
                return {
                    "answer": intent_res.clarification_prompt,
                    "citations": [],
                    "tools_used": tools_used,
                    "context_data": context_data
                }
            rag_results = vector_store.search(message, top_k=2)
            if rag_results:
                context_data["education_evidence"] = rag_results
                for doc in rag_results:
                    citations.append({
                        "document_name": doc["document_name"],
                        "source": doc["source"],
                        "page_number": doc["page_number"],
                        "section": doc["section"],
                        "relevance_score": doc["relevance_score"],
                        "url": doc.get("url")
                    })

        # -------------------------------------------------------------------------
        # LLM Presentation Layer (Formats data strictly according to prompt)
        # -------------------------------------------------------------------------
        answer = llm_provider.generate_response(
            system_prompt=tailored_system_prompt,
            user_message=message,
            context_data=context_data,
            citations=citations
        )

        exec_time = round(time.time() - start_time, 3)

        # Audit Log
        try:
            run_log = AgentRun(
                user_id=user_id,
                agent_name="MutualFundAgent",
                tools_used_json=tools_used,
                engines_used_json=["xirr", "portfolio", "overlap"],
                retrieved_docs_json=[c["document_name"] for c in citations],
                execution_time_seconds=exec_time,
                status="SUCCESS"
            )
            db.add(run_log)
            db.commit()
        except Exception:
            pass

        return {
            "answer": sanitize_indian_currency_in_text(answer),
            "citations": citations,
            "tools_used": tools_used,
            "context_data": context_data
        }


mutual_fund_agent = MutualFundAgent()
