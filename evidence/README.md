# Execution evidence (text only)

Everything here was produced by running the build on a Databricks workspace (serverless compute, Unity Catalog
`rachopra_catalog.fe_bar`), then exporting the outputs as text. Nothing is a screenshot.

| Folder | What it contains | How it was produced |
|---|---|---|
| [`job_run/`](job_run/README.md) | Every task of the end-to-end job run: each notebook's code cells followed by their actual outputs (tables, prints, errors), plus run IDs, durations and results | `scripts/export_run_evidence.py <run_id>` (decodes `jobs export-run`) |
| [`sql/`](sql/README.md) | Governed query results: pipeline expectations and update lifecycle, table inventory and row counts, dashboard KPIs via the metric view, expiring balances, alerts, procurement cycle, quarterly review, ML forecast, AI outputs and their grounding checks, UC policies, tags and column docs, and Lakebase write-backs landing in UC | `scripts/sql_evidence.py` against a SQL warehouse |
| [`app/`](app/README.md) | Every API call the Databricks App serves: dashboard, expiring balances, line detail, alerts, procurement, quarterly review, Genie. Includes real write-backs (alert assignment, AI package submission, CFO sign-off) with status codes and latencies | `scripts/app_evidence.py` against the deployed app URL |

## Where to look for each required stage

| Stage | Strongest evidence |
|---|---|
| Lakeflow (Spark Declarative Pipelines) | `job_run/03_ingest_and_transform.md`, `sql/00_pipeline_update.md`, `sql/00_pipeline_expectations.md`, `sql/02_row_counts.md`, and the reconciliation in `job_run/04_govern_and_document.md` |
| Unity Catalog | `job_run/04_govern_and_document.md`: the row filter shown before/after narrowing an entitlement, payee PII masked/unmasked, governed tags, the metric view. Also `sql/17_uc_policies.md`, `sql/18_uc_tags.md`, `sql/19_uc_column_docs.md` |
| Lakebase | `job_run/07_lakebase_serving.md` (synced tables ONLINE, Postgres row counts, app grants, CDF status, Postgres query latency), `sql/20-23` (write-backs landed in UC), `app/README.md` |
| ML | `job_run/05_train_lapse_risk_model.md` (point-in-time training set, inner-split model selection, hold-out vs baseline, error by horizon, permutation importance, UC registration @champion), `sql/11-12` |
| GenAI | `job_run/06_forecast_and_ai_briefings.md` (briefings, grounding check, quarterly narratives, validated procurement packages), `sql/13-16` |
| Genie | `job_run/08_genie_space.md` (space config, 8 benchmark questions with Genie's SQL and results), `app/README.md` (Genie via the app) |
| Databricks App | `app/README.md` |
