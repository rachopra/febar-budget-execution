# Budget Execution & Financial Oversight on Databricks

**A federal civilian agency's Office of the CFO gets one governed, current view of budget execution, from spend plan
to procurement request, obligation and invoice. It finds the money that is about to lapse early enough to put it
to work.**

> All data is synthetic, generated for a fictional agency (the "Department of Civic Infrastructure", Treasury agency
> code 999). The scenario is modelled on a real federal budget-execution requirement, but no customer data, names or
> documents are included.

---

## 1. The customer problem

Program offices track budget execution in separate, inconsistently updated spreadsheets:

| Today's silo | What it holds | Pain |
|---|---|---|
| **Spend-plan tracker** | Planned obligations by PPA (Program, Project, Activity), object class and month | Two templates (one in $K), offices re-plan irregularly or never |
| **Procurement-request (PR) tracker** | PR status changes from draft to award | No view of how long PRs sit in each stage, or which won't award before funds expire |
| **Invoice data** | Invoices and grant drawdowns after obligation | Not tied back to the budget line that funded it |

Leadership therefore can't see obligation rate, burn rate vs plan, or **unobligated balances approaching expiration**
until it's too late. Annual funds not obligated by **September 30** lapse and are lost to the program. The reporting
date in this build is **31 July 2026**: early Q4, 61 days before most balances expire, when this view matters most.

**Who it serves**

* **Executive sponsor: the CFO / Budget Director.** Wants fewer lapsed dollars, no Antideficiency Act exposure, and
  a defensible quarterly performance review.
* **Domain owners: budget analysts, program managers, contracting officers.** Want to know which lines and which PRs
  to act on this week, without reconciling three spreadsheets.

## 2. What was built

```
 Raw extracts (UC Volume)            Spark Declarative Pipeline (Lakeflow)                     Consumers
 ┌──────────────────────┐   Auto    ┌────────────┐  append flows,   ┌────────────┐  MVs   ┌──────────────────────────┐
 │ budget authority CSV │──Loader──▶│  bronze_*  │──AUTO CDC SCD1/2─▶│  silver_*  │──────▶│ gold_* + metric view      │
 │ spend plans (2 tmpl) │           │ (raw, lin- │  expectations,   │ (typed,    │       │ budget execution, monthly │
 │ PR-tracker JSON      │           │  eage cols)│  dedupe          │ conformed) │       │ burn, procurement cycle,  │
 │ invoice register CSV │           └────────────┘                  └────────────┘       │ risk alerts, quarterly    │
 └──────────────────────┘                 Unity Catalog: row filter (office), column mask (payee PII),     └─────┬────┘
                                          governed tags, column docs, lineage, metric view                     │
     ┌───────────────────────────────────────────────────────────────────────────────────────────────────────┤
     ▼                                   ▼                                      ▼                           ▼
 ML: lapse-risk model            GenAI: ai_query briefings,           Genie space                   Lakebase (Postgres)
 (MLflow, UC registry,           quarterly review narratives,         "Budget Execution -           synced gold tables ──▶ Databricks App
  @champion, point-in-time       procurement package drafts           Ask the Data"                 workflow write-back ──CDF──▶ UC Delta
  features, explained)           (grounding + validation checks)      (on-behalf-of-user in app)
```

| Required stage | Implementation | Code | Execution evidence |
|---|---|---|---|
| **Lakeflow**: ingest | Spark Declarative Pipeline (`pyspark.pipelines`): 6 Auto Loader bronze tables, 2 append flows normalising the spend-plan templates, AUTO CDC SCD1 + SCD2 over PR-tracker events, 24 data-quality expectations, gold materialized views in SQL | [`src/pipeline/`](src/pipeline) · [`resources/pipeline.yml`](resources/pipeline.yml) | [`evidence/job_run/03_ingest_and_transform.md`](evidence/job_run) · [`evidence/sql/00_pipeline_*`](evidence/sql) |
| **Unity Catalog**: govern | Office row filter + payee-PII column mask declared on pipeline tables, driven by one entitlements table; governed tags; column documentation; UC metric view `mv_budget_execution`; lineage | [`00_setup_governance.py`](src/notebooks/00_setup_governance.py) · [`02_govern_and_document.py`](src/notebooks/02_govern_and_document.py) | [`evidence/job_run/04_govern_and_document.md`](evidence/job_run) (row filter and mask demonstrated before/after) |
| **Lakebase**: operational serving | Lakebase Autoscaling project; 10 synced tables (gold → Postgres); `workflow` schema for app writes with least-privilege grants; CDF config streams writes back to UC Delta (`lb_app_*_history`) | [`05_lakebase_operational_serving.py`](src/notebooks/05_lakebase_operational_serving.py) | [`evidence/job_run/07_lakebase_serving.md`](evidence/job_run) · [`evidence/sql/20-23`](evidence/sql) (writes in UC) |
| **ML / GenAI**: make it intelligent | Lapse-risk GBM on point-in-time features, temporal validation vs the spend-plan baseline, registered in UC (`@champion`), per-line explanations. `ai_query` execution briefings, quarterly review narratives and procurement package drafts, each with grounding / validation checks | [`src/ml/`](src/ml) · [`03_train_lapse_risk_model.py`](src/notebooks/03_train_lapse_risk_model.py) · [`04_forecast_and_ai_briefings.py`](src/notebooks/04_forecast_and_ai_briefings.py) | [`evidence/job_run/05_*.md`, `06_*.md`](evidence/job_run) · [`evidence/sql/11-16`](evidence/sql) |
| **Genie**: natural language | Genie space over gold tables, metric view, forecast and row-filtered PR table; glossary, rules, trusted SQL; benchmark questions run through the Conversation API | [`06_genie_space.py`](src/notebooks/06_genie_space.py) | [`evidence/job_run/08_genie_space.md`](evidence/job_run) (questions, generated SQL, results) |
| **Databricks App**: surface it | FastAPI + React app on Lakebase: execution dashboard, expiring balances with forecasts and AI briefings, risk alerts with write-back, procurement pipeline, AI package initiation, quarterly sign-off, embedded Genie | [`app/`](app) · [`resources/app.yml`](resources/app.yml) | [`evidence/app/`](evidence/app) (API responses, writes round-tripped to UC) |

Everything is deployed and run with one Databricks Asset Bundle and one job,
[`febar-budget-execution-e2e`](resources/job.yml):
`setup_governance → land_raw_data → ingest_and_transform (SDP) → govern_and_document → train_lapse_risk_model →
forecast_and_ai_briefings → lakebase_serving → genie_space`.

## 3. Results (from the committed run)

All figures below are from the committed end-to-end run (`evidence/`), as of the 31 July 2026 reporting date.

### What leadership sees on day one

| Buyer KPI | Value | Evidence |
|---|---|---|
| Current budget authority under management | **$2.15B** across 45 budget lines, 29 PPAs, 6 offices | `sql/03_agency_kpis.md` |
| Obligated to date / obligation rate | **$1.36B / 63.2%** | `sql/03_agency_kpis.md` |
| Burn rate vs approved spend plan | **91.3%**, i.e. **$130M behind plan**; worst office OTS at 83% | `sql/04_funding_by_office.md` |
| Expended (paid) to date | $758M | `sql/03_agency_kpis.md` |
| Unobligated balances expiring in ≤ 90 days | **$306M on 29 lines**, of which **$46.6M is not even committed** | `sql/05_expiring_balances.md` |
| ML-projected year-end lapse (lines in forecast window) | **$65.9M**, $46.5M of it on 11 critical/high-risk lines | `sql/11_lapse_forecast.md` |
| Antideficiency Act exposure caught | 1 line obligated **$1.36M beyond its apportionment** | `sql/07_risk_alert_examples.md` |
| Funds-control exceptions | 4 lines with commitments exceeding available balance ($7.0M) | `sql/06_risk_alerts_summary.md` |
| Procurements that will miss fund expiration | 10 open PRs, **$19.6M**, flagged from historical PALT | `sql/08_procurement_cycle.md` |
| Improper-payment risks before payment | 20 potential duplicate invoices ($3.7M), 15 obligations over-billed ($3.5M), 12 invoices matching no obligation | `sql/06_risk_alerts_summary.md` |
| Prompt Payment Act exposure | 36 invoices due or past due ($6.2M); $96.9K interest already paid this fiscal year on 288 late payments | `sql/06_risk_alerts_summary.md` |

### Intelligence that is measured, not asserted

* **Lapse-risk model** (HistGradientBoosting, absolute-error loss, chosen on an inner FY2023→FY2024 split). On the
  FY2025 hold-out it cuts forecast error **62%** vs the status-quo spend-plan assumption: MAE 3.1 vs 8.2 percentage
  points, dollar MAE $1.09M vs $2.52M per line, R² 0.49 vs -2.3. As a yes/no ">5% lapse" flag it is level with the
  baseline (AUC 0.69 vs 0.71), so it is used to size dollars, not as a classifier. Registered as
  `rachopra_catalog.fe_bar.lapse_risk_model@champion`, with per-line drivers. `job_run/05_train_lapse_risk_model.md`.
* **GenAI** (`ai_query`, Claude Sonnet 4.6 batch; Claude Sonnet 5.5 real-time in the app) writes a briefing per
  line, a quarterly review per office and a procurement package per lapsing line. Every $ and % must trace to the
  facts the model was given: 27 of 29 briefings (93%) pass, and the rest, plus 4 of 6 office narratives where the
  model computed its own year-to-date percentage, are flagged for analyst review. All 26 package drafts ($34.9M)
  pass validation; packages are validated against acquisition types that can award in time
  (historical PALT), active contracts on the line, the projected lapse, and the contract's obligated value (a
  bona-fide-need guardrail against year-end "use it or lose it" spending). `sql/14_ai_grounding.md`, `sql/16_ai_procurement_packages.md`.
* **Genie** answered all 8 benchmark leadership questions with SQL over the metric view and gold tables
  (`job_run/08_genie_space.md`), and answers in the app on behalf of the signed-in user (`app/README.md`).

### Platform behaviour

* Spark Declarative Pipeline full refresh of ~100K raw records across 6 feeds: **~2.5 minutes** on serverless
  (`sql/00_pipeline_update.md`). 24 expectations; every anomaly the generator injected was caught (12 malformed
  contract numbers, 6 PR events without an ID, ~80 duplicate event deliveries removed).
* App reads from Lakebase return in **40-120 ms** (`app/README.md`). A write in the app (alert assignment, package
  submission, CFO sign-off) lands in Postgres and is streamed to Unity Catalog Delta by the CDF config
  (`sql/21-23_*.md`), so analysts and Genie can see what was done.
* Unity Catalog policies are declared on the pipeline tables and proven in the run: an OTS-scoped principal sees
  only OTS's procurement requests; payee TIN and bank numbers are masked unless entitled (`job_run/04_govern_and_document.md`).


## 4. Run it

```bash
databricks bundle deploy -t dev                    # SDP pipeline, e2e job, app
databricks bundle run budget_execution_e2e         # end-to-end on serverless (~25 min)
databricks bundle run budget_execution_app         # deploy + start the app
python scripts/export_run_evidence.py <run_id>     # executed notebooks -> evidence/job_run/*.md
python scripts/sql_evidence.py --pipeline-id <id>  # governed query results -> evidence/sql/*.md
python scripts/app_evidence.py                     # app API calls + write-backs -> evidence/app/README.md
```

First deployment on a new workspace: run the job once (it creates the Lakebase database and the Genie space),
set `lakebase_database` and `genie_space_id` in `databricks.yml`, then deploy the app. Later job runs re-apply
the app service principal's Postgres grants (notebook 05) after each synced-table refresh.

Configuration lives in [`databricks.yml`](databricks.yml): catalog `rachopra_catalog`, schema `fe_bar`, reporting
date `2026-07-31`, warehouse, Foundation Model endpoints, Lakebase project.

## 5. Repository map

```
databricks.yml, resources/        Asset Bundle: SDP pipeline, e2e job, app
src/datagen/budget_generator.py   synthetic agency simulator (CRs, Q4 sweep, PALT, anomalies)
src/pipeline/                     bronze.py (Auto Loader) · silver.py (append flows, AUTO CDC, policies) · gold.sql
src/ml/lapse_features.py          point-in-time feature SQL shared by training and scoring
src/notebooks/00-06               governance, landing, UC docs/policies, ML, GenAI, Lakebase, Genie
app/                              Databricks App (FastAPI + React, Lakebase, Genie, Foundation Model API)
evidence/                         text evidence of execution (see evidence/README.md)
docs/BUILD_NOTES.md               design decisions and the defects execution caught
```
