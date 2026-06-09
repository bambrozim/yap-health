import { Card } from "@/components/ui/card";
import type { CycleSummary } from "@/lib/api";

export function CycleCard({
  cycle,
  onClick,
}: {
  cycle: CycleSummary | undefined;
  onClick?: () => void;
}) {
  const body = !cycle?.has_data ? (
    <p className="text-sm text-slate-500">Sem registros de ciclo.</p>
  ) : (
    <div className="flex flex-col gap-1">
      <span className="text-4xl font-bold text-rose-600">
        Dia {cycle.current_cycle_day}
      </span>
      <span className="text-sm text-slate-500">
        Última menstruação: {cycle.last_period_start} – {cycle.last_period_end}
      </span>
      <span className="text-sm text-slate-500">
        Ciclo médio:{" "}
        {cycle.avg_cycle_length != null
          ? `${cycle.avg_cycle_length} dias`
          : "— (precisa de ≥ 2 ciclos)"}
      </span>
    </div>
  );

  return (
    <button type="button" className="w-full text-left" onClick={onClick}>
      <Card className="flex flex-col gap-2 p-6 transition hover:opacity-80">
        <span className="text-sm font-medium text-slate-600">Ciclo menstrual</span>
        {body}
      </Card>
    </button>
  );
}
