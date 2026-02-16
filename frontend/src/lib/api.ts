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
  // Auth
  login: (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);
    return fetchApi<AuthToken>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData.toString(),
    });
  },

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

  // Agent
  startAgent: (userId: string, strategyId: string, intervalSeconds = 300) =>
    fetchApi<{ message: string }>("/agent/start", {
      method: "POST",
      body: JSON.stringify({
        user_id: userId,
        strategy_id: strategyId,
        interval_seconds: intervalSeconds,
      }),
    }),

  stopAgent: (userId: string, strategyId: string) =>
    fetchApi<{ message: string }>("/agent/stop", {
      method: "POST",
      body: JSON.stringify({
        user_id: userId,
        strategy_id: strategyId,
      }),
    }),

  getAgentStatus: (userId: string) =>
    fetchApi<AgentStatus[]>(`/agent/status/${userId}`),
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

export interface AuthToken {
  access_token: string;
  token_type: string;
  user_id: string;
}

export interface AgentStatus {
  running: boolean;
  user_id: string | null;
  strategy_id: string | null;
}
