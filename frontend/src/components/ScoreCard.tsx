import { Card } from "@/components/ui/card";

const color = (s: number | null) =>
  s == null
    ? "text-slate-400"
    : s >= 80
      ? "text-green-600"
      : s >= 50
        ? "text-amber-600"
        : "text-red-600";

export function ScoreCard({ label, score }: { label: string; score: number | null }) {
  return (
    <Card className="flex flex-col gap-2 p-6">
      <span className="text-sm text-slate-500">{label}</span>
      <span className={`text-4xl font-bold ${color(score)}`}>
        {score == null ? "—" : Math.round(score)}
      </span>
    </Card>
  );
}
