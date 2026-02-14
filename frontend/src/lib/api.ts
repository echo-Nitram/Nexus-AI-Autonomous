const API_BASE = "/api/v1";

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "API error");
  }

  return res.json();
}

export const api = {
  // Dashboard
  getPortfolio: (userId: string) =>
    fetchApi<PortfolioSummary>(`/dashboard/portfolio/${userId}`),

  getThoughts: (userId: string) =>
    fetchApi<ThoughtLog[]>(`/dashboard/thoughts/${userId}`),

  // Trading
  getPositions: (userId: string) =>
    fetchApi<Trade[]>(`/trading/positions/${userId}`),

  getHistory: (userId: string) =>
    fetchApi<Trade[]>(`/trading/history/${userId}`),

  closeTrade: (tradeId: string) =>
    fetchApi<{ message: string; pnl: number }>(`/trading/close/${tradeId}`, {
      method: "POST",
    }),

  // Strategies
  getStrategies: (userId: string) =>
    fetchApi<Strategy[]>(`/strategies/user/${userId}`),

  createStrategy: (data: CreateStrategy) =>
    fetchApi<Strategy>("/strategies/", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

// Types
export interface PortfolioSummary {
  total_trades: number;
  open_positions: number;
  total_pnl: number;
  win_rate: number;
  shadow_trades: number;
}

export interface ThoughtLog {
  id: string;
  step: string;
  content: string;
  context: Record<string, unknown> | null;
  timestamp: string;
}

export interface Trade {
  id: string;
  pair: string;
  side: string;
  size: number;
  entry_price: number | null;
  status: string;
  is_shadow: boolean;
  pnl: number | null;
}

export interface Strategy {
  id: string;
  user_id: string;
  name: string;
  description: string;
  parsed_rules: Record<string, unknown> | null;
  timeframe: string;
  pairs: string[];
  is_active: boolean;
}

export interface CreateStrategy {
  user_id: string;
  name: string;
  description: string;
  timeframe: string;
  pairs: string[];
}
