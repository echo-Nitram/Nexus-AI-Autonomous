"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, ThoughtLog as ThoughtLogType } from "@/lib/api";
import { useApi, useUserId } from "@/lib/hooks";

const stepColors: Record<string, string> = {
  perception: "bg-blue-500/20 text-blue-400",
  memory: "bg-purple-500/20 text-purple-400",
  reasoning: "bg-yellow-500/20 text-yellow-400",
  risk_check: "bg-orange-500/20 text-orange-400",
  execution: "bg-green-500/20 text-green-400",
  reflection: "bg-cyan-500/20 text-cyan-400",
};

export function ThoughtLog() {
  const userId = useUserId();
  const { data: thoughts, loading, error } = useApi(
    () => api.getThoughts(userId),
    [userId],
  );

  const list: ThoughtLogType[] = thoughts ?? [];

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
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-16 bg-secondary/30 rounded animate-pulse" />
            ))}
          </div>
        ) : error ? (
          <p className="text-sm text-muted-foreground">Unable to load thought log</p>
        ) : list.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No agent activity yet. Deploy a strategy to see the AI reasoning here.
          </p>
        ) : (
          <div className="space-y-3">
            {list.map((thought) => (
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
        )}
      </CardContent>
    </Card>
  );
}
