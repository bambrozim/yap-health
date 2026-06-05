import { useQuery } from "@tanstack/react-query";

import { AlertsFeed } from "@/components/AlertsFeed";
import { ScoreCard } from "@/components/ScoreCard";
import { getAlerts, getInsights, getScore } from "@/lib/api";

const LABELS: Record<string, string> = {
  cardio: "Cardíaco",
  activity: "Atividade",
  sleep: "Sono",
};

type DomainKey = "cardio" | "activity" | "sleep";

export function Home({ onOpenDomain }: { onOpenDomain?: (d: DomainKey) => void }) {
  const score = useQuery({ queryKey: ["score"], queryFn: getScore });
  const alerts = useQuery({ queryKey: ["alerts"], queryFn: getAlerts });
  const insights = useQuery({ queryKey: ["insights"], queryFn: getInsights });

  return (
    <main className="mx-auto max-w-4xl space-y-8 p-8">
      <header>
        <h1 className="text-2xl font-bold">yap-health</h1>
        <p className="text-sm text-slate-500">
          Painel pessoal de saúde · dados de {score.data?.as_of ?? "—"}
        </p>
      </header>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
        <ScoreCard label="Score geral" score={score.data?.overall ?? null} />
        {Object.entries(score.data?.domains ?? {}).map(([k, v]) => (
          <button
            key={k}
            type="button"
            className="text-left transition hover:opacity-80"
            onClick={() => onOpenDomain?.(k as DomainKey)}
          >
            <ScoreCard label={LABELS[k] ?? k} score={v} />
          </button>
        ))}
      </div>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Alertas &amp; insights</h2>
        <AlertsFeed alerts={alerts.data ?? []} />
        {(insights.data ?? []).length > 0 && (
          <ul className="mt-3 space-y-2">
            {insights.data!.map((i) => (
              <li key={i.metric} className="text-sm text-slate-700">
                💡 {i.text}
              </li>
            ))}
          </ul>
        )}
      </section>

      <p className="text-xs text-slate-400">
        Informativo — não é aconselhamento médico.
      </p>
    </main>
  );
}
