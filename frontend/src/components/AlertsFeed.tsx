import { Badge } from "@/components/ui/badge";
import type { Alert } from "@/lib/api";

const tone = (s: string): "destructive" | "secondary" =>
  s === "red" ? "destructive" : "secondary";

export function AlertsFeed({ alerts }: { alerts: Alert[] }) {
  if (!alerts.length) {
    return <p className="text-slate-500">Sem alertas ativos.</p>;
  }
  return (
    <ul className="space-y-3">
      {alerts.map((a) => (
        <li key={a.metric} className="flex flex-col gap-1 border-b border-slate-100 pb-2">
          <div className="flex items-center gap-2">
            <Badge variant={tone(a.status)}>{a.status}</Badge>
            <span className="font-medium">{a.message}</span>
          </div>
          <span className="text-xs text-slate-500">Fonte: {a.source}</span>
        </li>
      ))}
    </ul>
  );
}
