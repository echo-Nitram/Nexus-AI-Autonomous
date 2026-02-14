"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatCurrency, formatPnl } from "@/lib/utils";

// Demo data
const positions = [
  {
    id: "1",
    pair: "BTC/USDT",
    side: "long",
    size: 0.05,
    entry_price: 97250.0,
    current_price: 98100.0,
    pnl: 42.5,
    pnl_pct: 0.87,
    is_shadow: true,
  },
  {
    id: "2",
    pair: "ETH/USDT",
    side: "long",
    size: 1.2,
    entry_price: 3450.0,
    current_price: 3520.0,
    pnl: 84.0,
    pnl_pct: 2.03,
    is_shadow: true,
  },
  {
    id: "3",
    pair: "SOL/USDT",
    side: "short",
    size: 10,
    entry_price: 195.0,
    current_price: 192.5,
    pnl: 25.0,
    pnl_pct: 1.28,
    is_shadow: true,
  },
];

export function PositionsTable() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Open Positions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-muted-foreground">
                <th className="text-left py-3 px-2">Pair</th>
                <th className="text-left py-3 px-2">Side</th>
                <th className="text-right py-3 px-2">Size</th>
                <th className="text-right py-3 px-2">Entry</th>
                <th className="text-right py-3 px-2">Current</th>
                <th className="text-right py-3 px-2">P&L</th>
                <th className="text-center py-3 px-2">Mode</th>
                <th className="text-center py-3 px-2">Action</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((pos) => (
                <tr key={pos.id} className="border-b border-border/50 hover:bg-secondary/30">
                  <td className="py-3 px-2 font-medium">{pos.pair}</td>
                  <td className="py-3 px-2">
                    <Badge variant={pos.side === "long" ? "profit" : "loss"}>
                      {pos.side.toUpperCase()}
                    </Badge>
                  </td>
                  <td className="text-right py-3 px-2">{pos.size}</td>
                  <td className="text-right py-3 px-2">
                    {formatCurrency(pos.entry_price)}
                  </td>
                  <td className="text-right py-3 px-2">
                    {formatCurrency(pos.current_price)}
                  </td>
                  <td
                    className={`text-right py-3 px-2 font-medium ${
                      pos.pnl >= 0 ? "text-green-400" : "text-red-400"
                    }`}
                  >
                    {formatPnl(pos.pnl)} ({pos.pnl_pct > 0 ? "+" : ""}
                    {pos.pnl_pct.toFixed(2)}%)
                  </td>
                  <td className="text-center py-3 px-2">
                    <Badge variant="shadow">Shadow</Badge>
                  </td>
                  <td className="text-center py-3 px-2">
                    <button className="text-xs text-red-400 hover:text-red-300 font-medium">
                      Close
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
