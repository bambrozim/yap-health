# yap-health — Design

**Data:** 2026-06-05
**Status:** Todos os 5 domínios entregues e merjados: Atividade, Cardíaco, Sono, Nutrição e Corpo.
**Autor:** Bruna Ambrozim Silveira (com Claude)

## 1. Visão geral

`yap-health` é um aplicativo **pessoal, local e offline** para centralizar, visualizar e
interpretar os dados de saúde da usuária. O app:

- importa automaticamente dados de saúde (passos, frequência cardíaca, sono, nutrição,
  peso/composição corporal, treinos, etc.);
- mostra **visualizações em gráficos** por domínio;
- gera **alertas e insights determinísticos** baseados em diretrizes clínicas oficiais,
  sempre citando a fonte;
- calcula **sub-scores por domínio** que agregam num **score geral de saúde**.

Nenhum dado sai da máquina. Sem telemetria, sem nuvem de terceiros, sem custo de API.

> **Disclaimer:** o app é informativo e **não constitui aconselhamento médico**. Alertas e
> scores são heurísticas baseadas em diretrizes populacionais, não diagnóstico.

## 2. Decisões de produto (resumo do brainstorming)

| Tema | Decisão |
|---|---|
| Forma do app | Web app local (rodando na máquina, acessado via navegador) |
| Ingestão de dados | Pasta auto-sincronizada (híbrido): Health Sync exporta automaticamente para uma pasta que sincroniza com o PC; o app observa a pasta e importa sozinho |
| Cérebro (insights/score) | Motor de **regras determinísticas** baseado em diretrizes oficiais; cada alerta cita a fonte. (Camada conversacional/LLM fica para depois, sem retrabalho.) |
| Stack backend | Python + **FastAPI** + SQLite |
| Stack frontend | **React** (Vite) + **shadcn/ui** + **Recharts** |
| Modelo de score | Sub-scores por domínio (0–100) → score geral ponderado |
| Escopo v1 | **Fatia vertical**: pipeline completo ponta-a-ponta para **Atividade + Cardíaco**, depois replicar para Sono → Nutrição → Corpo |

### Restrição técnica registrada

Health Connect só é legível **dentro do Android**. Um app web no PC não lê o Health Connect
diretamente. A automação "real local" escolhida é: Health Sync exporta no agendamento dele
para uma pasta sincronizada (Google Drive / Syncthing / etc.); o app **observa essa pasta** e
importa. Da perspectiva da usuária é automático ponta-a-ponta, sem nuvem de terceiros e sem
custo. (Alternativas descartadas: Terra/Rook = pago + nuvem; app nativo Android = muda a forma
do produto.)

## 3. Inventário dos dados (snapshot atual em `references/data/health_data`)

Duas fontes, **com sobreposição**:

### 3.1 Health Sync (arquivos CSV/FIT/TCX)

Exports diários e de intervalo mensal. Formato típico: colunas `Date,Time,<valor>,Source`.

| Domínio | Arquivos | Conteúdo |
|---|---|---|
| Heart rate | `Heart rate`, `HRV`, `RHR` | FC por minuto, HRV (rmssd), FC de repouso |
| Steps | `Steps` | Passos por intervalo |
| Sleep | `Sleep` | `Duration in seconds`, `Sleep stage` (light/deep/rem/awake) |
| Nutrition | `Nutrition` | kCal, carbo, colesterol, gordura, fibra, açúcar, proteína, vit. A/C/D |
| Weight | `Weight … Huawei Health` (CSV+FIT) | peso, % e massa de gordura, massa magra, músculo, água, TMB |
| Oxygen saturation | `Oxygen saturation` | SpO₂ % |
| Energy burned | `Energy burned` | calorias ativas/repouso/total |
| Activities | `TRAINING … .csv/.fit/.tcx` | tipo, duração, distância; FIT/TCX trazem laps/segmentos/GPS |

### 3.2 "Clue Woman Health" — export completo do Health Connect (SQLite, ~3 MB)

Apesar do nome, é um dump completo do Health Connect (`health_connect_export.db`), com dezenas
de `*_record_table`. Tabelas com dados (contagens no snapshot): `steps_record_table` (1612),
`total_calories_burned_record_table` (1027), `distance_record_table` (1177),
`active_calories_burned_record_table` (778), `oxygen_saturation_record_table` (735),
`heart_rate_variability_rmssd_record_table` (466), `activity_intensity_record_table` (254),
`heart_rate_record_table` (186), `nutrition_record_table` (52), `exercise_session_record_table`
(21), `sleep_session_record_table` (11), `resting_heart_rate_record_table` (8),
`weight_record_table` (3), entre outras.

⚠️ **As tabelas de ciclo menstrual estão vazias** (menstruação, muco cervical, ovulação,
temperatura basal = 0 linhas). O domínio "saúde da mulher" **não tem dados** neste export — não
faz parte do v1. Se dados de ciclo aparecerem em exports futuros, o esquema deve acomodá-los.

Cada registro do Health Connect tem `uuid` e `dedupe_hash` — base sólida para importação
idempotente.

## 4. Ingestão e deduplicação

### 4.1 Fonte canônica

O **Health Connect export (SQLite) é a fonte primária**: é o armazenamento estruturado de
origem, com `uuid`/`dedupe_hash`. Os CSVs do Health Sync são **derivados** dele (campo
`Source = nl.appyhapps.healthsync`).

- **Primário:** `HealthConnectSqliteImporter` — lê o `.db` e mapeia cada `*_record_table`
  relevante para o esquema canônico.
- **Suplementar:** `HealthSyncFitImporter` / `HealthSyncTcxImporter` para **detalhe de treino**
  (laps, segmentos, GPS) ausente no Health Connect; importers de CSV como fallback quando
  faltar algo.

### 4.2 Pipeline

```
inbox/  --(watcher: watchdog)-->  detecta arquivo novo
   -> seleciona importer pelo formato/nome
   -> parseia e normaliza para o esquema canônico
   -> upsert idempotente (dedup por chave natural)
   -> registra ImportRun (arquivo, origem, linhas, status, timestamp)
```

- **Watcher:** biblioteca `watchdog` observando a pasta sincronizada.
- **Idempotência:** chave natural = `source_uuid` quando existe; senão hash de
  `(metric, ts, value, source)`. Reimportar arquivos sobrepostos **não duplica**.
- **Reprocessável:** importar a mesma pasta duas vezes converge para o mesmo estado.

### 4.3 Esquema canônico (SQLite do app)

- `measurements` — séries numéricas em formato longo:
  `(id, metric, ts, value, unit, source, source_uuid, imported_at)`.
  Cobre FC, HRV, RHR, SpO₂, passos, calorias ativas/repouso/total, distância, peso e
  componentes de composição corporal.
- `sleep_segments` — `(start_ts, end_ts, stage, source, source_uuid)`.
- `workouts` — `(type, start_ts, end_ts, duration_s, distance_km, calories, avg_hr, source, source_uuid)`,
  com link opcional para samples detalhados (FIT/TCX).
- `nutrition_entries` — `(ts, meal, name, kcal, carb_g, fat_g, fiber_g, sugar_g, protein_g, chol_mg, vit_a_mcg, vit_c_mg, vit_d_mcg, source, source_uuid)`.
- `import_runs` — auditoria de importações.

Migrações versionadas (ex: Alembic ou SQL scripts simples).

## 5. Motor de regras: metas, alertas, score

Determinístico, transparente, testável. Sem LLM no v1.

### 5.1 Metas (`targets`)

Tabela de metas por métrica, **cada uma com citação da fonte**. Faixas a **validar em fonte
confiável** antes de cravar (ver §8). Referência inicial:

| Métrica | Meta (a validar) | Fonte |
|---|---|---|
| Atividade moderada | 150–300 min/semana | OMS |
| Passos/dia | ~8–10k (heurística) | literatura / OMS |
| SpO₂ | ≥ 95% | faixa clínica usual |
| FC de repouso | faixa por idade/sexo; tendência | ACSM / literatura |
| HRV | linha de base individual; tendência | literatura |
| Sódio | < 2 g/dia | OMS |
| Açúcar livre | < 10% das kcal totais | OMS |
| Sono | 7–9 h/noite (adulto) | literatura do sono |

As metas determinam **status por métrica** (verde/amarelo/vermelho) na agregação diária e
disparam **alertas** quando fora da faixa.

### 5.2 Scoring

- **Sub-score por domínio (0–100):** cada métrica do domínio vira uma aderência normalizada
  0–100 vs. sua meta; ponderação intradomínio configurável; agrega no sub-score.
- **Score geral:** combinação ponderada dos sub-scores (pesos configuráveis, default explícito).
- Domínios: **Atividade, Cardíaco, Sono, Nutrição, Corpo**.

### 5.3 Insights

Afirmações determinísticas a partir de tendências (médias móveis, deltas semana-a-semana,
detecção de fora-da-faixa). Ex: *"seu RHR subiu 6 bpm vs. a média das últimas 4 semanas"*.
Cada insight referencia a regra/fonte que o gerou.

## 6. API (FastAPI)

Endpoints REST consumidos pelo frontend (nomes indicativos):

- `GET /score` — score geral + sub-scores por domínio (período).
- `GET /metrics/{metric}?from&to&agg` — série temporal agregada.
- `GET /domains/{domain}` — métricas, aderência e gráficos do domínio.
- `GET /alerts` / `GET /insights` — itens ativos.
- `GET /import/status` — última sincronização, runs recentes.
- (interno) watcher dispara ingestão; sem endpoint de upload no v1.

## 7. Frontend (React + Vite + shadcn/ui + Recharts)

- **Home:** card do score geral + cards de sub-score por domínio + feed de alertas/insights.
- **Página por domínio:** gráficos de série temporal e distribuições, aderência às metas,
  histórico, status atual.
- **Status de importação:** última sync, registros importados, fonte.
- Tema limpo, responsivo; foco em legibilidade dos gráficos.

## 8. Escopo do v1 (fatia vertical)

Construir o pipeline **completo ponta-a-ponta** para dois domínios:

- **Atividade:** passos, energia gasta (ativa/repouso/total), treinos (FIT/TCX para detalhe).
- **Cardíaco:** FC, HRV, FC de repouso, SpO₂.

Entregáveis do v1:

1. Ingestão (Health Connect SQLite + Health Sync FIT/TCX/CSV) com dedup idempotente, para as
   métricas dos dois domínios.
2. Esquema canônico + migrações.
3. Metas validadas e motor de regras para Atividade + Cardíaco (status, alertas, insights).
4. Sub-scores dos dois domínios alimentando um score geral (parcial).
5. API FastAPI cobrindo os endpoints acima para esses domínios.
6. Frontend: Home (score + cards) + páginas de Atividade e Cardíaco com gráficos.
7. Watcher da pasta funcionando.

**Fora do v1 (próximas fatias):** Sono → Nutrição → Corpo; camada conversacional/LLM; dados de
ciclo menstrual (sem dados hoje).

## 9. Estrutura do projeto

```
yap-health/
  backend/
    app/
      api/          # rotas FastAPI
      ingestion/    # watcher + importers (HealthConnect SQLite, FIT, TCX, CSV)
      domain/       # modelos canônicos, métricas, agregações
      rules/        # targets, scoring, insights (com citações de fonte)
      db/           # SQLite, migrações
    tests/
  frontend/         # Vite + React + shadcn/ui + Recharts
  data/
    inbox/          # pasta observada (sincronizada)  [gitignored]
    app.db          # banco canônico do app           [gitignored]
  docs/superpowers/specs/
  references/       # overview.md + dados (já existe)
```

## 10. Itens em aberto / a resolver na implementação

- **Validar faixas de metas** (§5.1) em fontes confiáveis (OMS, ACSM, DRI/NIH, guias do sono)
  e registrar a citação exata de cada uma.
- Definir **pesos default** intradomínio e entre domínios para os scores.
- Estratégia de **médias móveis / janelas** para insights de tendência.
- Confirmar bibliotecas de parsing FIT/TCX (ex: `fitparse`, `python-tcxparser`).
- Tratamento de **timezones** (os exports trazem `zone_offset` no Health Connect).
- Tratamento de **lacunas/dias sem dados** no cálculo de score.
