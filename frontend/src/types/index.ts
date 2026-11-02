export interface FundBreakdown {
  scheme_code: string;
  scheme_name: string;
  total_units: number;
  invested_amount: number;
  latest_nav: number;
  current_value: number;
  profit_loss: number;
  profit_loss_pct: number;
  allocation_pct: number;
}

export interface PortfolioSummary {
  total_invested: number;
  current_value: number;
  total_profit_loss: number;
  profit_loss_percentage: number;
  xirr: number | null;
  fund_breakdown: FundBreakdown[];
  funds?: Array<{
    scheme_code: string;
    scheme_name: string;
    invested_amount: number;
    current_value: number;
    units: number;
    allocation_percentage: number;
    profit_loss: number;
    cagr: number;
  }>;
  risk_metrics?: {
    sharpe_ratio: number;
    sortino_ratio: number;
    beta: number;
    max_drawdown: number;
  };
  cagr?: number;
  unrealized_gain?: number;
  total_profit?: number;
}

export interface OverlappingStock {
  company_name: string;
  sector: string;
  effective_portfolio_weight_pct: number;
  held_by_funds: Array<{
    scheme_code: string;
    scheme_name: string;
    fund_allocation_pct: number;
  }>;
  total_weight?: number;
  schemes?: string[];
}

export interface SectorConcentration {
  sector: string;
  portfolio_weight_pct: number;
  weight?: number;
}

export interface PairwiseOverlap {
  fund_1: string;
  fund_2: string;
  overlap_percentage: number;
  common_stocks_count: number;
}

export interface OverlapAnalysis {
  success: boolean;
  top_portfolio_stocks: OverlappingStock[];
  overlapping_stocks: OverlappingStock[];
  pairwise_overlap: PairwiseOverlap[];
  sector_concentration: SectorConcentration[];
  message?: string;
  schemes?: Array<{ scheme_name: string; code: string }>;
  overlap_matrix?: number[][];
  top_common_holdings?: OverlappingStock[];
}

export interface Citation {
  document_name: string;
  source: string;
  page_number?: number;
  section?: string;
  relevance_score: number;
  url?: string;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  citations: Citation[];
  tools_used: string[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  citations?: Citation[];
  tools_used?: string[];
}
