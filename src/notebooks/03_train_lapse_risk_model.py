# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · Lapse-risk model: how much of each line will expire unobligated?
# MAGIC
# MAGIC **Business question.** Unobligated balances on expiring funds are lost to the agency ("lapse"). Leadership needs to know
# MAGIC *which* budget lines will lapse and *by how much* early enough to act: reprogram, accelerate an option exercise, or
# MAGIC re-scope a stalled procurement.
# MAGIC
# MAGIC **Status quo.** Spend plans assume the remaining plan will execute, so the implied lapse is
# MAGIC `1 - obligation_rate - planned_remaining_share`. Offices with late PRs and long PALT systematically miss that.
# MAGIC
# MAGIC **Approach.**
# MAGIC 1. For every line whose funds already expired, rebuild what was known at checkpoints 240..30 days before expiration
# MAGIC    (obligations, spend-plan revision in force, open procurement pipeline): point-in-time, no leakage.
# MAGIC 2. Label: share of budget authority left unobligated at expiration.
# MAGIC 3. Select the loss on an inner temporal split, train on lines that expired in FY2023-FY2024, hold out FY2025
# MAGIC    expirations, and compare with the spend-plan baseline.
# MAGIC 4. Refit on all expired lines, log to MLflow and register in Unity Catalog with the `champion` alias.

# COMMAND ----------

# MAGIC %pip install -q -U mlflow scikit-learn
# MAGIC %restart_python

# COMMAND ----------

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

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1 · Point-in-time training set

# COMMAND ----------

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

# COMMAND ----------

display(df[["line_id", "checkpoint_date", "days_to_expiration", "obligation_rate", "plan_attainment",
            "open_pipeline_share", "pipeline_coverage", "spend_plan_age_days", LABEL]]
        .sort_values(["line_id", "checkpoint_date"]).head(16))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2 · Temporal validation
# MAGIC Choose the loss on an inner split (FY2023 → FY2024), then train on FY2023-24 expirations and test on FY2025.

# COMMAND ----------

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

# COMMAND ----------

# MAGIC %md
# MAGIC ### Accuracy by how far out the forecast is made
# MAGIC The model should matter most 90-180 days out, when there is still time to act.

# COMMAND ----------

by_horizon = (test.assign(abs_err_model=np.abs(test[LABEL] - pred_model),
                          abs_err_baseline=np.abs(test[LABEL] - pred_base))
              .groupby("days_to_expiration")[["abs_err_model", "abs_err_baseline"]].mean()
              .mul(100).round(2).rename(columns=lambda c: c + "_pct_points").reset_index()
              .sort_values("days_to_expiration", ascending=False))
display(by_horizon)

# COMMAND ----------

# MAGIC %md
# MAGIC ### What drives lapse? (permutation importance on the hold-out year)

# COMMAND ----------

imp = permutation_importance(holdout_model, test[FEATURES], test[LABEL], n_repeats=20,
                             random_state=7, scoring="neg_mean_absolute_error")
importance = (pd.DataFrame({"feature": FEATURES, "mae_increase_pct_points": 100 * imp.importances_mean})
              .sort_values("mae_increase_pct_points", ascending=False).round(3))
display(importance)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3 · Refit on every expired line, log to MLflow, register in Unity Catalog

# COMMAND ----------

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

# COMMAND ----------

mv = client.get_model_version_by_alias(model_name, "champion")
display(pd.DataFrame([{"model": model_name, "alias": "champion", "version": mv.version,
                       "status": mv.status, "run_id": mv.run_id}]))
