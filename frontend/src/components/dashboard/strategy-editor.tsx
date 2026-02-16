"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { useUserId } from "@/lib/hooks";

const exampleStrategies = [
  "Busca divergencias en el RSI de 15m pero solo opera si el sentimiento en Twitter es alcista",
  "Buy BTC when RSI < 30 on 1h timeframe and Fear & Greed Index is below 25. Take profit at +5%, stop loss at -2%",
  "Scalp ETH/USDT on 5m candles. Enter long when EMA9 crosses above EMA21 with volume > 1.5x average. Exit at +1.5% or -0.5%",
];

export function StrategyEditor() {
  const userId = useUserId();
  const [strategy, setStrategy] = useState("");
  const [name, setName] = useState("");
  const [timeframe, setTimeframe] = useState("15m");
  const [pairs, setPairs] = useState("BTC/USDT");
  const [parsedRules, setParsedRules] = useState<Record<string, unknown> | null>(null);
  const [parsing, setParsing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleParse = async () => {
    if (!strategy.trim() || !name.trim()) return;
    setParsing(true);
    setMessage(null);
    try {
      const result = await api.createStrategy({
        user_id: userId,
        name,
        description: strategy,
        timeframe,
        pairs: pairs.split(",").map((p) => p.trim()).filter(Boolean),
      });
      setParsedRules(result.parsed_rules);
      setMessage({ type: "success", text: `Strategy "${result.name}" created and parsed successfully` });
    } catch (err) {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Failed to parse strategy" });
    } finally {
      setParsing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Strategy Input */}
      <Card>
        <CardHeader>
          <CardTitle>Strategy Editor</CardTitle>
          <p className="text-sm text-muted-foreground">
            Describe your trading strategy in natural language. The AI will parse
            it into actionable rules.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-muted-foreground">
              Strategy Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My RSI Divergence Strategy"
              className="w-full mt-1 px-3 py-2 bg-secondary border border-border rounded-md text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-muted-foreground">
                Timeframe
              </label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="w-full mt-1 px-3 py-2 bg-secondary border border-border rounded-md text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="1m">1m</option>
                <option value="5m">5m</option>
                <option value="15m">15m</option>
                <option value="1h">1h</option>
                <option value="4h">4h</option>
                <option value="1d">1d</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-muted-foreground">
                Trading Pairs
              </label>
              <input
                type="text"
                value={pairs}
                onChange={(e) => setPairs(e.target.value)}
                placeholder="BTC/USDT, ETH/USDT"
                className="w-full mt-1 px-3 py-2 bg-secondary border border-border rounded-md text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-muted-foreground">
              Strategy Description (Natural Language)
            </label>
            <textarea
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
              rows={4}
              placeholder="Describe your trading strategy in plain language..."
              className="w-full mt-1 px-3 py-2 bg-secondary border border-border rounded-md text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleParse}
              disabled={parsing || !strategy.trim() || !name.trim()}
              className="px-4 py-2 bg-primary text-primary-foreground text-sm font-medium rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {parsing ? "Parsing..." : "Parse Strategy with AI"}
            </button>
          </div>

          {message && (
            <div
              className={`text-sm p-3 rounded-md ${
                message.type === "success"
                  ? "bg-green-500/10 text-green-400"
                  : "bg-red-500/10 text-red-400"
              }`}
            >
              {message.text}
            </div>
          )}

          {/* Example strategies */}
          <div className="pt-2">
            <p className="text-xs text-muted-foreground mb-2">
              Example strategies (click to use):
            </p>
            <div className="space-y-2">
              {exampleStrategies.map((ex, i) => (
                <button
                  key={i}
                  onClick={() => setStrategy(ex)}
                  className="block w-full text-left text-xs text-muted-foreground hover:text-foreground p-2 rounded bg-secondary/30 hover:bg-secondary/50 transition-colors"
                >
                  &quot;{ex}&quot;
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Parsed Rules Preview */}
      {parsedRules && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Parsed Rules
              <Badge variant="profit">AI Parsed</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-xs bg-secondary/50 p-4 rounded-lg overflow-x-auto text-foreground/80">
              {JSON.stringify(parsedRules, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
