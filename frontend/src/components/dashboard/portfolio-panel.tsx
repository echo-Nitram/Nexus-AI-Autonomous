"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency, formatPnl } from "@/lib/utils";

// Demo data — in production, fetched from API
const portfolio = {
  total_trades: 47,
  open_positions: 3,
  total_pnl: 1284.56,
  win_rate: 63.8,
  shadow_trades: 42,
};

const stats = [
  {
    label: "Total P&L",
    value: formatPnl(portfolio.total_pnl),
    color: portfolio.total_pnl >= 0 ? "text-green-400" : "text-red-400",
  },
  {
    label: "Win Rate",
    value: `${portfolio.win_rate.toFixed(1)}%`,
    color: portfolio.win_rate >= 50 ? "text-green-400" : "text-red-400",
  },
  {
    label: "Total Trades",
    value: portfolio.total_trades.toString(),
    color: "text-foreground",
  },
  {
    label: "Open Positions",
    value: portfolio.open_positions.toString(),
    color: "text-blue-400",
  },
  {
    label: "Shadow Trades",
    value: portfolio.shadow_trades.toString(),
    color: "text-yellow-400",
  },
];

export function PortfolioPanel() {
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
            <div className={`text-2xl font-bold ${stat.color}`}>
              {stat.value}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
