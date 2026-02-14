"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PortfolioPanel } from "@/components/dashboard/portfolio-panel";
import { ThoughtLog } from "@/components/dashboard/thought-log";
import { PositionsTable } from "@/components/dashboard/positions-table";
import { StrategyEditor } from "@/components/dashboard/strategy-editor";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<"overview" | "thoughts" | "strategy">("overview");

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center font-bold text-sm">
              N
            </div>
            <div>
              <h1 className="text-lg font-bold">Nexus AI Trader</h1>
              <p className="text-xs text-muted-foreground">Autonomous Trading v2.0</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="shadow">Shadow Mode</Badge>
            <div className="w-2 h-2 rounded-full bg-green-500 pulse-green" />
            <span className="text-xs text-muted-foreground">Agent Active</span>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="container mx-auto px-6 pt-4">
        <nav className="flex gap-1 border-b border-border">
          {(["overview", "thoughts", "strategy"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium capitalize transition-colors border-b-2 -mb-px ${
                activeTab === tab
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab === "thoughts" ? "AI Thought Log" : tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <main className="container mx-auto px-6 py-6">
        {activeTab === "overview" && (
          <div className="space-y-6">
            <PortfolioPanel />
            <PositionsTable />
          </div>
        )}

        {activeTab === "thoughts" && <ThoughtLog />}

        {activeTab === "strategy" && <StrategyEditor />}
      </main>
    </div>
  );
}
