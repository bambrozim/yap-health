import { useQuery } from "@tanstack/react-query";

import { Card } from "@/components/ui/card";
import { getCycle } from "@/lib/api";
import { FLOW_CLASS, FLOW_LABEL } from "@/lib/flow";

export function Cycle() {
  const q = useQuery({ queryKey: ["cycle"], queryFn: getCycle });
  const c = q.data;

  return (
    <main className="mx-auto max-w-3xl space-y-6 p-8">
      <h1 className="text-2xl font-bold">Ciclo menstrual</h1>

      {!c?.has_data ? (
        <p className="text-slate-500">Nenhum registro de ciclo encontrado.</p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <Stat label="Dia do ciclo" value={`${c.current_cycle_day}`} />
            <Stat label="Ciclo médio" value={c.avg_cycle_length != null ? `${c.avg_cycle_length} d` : "—"} />
            <Stat label="Períodos registrados" value={`${c.period_count}`} />
            <Stat label="Última menstruação" value={c.last_period_start ?? "—"} />
          </div>

          <Card className="p-4">
            <h2 className="mb-3 font-medium">Dias de menstruação</h2>
            <ul className="space-y-2">
              {c.days.map((d) => (
                <li key={d.date} className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <span className="text-sm text-slate-700">{d.date}</span>
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${FLOW_CLASS[d.flow] ?? ""}`}>
                    {FLOW_LABEL[d.flow] ?? d.flow}
                  </span>
                </li>
              ))}
            </ul>
          </Card>
        </>
      )}

      <p className="text-xs text-slate-400">
        Registro informativo do ciclo — não é aconselhamento médico.
      </p>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <Card className="p-4">
      <span className="text-xs text-slate-500">{label}</span>
      <div className="text-lg font-semibold">{value}</div>
    </Card>
  );
}
