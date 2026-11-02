import time
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.engines.tax import calculate_income_tax, compare_tax_regimes, TaxRegime, FinancialYear
from app.services.scenario_extractor import scenario_extractor, apply_salary_scenario, ScenarioType, ScenarioExtractionResult, ChangeType
from app.services.intent_classifier import intent_classifier, Domain, TaxIntent, IntentResult
from app.rag.qdrant_client import VectorStoreService
from app.core.llm import llm_provider
from app.core.currency import sanitize_indian_currency_in_text, format_inr
from app.models.agent_log import AgentRun
from app.services.user_profiler_service import user_profiler_service


class TaxAgent:
    """
    Agent 2: Tax AI Advisor.
    Responsibilities:
    - Analyzes user tax liabilities across Old and New Regimes (Section 115BAC).
    - Universal Natural Language Intent Understanding across statutory sections, rebates, and scenarios.
    - Extracts natural-language scenario parameters (e.g. +1 Lakh, +5 Lakhs, +20%, -10%).
    - Executes 100% deterministic Python tax calculations using Decimal arithmetic.
    - Calculates exact baseline vs scenario tax liabilities and deltas in Python.
    - RAG retrieval over statutory Income Tax Act rules (80C, 80D, 87A, Standard Deduction).
    - Communicates clear, structured, formatted explanations via LLM presentation layer.
    
    ZERO-LLM-ARITHMETIC RULE:
    - Gemini NEVER calculates tax amounts, deductions, slabs, deltas, or savings.
    - Gemini strictly presents the pre-computed Decimal values produced by tax.py and scenario_extractor.py.
    """

    SYSTEM_PROMPT = """You are the ArthaAI Tax AI Assistant. You are responsible only for Indian income-tax analysis, tax calculations, tax scenarios, deductions, tax regimes, rebates, cess, and related statutory explanations.

CRITICAL IDENTITY & SAFETY RULES:
1. You are strictly the ArthaAI Tax AI Assistant. You must NEVER identify as the Mutual Fund Advisor or Personal Finance Advisor, and you must never pretend to be another ArthaAI agent.
2. You are strictly a communication and response presentation layer.
3. NEVER calculate, alter, or fabricate financial/tax math in natural language.
4. Every single tax amount, taxable income figure, rebate, cess, delta, and savings figure in your reply MUST come directly from the DETERMINISTIC CONTEXT provided to you.
5. MANDATORY INDIAN NUMBERING SYSTEM:
   - ALL monetary values, gross salaries, deductions, taxable incomes, tax amounts, rebates, cess, and savings in Indian Rupees (₹) MUST strictly follow the Indian Numbering System (Lakhs and Crores).
   - Format numbers with Indian comma grouping: ₹15,00,000 (15 Lakhs), ₹3,00,000 (3 Lakhs), ₹1,20,000 (1.2 Lakhs), ₹50,000, ₹75,000, ₹1,50,000.
   - NEVER use Western 3-digit comma groupings like 1,500,000 or 300,000.
6. When presenting a hypothetical scenario (e.g. salary increase of ₹5 Lakhs or 20% raise):
   - Explicitly display the **Baseline Annual Salary**, **Salary Modification Applied**, and **Scenario Annual Salary**.
   - Show the **Baseline Tax Liability** vs. **Scenario Tax Liability** for both Old and New Regimes.
   - Highlight the **Exact Additional Tax Liability (Delta)** computed by the engine.
   - Highlight the recommended regime and tax savings.
7. Ground your explanations with the provided CITATIONS (Document Name, Section, Source).
8. For casual greetings or conversational non-tax questions (e.g., "hello", "who are you", "what can you do", "thanks"), respond politely and conversationally as the Tax AI Assistant without generating calculations.
9. Format your answers clearly using Markdown headings, bold numerical figures, and clean bullet points. Include the educational disclaimer when giving calculations.
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
        context_data = {"domain": "tax"}
        citations = []

        # 0. Synthesize Tailored User Financial Dossier & Briefing
        user_dossier = user_profiler_service.get_user_dossier(db, user_id)
        context_data["user_dossier"] = user_dossier
        briefing_prompt = user_profiler_service.generate_personalized_briefing_prompt(db, user_id, agent_domain="tax")
        tailored_system_prompt = f"{self.SYSTEM_PROMPT}\n\n{briefing_prompt}"

        # 1. Universal Semantic Intent Classification
        intent_res: IntentResult = intent_classifier.classify(
            query=query,
            current_domain=Domain.TAX,
            conversation_history=conversation_history
        )

        # 2. Conversational Intent Check (No heavy calculation)
        if intent_res.intent == TaxIntent.CONVERSATIONAL.value:
            answer = llm_provider.generate_response(
                system_prompt=tailored_system_prompt,
                user_message=query,
                context_data={"conversational_mode": True, "domain": "tax", "user_dossier": user_dossier},
                citations=[]
            )
            return {
                "session_id": "tax_agent_session",
                "answer": answer,
                "citations": [],
                "tools_used": ["conversational_handler"],
                "context_data": {"conversational_mode": True},
                "deterministic_tax_summary": None
            }

        # 3. Out of Domain Guardrail
        if intent_res.is_out_of_domain:
            answer = intent_res.clarification_prompt or (
                "I am the ArthaAI Tax AI Assistant. For personal budgeting and car loan affordability, please visit the Personal Finance Assistant. "
                "For mutual fund portfolio valuation, returns, and stock overlap analytics, please visit the Mutual Fund AI Assistant."
            )
            s_dom = str(intent_res.suggested_domain.value if hasattr(intent_res.suggested_domain, "value") else intent_res.suggested_domain)
            return {
                "session_id": "tax_agent_session",
                "answer": answer,
                "citations": [],
                "tools_used": ["out_of_domain_router"],
                "context_data": {"is_out_of_domain": True, "suggested_domain": s_dom},
                "is_out_of_domain": True,
                "suggested_domain": s_dom,
                "deterministic_tax_summary": None
            }

        # 4. Determine User Baseline Income from Profile or Query Parameter
        monthly_salary = profile_dict.get("monthly_salary", 120000.0)
        other_monthly = profile_dict.get("other_monthly_income", 0.0)
        annual_salary = float(monthly_salary) * 12.0
        annual_other = float(other_monthly) * 12.0
        age = profile_dict.get("age", 28)

        # Override baseline salary if explicitly stated in query (e.g. "if i earn 15 lakh per year how much tax do i pay")
        stated_sal = intent_res.parameters.get("stated_salary")
        if stated_sal and float(stated_sal) > 0:
            annual_salary = float(stated_sal)

        # Extract 80C from actual ELSS investments in user portfolio
        elss_80c = profile_dict.get("elss_investments_annual", 0.0)
        if elss_80c == 0.0:
            elss_80c = 150000.0 if profile_dict.get("existing_investments", 0.0) > 150000.0 else 50000.0

        # 5. Deterministic Baseline Regime Comparison (Authoritative Base)
        tools_used.append("compare_tax_regimes")
        baseline_comp = compare_tax_regimes(
            gross_salary=annual_salary,
            other_income=annual_other,
            deductions_80c=elss_80c,
            deductions_80d=25000.0,
            financial_year=FinancialYear.FY_2025_26,
            is_salaried=True,
            age=age
        )

        active_tax_summary = baseline_comp

        # 6. Intent-Specific Tool Orchestration

        # A. Tax Scenarios (Salary modifications)
        if intent_res.intent == TaxIntent.TAX_SCENARIO.value:
            extraction = scenario_extractor.extract_scenario(query)
            if not extraction.is_scenario:
                params = intent_res.parameters
                ch_type_str = params.get("change_type", "ABSOLUTE")
                if ch_type_str == "SET_VALUE":
                    ch_type = ChangeType.SET_VALUE
                elif ch_type_str == "PERCENTAGE":
                    ch_type = ChangeType.PERCENTAGE
                else:
                    ch_type = ChangeType.ABSOLUTE

                tgt_val = Decimal(str(params.get("target_value", 0.0))) if params.get("target_value") else None
                extraction = ScenarioExtractionResult(
                    is_scenario=True,
                    scenario_type=ScenarioType.SALARY_CHANGE,
                    change_type=ch_type,
                    change_amount=Decimal(str(params.get("change_amount") or params.get("salary_delta") or 0.0)),
                    change_percentage=Decimal(str(params.get("change_percentage", 0.0))),
                    target_value=tgt_val
                )

            # Apply Scenario Modification Deterministically in Python
            scenario_sal_dec, delta_sal_dec, delta_desc = apply_salary_scenario(
                Decimal(str(annual_salary)),
                extraction
            )
            scenario_annual_salary = float(scenario_sal_dec)

            tools_used.append("simulate_tax_scenario")
            scenario_comp = compare_tax_regimes(
                gross_salary=scenario_annual_salary,
                other_income=annual_other,
                deductions_80c=elss_80c,
                deductions_80d=25000.0,
                financial_year=FinancialYear.FY_2025_26,
                is_salaried=True,
                age=age
            )
            active_tax_summary = scenario_comp

            # Deterministic Python Differences & Deltas
            old_base_tax = baseline_comp["old_regime"]["total_tax_liability"]
            new_base_tax = baseline_comp["new_regime"]["total_tax_liability"]

            old_scen_tax = scenario_comp["old_regime"]["total_tax_liability"]
            new_scen_tax = scenario_comp["new_regime"]["total_tax_liability"]

            old_tax_delta = round(old_scen_tax - old_base_tax, 2)
            new_tax_delta = round(new_scen_tax - new_base_tax, 2)

            context_data["scenario_analysis"] = {
                "is_scenario": True,
                "baseline_annual_salary": annual_salary,
                "scenario_annual_salary": scenario_annual_salary,
                "salary_change_applied": delta_desc,
                "salary_delta_inr": float(delta_sal_dec),
                "baseline_tax_summary": {
                    "old_regime_tax": old_base_tax,
                    "new_regime_tax": new_base_tax,
                    "recommended_regime": baseline_comp["recommended_regime"],
                    "tax_savings": baseline_comp["tax_savings"]
                },
                "scenario_tax_summary": {
                    "old_regime_tax": old_scen_tax,
                    "new_regime_tax": new_scen_tax,
                    "recommended_regime": scenario_comp["recommended_regime"],
                    "tax_savings": scenario_comp["tax_savings"]
                },
                "tax_liability_changes": {
                    "old_regime_tax_delta": old_tax_delta,
                    "new_regime_tax_delta": new_tax_delta,
                    "recommended_regime": scenario_comp["recommended_regime"],
                    "scenario_tax_savings": scenario_comp["tax_savings"]
                }
            }
            context_data["tax_regime_comparison"] = scenario_comp
            active_tax_summary = scenario_comp
        else:
            context_data["scenario_analysis"] = {
                "is_scenario": False,
                "baseline_annual_salary": annual_salary,
                "scenario_annual_salary": annual_salary,
                "salary_change_applied": "None (Baseline Query)"
            }
            context_data["tax_regime_comparison"] = baseline_comp

        context_data["profile_income_baseline"] = {
            "annual_salary": annual_salary,
            "annual_other_income": annual_other,
            "total_gross_income": annual_salary + annual_other,
            "claimed_80c": elss_80c,
            "claimed_80d": 25000.0,
            "financial_year": "2025-26"
        }

        # 7. RAG Search over Statutory Tax Knowledge
        tools_used.append("search_tax_knowledge_and_disclosures")
        rag_docs = self.rag_service.search(f"Income Tax {query}", top_k=3)
        context_data["tax_rag_results"] = rag_docs
        for doc in rag_docs:
            citations.append({
                "document_name": doc.get("document_name", "Statutory Income Tax Framework"),
                "source": doc.get("source", "Income Tax Department of India"),
                "section": doc.get("section", "Tax Rules & Deductions"),
                "relevance_score": doc.get("relevance_score", 0.9),
                "url": doc.get("url")
            })

        # 8. LLM Presentation Synthesis (Gemini with Strict Presentation Guardrails)
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
                agent_name="TaxAgent",
                tools_used_json=tools_used,
                engines_used_json=["tax", "compare_tax_regimes"],
                retrieved_docs_json=[c["document_name"] for c in citations],
                execution_time_seconds=exec_time,
                status="SUCCESS"
            )
            db.add(run_log)
            db.commit()
        except Exception:
            pass

        return {
            "session_id": "tax_agent_session",
            "answer": sanitize_indian_currency_in_text(answer),
            "citations": citations,
            "tools_used": tools_used,
            "context_data": context_data,
            "deterministic_tax_summary": active_tax_summary
        }


tax_agent = TaxAgent()
