import { MetricChart } from "@/components/MetricChart";

const LABELS: Record<string, string> = { cardio: "Cardíaco", activity: "Atividade" };

const DOMAIN_METRICS: Record<string, { metric: string; title: string }[]> = {
  cardio: [
    { metric: "resting_heart_rate", title: "FC de repouso" },
    { metric: "spo2", title: "SpO₂" },
    { metric: "hrv_rmssd", title: "HRV (rmssd)" },
    { metric: "heart_rate", title: "Frequência cardíaca" },
  ],
  activity: [
    { metric: "steps", title: "Passos" },
    { metric: "active_calories", title: "Calorias ativas" },
    { metric: "distance_km", title: "Distância" },
  ],
};

export function Domain({ domain }: { domain: "cardio" | "activity" }) {
  return (
    <main className="mx-auto max-w-4xl space-y-4 p-8">
      <h1 className="text-2xl font-bold">{LABELS[domain] ?? domain}</h1>
      <div className="grid gap-4 md:grid-cols-2">
        {DOMAIN_METRICS[domain].map((m) => (
          <MetricChart key={m.metric} {...m} />
        ))}
      </div>
    </main>
  );
}
