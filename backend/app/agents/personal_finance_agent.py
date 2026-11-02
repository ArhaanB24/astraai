import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.engines.personal_finance import calculate_financial_health, calculate_goal_required_sip
from app.engines.affordability import calculate_purchase_affordability
from app.engines.scenario_simulator import simulate_what_if_scenario
from app.services.intent_classifier import intent_classifier, Domain, PersonalFinanceIntent, IntentResult
from app.services.web_search_service import web_search_service
from app.rag.qdrant_client import VectorStoreService
from app.core.llm import llm_provider
from app.core.currency import sanitize_indian_currency_in_text, format_inr
from app.models.agent_log import AgentRun
from app.services.user_profiler_service import user_profiler_service


class PersonalFinanceAgent:
    """
    Agent 1: Personal Finance AI Agent.
    
    ARCHITECTURAL SEPARATION:
    - 100% Deterministic Python processing: All health ratios, 50/30/20 budgets, surplus,
      what-if deltas, goal PMT compounding, and affordability EMIs are calculated by Python engines.
    - LLM Presentation Layer: Google Gemini constructs natural language replies, understands
      conversational nuance, and presents the deterministic numbers cleanly without hallucinations.
    """

    SYSTEM_PROMPT = """You are the ArthaAI Personal Finance Assistant — an intelligent, friendly, and mathematically grounded financial advisor.
You are responsible for personal budgeting, financial health, what-if scenarios, goal planning, purchase affordability, and live financial web research.

CRITICAL IDENTITY & SAFETY RULES:
1. You are strictly the Personal Finance Assistant.
2. You are strictly a communication and response presentation layer.
3. DO NOT perform, invent, or modify any financial calculations, arithmetic, or numbers.
4. Every financial number, return percentage, EMI, surplus, net worth, score, and currency figure (₹) in your reply MUST come directly from the DETERMINISTIC CONTEXT.
5. MANDATORY INDIAN NUMBERING SYSTEM:
   - ALL monetary values, prices, salaries, expenses, EMIs, investments, and figures in Indian Rupees (₹) MUST strictly follow the Indian Numbering System (Lakhs and Crores).
   - Format numbers with Indian comma grouping: ₹15,00,000 (15 Lakhs), ₹3,00,000 (3 Lakhs), ₹1,20,000 (1.2 Lakhs), ₹45,000, ₹1,00,00,000 (1 Crore).
   - NEVER use Western 3-digit comma groupings like 1,500,000 or 300,000.
6. When the user asks for live web analysis, stock news, or company comparisons (e.g. "Tata Power vs Suzlon", "perform web analysis"):
   - Synthesize the provided LIVE WEB RESEARCH evidence into an objective, detailed comparative breakdown (business overview, renewable capacity/order book, financial health/debt profiles, catalysts, and risks).
   - Reference the provided web sources and citations.
   - Contextualize with their personal financial health status (e.g. reminding them to check their surplus, debt-to-income, and emergency fund buffer before risking capital).
7. Format your answers clearly using Markdown headings, bullet points, and bold numbers.
"""

    def __init__(self):
        self.rag_service = VectorStoreService()

    def process_query(
        self,
        db: Session,
        user_id: str,
        profile_dict: Dict[str, Any],
        query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        tools_used = []
        citations = []
        context_data = {"domain": "personal_finance"}

        # 0. Synthesize Tailored User Financial Dossier & Briefing
        user_dossier = user_profiler_service.get_user_dossier(db, user_id)
        context_data["user_dossier"] = user_dossier
        briefing_prompt = user_profiler_service.generate_personalized_briefing_prompt(db, user_id, agent_domain="personal_finance")
        tailored_system_prompt = f"{self.SYSTEM_PROMPT}\n\n{briefing_prompt}"

        # 1. Universal Semantic Intent Classification
        intent_res: IntentResult = intent_classifier.classify(
            query=query,
            current_domain=Domain.PERSONAL_FINANCE,
            conversation_history=conversation_history
        )

        # 2. Conversational Intent (No calculation needed)
        if intent_res.intent == PersonalFinanceIntent.CONVERSATIONAL.value:
            answer = llm_provider.generate_response(
                system_prompt=tailored_system_prompt,
                user_message=query,
                context_data={"conversational_mode": True, "domain": "personal_finance", "user_dossier": user_dossier},
                citations=[]
            )
            return {
                "session_id": "personal_finance_session",
                "answer": answer,
                "citations": [],
                "tools_used": ["conversational_handler"],
                "context_data": {"conversational_mode": True}
            }

        # Check for Live Web Search & Research Intent
        q_lower = query.lower()
        is_web_research = any(w in q_lower for w in [
            "web analysis", "web search", "browse", "news", "tata power", "suzlon",
            "stock", "stocks", "market research", "internet search", "google", "invest in"
        ]) and not any(w in q_lower for w in ["mutual fund", "sip for", "tax slab", "old regime", "new regime", "80c"])

        if is_web_research:
            tools_used.append("web_search_research_engine")
            web_res = web_search_service.search_and_research(query)
            context_data["web_research"] = web_res
            for src in web_res.get("evidence_sources", []):
                citations.append({
                    "document_name": src.get("title", "Live Financial News"),
                    "source": src.get("source", "Live Internet Search"),
                    "section": "Live Web Analysis",
                    "url": src.get("url", "")
                })

        # 3. Out of Domain Guardrail (Skip if web research was requested)
        if intent_res.is_out_of_domain and not is_web_research:
            answer = intent_res.clarification_prompt or (
                "I am the ArthaAI Personal Finance Assistant. For income tax questions, please visit the Tax AI module. "
                "For mutual fund portfolio returns and XIRR analytics, please visit the Mutual Fund AI Assistant."
            )
            s_dom = str(intent_res.suggested_domain.value if hasattr(intent_res.suggested_domain, "value") else intent_res.suggested_domain)
            return {
                "session_id": "personal_finance_session",
                "answer": answer,
                "citations": [],
                "tools_used": ["out_of_domain_router"],
                "context_data": {"is_out_of_domain": True, "suggested_domain": s_dom},
                "is_out_of_domain": True,
                "suggested_domain": s_dom
            }

        # 4. Missing Parameters Check
        if intent_res.missing_parameters and intent_res.clarification_prompt and not is_web_research:
            return {
                "session_id": "personal_finance_session",
                "answer": intent_res.clarification_prompt,
                "citations": [],
                "tools_used": ["parameter_clarification_handler"],
                "context_data": {"missing_parameters": intent_res.missing_parameters}
            }

        # 5. Deterministic Financial Health Base
        health_res = calculate_financial_health(profile_dict)
        context_data["financial_health"] = health_res
        tools_used.append("calculate_financial_health")

        # 6. Intent-Specific Tool Orchestration

        # A. Purchase Affordability (Car, House, Gadget)
        if intent_res.intent == PersonalFinanceIntent.AFFORDABILITY_CHECK.value:
            tools_used.append("calculate_purchase_affordability")
            params = intent_res.parameters
            v_name = params.get("vehicle_name") or params.get("check_online_vehicle") or "vehicle"
            is_online = bool(params.get("is_online_lookup", False))

            price = float(params.get("purchase_price") or 0.0)
            if price <= 0.0:
                # Discover price online using web search
                tools_used.append("web_search_research_engine")
                search_query = f"{v_name} on road price in India"
                web_results = web_search_service.search_internet(search_query, max_results=3)
                context_data["vehicle_market_research"] = {
                    "vehicle_name": v_name,
                    "search_query": search_query,
                    "results": web_results
                }
                for src in web_results:
                    citations.append({
                        "document_name": src.get("title", f"{v_name} Price in India"),
                        "source": src.get("source", "Live Market Search"),
                        "section": "Vehicle On-Road Price Discovery",
                        "url": src.get("url", "")
                    })

                # Estimated typical market price
                v_lower = str(v_name).lower()
                if "virtus" in v_lower:
                    price = 1500000.0  # Approx ₹15 Lakhs on-road average
                elif "slavia" in v_lower or "creta" in v_lower or "seltos" in v_lower:
                    price = 1600000.0
                elif "thar" in v_lower or "scorpio" in v_lower:
                    price = 1800000.0
                elif "nexon" in v_lower or "brezza" in v_lower:
                    price = 1200000.0
                elif "swift" in v_lower or "i20" in v_lower or "baleno" in v_lower:
                    price = 850000.0
                elif "activa" in v_lower or "jupiter" in v_lower:
                    price = 95000.0
                elif "bullet" in v_lower or "pulsar" in v_lower:
                    price = 190000.0
                else:
                    price = 1500000.0

            dp_supplied = bool(params.get("down_payment_supplied", False))
            down_payment = float(params.get("down_payment") if "down_payment" in params else (price * 0.20))
            interest_rate = float(params.get("interest_rate_pct") or 8.5)
            tenure_years = float(params.get("loan_tenure_years") or 5.0)
            vehicle_type = str(params.get("vehicle_type") or "vehicle")

            aff_res = calculate_purchase_affordability(
                purchase_price=price,
                down_payment=down_payment,
                loan_interest_rate_pct=interest_rate,
                loan_tenure_years=tenure_years,
                monthly_income=health_res["monthly_income"],
                monthly_expenses=health_res["monthly_expenses"],
                existing_emis=health_res["monthly_emis"],
                emergency_fund_balance=health_res["emergency_fund_balance"],
                monthly_sip=float(profile_dict.get("monthly_sip", 0.0))
            )
            aff_res["vehicle_type"] = vehicle_type
            aff_res["vehicle_name"] = v_name
            aff_res["down_payment_supplied"] = dp_supplied
            aff_res["is_online_price_discovery"] = is_online or (params.get("purchase_price") is None)
            context_data["affordability_analysis"] = aff_res

            # RAG retrieval for 20/4/10 car heuristic
            rag_docs = self.rag_service.search("20/4/10 auto purchase rule of thumb", top_k=2)
            for doc in rag_docs:
                citations.append({
                    "document_name": doc.get("document_name", "20/4/10 Auto Purchase Rule of Thumb"),
                    "source": doc.get("source", "ArthaAI Framework"),
                    "section": doc.get("section", "20/4/10 Auto Rule"),
                    "relevance_score": doc.get("relevance_score", 0.9),
                    "url": doc.get("url")
                })

        # B. What-If Scenarios (Salary, Expense, SIP, EMI)
        elif intent_res.intent == PersonalFinanceIntent.WHAT_IF_SCENARIO.value:
            tools_used.append("simulate_what_if_scenario")
            params = intent_res.parameters
            scen_type = params.get("scenario_type", "SALARY_CHANGE")
            change_type = params.get("change_type", "ABSOLUTE")
            sim_params: Dict[str, Any] = {}

            if scen_type == "SALARY_CHANGE":
                if change_type == "ABSOLUTE":
                    amt = float(params.get("change_amount", 100000.0))
                    sim_params["additional_annual_salary" if abs(amt) >= 50000 else "additional_monthly_salary"] = amt
                else:
                    sim_params["change_percentage"] = float(params.get("change_percentage", 20.0))
                scen_name = "SALARY_CHANGE"

            elif scen_type == "EXPENSE_CHANGE":
                if change_type == "ABSOLUTE":
                    sim_params["additional_monthly_expenses"] = float(params.get("change_amount", 10000.0))
                else:
                    sim_params["increase_percentage"] = float(params.get("change_percentage", 20.0))
                scen_name = "EXPENSE_INCREASE"

            elif scen_type == "SIP_CHANGE":
                sim_params["additional_monthly_sip"] = float(params.get("change_amount", 5000.0))
                scen_name = "INCREASE_SIP"

            elif scen_type == "EMI_CHANGE":
                sim_params["additional_monthly_emi"] = float(params.get("change_amount", 10000.0))
                scen_name = "TAKE_LOAN"
            else:
                scen_name = "SALARY_CHANGE"

            sim_res = simulate_what_if_scenario(
                baseline_profile=profile_dict,
                scenario_type=scen_name,
                scenario_params=sim_params
            )
            context_data["scenario_simulation"] = sim_res

        # C. Goal Planning & PMT SIP Compounding
        elif intent_res.intent == PersonalFinanceIntent.GOAL_PLANNING.value:
            tools_used.append("calculate_goal_required_sip")
            goals = profile_dict.get("goals", [])
            goal_entity = intent_res.entities.get("goal_name", "")

            matched_goal = None
            if goal_entity:
                for g in goals:
                    if goal_entity in g.get("name", "").lower():
                        matched_goal = g
                        break
            if not matched_goal and goals:
                matched_goal = goals[0]

            if matched_goal:
                req_sip = matched_goal.get("required_monthly_contribution")
                if req_sip is None or req_sip == 0:
                    pmt_res = calculate_goal_required_sip(
                        target_amount=matched_goal.get("target_amount", 0.0),
                        current_amount=matched_goal.get("current_amount", 0.0),
                        target_year=matched_goal.get("target_year", 2030),
                        expected_return_pct=matched_goal.get("expected_return_pct", 10.0)
                    )
                    req_sip = pmt_res["required_monthly_contribution"]

                context_data["goal_analysis"] = {
                    "goal_name": matched_goal.get("name"),
                    "target_amount": matched_goal.get("target_amount", 0.0),
                    "current_amount": matched_goal.get("current_amount", 0.0),
                    "target_year": matched_goal.get("target_year"),
                    "expected_return_pct": matched_goal.get("expected_return_pct"),
                    "required_monthly_contribution": req_sip
                }

        # D. Emergency Fund Analysis
        elif intent_res.intent == PersonalFinanceIntent.EMERGENCY_FUND.value:
            tools_used.append("search_financial_rules_and_disclosures")
            rag_docs = self.rag_service.search("Emergency Fund Coverage Guideline", top_k=2)
            context_data["emergency_fund_guidelines"] = rag_docs
            for doc in rag_docs:
                citations.append({
                    "document_name": doc.get("document_name", "Emergency Fund Coverage Guideline"),
                    "source": doc.get("source", "ArthaAI Framework"),
                    "section": doc.get("section", "Emergency Fund Coverage Guideline"),
                    "relevance_score": doc.get("relevance_score", 0.95),
                    "url": doc.get("url")
                })

        # E. General Financial Education
        elif intent_res.intent == PersonalFinanceIntent.GENERAL_EDUCATION.value:
            tools_used.append("search_financial_rules_and_disclosures")
            rag_docs = self.rag_service.search(query, top_k=2)
            for doc in rag_docs:
                citations.append({
                    "document_name": doc.get("document_name", "ArthaAI Financial Rules"),
                    "source": doc.get("source", "ArthaAI Framework"),
                    "section": doc.get("section", "Guidelines"),
                    "relevance_score": doc.get("relevance_score", 0.85),
                    "url": doc.get("url")
                })

        # 7. Synthesize Presentation via LLMProvider (Google Gemini)
        answer = llm_provider.generate_response(
            system_prompt=tailored_system_prompt,
            user_message=query,
            context_data=context_data,
            citations=citations
        )

        exec_time = round(time.time() - start_time, 3)

        # Audit Log
        try:
            run_log = AgentRun(
                user_id=user_id,
                agent_name="PersonalFinanceAgent",
                tools_used_json=tools_used,
                engines_used_json=["personal_finance", "affordability", "scenario_simulator"],
                retrieved_docs_json=[c["document_name"] for c in citations],
                execution_time_seconds=exec_time,
                status="SUCCESS"
            )
            db.add(run_log)
            db.commit()
        except Exception:
            pass

        return {
            "session_id": "personal_finance_session",
            "answer": sanitize_indian_currency_in_text(answer),
            "citations": citations,
            "tools_used": tools_used,
            "context_data": context_data
        }


personal_finance_agent = PersonalFinanceAgent()
