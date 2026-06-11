import { useMutation, useQueryClient } from "@tanstack/react-query";

import { runImport } from "@/lib/api";

export function SyncButton() {
  const qc = useQueryClient();
  const sync = useMutation({
    mutationFn: runImport,
    onSuccess: () => {
      // Refresh every dashboard query after a successful import.
      qc.invalidateQueries();
    },
  });

  const result = sync.data;

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        type="button"
        onClick={() => sync.mutate()}
        disabled={sync.isPending}
        className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
      >
        {sync.isPending ? "Sincronizando…" : "Sincronizar do Drive"}
      </button>
      {sync.isError && (
        <span className="text-xs text-red-600">Falha ao sincronizar.</span>
      )}
      {result &&
        (result.ok ? (
          <span className="text-xs text-slate-500">
            {result.rows} registros de {result.files} arquivos
          </span>
        ) : (
          <span className="max-w-xs text-right text-xs text-amber-600">
            {result.reason}
          </span>
        ))}
    </div>
  );
}
