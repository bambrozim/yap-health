import { MetricChart } from "@/components/MetricChart";

const LABELS: Record<string, string> = {
  cardio: "Cardíaco",
  activity: "Atividade",
  sleep: "Sono",
  nutrition: "Nutrição",
  body: "Corpo",
};

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
  sleep: [
    { metric: "sleep_duration", title: "Duração do sono" },
    { metric: "sleep_deep", title: "Sono profundo" },
    { metric: "sleep_rem", title: "Sono REM" },
  ],
  nutrition: [
    { metric: "energy_kcal", title: "Energia" },
    { metric: "protein_g", title: "Proteína" },
    { metric: "carbs_g", title: "Carboidratos" },
    { metric: "fat_g", title: "Gordura" },
    { metric: "fiber_g", title: "Fibra" },
    { metric: "sugar_g", title: "Açúcar" },
    { metric: "sodium_mg", title: "Sódio" },
  ],
  body: [
    { metric: "weight_kg", title: "Peso" },
    { metric: "bmi", title: "IMC" },
    { metric: "body_fat_pct", title: "Gordura corporal" },
  ],
};

export function Domain({
  domain,
}: {
  domain: "cardio" | "activity" | "sleep" | "nutrition" | "body";
}) {
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
