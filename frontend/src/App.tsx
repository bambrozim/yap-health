import { useState } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { Cycle } from "@/pages/Cycle";
import { Domain } from "@/pages/Domain";
import { Home } from "@/pages/Home";

const qc = new QueryClient();

export type Route =
  | "home"
  | "cardio"
  | "activity"
  | "sleep"
  | "nutrition"
  | "body"
  | "cycle";

export default function App() {
  const [route, setRoute] = useState<Route>("home");

  const page =
    route === "home" ? (
      <Home onNavigate={setRoute} />
    ) : route === "cycle" ? (
      <Cycle />
    ) : (
      <Domain domain={route} />
    );

  return (
    <QueryClientProvider client={qc}>
      {route !== "home" && (
        <button
          type="button"
          className="m-4 text-sm text-slate-600 underline"
          onClick={() => setRoute("home")}
        >
          ← Home
        </button>
      )}
      {page}
    </QueryClientProvider>
  );
}
