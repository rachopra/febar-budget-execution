# Build notes: how this was built, and what running it taught us

This prototype was built AI-first: an agentic coding assistant (Claude Code) wrote the code, deployed it with
Databricks Asset Bundles and ran it on the workspace, under direction from the field engineer, who owned the
problem framing, design choices and review. Every claim in the README is backed by a run output in `evidence/`.
Below are the decisions that mattered and the defects that only showed up because the build was executed rather
than just written.

## Design decisions

| Decision | Why |
|---|---|
| Spark Declarative Pipelines for all of Lakeflow (Auto Loader → AUTO CDC → materialized views) | One declarative graph for ingestion, CDC, quality rules and the gold model; lineage and an event log for free. |
| Keep each tracker as its own bronze table; conform in silver | The customer requires the authoritative sources to stay intact. Bronze keeps source file, modification time and ingest time per record. |
| Two append flows into one `silver_spend_plan` | Offices submit spend plans on two different spreadsheet templates (one in $K). Each template gets its own normalising flow, and the target table is unified. |
| AUTO CDC SCD1 + SCD2 from the PR-tracker events | SCD1 gives the current state of each request. SCD2 gives the time spent in each stage, which drives PALT and procurement forecasting. |
| Invoices keyed by obligation document, not contract number | Option exercises funded from a later fiscal year share a contract number with the original award. Joining on the contract alone would charge expenditures to the wrong year's funds. |
| Row filter and column mask declared on the pipeline tables, driven by one entitlements table | Policies exist from the first write. The app's office scoping uses the same `office_access_map` (synced to Lakebase), so who-sees-which-office has one source of truth. |
| UC metric view for KPIs | Obligation rate and burn rate vs plan are defined once; Genie, the SQL evidence and the dashboard all use the same definition. |
| Lakebase for the app, not the warehouse | The app needs millisecond reads and transactional writes (alert actions, package requests, sign-offs). A CDF config streams those writes back to UC Delta, so leadership analytics sees the workflow too. |
| Point-in-time ML features, temporal validation | Lapse is forecast from what was knowable on each checkpoint date, rebuilt from event timestamps. Model selection uses an inner split (FY2023 → FY2024), and FY2025 is held out and never used for selection. |
| AI outputs are checked, not trusted | Every dollar figure and percentage in a briefing must trace back to a fact the model was given. Package drafts are validated against feasible acquisition types (by historical PALT) and the contracts on the line. |
| On-behalf-of-user Genie in the app | Genie questions run with the signed-in user's Unity Catalog permissions, so row filters apply per person. |

## Defects that execution caught (and the fix)

1. **Nested JSON arrived as strings.** Auto Loader with `inferColumnTypes=false` inferred the PR tracker's nested
   `pr` / `award` objects as STRING, so the silver flattening failed to resolve. Fix: infer types for the JSON feed
   only (CSV feeds stay raw strings typed in silver). Evidence: the pipeline event log for the failed update.
2. **Synthetic data was too pessimistic.** The first calibration produced 33% median lapse for the weakest office,
   but real agencies typically lapse a few percent of annual funds. The generator was recalibrated (PALT inflation,
   late submission, sweep behaviour) to a 2.9% median and a 5.8% dollar-weighted lapse, keeping the health → lapse
   signal (correlation -0.68).
3. **Injected anomalies were too frequent, and some were silently wrong.** Over-billing and duplicate rates
   produced about 85 alerts each, too noisy for a leadership view, so they were cut to realistic rates. Mis-keyed
   contract numbers sometimes collided with real contracts, which would have misattributed spend without any
   error. They are now malformed, so the `well_formed_contract_number` expectation flags them.
4. **Governed tags rejected our values.** The account enforces tag policies (`domain`, `layer`,
   `data_classification`, `source_system`, ...). We adopted the governed keys with their allowed values
   (`domain=finance`, `layer=gold`, `data_classification=cui`, `contains_pii=true`) and moved the source tracker to
   a free-form key.
5. **`ai_query` structured output.** DDL `responseFormat` takes exactly one top-level field. The briefing, review
   and package schemas are now wrapped in a single struct.
6. **Model choice is made on an inner split and the hold-out is reported as found.** The first (squared-loss) GBM
   halved forecast error, but a handful of programs lapse 30-50% and pull squared loss around. An inner temporal
   split (FY2023 → FY2024, never touching the FY2025 hold-out) selected absolute-error (median) loss. On the hold-out
   it cuts error 62% vs the spend-plan baseline (MAE 3.1 vs 8.2 pp, dollar MAE $1.09M vs $2.52M per line, R² 0.49
   vs -2.3). As a binary ">5% lapse" flag its AUC is level with the baseline (0.69 vs 0.71): the model's value is in
   sizing the lapse in dollars, which is what the procurement-package step needs. A random forest scored higher AUC
   on the hold-out, but it lost the inner-split selection, and picking it after seeing hold-out results would leak.
   It is the next candidate to evaluate on FY2026 expirations.
7. **Library version changes the model.** The same data and code gave hold-out MAE 2.6 pp under scikit-learn 1.6
   and 3.1 pp under 1.9 (the absolute-error loss implementation changed). The committed results use the version the
   job installed (1.9.x, recorded with the model in MLflow). Production should pin the training environment rather
   than pick a version by its score.
8. **Batch `ai_query` isn't available on every endpoint.** The newest Claude endpoints in the workspace rejected batch
   inference (`not supported for batch inference`); tested endpoint by endpoint, Claude Sonnet 4.6 supports it. Batch
   briefings use Sonnet 4.6 and the app's real-time drafting uses Sonnet 5.5 (which also rejects `temperature`).
9. **Prompts must never be spliced into SQL.** An apostrophe ("office's") in a prompt broke an `ai_query` statement
   built with string concatenation. All prompts are now DataFrame columns.
10. **The CDF to Unity Catalog silently skipped every table.** `list-cdf-statuses` reported "Does not have REPLICA
    IDENTITY FULL". The workflow DDL now sets it, and the notebook prints per-table CDF status, so a skip is visible.
11. **Measuring against a re-forecast hides the problem.** Offices' later spend-plan revisions true past months up to
    actuals, so the first quarterly review showed every office within 0.5% of plan, which is useless for a review.
    Execution is now measured against the approved baseline (the first revision after enactment); the latest
    revision is kept as the re-forecast. Agency burn vs plan went from "about 97%" to a meaningful 91.3%, with OTS at 83%.
12. **Lapse prevention must not create improper year-end spending.** An AI package put $7.4M onto a contract with
    $4.2M obligated. The prompt and validator now cap option exercises and modifications at the contract's obligated
    value and require a bona fide need of the current period; the batch total fell from $52.3M to $34.9M, all valid.
13. **Hard-coded scoring loops are slow on serverless.** Per-row, per-feature explanations took 10 minutes. Vectorised
    (12 batch predictions), scoring takes seconds.
