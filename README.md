# yap-health

Aplicativo **pessoal, local e offline** para centralizar, visualizar e interpretar os seus
dados de saúde. Importa dados de **Health Sync** e **Health Connect**, mostra gráficos por
domínio, gera **alertas e insights** baseados em diretrizes clínicas oficiais (com citação da
fonte) e calcula **sub-scores por domínio** que agregam num **score geral de saúde**.

> ⚠️ **Informativo — não é aconselhamento médico.** Alertas e scores são heurísticas baseadas em
> diretrizes populacionais (OMS, AHA, normas clínicas), não diagnóstico.

Nenhum dado sai da sua máquina: sem nuvem de terceiros, sem telemetria, sem custo de API.

## Arquitetura

```
pasta sincronizada (inbox)  →  ingestão  →  SQLite canônico  →  motor de regras
                                                  │                    │
                                                  └──→  FastAPI  ←──────┘
                                                          │
                                                   React (Vite) dashboard
```

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, SQLite.
- **Frontend:** React + TypeScript (Vite), Recharts, Tailwind.
- **Domínios:** Atividade, Cardíaco, Sono, Nutrição e Corpo (todos pontuados). Além de uma
  seção de **Ciclo menstrual** (do Clue), informativa e não pontuada.

## Fontes de dados e deduplicação

| Fonte | Papel |
|---|---|
| Health Connect export (`.db` SQLite) | Fonte dos 5 domínios (energia em cal, massa em g) |
| Health Sync CSVs (`*.csv`) | Fonte alternativa dos 5 domínios, já em unidades canônicas (kcal/g/kg) |
| Health Sync `.tcx` (treinos) | Suplemento — resumo de treino (duração, distância, calorias) |
| Clue export nativo (`measurements.json`) | Ciclo menstrual (período/fluxo) — informativo, **não pontuado** |

> **Importe só uma** das fontes dos 5 domínios por período (o `.db` do Health Connect **ou** os
> CSVs do Health Sync). As duas trazem as mesmas leituras; importar ambas duplicaria os dados.
> Os CSVs não têm sódio nem altura, então `sodium_mg` fica ausente e o IMC usa `YAP_HEIGHT_M`.

A ingestão é **idempotente**: cada medição recebe uma `dedup_key` (hash de
`métrica+timestamp+valor`), então reimportar arquivos sobrepostos não duplica.

## Pré-requisitos

- [uv](https://docs.astral.sh/uv/) (gerencia o Python 3.12 do backend)
- Node.js 18+ e npm (frontend)

## Como rodar

### Backend

```bash
cd backend
uv venv --python 3.12 .venv
uv pip install -e ".[dev]"

# Importar da origem (Drive auto-detectado ou pasta explícita):
.venv/bin/python -m app.cli                              # usa a origem resolvida
.venv/bin/python -m app.cli "../references/data/health_data"   # ou uma pasta específica

# Subir a API:
.venv/bin/uvicorn app.api.main:app --port 8000
```

A API serve em `http://localhost:8000`. Endpoints:
`/api/score`, `/api/metrics/{metric}`, `/api/alerts`, `/api/insights`, `/api/cycle`,
`POST /api/import/run`, `/api/import/status` (janela: `?from=YYYY-MM-DD&to=YYYY-MM-DD`).

### Ingestão a partir do Google Drive

O fluxo recomendado usa o **Google Drive for Desktop**, que monta o Drive como uma pasta local:

1. Instale o **Google Drive para computador** e faça login. O Drive vira algo como
   `~/Library/CloudStorage/GoogleDrive-<email>/My Drive/...`.
2. Coloque ali as pastas com os **mesmos nomes** de `data/health_data` (`Clue Woman Health`,
   `Health Sync Steps`, …) e jogue os arquivos novos nelas de tempos em tempos.
3. No dashboard, clique em **"Sincronizar do Drive"** (chama `POST /api/import/run`). O app
   **encontra a pasta automaticamente** dentro do mount do Drive e reimporta (idempotente).

A origem é resolvida assim: `YAP_SOURCE_DIR` (se definido) → auto-detecção do mount do Drive.
Defina `YAP_SOURCE_DIR` para forçar um caminho específico. O `.db`/`db_path` e outras opções
ficam em `app/config.py` (env `YAP_*`).

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

A v1 usa uma janela de datas fixa (abril–junho/2026) em `src/lib/api.ts` — torná-la
selecionável é um próximo passo.

## Testes

```bash
cd backend  && .venv/bin/python -m pytest -q
cd frontend && npm test
```

## Score de saúde

Cada métrica com meta vira uma aderência (verde=100, amarelo=60, vermelho=20). O sub-score do
domínio é a média das métricas pontuadas; o score geral é a média ponderada dos domínios.

| Métrica | Meta | Fonte |
|---|---|---|
| Passos | ≥ 8.000/dia (amarelo 5–8k) | OMS / literatura |
| FC de repouso | 60–100 bpm | American Heart Association |
| SpO₂ | ≥ 95% (amarelo 92–95) | norma clínica (Mayo/AHA) |
| Duração do sono | 7–9 h/noite (amarelo 6–10) | National Sleep Foundation |
| Sódio | < 2000 mg/dia (amarelo 2000–2500) | OMS |
| Açúcar | < 50 g/dia (amarelo 50–65) | OMS (proxy de açúcar total) |
| Fibra | ≥ 25 g/dia (amarelo 15–25) | OMS / DRI |
| IMC | 18,5–24,9 (amarelo 17–29,9) | OMS |
| HRV / FC / sono profundo·REM / energia·macros / peso·gordura | tendência (insight) / gráfico | — |
| Atividade moderada | 150–300 min/semana | OMS 2020 |
