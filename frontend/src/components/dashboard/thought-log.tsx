"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// Demo thought data — in production, fetched from /api/v1/dashboard/thoughts/:userId
const thoughts = [
  {
    id: "1",
    step: "perception",
    content:
      "Analyzed BTC/USDT: price=$97,250.00, RSI=42.3, trend=sideways, volume_ratio=1.45. Volume spike detected.",
    timestamp: "2026-02-14T10:30:00Z",
  },
  {
    id: "2",
    step: "perception",
    content:
      'Analyzed ETH/USDT: price=$3,450.00, RSI=55.1, trend=bullish, sentiment=greed. Network upgrade announced.',
    timestamp: "2026-02-14T10:30:05Z",
  },
  {
    id: "3",
    step: "memory",
    content:
      "Recalled 3 past trade outcomes. Last similar RSI divergence on ETH resulted in +4.2% gain over 6 hours.",
    timestamp: "2026-02-14T10:30:10Z",
  },
  {
    id: "4",
    step: "reasoning",
    content:
      "Evaluated ETH/USDT: should_trade=true, direction=long, confidence=0.78. RSI divergence confirmed with bullish EMA crossover. Social sentiment aligns with technical signal.",
    timestamp: "2026-02-14T10:30:15Z",
  },
  {
    id: "5",
    step: "risk_check",
    content:
      "Risk guardrail: APPROVED. Position size $172.50 within 5% limit ($250). 2 open positions of 5 max. Daily loss $0 of $100 limit.",
    timestamp: "2026-02-14T10:30:16Z",
  },
  {
    id: "6",
    step: "execution",
    content:
      "[SHADOW] Executed LONG ETH/USDT @ $3,450.00. Size: 0.05 ETH. SL: $3,381 (-2%). TP: $3,588 (+4%).",
    timestamp: "2026-02-14T10:30:17Z",
  },
  {
    id: "7",
    step: "reflection",
    content:
      "Cycle complete. Analyzed 2 pairs. Decision: TRADE. Confidence: 0.78. Entry executed in shadow mode.",
    timestamp: "2026-02-14T10:30:20Z",
  },
];

const stepColors: Record<string, string> = {
  perception: "bg-blue-500/20 text-blue-400",
  memory: "bg-purple-500/20 text-purple-400",
  reasoning: "bg-yellow-500/20 text-yellow-400",
  risk_check: "bg-orange-500/20 text-orange-400",
  execution: "bg-green-500/20 text-green-400",
  reflection: "bg-cyan-500/20 text-cyan-400",
};

export function ThoughtLog() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          AI Thought Log
          <span className="text-xs font-normal text-muted-foreground">
            Real-time reasoning of the trading agent
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {thoughts.map((thought) => (
            <div
              key={thought.id}
              className="flex gap-3 p-3 rounded-lg bg-secondary/30 hover:bg-secondary/50 transition-colors"
            >
              <div className="flex-shrink-0 pt-0.5">
                <span
                  className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                    stepColors[thought.step] || "bg-gray-500/20 text-gray-400"
                  }`}
                >
                  {thought.step}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-foreground/90 leading-relaxed">
                  {thought.content}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {new Date(thought.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
