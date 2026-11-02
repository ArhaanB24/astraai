"use client";

import { useState } from "react";
import {
  fetchFinanceSummary,
  updateFinancialProfileApi,
  addIncomeSourceApi,
  deleteIncomeSourceApi,
  addExpenseItemApi,
  deleteExpenseItemApi,
  addAssetItemApi,
  deleteAssetItemApi,
  addLiabilityItemApi,
  deleteLiabilityItemApi,
} from "@/lib/api";
import { formatINR } from "@/lib/utils";
import {
  Landmark,
  Plus,
  Trash2,
  Edit3,
  ShieldCheck,
  DollarSign,
  UserCheck,
  X,
  CreditCard,
  Wallet,
  TrendingDown,
} from "lucide-react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { useAutoRefresh } from "@/lib/dataSync";

export default function IncomeExpensesPage() {
  const { isAuthenticated, isLoading } = useRequireAuth();
  const [summary, setSummary] = useState<any>(null);
  const [loadingData, setLoadingData] = useState(true);

  // Edit Profile Modal State
  const [showEditProfileModal, setShowEditProfileModal] = useState(false);
  const [salary, setSalary] = useState(0);
  const [otherIncome, setOtherIncome] = useState(0);
  const [expenses, setExpenses] = useState(0);
  const [emis, setEmis] = useState(0);
  const [bankBalance, setBankBalance] = useState(0);
  const [emergencyFund, setEmergencyFund] = useState(0);
  const [existingInvestments, setExistingInvestments] = useState(0);
  const [savingProfile, setSavingProfile] = useState(false);

  // Add Item Modal State
  const [showAddItemModal, setShowAddItemModal] = useState<"income" | "expense" | "asset" | "liability" | null>(null);
  const [itemName, setItemName] = useState("");
  const [itemAmount, setItemAmount] = useState(0);
  const [itemCategory, setItemCategory] = useState("General");
  const [savingItem, setSavingItem] = useState(false);

  const loadData = async () => {
    try {
      const data = await fetchFinanceSummary();
      setSummary(data);
      if (data && !showEditProfileModal) {
        setSalary(data.monthly_salary || 0);
        setOtherIncome(data.other_monthly_income || 0);
        setExpenses(data.monthly_expenses || 0);
        setEmis(data.monthly_emi || 0);
        setBankBalance(data.bank_balance || 0);
        setEmergencyFund(data.emergency_fund_balance || 0);
        setExistingInvestments(data.existing_investments || 0);
      }
    } catch (e) {
      console.warn("Summary error", e);
    } finally {
      setLoadingData(false);
    }
  };

  useAutoRefresh(loadData, {
    intervalMs: 4000,
    enabled: isAuthenticated && !showEditProfileModal && !showAddItemModal,
    eventScopes: ["finance", "all"],
    refreshOnFocus: true,
    fetchOnMount: true,
  });

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[70vh] text-slate-400 font-semibold text-xs">
        Authenticating...
      </div>
    );
  }

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    try {
      await updateFinancialProfileApi({
        monthly_salary: salary,
        other_monthly_income: otherIncome,
        monthly_expenses: expenses,
        monthly_emi: emis,
        bank_balance: bankBalance,
        emergency_fund_balance: emergencyFund,
        existing_investments: existingInvestments,
      });
      setShowEditProfileModal(false);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to update financial profile");
    } finally {
      setSavingProfile(false);
    }
  };

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!itemName || itemAmount <= 0) return;
    setSavingItem(true);
    try {
      if (showAddItemModal === "income") {
        await addIncomeSourceApi({
          name: itemName,
          amount: itemAmount,
          category: itemCategory || "Salary",
          frequency: "Monthly",
        });
      } else if (showAddItemModal === "expense") {
        await addExpenseItemApi({
          name: itemName,
          amount: itemAmount,
          category: itemCategory || "Living",
          is_essential: true,
        });
      } else if (showAddItemModal === "asset") {
        await addAssetItemApi({
          name: itemName,
          amount: itemAmount,
          category: itemCategory || "Liquid",
          liquidity_tier: "High",
        });
      } else if (showAddItemModal === "liability") {
        await addLiabilityItemApi({
          name: itemName,
          principal_outstanding: itemAmount,
          monthly_emi: Math.round(itemAmount * 0.02),
          interest_rate_pct: 10.0,
          tenure_months_left: 36,
        });
      }
      setShowAddItemModal(null);
      setItemName("");
      setItemAmount(0);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to add item");
    } finally {
      setSavingItem(false);
    }
  };

  const handleDeleteIncome = async (id: string) => {
    if (!confirm("Are you sure you want to delete this income source?")) return;
    try {
      await deleteIncomeSourceApi(id);
      await loadData();
    } catch (err: any) {
      alert("Failed to delete income source");
    }
  };

  const handleDeleteExpense = async (id: string) => {
    if (!confirm("Are you sure you want to delete this expense item?")) return;
    try {
      await deleteExpenseItemApi(id);
      await loadData();
    } catch (err: any) {
      alert("Failed to delete expense item");
    }
  };

  const handleDeleteAsset = async (id: string) => {
    if (!confirm("Are you sure you want to delete this asset?")) return;
    try {
      await deleteAssetItemApi(id);
      await loadData();
    } catch (err: any) {
      alert("Failed to delete asset");
    }
  };

  const handleDeleteLiability = async (id: string) => {
    if (!confirm("Are you sure you want to delete this liability?")) return;
    try {
      await deleteLiabilityItemApi(id);
      await loadData();
    } catch (err: any) {
      alert("Failed to delete liability");
    }
  };

  if (loadingData && !summary) {
    return <div className="p-6 text-emerald-400 font-semibold text-xs">Loading Financial Profile...</div>;
  }

  const totalMonthlyIncome = (summary?.monthly_salary || 0) + (summary?.other_monthly_income || 0);
  const totalMonthlyOutflow = (summary?.monthly_expenses || 0) + (summary?.monthly_emi || 0);
  const netSurplus = totalMonthlyIncome - totalMonthlyOutflow;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="p-6 rounded-2xl bg-card border border-border flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
            Shared Financial Profile
          </span>
          <h1 className="text-xl font-black text-white mt-1">Income, Expenses, Assets &amp; Liabilities Manager</h1>
          <p className="text-xs text-slate-400 mt-1">
            Edit your monthly salary, living costs, EMIs, and assets directly in the database.
          </p>
        </div>

        <button
          onClick={() => {
            setSalary(summary?.monthly_salary || 0);
            setOtherIncome(summary?.other_monthly_income || 0);
            setExpenses(summary?.monthly_expenses || 0);
            setEmis(summary?.monthly_emi || 0);
            setBankBalance(summary?.bank_balance || 0);
            setEmergencyFund(summary?.emergency_fund_balance || 0);
            setExistingInvestments(summary?.existing_investments || 0);
            setShowEditProfileModal(true);
          }}
          className="bg-emerald-500 hover:bg-emerald-600 active:bg-emerald-700 text-slate-950 font-bold text-xs px-5 py-2.5 rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center gap-2 shrink-0"
        >
          <Edit3 className="w-4 h-4" /> Edit Financial Profile
        </button>
      </div>

      {summary ? (
        <div className="space-y-6">
          {/* Quick Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl bg-card border border-border">
              <span className="text-[10px] text-slate-400 font-semibold uppercase">Total Monthly Income</span>
              <p className="text-lg font-bold text-emerald-400 mt-1">{formatINR(totalMonthlyIncome)}</p>
              <span className="text-[10px] text-slate-500">Salary + Other Income</span>
            </div>
            <div className="p-4 rounded-2xl bg-card border border-border">
              <span className="text-[10px] text-slate-400 font-semibold uppercase">Monthly Living Outflow</span>
              <p className="text-lg font-bold text-rose-400 mt-1">{formatINR(totalMonthlyOutflow)}</p>
              <span className="text-[10px] text-slate-500">Expenses + EMIs</span>
            </div>
            <div className="p-4 rounded-2xl bg-card border border-border">
              <span className="text-[10px] text-slate-400 font-semibold uppercase">Net Monthly Surplus</span>
              <p className={`text-lg font-bold mt-1 ${netSurplus >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                {formatINR(netSurplus)}
              </p>
              <span className="text-[10px] text-slate-500">Investable cash flow</span>
            </div>
            <div className="p-4 rounded-2xl bg-card border border-border">
              <span className="text-[10px] text-slate-400 font-semibold uppercase">Emergency Reserves</span>
              <p className="text-lg font-bold text-cyan-400 mt-1">{formatINR(summary.emergency_fund_balance || 0)}</p>
              <span className="text-[10px] text-slate-500">
                {summary.monthly_expenses > 0
                  ? `${((summary.emergency_fund_balance || 0) / summary.monthly_expenses).toFixed(1)} months buffer`
                  : "Liquid safety buffer"}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 1. Income Sources */}
            <div className="p-5 rounded-2xl bg-card border border-border space-y-3">
              <div className="flex items-center justify-between border-b border-border/80 pb-2">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-emerald-400" /> Income Sources
                </h3>
                <button
                  onClick={() => {
                    setShowAddItemModal("income");
                    setItemName("");
                    setItemAmount(10000);
                    setItemCategory("Salary");
                  }}
                  className="text-[11px] font-bold text-emerald-400 hover:text-emerald-300 flex items-center gap-1 bg-emerald-950/40 border border-emerald-800/40 px-2.5 py-1 rounded-lg transition-colors"
                >
                  <Plus className="w-3 h-3" /> Add Source
                </button>
              </div>

              <div className="space-y-2 text-xs">
                {/* Primary Baseline Salary */}
                <div className="p-3 rounded-xl bg-surface border border-border flex justify-between items-center">
                  <div>
                    <p className="font-bold text-white">Primary Salary</p>
                    <span className="text-[10px] text-slate-400">Salary &middot; Monthly</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-emerald-400">{formatINR(summary.monthly_salary || 0)}</span>
                    <button
                      onClick={() => setShowEditProfileModal(true)}
                      className="text-slate-400 hover:text-emerald-400 p-1"
                      title="Edit Salary"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Other Monthly Income if > 0 */}
                {summary.other_monthly_income > 0 && (
                  <div className="p-3 rounded-xl bg-surface border border-border flex justify-between items-center">
                    <div>
                      <p className="font-bold text-white">Other Monthly Income</p>
                      <span className="text-[10px] text-slate-400">Secondary &middot; Monthly</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-emerald-400">{formatINR(summary.other_monthly_income)}</span>
                      <button
                        onClick={() => setShowEditProfileModal(true)}
                        className="text-slate-400 hover:text-emerald-400 p-1"
                        title="Edit Other Income"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                )}

                {/* Custom Itemized Income Sources */}
                {summary.income_sources?.map((item: any) => (
                  <div
                    key={item.id}
                    className="p-3 rounded-xl bg-surface border border-border flex justify-between items-center group"
                  >
                    <div>
                      <p className="font-bold text-white">{item.name}</p>
                      <span className="text-[10px] text-slate-400">
                        {item.category} &middot; {item.frequency}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-emerald-400">{formatINR(item.amount)}</span>
                      <button
                        onClick={() => handleDeleteIncome(item.id)}
                        className="text-slate-500 hover:text-rose-400 p-1 transition-colors"
                        title="Delete Source"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 2. Monthly Expenses & EMIs */}
            <div className="p-5 rounded-2xl bg-card border border-border space-y-3">
              <div className="flex items-center justify-between border-b border-border/80 pb-2">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <TrendingDown className="w-4 h-4 text-rose-400" /> Monthly Expenses &amp; EMIs
                </h3>
                <button
                  onClick={() => {
                    setShowAddItemModal("expense");
                    setItemName("");
                    setItemAmount(5000);
                    setItemCategory("Living");
                  }}
                  className="text-[11px] font-bold text-rose-400 hover:text-rose-300 flex items-center gap-1 bg-rose-950/40 border border-rose-800/40 px-2.5 py-1 rounded-lg transition-colors"
                >
                  <Plus className="w-3 h-3" /> Add Expense
                </button>
              </div>

              <div className="space-y-2 text-xs">
                {/* Baseline Living Expenses */}
                <div className="p-3 rounded-xl bg-surface border border-border flex justify-between items-center">
                  <div>
                    <p className="font-bold text-white">Living &amp; Household Expenses</p>
                    <span className="text-[10px] text-slate-400">Living &middot; Essential</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-rose-400">{formatINR(summary.monthly_expenses || 0)}</span>
                    <button
                      onClick={() => setShowEditProfileModal(true)}
                      className="text-slate-400 hover:text-rose-400 p-1"
                      title="Edit Living Expenses"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Monthly EMIs */}
                <div className="p-3 rounded-xl bg-surface border border-border flex justify-between items-center">
                  <div>
                    <p className="font-bold text-white">Monthly Loan EMIs</p>
                    <span className="text-[10px] text-slate-400">Debt Servicing &middot; Monthly</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-rose-400">{formatINR(summary.monthly_emi || 0)}</span>
                    <button
                      onClick={() => setShowEditProfileModal(true)}
                      className="text-slate-400 hover:text-rose-400 p-1"
                      title="Edit EMIs"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Custom Itemized Expense Items */}
                {summary.expense_items?.map((item: any) => (
                  <div
                    key={item.id}
                    className="p-3 rounded-xl bg-surface border border-border flex justify-between items-center group"
                  >
                    <div>
                      <p className="font-bold text-white">{item.name}</p>
                      <span className="text-[10px] text-slate-400">
                        {item.category} &middot; {item.is_essential ? "Essential" : "Discretionary"}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-rose-400">{formatINR(item.amount)}</span>
                      <button
                        onClick={() => handleDeleteExpense(item.id)}
                        className="text-slate-500 hover:text-rose-400 p-1 transition-colors"
                        title="Delete Expense"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 3. Assets & Bank Balances */}
            <div className="p-5 rounded-2xl bg-card border border-border space-y-3">
              <div className="flex items-center justify-between border-b border-border/80 pb-2">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Wallet className="w-4 h-4 text-cyan-400" /> Assets &amp; Liquid Reserves
                </h3>
                <button
                  onClick={() => {
                    setShowAddItemModal("asset");
                    setItemName("");
                    setItemAmount(50000);
                    setItemCategory("Fixed Deposit");
                  }}
                  className="text-[11px] font-bold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 bg-cyan-950/40 border border-cyan-800/40 px-2.5 py-1 rounded-lg transition-colors"
                >
                  <Plus className="w-3 h-3" /> Add Asset
                </button>
              </div>

              <div className="space-y-2 text-xs">
                <div className="p-3 rounded-xl bg-surface border border-border flex justify-between items-center">
                  <div>
                    <p className="font-bold text-white">Savings &amp; Bank Account</p>
                    <span className="text-[10px] text-slate-400">Liquid Cash</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-cyan-400">{formatINR(summary.bank_balance || 0)}</span>
                    <button
                      onClick={() => setShowEditProfileModal(true)}
                      className="text-slate-400 hover:text-cyan-400 p-1"
                      title="Edit Bank Balance"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-surface border border-border flex justify-between items-center">
                  <div>
                    <p className="font-bold text-white">Emergency Fund</p>
                    <span className="text-[10px] text-slate-400">Safety Buffer</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-cyan-400">{formatINR(summary.emergency_fund_balance || 0)}</span>
                    <button
                      onClick={() => setShowEditProfileModal(true)}
                      className="text-slate-400 hover:text-cyan-400 p-1"
                      title="Edit Emergency Fund"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-surface border border-border flex justify-between items-center">
                  <div>
                    <p className="font-bold text-white">Existing Investments</p>
                    <span className="text-[10px] text-slate-400">Mutual Funds &amp; Equities</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-cyan-400">{formatINR(summary.existing_investments || 0)}</span>
                    <button
                      onClick={() => setShowEditProfileModal(true)}
                      className="text-slate-400 hover:text-cyan-400 p-1"
                      title="Edit Investments"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {summary.asset_items?.map((item: any) => (
                  <div
                    key={item.id}
                    className="p-3 rounded-xl bg-surface border border-border flex justify-between items-center group"
                  >
                    <div>
                      <p className="font-bold text-white">{item.name}</p>
                      <span className="text-[10px] text-slate-400">{item.category}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-cyan-400">{formatINR(item.amount)}</span>
                      <button
                        onClick={() => handleDeleteAsset(item.id)}
                        className="text-slate-500 hover:text-rose-400 p-1 transition-colors"
                        title="Delete Asset"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 4. Liabilities & Loans */}
            <div className="p-5 rounded-2xl bg-card border border-border space-y-3">
              <div className="flex items-center justify-between border-b border-border/80 pb-2">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <CreditCard className="w-4 h-4 text-amber-400" /> Liabilities &amp; Outstanding Loans
                </h3>
                <button
                  onClick={() => {
                    setShowAddItemModal("liability");
                    setItemName("");
                    setItemAmount(100000);
                    setItemCategory("Personal Loan");
                  }}
                  className="text-[11px] font-bold text-amber-400 hover:text-amber-300 flex items-center gap-1 bg-amber-950/40 border border-amber-800/40 px-2.5 py-1 rounded-lg transition-colors"
                >
                  <Plus className="w-3 h-3" /> Add Loan
                </button>
              </div>

              <div className="space-y-2 text-xs">
                {summary.liability_items && summary.liability_items.length > 0 ? (
                  summary.liability_items.map((item: any) => (
                    <div
                      key={item.id}
                      className="p-3 rounded-xl bg-surface border border-border flex justify-between items-center group"
                    >
                      <div>
                        <p className="font-bold text-white">{item.name}</p>
                        <span className="text-[10px] text-slate-400">
                          {item.category} &middot; EMI: {formatINR(item.monthly_emi || 0)}/mo
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="font-bold text-amber-400">{formatINR(item.principal_outstanding || 0)}</span>
                        <button
                          onClick={() => handleDeleteLiability(item.id)}
                          className="text-slate-500 hover:text-rose-400 p-1 transition-colors"
                          title="Delete Loan"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="p-4 rounded-xl bg-surface/50 border border-border/50 text-center text-slate-500">
                    No itemized loan liabilities logged. Use &ldquo;Add Loan&rdquo; to track outstanding balances.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="p-8 text-center bg-card rounded-2xl border border-border text-slate-400 space-y-3">
          <UserCheck className="w-8 h-8 mx-auto text-emerald-400" />
          <h3 className="text-sm font-bold text-white">Profile Not Initialized</h3>
          <p className="text-xs">Complete onboarding to configure your salary, expenses, and assets.</p>
          <Link
            href="/onboarding"
            className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 font-bold text-slate-950 text-xs px-4 py-2 rounded-xl transition-all"
          >
            Start Onboarding
          </Link>
        </div>
      )}

      {/* Edit Base Profile Modal */}
      {showEditProfileModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-card border border-border rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4 my-8">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Edit3 className="w-4 h-4 text-emerald-400" /> Edit Financial Profile
              </h2>
              <button
                onClick={() => setShowEditProfileModal(false)}
                className="text-slate-400 hover:text-white p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveProfile} className="space-y-3 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 uppercase">Primary Salary (₹/mo)</label>
                  <input
                    type="number"
                    value={salary}
                    onChange={(e) => setSalary(Number(e.target.value))}
                    required
                    className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 uppercase">Other Income (₹/mo)</label>
                  <input
                    type="number"
                    value={otherIncome}
                    onChange={(e) => setOtherIncome(Number(e.target.value))}
                    className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 uppercase">Living Expenses (₹/mo)</label>
                  <input
                    type="number"
                    value={expenses}
                    onChange={(e) => setExpenses(Number(e.target.value))}
                    required
                    className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 uppercase">Monthly EMIs (₹/mo)</label>
                  <input
                    type="number"
                    value={emis}
                    onChange={(e) => setEmis(Number(e.target.value))}
                    className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 uppercase">Bank Balance (₹)</label>
                  <input
                    type="number"
                    value={bankBalance}
                    onChange={(e) => setBankBalance(Number(e.target.value))}
                    className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 uppercase">Emergency Fund (₹)</label>
                  <input
                    type="number"
                    value={emergencyFund}
                    onChange={(e) => setEmergencyFund(Number(e.target.value))}
                    className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-400 uppercase">Existing Investments (₹)</label>
                <input
                  type="number"
                  value={existingInvestments}
                  onChange={(e) => setExistingInvestments(Number(e.target.value))}
                  className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-border mt-4">
                <button
                  type="button"
                  onClick={() => setShowEditProfileModal(false)}
                  className="px-4 py-2 rounded-xl border border-border text-slate-400 hover:text-white font-semibold text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingProfile}
                  className="px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 active:bg-emerald-700 text-slate-950 font-bold text-xs shadow-lg shadow-emerald-500/20"
                >
                  {savingProfile ? "Saving to DB..." : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Custom Item Modal */}
      {showAddItemModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h2 className="text-base font-bold text-white capitalize">
                Add {showAddItemModal === "liability" ? "Loan / Liability" : showAddItemModal}
              </h2>
              <button onClick={() => setShowAddItemModal(null)} className="text-slate-400 hover:text-white p-1">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddItem} className="space-y-3 text-xs">
              <div>
                <label className="text-[11px] font-semibold text-slate-400 uppercase">Item Name / Description</label>
                <input
                  type="text"
                  placeholder="e.g. Freelance Consulting, Car Loan, Gold"
                  value={itemName}
                  onChange={(e) => setItemName(e.target.value)}
                  required
                  className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-400 uppercase">
                  {showAddItemModal === "liability" ? "Outstanding Principal (₹)" : "Amount (₹)"}
                </label>
                <input
                  type="number"
                  value={itemAmount}
                  onChange={(e) => setItemAmount(Number(e.target.value))}
                  required
                  className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-400 uppercase">Category</label>
                <input
                  type="text"
                  placeholder="e.g. Salary, Rent, Equity, Secured Loan"
                  value={itemCategory}
                  onChange={(e) => setItemCategory(e.target.value)}
                  className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-border mt-4">
                <button
                  type="button"
                  onClick={() => setShowAddItemModal(null)}
                  className="px-4 py-2 rounded-xl border border-border text-slate-400 hover:text-white font-semibold text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingItem}
                  className="px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 active:bg-emerald-700 text-slate-950 font-bold text-xs shadow-lg shadow-emerald-500/20"
                >
                  {savingItem ? "Adding..." : "Add to Profile"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
