# Train Lapse Risk Model

- Job task: `train_lapse_risk_model` (task run `90730746820214`)
- Result: **SUCCESS**, started 2026-10-15 13:52:51 UTC, ran 126s on serverless compute
- Notebook: `/Workspace/Users/rahul.chopra@databricks.com/.bundle/febar-budget-execution/dev/files/src/notebooks/03_train_lapse_risk_model`

# 03 · Lapse-risk model: how much of each line will expire unobligated?

**Business question.** Unobligated balances on expiring funds are lost to the agency ("lapse"). Leadership needs to know
*which* budget lines will lapse and *by how much* early enough to act: reprogram, accelerate an option exercise, or
re-scope a stalled procurement.

**Status quo.** Spend plans assume the remaining plan will execute, so the implied lapse is
`1 - obligation_rate - planned_remaining_share`. Offices with late PRs and long PALT systematically miss that.

**Approach.**
1. For every line whose funds already expired, rebuild what was known at checkpoints 240..30 days before expiration
   (obligations, spend-plan revision in force, open procurement pipeline): point-in-time, no leakage.
2. Label: share of budget authority left unobligated at expiration.
3. Select the loss on an inner temporal split, train on lines that expired in FY2023-FY2024, hold out FY2025
   expirations, and compare with the spend-plan baseline.
4. Refit on all expired lines, log to MLflow and register in Unity Catalog with the `champion` alias.

```text
%pip install -q -U mlflow scikit-learn
%restart_python
```

```python
dbutils.widgets.text("catalog", "rachopra_catalog")
dbutils.widgets.text("schema", "fe_bar")
dbutils.widgets.text("as_of_date", "2026-07-31")

import os
import sys

import mlflow
import numpy as np
import pandas as pd
from mlflow.models import infer_signature
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, r2_score, roc_auc_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
as_of = dbutils.widgets.get("as_of_date")
fq = f"{catalog}.{schema}"
model_name = f"{fq}.lapse_risk_model"

sys.path.append(os.path.abspath(".."))
from ml.lapse_features import CATEGORICAL_FEATURES, FEATURES, LABEL, NUMERIC_FEATURES, feature_sql

mlflow.set_registry_uri("databricks-uc")
me = spark.sql("SELECT current_user()").first()[0]
mlflow.set_experiment(f"/Users/{me}/febar_lapse_risk")
print(f"Model: {model_name}   as of {as_of}")
```

**Output:**

```text
Model: rachopra_catalog.fe_bar.lapse_risk_model   as of 2026-07-31
```

```text
If you are using MLflow Tracing, you can migrate your traces to Unity Catalog for unlimited storage, fine-grained access controls, and queryability from notebooks, SQL, and dashboards. Learn more: https://docs.databricks.com/aws/en/mlflow3/genai/tracing/migrate-traces-to-uc
```

## 1 · Point-in-time training set

```python
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW checkpoints AS
SELECT l.line_id, date_sub(l.expiration_date, k) AS checkpoint_date
FROM {fq}.silver_budget_lines l
LATERAL VIEW explode(array(240, 210, 180, 150, 120, 90, 60, 30)) t AS k
WHERE l.expiration_date <= DATE '{as_of}'
""")
train_sdf = spark.sql(feature_sql(fq, as_of))
train_sdf.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{fq}.ml_lapse_training_set")
spark.sql(f"COMMENT ON TABLE {fq}.ml_lapse_training_set IS 'Point-in-time lapse-risk training set: features as known at each checkpoint before expiration, label = share of budget authority unobligated at expiration.'")

df = spark.table(f"{fq}.ml_lapse_training_set").toPandas()
df["expiration_fy"] = pd.to_datetime(df["expiration_date"]).dt.year
print(f"{len(df)} rows from {df.line_id.nunique()} expired budget lines")
display(df.groupby("expiration_fy").agg(lines=("line_id", "nunique"), rows=("line_id", "size"),
                                        mean_lapse_rate=(LABEL, "mean")).reset_index())
```

**Output:**

```text
568 rows from 71 expired budget lines
```

| expiration_fy | lines | rows | mean_lapse_rate |
|---|---|---|---|
| 2023 | 19 | 152 | 0.05772911852631579 |
| 2024 | 23 | 184 | 0.0625583952173913 |
| 2025 | 29 | 232 | 0.058820954689655175 |

```python
display(df[["line_id", "checkpoint_date", "days_to_expiration", "obligation_rate", "plan_attainment",
            "open_pipeline_share", "pipeline_coverage", "spend_plan_age_days", LABEL]]
        .sort_values(["line_id", "checkpoint_date"]).head(16))
```

**Output:**

| line_id | checkpoint_date | days_to_expiration | obligation_rate | plan_attainment | open_pipeline_share | pipeline_coverage | spend_plan_age_days | lapse_rate |
|---|---|---|---|---|---|---|---|---|
| OCIO-OS-01-FY2023 | 2023-02-02 | 240 | 0.1525910883 | 0.5354985422 | 0.2908762084 | 0.443467297 | 14.0 | 0.013409817 |
| OCIO-OS-01-FY2023 | 2023-03-04 | 210 | 0.3300979936 | 0.9074850955 | 0.3478228351 | 0.677920829 | 44.0 | 0.013409817 |
| OCIO-OS-01-FY2023 | 2023-04-03 | 180 | 0.3717854786 | 0.8342947729 | 0.3662637498 | 0.738049228 | 74.0 | 0.013409817 |
| OCIO-OS-01-FY2023 | 2023-05-03 | 150 | 0.5291506162 | 0.9841850736 | 0.2632427278 | 0.792393344 | 18.0 | 0.013409817 |
| OCIO-OS-01-FY2023 | 2023-06-02 | 120 | 0.6904553119 | 1.0812757748 | 0.1229754942 | 0.813430806 | 48.0 | 0.013409817 |
| OCIO-OS-01-FY2023 | 2023-07-02 | 90 | 0.7527499714 | 1.0129565322 | 0.1629641592 | 0.915714131 | 78.0 | 0.013409817 |
| OCIO-OS-01-FY2023 | 2023-08-01 | 60 | 0.8050807138 | 0.8945705702 | 0.1466811883 | 0.951761902 | 22.0 | 0.013409817 |
| OCIO-OS-01-FY2023 | 2023-08-31 | 30 | 0.941531249 | 1.0461884527 | 0.0459317354 | 0.987462984 | 52.0 | 0.013409817 |
| OCIO-OS-01-FY2024 | 2024-02-03 | 240 | 0.0388674051 | 0.1352516968 | 0.5474980126 | 0.586365418 | 145.0 | 0.050012748 |
| OCIO-OS-01-FY2024 | 2024-03-04 | 210 | 0.0841110954 | 0.2304668411 | 0.5209462049 | 0.6050573 | 175.0 | 0.050012748 |
| OCIO-OS-01-FY2024 | 2024-04-03 | 180 | 0.1960798427 | 0.4404019026 | 0.4388337701 | 0.634913613 | 205.0 | 0.050012748 |
| OCIO-OS-01-FY2024 | 2024-05-03 | 150 | 0.4786513489 | 1.1570478865 | 0.217028997 | 0.695680346 | 18.0 | 0.050012748 |
| OCIO-OS-01-FY2024 | 2024-06-02 | 120 | 0.496952405 | 0.9132856802 | 0.3340288479 | 0.830981253 | 48.0 | 0.050012748 |
| OCIO-OS-01-FY2024 | 2024-07-02 | 90 | 0.632319121 | 0.9322467011 | 0.22626249 | 0.858581611 | 78.0 | 0.050012748 |
| OCIO-OS-01-FY2024 | 2024-08-01 | 60 | 0.7907173363 | 0.9233485768 | 0.1776214608 | 0.968338797 | 22.0 | 0.050012748 |
| OCIO-OS-01-FY2024 | 2024-08-31 | 30 | 0.9119453857 | 1.0649108542 | 0.1158968965 | 1.027842282 | 52.0 | 0.050012748 |

## 2 · Temporal validation
Choose the loss on an inner split (FY2023 → FY2024), then train on FY2023-24 expirations and test on FY2025.

```python
CANDIDATE_LOSSES = ["squared_error", "absolute_error"]


def make_model(loss="absolute_error"):
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ("num", "passthrough", NUMERIC_FEATURES),
    ])
    reg = HistGradientBoostingRegressor(loss=loss, max_depth=3, learning_rate=0.05, max_iter=400,
                                        min_samples_leaf=10, random_state=7)
    return Pipeline([("prep", pre), ("model", reg)])


def baseline(frame):
    """Spend-plan assumption: everything still planned will be obligated."""
    return np.clip(1 - frame.obligation_rate - frame.planned_remaining_share, 0, 1)


def evaluate(y_true, y_pred, budget, threshold=0.05):
    hi = (y_true > threshold).astype(int)
    pred_hi = (y_pred > threshold).astype(int)
    return {
        "mae_pct_points": 100 * mean_absolute_error(y_true, y_pred),
        "r2": r2_score(y_true, y_pred),
        "dollar_mae_millions": float(np.mean(np.abs(y_true - y_pred) * budget) / 1e6),
        "auc_lapse_over_5pct": roc_auc_score(hi, y_pred) if hi.nunique() > 1 else float("nan"),
        "precision_lapse_over_5pct": precision_score(hi, pred_hi, zero_division=0),
        "recall_lapse_over_5pct": recall_score(hi, pred_hi, zero_division=0),
    }


# Model selection never sees the hold-out year: inner split FY2023 -> FY2024.
inner_train, inner_val = df[df.expiration_fy == 2023], df[df.expiration_fy == 2024]
selection = pd.DataFrame([
    {"loss": loss, **evaluate(inner_val[LABEL],
                              np.clip(make_model(loss).fit(inner_train[FEATURES], inner_train[LABEL]).predict(inner_val[FEATURES]), 0, 1),
                              inner_val.total_budget)}
    for loss in CANDIDATE_LOSSES]).round(3)
best_loss = selection.sort_values("mae_pct_points").iloc[0]["loss"]
print(f"Selected loss on inner validation: {best_loss} (lapse rates are heavy-tailed; median regression is robust to outlier programs)")
display(selection)

train = df[df.expiration_fy <= 2024]
test = df[df.expiration_fy == 2025]
holdout_model = make_model(best_loss).fit(train[FEATURES], train[LABEL])
pred_model = np.clip(holdout_model.predict(test[FEATURES]), 0, 1)
pred_base = baseline(test)

results = pd.DataFrame([
    {"approach": "Spend-plan baseline (status quo)", **evaluate(test[LABEL], pred_base, test.total_budget)},
    {"approach": "Lapse-risk model (GBM)", **evaluate(test[LABEL], pred_model, test.total_budget)},
]).round(3)
print(f"train rows={len(train)}  test rows={len(test)}")
display(results)
```

**Output:**

```text
Selected loss on inner validation: absolute_error (lapse rates are heavy-tailed; median regression is robust to outlier programs)
```

| loss | mae_pct_points | r2 | dollar_mae_millions | auc_lapse_over_5pct | precision_lapse_over_5pct | recall_lapse_over_5pct |
|---|---|---|---|---|---|---|
| squared_error | 5.273 | 0.117 | 1.533 | 0.742 | 0.706 | 0.667 |
| absolute_error | 4.96 | 0.15 | 1.451 | 0.739 | 0.613 | 0.639 |

```text
train rows=336  test rows=232
```

| approach | mae_pct_points | r2 | dollar_mae_millions | auc_lapse_over_5pct | precision_lapse_over_5pct | recall_lapse_over_5pct |
|---|---|---|---|---|---|---|
| Spend-plan baseline (status quo) | 8.183 | -2.335 | 2.52 | 0.705 | 0.41 | 0.764 |
| Lapse-risk model (GBM) | 3.113 | 0.493 | 1.093 | 0.686 | 0.402 | 0.514 |

### Accuracy by how far out the forecast is made
The model should matter most 90-180 days out, when there is still time to act.

```python
by_horizon = (test.assign(abs_err_model=np.abs(test[LABEL] - pred_model),
                          abs_err_baseline=np.abs(test[LABEL] - pred_base))
              .groupby("days_to_expiration")[["abs_err_model", "abs_err_baseline"]].mean()
              .mul(100).round(2).rename(columns=lambda c: c + "_pct_points").reset_index()
              .sort_values("days_to_expiration", ascending=False))
display(by_horizon)
```

**Output:**

| days_to_expiration | abs_err_model_pct_points | abs_err_baseline_pct_points |
|---|---|---|
| 240 | 3.25 | 10.41 |
| 210 | 3.17 | 13.38 |
| 180 | 3.2 | 12.77 |
| 150 | 3.23 | 4.75 |
| 120 | 3.22 | 5.51 |
| 90 | 3.02 | 6.27 |
| 60 | 3.1 | 8.51 |
| 30 | 2.71 | 3.86 |

### What drives lapse? (permutation importance on the hold-out year)

```python
imp = permutation_importance(holdout_model, test[FEATURES], test[LABEL], n_repeats=20,
                             random_state=7, scoring="neg_mean_absolute_error")
importance = (pd.DataFrame({"feature": FEATURES, "mae_increase_pct_points": 100 * imp.importances_mean})
              .sort_values("mae_increase_pct_points", ascending=False).round(3))
display(importance)
```

**Output:**

| feature | mae_increase_pct_points |
|---|---|
| office_code | 1.359 |
| cancelled_share | 0.271 |
| prior_year_lapse_rate | 0.224 |
| long_palt_pipeline_share | 0.203 |
| log_total_budget | 0.137 |
| plan_attainment | 0.133 |
| pipeline_coverage | 0.025 |
| obligation_rate | 0.018 |
| planned_remaining_share | 0.009 |
| open_pipeline_share | 0.005 |
| certified_pipeline_share | 0.003 |
| fund_type | 0.0 |
| spend_plan_age_days | -0.005 |
| obligated_last_60d_share | -0.021 |
| days_to_expiration | -0.026 |
| open_pr_avg_age_days | -0.036 |
| appropriation_code | -0.146 |

## 3 · Refit on every expired line, log to MLflow, register in Unity Catalog

```python
final_model = make_model(best_loss).fit(df[FEATURES], df[LABEL])
example = df[FEATURES].head(5)
signature = infer_signature(example, final_model.predict(example))

with mlflow.start_run(run_name=f"lapse_risk_gbm_asof_{as_of}") as run:
    mlflow.log_params({
        "algorithm": "HistGradientBoostingRegressor", "loss": best_loss, "max_depth": 3, "learning_rate": 0.05,
        "max_iter": 400, "train_rows": len(df), "expired_lines": df.line_id.nunique(),
        "holdout": "FY2025 expirations", "as_of_date": as_of,
        "training_table": f"{fq}.ml_lapse_training_set",
    })
    model_metrics = results.iloc[1].drop("approach").to_dict()
    base_metrics = results.iloc[0].drop("approach").to_dict()
    mlflow.log_metrics({f"holdout_{k}": float(v) for k, v in model_metrics.items()})
    mlflow.log_metrics({f"baseline_{k}": float(v) for k, v in base_metrics.items()})
    mlflow.log_table(selection, "model_selection_inner_split.json")
    mlflow.log_table(importance, "permutation_importance.json")
    mlflow.log_table(by_horizon, "error_by_horizon.json")
    info = mlflow.sklearn.log_model(final_model, name="model", signature=signature,
                                    input_example=example, registered_model_name=model_name)

client = mlflow.MlflowClient()
version = info.registered_model_version
client.set_registered_model_alias(model_name, "champion", version)
client.update_registered_model(model_name, description=(
    "Forecasts the share of a budget line's authority that will lapse (remain unobligated) at fund expiration, "
    "from point-in-time obligation, spend-plan and procurement-pipeline features. Trained on synthetic data."))
client.update_model_version(model_name, version, description=(
    f"GBM refit on {df.line_id.nunique()} expired lines ({len(df)} checkpoints). Hold-out FY2025 MAE "
    f"{model_metrics['mae_pct_points']:.2f} pp vs spend-plan baseline {base_metrics['mae_pct_points']:.2f} pp."))
print(f"Registered {model_name} version {version} as @champion (run {run.info.run_id})")
```

**Output:**

```text
/local_disk0/.ephemeral_nfs/envs/pythonEnv-a9016201-7c25-494d-af43-d9e3c994d026/lib/python3.12/site-packages/mlflow/types/utils.py:440: UserWarning: Hint: Inferred schema contains integer column(s). Integer columns in Python cannot represent missing values. If your input data contains missing values at inference time, it will be encoded as floats and will cause a schema enforcement error. The best way to avoid this problem is to infer the model schema based on a realistic data sample (training dataset) that includes missing values. Alternatively, you can declare integer columns as doubles (float64) whenever these columns may have missing values. See `Handling Integers With Missing Values <https://www.mlflow.org/docs/latest/models.html#handling-integers-with-missing-values>`_ for more details.
  warnings.warn(
🔗 View Logged Model at: https://fevm-rachopra-cyber-demo.cloud.databricks.com/ml/experiments/73658048007916/models/m-66631fdf3611449e854ff7f832d7b697?o=7474648312380302
Registered model 'rachopra_catalog.fe_bar.lapse_risk_model' already exists. Creating a new version of this model...
```

```text
🔗 Created version '2' of model 'rachopra_catalog.fe_bar.lapse_risk_model': https://fevm-rachopra-cyber-demo.cloud.databricks.com/explore/data/models/rachopra_catalog/fe_bar/lapse_risk_model/version/2?o=7474648312380302
```

```text
Registered rachopra_catalog.fe_bar.lapse_risk_model version 2 as @champion (run ee441afed6a549a9a85b222e713dd892)
```

```python
mv = client.get_model_version_by_alias(model_name, "champion")
display(pd.DataFrame([{"model": model_name, "alias": "champion", "version": mv.version,
                       "status": mv.status, "run_id": mv.run_id}]))
```

**Output:**

| model | alias | version | status | run_id |
|---|---|---|---|---|
| rachopra_catalog.fe_bar.lapse_risk_model | champion | 2 | READY | ee441afed6a549a9a85b222e713dd892 |
