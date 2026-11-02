# Job run 252269105798616: `[dev rahul_chopra] febar-budget-execution-e2e`

Run page: https://fevm-rachopra-cyber-demo.cloud.databricks.com/?o=7474648312380302#job/135488465251280/run/252269105798616

Overall result: **SUCCESS**. Tasks forecast_and_ai_briefings, genie_space, lakebase_serving were re-run in a repair of this run; the final attempt of each task is shown. Repairs: (1) forecast_and_ai_briefings, lakebase_serving and genie_space after the bona-fide-need guardrail was added to procurement package drafting; (2) lakebase_serving after the app gained reprogramming and line-notes workflow tables (the CDF config had to be recreated to stream them, see docs/BUILD_NOTES.md items 15-16); (3) genie_space so the space reads the live CDF history tables, including reprogramming and notes.

| # | Task | Type | Result | Duration (s) | Evidence |
|---|---|---|---|---|---|
| 1 | `setup_governance` | notebook | SUCCESS | 50 | [01_setup_governance.md](01_setup_governance.md) |
| 2 | `land_raw_data` | notebook | SUCCESS | 74 | [02_land_raw_data.md](02_land_raw_data.md) |
| 3 | `ingest_and_transform` | pipeline | SUCCESS | 173 | [03_ingest_and_transform.md](03_ingest_and_transform.md) |
| 4 | `govern_and_document` | notebook | SUCCESS | 114 | [04_govern_and_document.md](04_govern_and_document.md) |
| 5 | `train_lapse_risk_model` | notebook | SUCCESS | 126 | [05_train_lapse_risk_model.md](05_train_lapse_risk_model.md) |
| 6 | `forecast_and_ai_briefings` | notebook | SUCCESS | 307 | [06_forecast_and_ai_briefings.md](06_forecast_and_ai_briefings.md) |
| 7 | `lakebase_serving` | notebook | SUCCESS | 213 | [07_lakebase_serving.md](07_lakebase_serving.md) |
| 8 | `genie_space` | notebook | SUCCESS | 206 | [08_genie_space.md](08_genie_space.md) |
