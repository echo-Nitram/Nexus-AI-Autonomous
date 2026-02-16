"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatCurrency, formatPnl } from "@/lib/utils";
import { api, Trade } from "@/lib/api";
import { useApi, useUserId } from "@/lib/hooks";

export function PositionsTable() {
  const userId = useUserId();
  const { data: positions, loading, error, refetch } = useApi(
    () => api.getPositions(userId),
    [userId],
  );
  const [closingId, setClosingId] = useState<string | null>(null);

  const handleClose = async (tradeId: string) => {
    setClosingId(tradeId);
    try {
      await api.closeTrade(tradeId);
      refetch();
    } catch (err) {
      console.error("Failed to close trade:", err);
    } finally {
      setClosingId(null);
    }
  };

  const list: Trade[] = positions ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Open Positions</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-10 bg-secondary/30 rounded animate-pulse" />
            ))}
          </div>
        ) : error ? (
          <p className="text-sm text-muted-foreground">Unable to load positions</p>
        ) : list.length === 0 ? (
          <p className="text-sm text-muted-foreground">No open positions</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-muted-foreground">
                  <th className="text-left py-3 px-2">Pair</th>
                  <th className="text-left py-3 px-2">Side</th>
                  <th className="text-right py-3 px-2">Size</th>
                  <th className="text-right py-3 px-2">Entry</th>
                  <th className="text-right py-3 px-2">P&L</th>
                  <th className="text-center py-3 px-2">Mode</th>
                  <th className="text-center py-3 px-2">Action</th>
                </tr>
              </thead>
              <tbody>
                {list.map((pos) => (
                  <tr key={pos.id} className="border-b border-border/50 hover:bg-secondary/30">
                    <td className="py-3 px-2 font-medium">{pos.pair}</td>
                    <td className="py-3 px-2">
                      <Badge variant={pos.side === "long" ? "profit" : "loss"}>
                        {pos.side.toUpperCase()}
                      </Badge>
                    </td>
                    <td className="text-right py-3 px-2">{pos.size}</td>
                    <td className="text-right py-3 px-2">
                      {pos.entry_price ? formatCurrency(pos.entry_price) : "--"}
                    </td>
                    <td
                      className={`text-right py-3 px-2 font-medium ${
                        (pos.pnl ?? 0) >= 0 ? "text-green-400" : "text-red-400"
                      }`}
                    >
                      {pos.pnl != null ? formatPnl(pos.pnl) : "--"}
                    </td>
                    <td className="text-center py-3 px-2">
                      <Badge variant={pos.is_shadow ? "shadow" : "default"}>
                        {pos.is_shadow ? "Shadow" : "Live"}
                      </Badge>
                    </td>
                    <td className="text-center py-3 px-2">
                      <button
                        onClick={() => handleClose(pos.id)}
                        disabled={closingId === pos.id}
                        className="text-xs text-red-400 hover:text-red-300 font-medium disabled:opacity-50"
                      >
                        {closingId === pos.id ? "Closing..." : "Close"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
