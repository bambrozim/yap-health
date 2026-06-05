import { useState } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { Domain } from "@/pages/Domain";
import { Home } from "@/pages/Home";

const qc = new QueryClient();

export type Route = "home" | "cardio" | "activity" | "sleep";

export default function App() {
  const [route, setRoute] = useState<Route>("home");
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
      {route === "home" ? <Home onOpenDomain={setRoute} /> : <Domain domain={route} />}
    </QueryClientProvider>
  );
}
