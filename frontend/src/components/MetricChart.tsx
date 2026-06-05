import { useQuery } from "@tanstack/react-query";
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card } from "@/components/ui/card";
import { getMetric } from "@/lib/api";

export function MetricChart({ metric, title }: { metric: string; title: string }) {
  const q = useQuery({ queryKey: ["metric", metric], queryFn: () => getMetric(metric) });
  const data = q.data?.points ?? [];
  return (
    <Card className="p-4">
      <h3 className="mb-2 font-medium">
        {title} <span className="text-xs text-slate-400">({q.data?.unit})</span>
      </h3>
      {data.length === 0 ? (
        <p className="py-12 text-center text-sm text-slate-400">Sem dados no período.</p>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data}>
            <XAxis dataKey="date" hide />
            <YAxis width={40} domain={["auto", "auto"]} />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke="#2563eb" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
