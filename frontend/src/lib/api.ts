import axios from "axios";

const client = axios.create({ baseURL: "http://localhost:8000/api" });

export interface Scoreboard {
  overall: number | null;
  domains: Record<string, number | null>;
  as_of: string;
}

export interface Series {
  metric: string;
  unit: string;
  points: { date: string; value: number }[];
}

export interface Alert {
  metric: string;
  status: string;
  message: string;
  source: string;
  value: number;
}

export interface Insight {
  metric: string;
  text: string;
  severity: string;
}

// v1: fixed window covering the available snapshot (Apr–May 2026).
// Make this user-selectable in a later iteration.
const range = "from=2026-04-01&to=2026-06-30";

export const getScore = () =>
  client.get<Scoreboard>(`/score?${range}`).then((r) => r.data);
export const getMetric = (m: string) =>
  client.get<Series>(`/metrics/${m}?${range}`).then((r) => r.data);
export const getAlerts = () =>
  client.get<{ alerts: Alert[] }>(`/alerts?${range}`).then((r) => r.data.alerts);
export const getInsights = () =>
  client
    .get<{ insights: Insight[] }>(`/insights?${range}`)
    .then((r) => r.data.insights);
