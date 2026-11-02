"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/AuthContext";
import { useRequireAuth } from "@/lib/useRequireAuth";
import {
  User,
  Calendar,
  IndianRupee,
  CreditCard,
  PiggyBank,
  Shield,
  Briefcase,
  Target,
  Clock,
  Coins,
  Compass,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Sparkles,
  TrendingUp,
  FileCheck,
  Building2,
  MapPin,
  Users,
  Activity,
  Umbrella,
  Percent,
  Check,
  ShieldCheck,
  AlertCircle
} from "lucide-react";

import { saveQuestionnaireApi } from "@/lib/api";

export default function OnboardingPage() {
  const router = useRouter();
  const { user, refreshUser } = useAuth();
  // Allow authenticated users to view onboarding even if onboarding_completed is false
  useRequireAuth({ requireOnboarding: false });

  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    // Step 1: Personal Demographics & Career
    full_name: "",
    age: 28,
    employment_type: "Salaried (Private / Tech)",
    city_tier: "Tier 1 Metro (Mumbai, Delhi-NCR, BLR, HYD, PNQ)",
    dependents: 1,

    // Step 2: Income & Cash Flow Dynamics
    monthly_salary: 125000,
    other_monthly_income: 15000,
    income_stability: "Very Stable (Fixed Monthly)",

    // Step 3: Expenses, Debt & Liabilities
    monthly_expenses: 45000,
    discretionary_expenses: 15000,
    monthly_emi: 15000,
    debt_types: ["Credit Card / BNPL"] as string[],

    // Step 4: Safety Net & Insurance Protection
    emergency_fund: 350000,
    target_emergency_months: 6,
    insurance_health: "Comprehensive (Both Corporate + Floater)",
    insurance_term: "Adequate (>10x Annual Income)",

    // Step 5: Existing Assets & Net Worth
    existing_investment_amount: 500000,
    existing_investments: ["Mutual Funds", "Fixed Deposits"] as string[],

    // Step 6: Risk Capacity & Behavioral Loss Tolerance
    market_drop_reaction: "Disciplined Compounder (Continue regular SIPs)",
    risk_tolerance: "Moderate",
    investment_experience: "Intermediate",

    // Step 7: Goals, Investment Horizon & SIP Commitment
    primary_goal: "Wealth Creation",
    investment_horizon: "5–10 Years",
    target_monthly_sip: 35000,

    // Step 8: Tax Planning & Strategic Preferences
    tax_regime: "New Tax Regime (Section 115BAC)",
    section_80c_status: "Partially Utilized (₹50k - ₹1L)",
    financial_preferences: "Disciplined growth with passive index funds and tax optimization."
  });

  useEffect(() => {
    if (user?.full_name && !formData.full_name) {
      setFormData((prev) => ({ ...prev, full_name: user.full_name }));
    }
  }, [user]);

  const totalSteps = 9; // 8 Detailed Modular Steps + 1 Comprehensive Review/Diagnostics Step

  // Dynamic Calculated Metrics
  const totalMonthlyInflow = (formData.monthly_salary || 0) + (formData.other_monthly_income || 0);
  const totalAnnualInflow = totalMonthlyInflow * 12;
  const totalMonthlyOutflow = (formData.monthly_expenses || 0) + (formData.discretionary_expenses || 0) + (formData.monthly_emi || 0);
  const monthlySurplus = Math.max(0, totalMonthlyInflow - totalMonthlyOutflow);
  const savingsRate = totalMonthlyInflow > 0 ? Math.round((monthlySurplus / totalMonthlyInflow) * 100) : 0;
  const dtiRatio = totalMonthlyInflow > 0 ? Number(((formData.monthly_emi / totalMonthlyInflow) * 100).toFixed(1)) : 0;
  const emergencyRunwayMonths = totalMonthlyOutflow > 0 ? Number((formData.emergency_fund / totalMonthlyOutflow).toFixed(1)) : 0;

  // Investor Persona Calibration
  const getInvestorPersona = () => {
    if (formData.risk_tolerance === "Aggressive") {
      return { title: "High-Growth Wealth Maximizer", badge: "Aggressive Equity", color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30" };
    }
    if (formData.risk_tolerance === "Moderate") {
      return { title: "Disciplined Balanced Compounder", badge: "Moderate Growth", color: "text-teal-400 bg-teal-500/10 border-teal-500/30" };
    }
    return { title: "Conservative Capital Preserver", badge: "Capital Protection", color: "text-blue-400 bg-blue-500/10 border-blue-500/30" };
  };

  const persona = getInvestorPersona();

  // Multi-select toggle helpers
  const handleToggleDebtType = (debt: string) => {
    setFormData((prev) => {
      let current = [...prev.debt_types];
      if (debt === "None (Debt-Free)") {
        return { ...prev, debt_types: ["None (Debt-Free)"], monthly_emi: 0 };
      }
      current = current.filter((d) => d !== "None (Debt-Free)");
      if (current.includes(debt)) {
        current = current.filter((d) => d !== debt);
      } else {
        current.push(debt);
      }
      if (current.length === 0) {
        current = ["None (Debt-Free)"];
      }
      return { ...prev, debt_types: current };
    });
  };

  const handleToggleInvestment = (inv: string) => {
    setFormData((prev) => {
      let current = [...prev.existing_investments];
      if (inv === "None (Starting Fresh)") {
        return { ...prev, existing_investments: ["None (Starting Fresh)"], existing_investment_amount: 0 };
      }
      current = current.filter((item) => item !== "None (Starting Fresh)");
      if (current.includes(inv)) {
        current = current.filter((item) => item !== inv);
      } else {
        current.push(inv);
      }
      if (current.length === 0) {
        current = ["None (Starting Fresh)"];
      }
      return { ...prev, existing_investments: current };
    });
  };

  const validateCurrentStep = () => {
    setError(null);
    if (step === 1) {
      if (!formData.full_name.trim()) {
        setError("Please enter your full legal name.");
        return false;
      }
      if (formData.age < 18 || formData.age > 100) {
        setError("Please specify a valid age between 18 and 100.");
        return false;
      }
    }
    if (step === 2) {
      if (formData.monthly_salary <= 0) {
        setError("Please enter your primary monthly take-home income.");
        return false;
      }
      if (formData.other_monthly_income < 0) {
        setError("Other income cannot be negative.");
        return false;
      }
    }
    if (step === 3) {
      if (formData.monthly_expenses <= 0) {
        setError("Please enter your estimated monthly core living expenses.");
        return false;
      }
      if (formData.discretionary_expenses < 0 || formData.monthly_emi < 0) {
        setError("Expense values cannot be negative.");
        return false;
      }
    }
    if (step === 4) {
      if (formData.emergency_fund < 0) {
        setError("Emergency reserve cannot be negative.");
        return false;
      }
    }
    if (step === 5) {
      if (formData.existing_investment_amount < 0) {
        setError("Current investment valuation cannot be negative.");
        return false;
      }
      if (formData.existing_investments.length === 0) {
        setError("Please select at least one asset class or 'None'.");
        return false;
      }
    }
    if (step === 7) {
      if (formData.target_monthly_sip < 0) {
        setError("Target monthly SIP cannot be negative.");
        return false;
      }
    }
    return true;
  };

  const handleNext = () => {
    if (!validateCurrentStep()) return;
    if (step < totalSteps) {
      setStep(step + 1);
    } else {
      handleComplete();
    }
  };

  const handleBack = () => {
    setError(null);
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const handleComplete = async () => {
    setSaving(true);
    setError(null);

    const existingInvestmentsStr = formData.existing_investments.join(", ");
    const debtTypesStr = formData.debt_types.join(", ");
    const totalExpenses = (formData.monthly_expenses || 0) + (formData.discretionary_expenses || 0);

    const submissionPayload = {
      full_name: formData.full_name,
      age: formData.age,
      employment_type: formData.employment_type,
      city_tier: formData.city_tier,
      dependents: formData.dependents,
      monthly_salary: formData.monthly_salary,
      other_monthly_income: formData.other_monthly_income,
      income_stability: formData.income_stability,
      monthly_expenses: totalExpenses,
      discretionary_expenses: formData.discretionary_expenses,
      monthly_emi: formData.monthly_emi,
      debt_types: debtTypesStr,
      emergency_fund: formData.emergency_fund,
      target_emergency_months: formData.target_emergency_months,
      insurance_health: formData.insurance_health,
      insurance_term: formData.insurance_term,
      existing_investment_amount: formData.existing_investment_amount,
      existing_investments: existingInvestmentsStr,
      market_drop_reaction: formData.market_drop_reaction,
      risk_tolerance: formData.risk_tolerance,
      investment_experience: formData.investment_experience,
      primary_goal: formData.primary_goal,
      investment_horizon: formData.investment_horizon,
      target_monthly_sip: formData.target_monthly_sip,
      tax_regime: formData.tax_regime,
      section_80c_status: formData.section_80c_status,
      financial_preferences: formData.financial_preferences,
      raw_responses: [
        { question_key: "full_name", answer: formData.full_name },
        { question_key: "age", answer: String(formData.age) },
        { question_key: "employment_type", answer: formData.employment_type },
        { question_key: "city_tier", answer: formData.city_tier },
        { question_key: "dependents", answer: String(formData.dependents) },
        { question_key: "monthly_salary", answer: String(formData.monthly_salary) },
        { question_key: "other_monthly_income", answer: String(formData.other_monthly_income) },
        { question_key: "income_stability", answer: formData.income_stability },
        { question_key: "monthly_expenses", answer: String(totalExpenses) },
        { question_key: "discretionary_expenses", answer: String(formData.discretionary_expenses) },
        { question_key: "monthly_emi", answer: String(formData.monthly_emi) },
        { question_key: "debt_types", answer: debtTypesStr },
        { question_key: "emergency_fund", answer: String(formData.emergency_fund) },
        { question_key: "target_emergency_months", answer: String(formData.target_emergency_months) },
        { question_key: "insurance_health", answer: formData.insurance_health },
        { question_key: "insurance_term", answer: formData.insurance_term },
        { question_key: "existing_investment_amount", answer: String(formData.existing_investment_amount) },
        { question_key: "existing_investments", answer: existingInvestmentsStr },
        { question_key: "market_drop_reaction", answer: formData.market_drop_reaction },
        { question_key: "risk_tolerance", answer: formData.risk_tolerance },
        { question_key: "investment_experience", answer: formData.investment_experience },
        { question_key: "primary_goal", answer: formData.primary_goal },
        { question_key: "investment_horizon", answer: formData.investment_horizon },
        { question_key: "target_monthly_sip", answer: String(formData.target_monthly_sip) },
        { question_key: "tax_regime", answer: formData.tax_regime },
        { question_key: "section_80c_status", answer: formData.section_80c_status },
        { question_key: "financial_preferences", answer: formData.financial_preferences }
      ]
    };

    try {
      await saveQuestionnaireApi(submissionPayload);

      // Refresh user profile so onboarding_completed is true
      if (refreshUser) {
        await refreshUser().catch(() => null);
      }

      // Update local storage user object immediately
      try {
        const savedUserStr = localStorage.getItem("arthaai_user");
        if (savedUserStr) {
          const parsedUser = JSON.parse(savedUserStr);
          parsedUser.onboarding_completed = true;
          parsedUser.full_name = formData.full_name;
          localStorage.setItem("arthaai_user", JSON.stringify(parsedUser));
        }
      } catch {}

      router.replace("/dashboard");
    } catch (e: any) {
      console.warn("Could not save questionnaire", e);
      let errMsg = e.message || "Failed to complete onboarding. Please try again.";
      if (errMsg === "Load failed" || errMsg.includes("fetch")) {
        errMsg = "Network communication error. Please check connection and retry.";
      }
      setError(errMsg);
    } finally {
      setSaving(false);
    }
  };

  const stepTitles = [
    "Personal Demographics & Career",
    "Income & Cash Flow Stability",
    "Living Expenses, Debt & Liabilities",
    "Safety Net & Insurance Protection",
    "Existing Assets & Net Worth",
    "Risk Capacity & Behavioral Tolerance",
    "Financial Goals, Horizon & SIP Budget",
    "Tax Planning & Strategic Preferences",
    "Comprehensive Profile Review & Diagnostics"
  ];

  const progress = Math.round(((step - 1) / (totalSteps - 1)) * 100);

  return (
    <div className="min-h-[90vh] flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-3xl bg-card border border-border rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6">
        {/* Progress Header */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="font-semibold text-emerald-400 flex items-center gap-1.5">
              <Sparkles className="w-4 h-4" /> Comprehensive Wealth Onboarding
            </span>
            <span className="font-medium text-gray-300">
              Module {step} of {totalSteps} ({progress}%)
            </span>
          </div>
          <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-400 transition-all duration-300 rounded-full"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="text-sm font-semibold text-gray-200">
            {stepTitles[step - 1]}
          </div>
        </div>

        {error && (
          <div className="p-3.5 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold rounded-2xl flex items-center gap-2 animate-in fade-in">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Modular Step Content */}
        <div className="min-h-[340px] flex flex-col justify-center">
          {/* STEP 1: Personal Demographics & Career */}
          {step === 1 && (
            <div className="space-y-5 animate-in fade-in duration-300">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Full Name */}
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5 text-emerald-400" /> Full Legal Name
                  </label>
                  <input
                    type="text"
                    autoFocus
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    placeholder="e.g. Priya Sharma"
                    className="w-full bg-gray-900 border border-border rounded-xl px-4 py-3 text-sm text-white focus:border-emerald-500 outline-none transition-colors"
                  />
                </div>

                {/* Age */}
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-gray-300 flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-emerald-400" /> Current Age
                    </span>
                    <span className="text-[11px] text-emerald-400/80">
                      {formData.age < 30 ? "Early Career Phase" : formData.age <= 45 ? "Peak Wealth Accumulation" : "Pre-Retirement Phase"}
                    </span>
                  </label>
                  <input
                    type="number"
                    min={18}
                    max={100}
                    value={formData.age}
                    onChange={(e) => setFormData({ ...formData, age: parseInt(e.target.value) || 25 })}
                    className="w-full bg-gray-900 border border-border rounded-xl px-4 py-3 text-sm text-white focus:border-emerald-500 outline-none transition-colors"
                  />
                </div>
              </div>

              {/* Employment Type */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                  <Briefcase className="w-3.5 h-3.5 text-emerald-400" /> Employment & Occupation
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                  {[
                    "Salaried (Private / Tech)",
                    "Salaried (PSU / Govt)",
                    "Self-Employed Professional",
                    "Business Owner",
                    "Freelancer / Creator",
                    "Retired / Homemaker"
                  ].map((emp) => (
                    <button
                      key={emp}
                      type="button"
                      onClick={() => setFormData({ ...formData, employment_type: emp })}
                      className={`p-3 rounded-xl border text-xs font-semibold text-left transition-all ${
                        formData.employment_type === emp
                          ? "bg-emerald-500/15 border-emerald-500 text-emerald-300 shadow-md ring-1 ring-emerald-500/40"
                          : "bg-gray-900 border-border text-gray-400 hover:border-gray-700 hover:text-gray-200"
                      }`}
                    >
                      {emp}
                    </button>
                  ))}
                </div>
              </div>

              {/* City Tier & Dependents */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-emerald-400" /> City of Residence
                  </label>
                  <select
                    value={formData.city_tier}
                    onChange={(e) => setFormData({ ...formData, city_tier: e.target.value })}
                    className="w-full bg-gray-900 border border-border rounded-xl px-3 py-3 text-xs text-white focus:border-emerald-500 outline-none"
                  >
                    <option value="Tier 1 Metro (Mumbai, Delhi-NCR, BLR, HYD, PNQ)">Tier 1 Metro (Mumbai, Delhi-NCR, BLR, HYD, PNQ)</option>
                    <option value="Tier 2 City (Ahmedabad, Jaipur, Chandigarh, Kochi)">Tier 2 City (Ahmedabad, Jaipur, Chandigarh, Kochi)</option>
                    <option value="Tier 3 / Emerging Town">Tier 3 / Emerging Town</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                    <Users className="w-3.5 h-3.5 text-emerald-400" /> Financial Dependents
                  </label>
                  <div className="grid grid-cols-5 gap-2">
                    {[0, 1, 2, 3, 4].map((dep) => (
                      <button
                        key={dep}
                        type="button"
                        onClick={() => setFormData({ ...formData, dependents: dep })}
                        className={`py-2.5 rounded-xl border text-xs font-bold transition-all text-center ${
                          formData.dependents === dep
                            ? "bg-emerald-500/15 border-emerald-500 text-emerald-300 shadow-md ring-1 ring-emerald-500/40"
                            : "bg-gray-900 border-border text-gray-400 hover:border-gray-700"
                        }`}
                      >
                        {dep === 4 ? "4+" : dep}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: Income & Cash Flow Stability */}
          {step === 2 && (
            <div className="space-y-5 animate-in fade-in duration-300">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Primary Salary */}
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                    <IndianRupee className="w-3.5 h-3.5 text-emerald-400" /> Primary Net Take-Home Salary (Monthly)
                  </label>
                  <div className="relative">
                    <span className="absolute left-3.5 top-3 text-gray-400 font-bold text-sm">₹</span>
                    <input
                      type="number"
                      autoFocus
                      step={5000}
                      value={formData.monthly_salary}
                      onChange={(e) => setFormData({ ...formData, monthly_salary: parseFloat(e.target.value) || 0 })}
                      className="w-full bg-gray-900 border border-border rounded-xl pl-8 pr-4 py-3 text-sm text-white focus:border-emerald-500 outline-none font-mono"
                    />
                  </div>
                  <span className="text-[11px] text-gray-400">Net credited cash flow to bank per month</span>
                </div>

                {/* Secondary Income */}
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                    <Coins className="w-3.5 h-3.5 text-emerald-400" /> Secondary / Other Monthly Inflow
                  </label>
                  <div className="relative">
                    <span className="absolute left-3.5 top-3 text-gray-400 font-bold text-sm">₹</span>
                    <input
                      type="number"
                      step={2000}
                      value={formData.other_monthly_income}
                      onChange={(e) => setFormData({ ...formData, other_monthly_income: parseFloat(e.target.value) || 0 })}
                      className="w-full bg-gray-900 border border-border rounded-xl pl-8 pr-4 py-3 text-sm text-white focus:border-emerald-500 outline-none font-mono"
                    />
                  </div>
                  <span className="text-[11px] text-gray-400">Rental, freelance, dividends, or consulting</span>
                </div>
              </div>

              {/* Income Stability */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-emerald-400" /> Cash Flow Predictability & Stability
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {[
                    { label: "Very Stable (Fixed Monthly)", desc: "Guaranteed monthly payroll / pension" },
                    { label: "Moderate (Base + Variable)", desc: "Performance bonus or sales incentives" },
                    { label: "Fluctuating / Seasonal", desc: "Contracting, consulting, or business" }
                  ].map((stab) => (
                    <button
                      key={stab.label}
                      type="button"
                      onClick={() => setFormData({ ...formData, income_stability: stab.label })}
                      className={`p-3.5 rounded-xl border text-left transition-all ${
                        formData.income_stability === stab.label
                          ? "bg-emerald-500/15 border-emerald-500 text-emerald-300 shadow-md ring-1 ring-emerald-500/40"
                          : "bg-gray-900 border-border text-gray-400 hover:border-gray-700"
                      }`}
                    >
                      <div className="font-bold text-xs">{stab.label}</div>
                      <div className="text-[10px] text-gray-400 mt-1">{stab.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Dynamic Inflow Banner */}
              <div className="p-4 bg-gray-900/90 border border-border rounded-2xl flex items-center justify-between text-xs">
                <div>
                  <span className="text-gray-400">Total Monthly Cash Inflow:</span>
                  <div className="text-emerald-400 font-bold text-base mt-0.5">
                    ₹{totalMonthlyInflow.toLocaleString("en-IN")}
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-gray-400">Gross Annual Inflow:</span>
                  <div className="text-white font-bold text-base mt-0.5">
                    ₹{totalAnnualInflow.toLocaleString("en-IN")}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: Living Expenses, Debt & Liabilities */}
          {step === 3 && (
            <div className="space-y-5 animate-in fade-in duration-300">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {/* Core Living Expenses */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-300 flex items-center gap-1">
                    <CreditCard className="w-3.5 h-3.5 text-rose-400" /> Core Living Expenses (₹)
                  </label>
                  <input
                    type="number"
                    autoFocus
                    step={2000}
                    value={formData.monthly_expenses}
                    onChange={(e) => setFormData({ ...formData, monthly_expenses: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-gray-900 border border-border rounded-xl px-3.5 py-2.5 text-xs text-white focus:border-emerald-500 outline-none font-mono"
                  />
                  <p className="text-[10px] text-gray-400">Rent, groceries, utilities, school</p>
                </div>

                {/* Discretionary Lifestyle Spending */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-300 flex items-center gap-1">
                    <Compass className="w-3.5 h-3.5 text-amber-400" /> Discretionary Spend (₹)
                  </label>
                  <input
                    type="number"
                    step={1000}
                    value={formData.discretionary_expenses}
                    onChange={(e) => setFormData({ ...formData, discretionary_expenses: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-gray-900 border border-border rounded-xl px-3.5 py-2.5 text-xs text-white focus:border-emerald-500 outline-none font-mono"
                  />
                  <p className="text-[10px] text-gray-400">Dining, shopping, travel, OTT</p>
                </div>

                {/* Monthly EMIs */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-300 flex items-center gap-1">
                    <TrendingUp className="w-3.5 h-3.5 text-orange-400" /> Total Monthly EMIs (₹)
                  </label>
                  <input
                    type="number"
                    step={1000}
                    value={formData.monthly_emi}
                    onChange={(e) => setFormData({ ...formData, monthly_emi: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-gray-900 border border-border rounded-xl px-3.5 py-2.5 text-xs text-white focus:border-emerald-500 outline-none font-mono"
                  />
                  <p className="text-[10px] text-gray-400">Home, car, personal loan service</p>
                </div>
              </div>

              {/* Debt Types Selection */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-300">Active Debt & Liabilities (Select all that apply)</label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {[
                    "Home Loan",
                    "Auto Loan",
                    "Education Loan",
                    "Personal Loan",
                    "Credit Card / BNPL",
                    "None (Debt-Free)"
                  ].map((debt) => {
                    const isSelected = formData.debt_types.includes(debt);
                    return (
                      <button
                        key={debt}
                        type="button"
                        onClick={() => handleToggleDebtType(debt)}
                        className={`p-2.5 rounded-xl border text-xs font-medium flex items-center justify-between transition-all ${
                          isSelected
                            ? "bg-emerald-500/15 border-emerald-500 text-emerald-300"
                            : "bg-gray-900 border-border text-gray-400 hover:border-gray-700"
                        }`}
                      >
                        <span>{debt}</span>
                        {isSelected && <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Live Cash Flow Diagnostics Bar */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-3.5 bg-gray-900 border border-border rounded-2xl text-xs">
                <div>
                  <span className="text-gray-400">Total Outflows:</span>
                  <div className="text-rose-400 font-bold mt-0.5">₹{totalMonthlyOutflow.toLocaleString("en-IN")}/mo</div>
                </div>
                <div>
                  <span className="text-gray-400">Net Savings Surplus:</span>
                  <div className="text-emerald-400 font-bold mt-0.5">
                    ₹{monthlySurplus.toLocaleString("en-IN")}/mo ({savingsRate}%)
                  </div>
                </div>
                <div className="col-span-2 sm:col-span-1">
                  <span className="text-gray-400">DTI Debt Ratio:</span>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="font-bold text-white">{dtiRatio}%</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                      dtiRatio <= 30 ? "bg-emerald-500/20 text-emerald-400" : dtiRatio <= 50 ? "bg-amber-500/20 text-amber-400" : "bg-rose-500/20 text-rose-400"
                    }`}>
                      {dtiRatio <= 30 ? "Safe" : dtiRatio <= 50 ? "Moderate" : "High Risk"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 4: Safety Net & Insurance Protection */}
          {step === 4 && (
            <div className="space-y-5 animate-in fade-in duration-300">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Emergency Fund Balance */}
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                    <PiggyBank className="w-3.5 h-3.5 text-teal-400" /> Liquid Emergency Reserves (₹)
                  </label>
                  <div className="relative">
                    <span className="absolute left-3.5 top-3 text-gray-400 font-bold text-sm">₹</span>
                    <input
                      type="number"
                      autoFocus
                      step={25000}
                      value={formData.emergency_fund}
                      onChange={(e) => setFormData({ ...formData, emergency_fund: parseFloat(e.target.value) || 0 })}
                      className="w-full bg-gray-900 border border-border rounded-xl pl-8 pr-4 py-3 text-sm text-white focus:border-emerald-500 outline-none font-mono"
                    />
                  </div>
                  <span className="text-[11px] text-teal-400/80">
                    Currently covers ~{emergencyRunwayMonths} months of living expenses
                  </span>
                </div>

                {/* Target Emergency Months */}
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-emerald-400" /> Desired Safety Runway
                  </label>
                  <div className="grid grid-cols-4 gap-2">
                    {[3, 6, 9, 12].map((m) => (
                      <button
                        key={m}
                        type="button"
                        onClick={() => setFormData({ ...formData, target_emergency_months: m })}
                        className={`py-3 rounded-xl border text-xs font-bold transition-all text-center ${
                          formData.target_emergency_months === m
                            ? "bg-emerald-500/15 border-emerald-500 text-emerald-300 ring-1 ring-emerald-500/40"
                            : "bg-gray-900 border-border text-gray-400 hover:border-gray-700"
                        }`}
                      >
                        {m} Mos
                      </button>
                    ))}
                  </div>
                  <span className="text-[11px] text-gray-400">Recommended standard: 6 months of fixed outflow</span>
                </div>
              </div>

              {/* Health Insurance */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Health Insurance Protection
                </label>
                <div className="grid grid-cols-2 gap-2.5">
                  {[
                    "Corporate Health Cover only",
                    "Independent Personal Floater (₹10L+)",
                    "Comprehensive (Both Corporate + Floater)",
                    "No Health Insurance Cover"
                  ].map((h) => (
                    <button
                      key={h}
                      type="button"
                      onClick={() => setFormData({ ...formData, insurance_health: h })}
                      className={`p-3 rounded-xl border text-xs font-semibold text-left transition-all ${
                        formData.insurance_health === h
                          ? "bg-emerald-500/15 border-emerald-500 text-emerald-300 ring-1 ring-emerald-500/40"
                          : "bg-gray-900 border-border text-gray-400 hover:border-gray-700"
                      }`}
                    >
                      {h}
                    </button>
                  ))}
                </div>
              </div>

              {/* Term Life Insurance */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                  <Umbrella className="w-3.5 h-3.5 text-emerald-400" /> Term Life Insurance Cover
                </label>
                <div className="grid grid-cols-3 gap-2.5">
                  {[
                    "Adequate (>10x Annual Income)",
                    "Partial Cover (<10x)",
                    "No Term Insurance"
                  ].map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setFormData({ ...formData, insurance_term: t })}
                      className={`p-3 rounded-xl border text-xs font-semibold text-left transition-all ${
                        formData.insurance_term === t
                          ? "bg-emerald-500/15 border-emerald-500 text-emerald-300 ring-1 ring-emerald-500/40"
                          : "bg-gray-900 border-border text-gray-400 hover:border-gray-700"
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* STEP 5: Existing Assets & Net Worth */}
          {step === 5 && (
            <div className="space-y-5 animate-in fade-in duration-300">
              {/* Existing Investment Amount */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-300 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Coins className="w-3.5 h-3.5 text-emerald-400" /> Total Current Portfolio Valuation (₹)
                  </span>
                  <span className="text-[11px] text-gray-400">Approximate liquid / marketable net worth</span>
                </label>
                <div className="relative">
                  <span className="absolute left-3.5 top-3 text-gray-400 font-bold text-sm">₹</span>
                  <input
                    type="number"
                    autoFocus
                    step={50000}
                    value={formData.existing_investment_amount}
                    onChange={(e) => setFormData({ ...formData, existing_investment_amount: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-gray-900 border border-border rounded-xl pl-8 pr-4 py-3 text-sm text-white focus:border-emerald-500 outline-none font-mono"
                  />
                </div>
              </div>

              {/* Asset Classes Held */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-300">
                  Asset Classes Currently Owned (Select all that apply)
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  {[
                    "Mutual Funds",
                    "Direct Stocks",
                    "Fixed Deposits",
                    "EPF / PPF / NPS",
                    "Real Estate",
                    "Gold / SGBs",
                    "Crypto / US Stocks",
                    "None (Starting Fresh)"
                  ].map((asset) => {
                    const isSelected = formData.existing_investments.includes(asset);
                    return (
                      <button
                        key={asset}
                        type="button"
                        onClick={() => handleToggleInvestment(asset)}
                        className={`p-3 rounded-xl border text-xs font-semibold text-left flex items-center justify-between transition-all ${
                          isSelected
                            ? "bg-emerald-500/15 border-emerald-500 text-emerald-300 ring-1 ring-emerald-500/40"
                            : "bg-gray-900 border-border text-gray-400 hover:border-gray-700"
                        }`}
                      >
                        <span>{asset}</span>
                        {isSelected && <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* STEP 6: Risk Capacity & Behavioral Tolerance */}
          {step === 6 && (
            <div className="space-y-5 animate-in fade-in duration-300">
              {/* Market Drawdown Reaction */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-emerald-400" /> Behavioral Reaction: Sudden 20% Market Drop
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {[
                    { label: "Panic & Sell", desc: "Liquidate holdings to prevent further losses" },
                    { label: "Cautious & Anxious", desc: "Pause SIPs and wait cautiously for market to recover" },
                    { label: "Disciplined Compounder", desc: "Stay calm, do nothing, and continue regular SIPs" },
                    { label: "Opportunistic Buyer", desc: "Deploy surplus capital aggressively at discounted valuations" }
                  ].map((rx) => (
                    <button
                      key={rx.label}
                      type="button"
                      onClick={() => setFormData({ ...formData, market_drop_reaction: rx.label })}
                      className={`p-3.5 rounded-xl border text-left transition-all ${
                        formData.market_drop_reaction === rx.label
                          ? "bg-emerald-500/15 border-emerald-500 text-emerald-300 ring-1 ring-emerald-500/40"
                          : "bg-gray-900 border-border text-gray-400 hover:border-gray-700"
                      }`}
                    >
                      <div className="font-bold text-xs">{rx.label}</div>
                      <div className="text-[11px] text-gray-400 mt-1">{rx.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Overall Risk Tolerance & Knowledge */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-emerald-400" /> Self-Assessed Risk Tolerance
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {["Conservative", "Moderate", "Aggressive"].map((r) => (
                      <button
                        key={r}
                        type="button"
                        onClick={() => setFormData({ ...formData, risk_tolerance: r })}
                        className={`py-3 rounded-xl border text-xs font-bold transition-all text-center ${
                          formData.risk_tolerance === r
                            ? "bg-emerald-500/15 border-emerald-500 text-emerald-300 ring-1 ring-emerald-500/40"
                            : "bg-gray-900 border-border text-gray-400 hover:border-gray-700"
                        }`}
                      >
                        {r}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                    <Briefcase className="w-3.5 h-3.5 text-emerald-400" /> Investment Experience
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {["Beginner", "Intermediate", "Advanced"].map((exp) => (
                      <button
                        key={exp}
                        type="button"
                        onClick={() => setFormData({ ...formData, investment_experience: exp })}
                        className={`py-3 rounded-xl border text-xs font-bold transition-all text-center ${
                          formData.investment_experience === exp
                            ? "bg-emerald-500/15 border-emerald-500 text-emerald-300 ring-1 ring-emerald-500/40"
                            : "bg-gray-900 border-border text-gray-400 hover:border-gray-700"
                        }`}
                      >
                        {exp}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 7: Goals, Investment Horizon & SIP Commitment */}
          {step === 7 && (
            <div className="space-y-5 animate-in fade-in duration-300">
              {/* Primary Milestone */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                  <Target className="w-3.5 h-3.5 text-emerald-400" /> Primary Financial Milestone
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                  {[
                    "Wealth Creation",
                    "FIRE / Independence",
                    "Purchasing a Home",
                    "Child's Higher Education",
                    "Retirement Nest Egg",
                    "Emergency Safety Net"
                  ].map((g) => (
                    <button
                      key={g}
                      type="button"
                      onClick={() => setFormData({ ...formData, primary_goal: g })}
                      className={`p-3 rounded-xl border text-xs font-semibold text-left transition-all ${
                        formData.primary_goal === g
                          ? "bg-emerald-500/15 border-emerald-500 text-emerald-300 ring-1 ring-emerald-500/40"
                          : "bg-gray-900 border-border text-gray-400 hover:border-gray-700"
                      }`}
                    >
                      {g}
                    </button>
                  ))}
                </div>
              </div>

              {/* Horizon & Monthly SIP */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-emerald-400" /> Target Investment Horizon
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {["1–3 Years", "3–5 Years", "5–10 Years", "10+ Years"].map((h) => (
                      <button
                        key={h}
                        type="button"
                        onClick={() => setFormData({ ...formData, investment_horizon: h })}
                        className={`py-2.5 rounded-xl border text-xs font-semibold transition-all text-center ${
                          formData.investment_horizon === h
                            ? "bg-emerald-500/15 border-emerald-500 text-emerald-300 ring-1 ring-emerald-500/40"
                            : "bg-gray-900 border-border text-gray-400 hover:border-gray-700"
                        }`}
                      >
                        {h}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                      <IndianRupee className="w-3.5 h-3.5 text-emerald-400" /> Target Monthly SIP (₹)
                    </label>
                    {monthlySurplus > 0 && (
                      <button
                        type="button"
                        onClick={() => setFormData({ ...formData, target_monthly_sip: Math.round(monthlySurplus * 0.5) })}
                        className="text-[10px] text-emerald-400 hover:underline font-medium"
                      >
                        Use 50% Surplus (₹{Math.round(monthlySurplus * 0.5).toLocaleString("en-IN")})
                      </button>
                    )}
                  </div>
                  <div className="relative">
                    <span className="absolute left-3.5 top-2.5 text-gray-400 font-bold text-sm">₹</span>
                    <input
                      type="number"
                      step={5000}
                      value={formData.target_monthly_sip}
                      onChange={(e) => setFormData({ ...formData, target_monthly_sip: parseFloat(e.target.value) || 0 })}
                      className="w-full bg-gray-900 border border-border rounded-xl pl-8 pr-4 py-2.5 text-xs text-white focus:border-emerald-500 outline-none font-mono"
                    />
                  </div>
                  <span className="text-[10px] text-gray-400">
                    Annual SIP commitment: ₹{(formData.target_monthly_sip * 12).toLocaleString("en-IN")}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* STEP 8: Tax Planning & Strategic Preferences */}
          {step === 8 && (
            <div className="space-y-5 animate-in fade-in duration-300">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Tax Regime */}
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                    <Percent className="w-3.5 h-3.5 text-emerald-400" /> Preferred Income Tax Framework
                  </label>
                  <div className="space-y-2">
                    {[
                      "New Tax Regime (Section 115BAC)",
                      "Old Tax Regime (With 80C/80D Deductions)",
                      "Let ArthaAI Optimize Regime"
                    ].map((reg) => (
                      <button
                        key={reg}
                        type="button"
                        onClick={() => setFormData({ ...formData, tax_regime: reg })}
                        className={`w-full p-2.5 rounded-xl border text-xs font-semibold text-left transition-all ${
                          formData.tax_regime === reg
                            ? "bg-emerald-500/15 border-emerald-500 text-emerald-300 ring-1 ring-emerald-500/40"
                            : "bg-gray-900 border-border text-gray-400 hover:border-gray-700"
                        }`}
                      >
                        {reg}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Section 80C Status */}
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Section 80C Deductions Readiness
                  </label>
                  <div className="space-y-2">
                    {[
                      "Fully Maxed Out (₹1.50 Lakh in ELSS/PPF)",
                      "Partially Utilized (₹50k - ₹1L)",
                      "Haven't Started (< ₹50k)"
                    ].map((st) => (
                      <button
                        key={st}
                        type="button"
                        onClick={() => setFormData({ ...formData, section_80c_status: st })}
                        className={`w-full p-2.5 rounded-xl border text-xs font-semibold text-left transition-all ${
                          formData.section_80c_status === st
                            ? "bg-emerald-500/15 border-emerald-500 text-emerald-300 ring-1 ring-emerald-500/40"
                            : "bg-gray-900 border-border text-gray-400 hover:border-gray-700"
                        }`}
                      >
                        {st}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Freeform Strategy Preferences */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                  <Compass className="w-3.5 h-3.5 text-emerald-400" /> Custom Investment Strategy & Preferences
                </label>
                <textarea
                  rows={2}
                  value={formData.financial_preferences}
                  onChange={(e) => setFormData({ ...formData, financial_preferences: e.target.value })}
                  placeholder="e.g. Focus on passive low-cost index funds, tax optimization, and dividend reinvestment."
                  className="w-full bg-gray-900 border border-border rounded-xl px-4 py-3 text-xs text-white focus:border-emerald-500 outline-none resize-none transition-colors"
                />
              </div>
            </div>
          )}

          {/* STEP 9: Comprehensive Review & AI Diagnostics */}
          {step === 9 && (
            <div className="space-y-4 animate-in fade-in duration-300">
              <div className="flex items-center justify-between pb-2 border-b border-border/50">
                <div className="flex items-center gap-2">
                  <FileCheck className="w-5 h-5 text-emerald-400" />
                  <h3 className="text-base font-bold text-white">Financial Profile Diagnostics</h3>
                </div>
                <div className={`px-2.5 py-1 rounded-full text-xs font-bold border ${persona.color}`}>
                  {persona.title}
                </div>
              </div>

              {/* Diagnostic Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
                <div className="p-3 bg-gray-900/90 border border-border rounded-xl">
                  <span className="text-gray-400 text-[11px]">Monthly Inflow</span>
                  <div className="text-emerald-400 font-bold text-sm mt-0.5">₹{totalMonthlyInflow.toLocaleString("en-IN")}</div>
                  <span className="text-[10px] text-gray-400">Salary + Secondary</span>
                </div>
                <div className="p-3 bg-gray-900/90 border border-border rounded-xl">
                  <span className="text-gray-400 text-[11px]">Monthly Surplus</span>
                  <div className="text-teal-400 font-bold text-sm mt-0.5">₹{monthlySurplus.toLocaleString("en-IN")}</div>
                  <span className="text-[10px] text-teal-400/80">{savingsRate}% Savings Rate</span>
                </div>
                <div className="p-3 bg-gray-900/90 border border-border rounded-xl">
                  <span className="text-gray-400 text-[11px]">DTI Ratio</span>
                  <div className="text-white font-bold text-sm mt-0.5">{dtiRatio}%</div>
                  <span className={`text-[10px] font-semibold ${dtiRatio <= 30 ? "text-emerald-400" : "text-amber-400"}`}>
                    {dtiRatio <= 30 ? "Safe Debt Load" : "Elevated Debt"}
                  </span>
                </div>
                <div className="p-3 bg-gray-900/90 border border-border rounded-xl">
                  <span className="text-gray-400 text-[11px]">Emergency Runway</span>
                  <div className="text-cyan-400 font-bold text-sm mt-0.5">{emergencyRunwayMonths} Months</div>
                  <span className="text-[10px] text-gray-400">Target: {formData.target_emergency_months} mos</span>
                </div>
              </div>

              {/* Key Attributes Table */}
              <div className="grid grid-cols-2 gap-2 p-3 bg-gray-900/60 border border-border/80 rounded-xl text-[11px]">
                <div>
                  <span className="text-gray-400">Investor Name:</span> <span className="text-white font-semibold">{formData.full_name} ({formData.age} yrs)</span>
                </div>
                <div>
                  <span className="text-gray-400">Employment:</span> <span className="text-white font-semibold">{formData.employment_type}</span>
                </div>
                <div>
                  <span className="text-gray-400">Core Expenses:</span> <span className="text-rose-400 font-semibold">₹{((formData.monthly_expenses || 0) + (formData.discretionary_expenses || 0)).toLocaleString("en-IN")}/mo</span>
                </div>
                <div>
                  <span className="text-gray-400">Monthly EMI:</span> <span className="text-orange-400 font-semibold">₹{formData.monthly_emi.toLocaleString("en-IN")}/mo</span>
                </div>
                <div>
                  <span className="text-gray-400">Current Portfolio:</span> <span className="text-emerald-400 font-semibold">₹{formData.existing_investment_amount.toLocaleString("en-IN")}</span>
                </div>
                <div>
                  <span className="text-gray-400">Target SIP:</span> <span className="text-emerald-400 font-semibold">₹{formData.target_monthly_sip.toLocaleString("en-IN")}/mo</span>
                </div>
                <div>
                  <span className="text-gray-400">Milestone:</span> <span className="text-white font-semibold">{formData.primary_goal} ({formData.investment_horizon})</span>
                </div>
                <div>
                  <span className="text-gray-400">Tax Regime:</span> <span className="text-white font-semibold">{formData.tax_regime.split("(")[0]}</span>
                </div>
                <div className="col-span-2">
                  <span className="text-gray-400">Assets Held:</span> <span className="text-gray-200">{formData.existing_investments.join(", ")}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Navigation Controls */}
        <div className="flex items-center justify-between pt-4 border-t border-border/50">
          <button
            type="button"
            onClick={handleBack}
            disabled={step === 1 || saving}
            className="flex items-center gap-2 text-xs font-semibold px-4 py-2.5 rounded-xl border border-border text-gray-400 hover:text-white hover:bg-gray-800 disabled:opacity-30 disabled:pointer-events-none transition-all"
          >
            <ArrowLeft className="w-4 h-4" /> Back
          </button>

          <button
            type="button"
            onClick={handleNext}
            disabled={saving}
            className="flex items-center gap-2 text-xs font-bold px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white transition-all shadow-lg shadow-emerald-950 disabled:opacity-50"
          >
            {step === totalSteps ? (
              saving ? (
                "Building AI Profile & Launching..."
              ) : (
                <>
                  Confirm Profile & Access Dashboard <CheckCircle2 className="w-4 h-4" />
                </>
              )
            ) : (
              <>
                Continue to Next Module <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
