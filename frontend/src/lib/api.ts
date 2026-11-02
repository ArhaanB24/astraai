import { PortfolioSummary, OverlapAnalysis, ChatResponse } from "@/types";
import { notifyDataMutation } from "./dataSync";

const getApiBase = () => {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== "undefined") {
    return "/api/v1";
  }
  return "http://localhost:8000/api/v1";
};

export function getAuthToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("arthaai_token");
  }
  return null;
}

export function handleAuthError() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("arthaai_token");
    localStorage.removeItem("arthaai_user");
    if (!window.location.pathname.startsWith("/login") && !window.location.pathname.startsWith("/signup")) {
      window.location.href = "/login";
    }
  }
}

function getAuthHeaders(extraHeaders: Record<string, string> = {}) {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    ...extraHeaders,
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function authenticatedFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const token = getAuthToken();
  if (!token && typeof window !== "undefined") {
    handleAuthError();
    throw new Error("Not authenticated");
  }

  const mergedHeaders = getAuthHeaders((options.headers as Record<string, string>) || {});
  const res = await fetch(url, {
    ...options,
    headers: mergedHeaders,
  });

  if (res.status === 401) {
    handleAuthError();
    throw new Error("Session expired or unauthorized");
  }

  return res;
}

// --- MUTUAL FUND AI MODULE APIs ---
export async function fetchPortfolioSummary(): Promise<PortfolioSummary> {
  const res = await authenticatedFetch(`${getApiBase()}/portfolio`);
  if (!res.ok) {
    throw new Error(`Failed to fetch portfolio summary: ${res.statusText}`);
  }
  return await res.json();
}

export async function fetchPortfolioHistory(): Promise<any[]> {
  const res = await authenticatedFetch(`${getApiBase()}/portfolio/history`);
  if (!res.ok) {
    return [];
  }
  return await res.json();
}

export async function fetchOverlapAnalysis(): Promise<OverlapAnalysis> {
  const res = await authenticatedFetch(`${getApiBase()}/portfolio/overlap`);
  if (!res.ok) {
    throw new Error(`Failed to fetch overlap analysis: ${res.statusText}`);
  }
  return await res.json();
}

export async function fetchPortfolioOverlap(): Promise<OverlapAnalysis> {
  return await fetchOverlapAnalysis();
}

export async function addTransactionApi(txData: any) {
  const res = await authenticatedFetch(`${getApiBase()}/portfolio/transactions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(txData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Transaction failed" }));
    throw new Error(err.detail || "Failed to add transaction");
  }
  const data = await res.json();
  notifyDataMutation("portfolio");
  return data;
}

export async function sendChatMessage(message: string): Promise<ChatResponse> {
  const res = await authenticatedFetch(`${getApiBase()}/chat/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Chat failed" }));
    throw new Error(err.detail || "Failed to communicate with Mutual Fund AI");
  }
  return await res.json();
}

export async function searchMutualFundsApi(query: string) {
  const res = await authenticatedFetch(`${getApiBase()}/mutual-funds/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) return [];
  return await res.json();
}

export async function fetchMutualFundsCatalogApi() {
  const res = await authenticatedFetch(`${getApiBase()}/mutual-funds/catalog`);
  if (!res.ok) return [];
  return await res.json();
}

export async function getMutualFundDetailsApi(schemeCode: string) {
  const res = await authenticatedFetch(`${getApiBase()}/mutual-funds/${schemeCode}`);
  if (!res.ok) throw new Error("Failed to load fund details");
  return await res.json();
}

// --- PERSONAL FINANCE AI MODULE APIs ---
export async function getFinancialHealth() {
  const res = await authenticatedFetch(`${getApiBase()}/finance/health`);
  if (!res.ok) {
    return null;
  }
  return await res.json();
}

export async function fetchFinanceHealth() {
  return await getFinancialHealth();
}

export async function fetchFinanceSummary() {
  const res = await authenticatedFetch(`${getApiBase()}/finance/summary`);
  if (!res.ok) return null;
  return await res.json();
}

export async function updateFinancialProfileApi(profileData: any) {
  const res = await authenticatedFetch(`${getApiBase()}/finance/profile`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profileData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to update profile" }));
    throw new Error(err.detail || "Failed to update profile");
  }
  const data = await res.json();
  notifyDataMutation("finance");
  return data;
}

export async function addIncomeSourceApi(item: any) {
  const res = await authenticatedFetch(`${getApiBase()}/finance/income`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(item),
  });
  if (!res.ok) throw new Error("Failed to add income source");
  const data = await res.json();
  notifyDataMutation("finance");
  return data;
}

export async function deleteIncomeSourceApi(itemId: string) {
  const res = await authenticatedFetch(`${getApiBase()}/finance/income/${itemId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete income source");
  notifyDataMutation("finance");
  return true;
}

export async function addExpenseItemApi(item: any) {
  const res = await authenticatedFetch(`${getApiBase()}/finance/expenses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(item),
  });
  if (!res.ok) throw new Error("Failed to add expense item");
  const data = await res.json();
  notifyDataMutation("finance");
  return data;
}

export async function deleteExpenseItemApi(itemId: string) {
  const res = await authenticatedFetch(`${getApiBase()}/finance/expenses/${itemId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete expense item");
  notifyDataMutation("finance");
  return true;
}

export async function addAssetItemApi(item: any) {
  const res = await authenticatedFetch(`${getApiBase()}/finance/assets`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(item),
  });
  if (!res.ok) throw new Error("Failed to add asset");
  const data = await res.json();
  notifyDataMutation("finance");
  return data;
}

export async function deleteAssetItemApi(itemId: string) {
  const res = await authenticatedFetch(`${getApiBase()}/finance/assets/${itemId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete asset");
  notifyDataMutation("finance");
  return true;
}

export async function addLiabilityItemApi(item: any) {
  const res = await authenticatedFetch(`${getApiBase()}/finance/liabilities`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(item),
  });
  if (!res.ok) throw new Error("Failed to add liability");
  const data = await res.json();
  notifyDataMutation("finance");
  return data;
}

export async function deleteLiabilityItemApi(itemId: string) {
  const res = await authenticatedFetch(`${getApiBase()}/finance/liabilities/${itemId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete liability");
  notifyDataMutation("finance");
  return true;
}

export async function fetchStockHoldingsApi() {
  const res = await authenticatedFetch(`${getApiBase()}/portfolio/stocks`);
  if (!res.ok) return [];
  return await res.json();
}

export async function addStockHoldingApi(stock: any) {
  const res = await authenticatedFetch(`${getApiBase()}/portfolio/stocks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(stock),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to add stock" }));
    throw new Error(err.detail || "Failed to add stock holding");
  }
  const data = await res.json();
  notifyDataMutation("portfolio");
  return data;
}

export async function deleteStockHoldingApi(stockId: string) {
  const res = await authenticatedFetch(`${getApiBase()}/portfolio/stocks/${stockId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete stock holding");
  notifyDataMutation("portfolio");
  return true;
}

export async function saveQuestionnaireApi(submissionData: any) {
  const res = await authenticatedFetch(`${getApiBase()}/profile/questionnaire`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(submissionData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to save financial profile" }));
    throw new Error(err.detail || "Failed to save financial profile");
  }
  const data = await res.json();
  notifyDataMutation("profile");
  notifyDataMutation("finance");
  return data;
}

export async function getFinancialProfile() {
  const res = await authenticatedFetch(`${getApiBase()}/profile/current`);
  if (!res.ok) {
    return null;
  }
  return await res.json();
}

export async function calculateAffordability(
  price: number,
  downPayment: number,
  interestRate: number,
  tenureMonths: number,
  itemType: string = "Car"
) {
  const res = await authenticatedFetch(`${getApiBase()}/finance/affordability`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      item_price: price,
      down_payment: downPayment,
      interest_rate_pct: interestRate,
      loan_tenure_months: tenureMonths,
      item_type: itemType,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Calculation failed" }));
    throw new Error(err.detail || "Failed to calculate affordability");
  }
  return await res.json();
}

export async function calculateCarAffordabilityApi(
  payloadOrPrice: any,
  downPayment?: number,
  interestRate?: number,
  tenureMonths?: number,
  itemType: string = "Car"
) {
  const body =
    typeof payloadOrPrice === "object"
      ? payloadOrPrice
      : {
          item_price: payloadOrPrice,
          down_payment: downPayment,
          interest_rate_pct: interestRate,
          loan_tenure_months: tenureMonths,
          item_type: itemType,
        };

  const res = await authenticatedFetch(`${getApiBase()}/finance/affordability`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Calculation failed" }));
    throw new Error(err.detail || "Failed to calculate affordability");
  }
  return await res.json();
}

export async function getGoals() {
  const res = await authenticatedFetch(`${getApiBase()}/finance/goals`);
  if (!res.ok) return [];
  return await res.json();
}

export async function createGoal(goal: any) {
  const res = await authenticatedFetch(`${getApiBase()}/finance/goals`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(goal),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to create goal" }));
    throw new Error(err.detail || "Failed to create goal");
  }
  const data = await res.json();
  notifyDataMutation("goals");
  notifyDataMutation("finance");
  return data;
}

export async function simulateScenario(req: any) {
  const res = await authenticatedFetch(`${getApiBase()}/finance/scenarios/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Simulation failed" }));
    throw new Error(err.detail || "Failed to simulate scenario");
  }
  return await res.json();
}

export async function simulateScenarioApi(req: any) {
  return await simulateScenario(req);
}

export async function sendFinanceChat(message: string): Promise<ChatResponse> {
  const res = await authenticatedFetch(`${getApiBase()}/finance/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Finance chat failed" }));
    throw new Error(err.detail || "Failed to communicate with Personal Finance AI");
  }
  return await res.json();
}

// --- NEWS & RESEARCH MODULE APIs ---
export interface SearchResearchResult {
  query: string;
  evidence_sources: Array<{
    title: string;
    snippet: string;
    url: string;
    source: string;
  }>;
  answer: string;
}

export async function sendSearchResearch(query: string): Promise<SearchResearchResult> {
  const res = await authenticatedFetch(`${getApiBase()}/search/research`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Search failed" }));
    throw new Error(err.detail || "Failed to fetch research results");
  }
  return await res.json();
}

// --- TAX AI MODULE APIs ---
export interface TaxCalculatePayload {
  gross_salary: number;
  other_income: number;
  deductions_80c: number;
  deductions_80d: number;
  other_deductions?: number;
  regime?: string;
  financial_year?: string;
  is_salaried?: boolean;
  age?: number;
}

export async function getTaxSummary(financialYear: string = "2025-26") {
  const res = await authenticatedFetch(`${getApiBase()}/tax/summary?financial_year=${financialYear}`);
  if (!res.ok) {
    return null;
  }
  return await res.json();
}

export async function calculateTax(payload: TaxCalculatePayload) {
  const res = await authenticatedFetch(`${getApiBase()}/tax/calculate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Tax calculation failed" }));
    throw new Error(err.detail || "Failed to calculate tax");
  }
  return await res.json();
}

export async function sendTaxChat(message: string): Promise<ChatResponse> {
  const res = await authenticatedFetch(`${getApiBase()}/tax/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Tax chat failed" }));
    throw new Error(err.detail || "Failed to communicate with Tax AI");
  }
  return await res.json();
}
