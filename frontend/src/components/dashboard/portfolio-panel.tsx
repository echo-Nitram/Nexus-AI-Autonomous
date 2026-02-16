"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatPnl } from "@/lib/utils";
import { api, PortfolioSummary } from "@/lib/api";
import { useApi, useUserId } from "@/lib/hooks";

const fallback: PortfolioSummary = {
  total_trades: 0,
  open_positions: 0,
  total_pnl: 0,
  win_rate: 0,
  shadow_trades: 0,
};

export function PortfolioPanel() {
  const userId = useUserId();
  const { data: portfolio, loading, error } = useApi(
    () => api.getPortfolio(userId),
    [userId],
  );

  const p = portfolio ?? fallback;

  const stats = [
    {
      label: "Total P&L",
      value: formatPnl(p.total_pnl),
      color: p.total_pnl >= 0 ? "text-green-400" : "text-red-400",
    },
    {
      label: "Win Rate",
      value: `${p.win_rate.toFixed(1)}%`,
      color: p.win_rate >= 50 ? "text-green-400" : "text-red-400",
    },
    {
      label: "Total Trades",
      value: p.total_trades.toString(),
      color: "text-foreground",
    },
    {
      label: "Open Positions",
      value: p.open_positions.toString(),
      color: "text-blue-400",
    },
    {
      label: "Shadow Trades",
      value: p.shadow_trades.toString(),
      color: "text-yellow-400",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      {stats.map((stat) => (
        <Card key={stat.label}>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">
              {stat.label}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-8 w-20 bg-secondary/50 rounded animate-pulse" />
            ) : error ? (
              <div className="text-xs text-red-400">--</div>
            ) : (
              <div className={`text-2xl font-bold ${stat.color}`}>
                {stat.value}
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
