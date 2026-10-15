# Databricks notebook source
# MAGIC %md
# MAGIC # 04 · Forecast lapse, brief leadership, initiate procurement packages
# MAGIC
# MAGIC 1. **Score** every current budget line with the `@champion` lapse-risk model and explain each forecast
# MAGIC    (which features move it most versus a typical line).
# MAGIC 2. **Brief**: `ai_query` turns each line's governed facts into a short execution briefing with recommended actions,
# MAGIC    and each office's quarter into a quarterly budget-performance review narrative.
# MAGIC 3. **Initiate**: for lines forecast to lapse, draft a procurement package sized to the gap, using only acquisition
# MAGIC    types whose historical PALT can still award before the funds expire.
# MAGIC 4. **Check**: every dollar figure and percentage the LLM writes is verified against the facts it was given.

# COMMAND ----------

# MAGIC %pip install -q -U mlflow scikit-learn
# MAGIC %restart_python

# COMMAND ----------

dbutils.widgets.text("catalog", "rachopra_catalog")
dbutils.widgets.text("schema", "fe_bar")
dbutils.widgets.text("as_of_date", "2026-07-31")
dbutils.widgets.text("llm_endpoint", "databricks-claude-sonnet-4-6")

import json
import os
import re
import sys
from datetime import datetime, timezone

import mlflow
import numpy as np
import pandas as pd

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
as_of = dbutils.widgets.get("as_of_date")
llm = dbutils.widgets.get("llm_endpoint")
fq = f"{catalog}.{schema}"
model_name = f"{fq}.lapse_risk_model"
FORECAST_WINDOW_DAYS = 240  # the model was trained on checkpoints 30-240 days before expiration

sys.path.append(os.path.abspath(".."))
from ml.lapse_features import FEATURES, NUMERIC_FEATURES, feature_sql

from pyspark.sql import functions as F


def to_spark(pdf, list_cols=()):
    """pandas -> Spark with list columns typed as array<string> (all-empty lists otherwise infer as NullType)."""
    sdf = spark.createDataFrame(pdf)
    for c in list_cols:
        sdf = sdf.withColumn(c, F.col(c).cast("array<string>"))
    return sdf


mlflow.set_registry_uri("databricks-uc")
client = mlflow.MlflowClient()
champion = client.get_model_version_by_alias(model_name, "champion")
model = mlflow.sklearn.load_model(f"models:/{model_name}@champion")
print(f"Scoring with {model_name} v{champion.version} as of {as_of}; LLM endpoint {llm}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1 · Score current lines

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TEMP VIEW checkpoints AS
SELECT line_id, DATE '{as_of}' AS checkpoint_date
FROM {fq}.silver_budget_lines
WHERE expiration_date > DATE '{as_of}'
""")
cur = spark.sql(feature_sql(fq, as_of)).toPandas()
in_window = cur.days_to_expiration <= FORECAST_WINDOW_DAYS
cur["predicted_lapse_rate"] = np.where(in_window, np.clip(model.predict(cur[FEATURES]), 0, 1), np.nan)
cur["spend_plan_implied_lapse_rate"] = np.clip(1 - cur.obligation_rate - cur.planned_remaining_share, 0, 1)

# Explain: swap each numeric feature for its typical value among comparable training checkpoints
train = spark.table(f"{fq}.ml_lapse_training_set").toPandas()
typical = train[train.days_to_expiration.between(30, 120)][NUMERIC_FEATURES].median()
LABELS = {
    "obligation_rate": "obligation rate", "plan_attainment": "obligations vs spend plan",
    "planned_remaining_share": "plan still to obligate", "open_pipeline_share": "open procurement pipeline",
    "certified_pipeline_share": "funds-certified pipeline", "long_palt_pipeline_share": "long-PALT pipeline (new awards/grants)",
    "pipeline_coverage": "obligated + pipeline coverage", "open_pr_avg_age_days": "avg age of open PRs (days)",
    "cancelled_share": "cancelled PR value", "obligated_last_60d_share": "obligations in last 60 days",
    "spend_plan_age_days": "spend plan age (days)", "prior_year_lapse_rate": "prior-year lapse rate",
    "days_to_expiration": "days to expiration", "log_total_budget": "line size",
}
PCT = {"obligation_rate", "plan_attainment", "planned_remaining_share", "open_pipeline_share",
       "certified_pipeline_share", "long_palt_pipeline_share", "pipeline_coverage", "cancelled_share",
       "obligated_last_60d_share", "prior_year_lapse_rate"}


def fmt(feature, v):
    return f"{100 * v:.0f}%" if feature in PCT else f"{v:.0f}"


def explain(frame):
    """Per line: how much each feature adds to the forecast versus a typical value (top 3 positive)."""
    base = np.clip(model.predict(frame[FEATURES]), 0, 1)
    effects = {}
    for f in NUMERIC_FEATURES:
        if f in ("days_to_expiration", "log_total_budget"):
            continue
        alt = frame[FEATURES].copy()
        alt[f] = typical[f]
        effects[f] = base - np.clip(model.predict(alt), 0, 1)
    eff = pd.DataFrame(effects, index=frame.index)
    out = []
    for i, row in frame.iterrows():
        top = eff.loc[i].sort_values(ascending=False).head(3)
        out.append([f"{LABELS[f]} {fmt(f, row[f])} vs typical {fmt(f, typical[f])} (+{100 * d:.1f} pp)"
                    for f, d in top.items() if d > 0.002])
    return out


explained = dict(zip(cur.index[in_window], explain(cur[in_window]))) if in_window.any() else {}
cur["top_risk_drivers"] = [explained.get(i, []) for i in cur.index]


def tier(r):
    if np.isnan(r):
        return "Outside forecast window"
    return "Critical" if r >= 0.10 else "High" if r >= 0.05 else "Moderate" if r >= 0.02 else "Low"


forecast = pd.DataFrame({
    "line_id": cur.line_id, "budget_fiscal_year": cur.budget_fiscal_year, "ppa_code": cur.ppa_code,
    "ppa_name": cur.ppa_name, "office_code": cur.office_code, "tas": cur.tas,
    "expiration_date": cur.expiration_date, "days_to_expiration": cur.days_to_expiration,
    "total_budget": cur.total_budget, "obligated_to_date": cur.obligated_at_checkpoint,
    "open_pipeline": cur.open_pipeline_at_checkpoint,
    "obligation_rate": cur.obligation_rate, "pipeline_coverage": cur.pipeline_coverage,
    "predicted_lapse_rate": cur.predicted_lapse_rate,
    "projected_lapse_amount": (cur.predicted_lapse_rate * cur.total_budget).round(2),
    "projected_year_end_obligations": ((1 - cur.predicted_lapse_rate) * cur.total_budget).round(2),
    "spend_plan_implied_lapse_rate": cur.spend_plan_implied_lapse_rate,
    "risk_tier": cur.predicted_lapse_rate.map(tier),
    "top_risk_drivers": cur.top_risk_drivers,
    "model_version": str(champion.version), "as_of_date": pd.to_datetime(as_of).date(),
    "scored_at": datetime.now(timezone.utc),
})
(to_spark(forecast, ["top_risk_drivers"]).write.mode("overwrite").option("overwriteSchema", "true")
 .saveAsTable(f"{fq}.gold_lapse_risk_forecast"))
spark.sql(f"ALTER TABLE {fq}.gold_lapse_risk_forecast ALTER COLUMN line_id SET NOT NULL")
spark.sql(f"ALTER TABLE {fq}.gold_lapse_risk_forecast ADD CONSTRAINT lapse_forecast_pk PRIMARY KEY (line_id)")
spark.sql(f"COMMENT ON TABLE {fq}.gold_lapse_risk_forecast IS 'Lapse-risk forecast for every current budget line as of the reporting date: predicted share and dollars expiring unobligated, risk tier and top drivers (model {model_name}@champion).'")

display(spark.sql(f"""
SELECT risk_tier, COUNT(*) AS lines, ROUND(SUM(total_budget)/1e6, 1) AS budget_m,
       ROUND(SUM(projected_lapse_amount)/1e6, 2) AS projected_lapse_m,
       ROUND(SUM(spend_plan_implied_lapse_rate * total_budget)/1e6, 2) AS spend_plan_implied_lapse_m
FROM {fq}.gold_lapse_risk_forecast GROUP BY risk_tier ORDER BY projected_lapse_m DESC NULLS LAST
"""))

# COMMAND ----------

display(spark.sql(f"""
SELECT line_id, ppa_name, days_to_expiration, ROUND(total_budget/1e6, 2) AS budget_m,
       ROUND(100*obligation_rate, 1) AS obligated_pct, ROUND(100*predicted_lapse_rate, 1) AS predicted_lapse_pct,
       ROUND(projected_lapse_amount/1e6, 2) AS projected_lapse_m, risk_tier, top_risk_drivers
FROM {fq}.gold_lapse_risk_forecast
WHERE risk_tier IN ('Critical', 'High')
ORDER BY projected_lapse_amount DESC LIMIT 15
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2 · Execution briefings (one per line in the forecast window)

# COMMAND ----------

def money(v):
    return None if v is None or pd.isna(v) else round(float(v), 2)


ex = spark.sql(f"SELECT * FROM {fq}.gold_budget_execution WHERE fund_status = 'Current'").toPandas()
alerts = spark.sql(f"SELECT * FROM {fq}.gold_financial_risk_alerts").toPandas()
prs = spark.sql(f"""SELECT * FROM {fq}.gold_procurement_pipeline WHERE is_open""").toPandas()
fc = forecast.set_index("line_id")

facts = {}
for _, r in ex.iterrows():
    f = fc.loc[r.line_id] if r.line_id in fc.index else None
    if f is None or f.risk_tier == "Outside forecast window":
        continue
    line_alerts = alerts[(alerts.line_id == r.line_id)].sort_values("amount_at_risk", ascending=False).head(5)
    line_prs = prs[prs.line_id == r.line_id].sort_values("estimated_amount", ascending=False).head(5)
    facts[r.line_id] = {
        "ppa": f"{r.ppa_name} ({r.ppa_code})", "office": r.office_name, "fund": r.tas,
        "fund_type": r.fund_type, "budget_fiscal_year": int(r.budget_fiscal_year),
        "expires_on": str(r.expiration_date), "days_to_expiration": int(r.days_to_expiration),
        "total_budget": money(r.total_budget), "planned_obligations_to_date": money(r.planned_obligations_to_date),
        "obligated_to_date": money(r.obligated_to_date), "obligation_rate_pct": round(100 * float(r.obligation_rate), 1),
        "burn_rate_vs_plan_pct": None if pd.isna(r.burn_rate_vs_plan) else round(100 * float(r.burn_rate_vs_plan), 1),
        "committed_not_obligated": money(r.committed_not_obligated), "uncommitted_balance": money(r.uncommitted_balance),
        "unobligated_balance": money(r.unobligated_balance), "expended_to_date": money(r.expended_to_date),
        "spend_plan_revision": None if pd.isna(r.spend_plan_revision) else int(r.spend_plan_revision),
        "spend_plan_age_days": None if pd.isna(r.spend_plan_age_days) else int(r.spend_plan_age_days),
        "forecast": {
            "projected_lapse_amount": money(f.projected_lapse_amount),
            "projected_lapse_pct": round(100 * float(f.predicted_lapse_rate), 1),
            "spend_plan_implied_lapse_pct": round(100 * float(f.spend_plan_implied_lapse_rate), 1),
            "risk_tier": f.risk_tier, "drivers": list(f.top_risk_drivers),
        },
        "open_procurements": [
            {"pr_id": p.pr_id, "title": p.title, "amount": money(p.estimated_amount), "status": p.status,
             "acquisition_type": p.acquisition_type, "days_in_status": int(p.days_in_status),
             "forecast_award_date": str(p.forecast_award_date),
             "will_miss_expiration": bool(p.at_risk_of_missing_expiration)}
            for p in line_prs.itertuples()],
        "alerts": [{"type": a.alert_type, "severity": a.severity, "detail": a.detail}
                   for a in line_alerts.itertuples()],
    }
print(f"{len(facts)} lines to brief")

BRIEFING_PROMPT = """You are a senior budget analyst in a federal agency's Office of the CFO preparing the weekly
budget-execution brief for the Budget Director. Use ONLY the facts in the JSON below. Do not invent numbers,
vendors, dates or regulations. Write dollar amounts as $X.XM or $XK, rounded from the facts.

Return:
- headline: <= 15 words, the single most important point about this line.
- summary: 2-3 sentences on execution status vs plan, the lapse forecast and why.
- recommended_actions: 1-3 concrete actions (who should do what, by when), tied to specific PRs or balances in the facts.

FACTS:
{facts}"""

prompts = pd.DataFrame([{"line_id": k, "prompt": BRIEFING_PROMPT.format(facts=json.dumps(v, indent=1)),
                         "facts_json": json.dumps(v)} for k, v in facts.items()])
spark.createDataFrame(prompts).createOrReplaceTempView("briefing_prompts")

# ai_query's DDL responseFormat takes a single top-level field and returns that field's JSON object
BRIEFING_SCHEMA = "STRUCT<headline: STRING, summary: STRING, recommended_actions: ARRAY<STRING>>"
briefings = spark.sql(f"""
SELECT line_id, facts_json,
       from_json(ai_query('{llm}', prompt, responseFormat => 'STRUCT<briefing: {BRIEFING_SCHEMA}>'), '{BRIEFING_SCHEMA}') AS b
FROM briefing_prompts
""").selectExpr("line_id", "facts_json", "b.headline", "b.summary", "b.recommended_actions").toPandas()
print(f"Generated {len(briefings)} briefings")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Grounding check: every $ and % in the briefing must trace to a fact

# COMMAND ----------

NUM = re.compile(r"\$\s?([\d,]+(?:\.\d+)?)\s?([KMB])?|(\d+(?:\.\d+)?)\s?%")


def fact_numbers(obj, out):
    if isinstance(obj, dict):
        for v in obj.values():
            fact_numbers(v, out)
    elif isinstance(obj, list):
        for v in obj:
            fact_numbers(v, out)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out.append(float(obj))
    elif isinstance(obj, str):
        for m in NUM.finditer(obj):
            if m.group(1):
                out.append(float(m.group(1).replace(",", "")) * {"K": 1e3, "M": 1e6, "B": 1e9}.get(m.group(2), 1))
            else:
                out.append(float(m.group(3)))
    return out


def list_totals(obj, out):
    """Running totals of each numeric field across listed items (e.g. "three open PRs totaling $X")."""
    if isinstance(obj, dict):
        for v in obj.values():
            list_totals(v, out)
    elif isinstance(obj, list) and obj and all(isinstance(x, dict) for x in obj):
        for key in {k for x in obj for k, v in x.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}:
            vals = [float(x[key]) for x in obj if isinstance(x.get(key), (int, float))]
            out += [sum(vals[:k]) for k in range(2, len(vals) + 1)]
        for x in obj:
            list_totals(x, out)
    return out


def ungrounded(text, facts_json):
    facts = json.loads(facts_json)
    known = fact_numbers(facts, [])
    # differences and sums of two facts (e.g. "a gap of $X") and totals of listed items
    derived = [a - b for a in known for b in known if a > b] + [a + b for a in known for b in known]
    derived += list_totals(facts, [])
    bad = []
    for m in NUM.finditer(text or ""):
        if m.group(1):
            v = float(m.group(1).replace(",", "")) * {"K": 1e3, "M": 1e6, "B": 1e9}.get(m.group(2), 1)
            ok = any(abs(v - k) <= max(0.051 * abs(k), 1000) for k in known + derived)
        else:
            v = float(m.group(3))
            ok = any(abs(v - k) <= 1.0 for k in known) or any(abs(v - 100 * k) <= 1.0 for k in known if k <= 1.5)
        if not ok:
            bad.append(m.group(0))
    return bad


briefings["text"] = briefings.headline + " " + briefings.summary + " " + briefings.recommended_actions.map(" ".join)
briefings["ungrounded_figures"] = [ungrounded(t, f) for t, f in zip(briefings.text, briefings.facts_json)]
briefings["grounding_passed"] = briefings.ungrounded_figures.map(len) == 0
print(f"Grounding check passed for {briefings.grounding_passed.mean():.0%} of briefings "
      f"({briefings.grounding_passed.sum()}/{len(briefings)})")
display(briefings[~briefings.grounding_passed][["line_id", "ungrounded_figures", "summary"]].head(10))

# COMMAND ----------

out = briefings.drop(columns=["text"]).assign(model_endpoint=llm, generated_at=datetime.now(timezone.utc),
                                               as_of_date=pd.to_datetime(as_of).date())
(to_spark(out, ["recommended_actions", "ungrounded_figures"]).write.mode("overwrite").option("overwriteSchema", "true")
 .saveAsTable(f"{fq}.gold_execution_briefings"))
spark.sql(f"ALTER TABLE {fq}.gold_execution_briefings ALTER COLUMN line_id SET NOT NULL")
spark.sql(f"ALTER TABLE {fq}.gold_execution_briefings ADD CONSTRAINT execution_briefings_pk PRIMARY KEY (line_id)")
spark.sql(f"COMMENT ON TABLE {fq}.gold_execution_briefings IS 'AI-generated weekly execution briefing per current budget line (ai_query over governed gold facts), with a numeric grounding check.'")
display(spark.sql(f"""
SELECT b.line_id, f.risk_tier, b.headline, b.summary, b.recommended_actions, b.grounding_passed
FROM {fq}.gold_execution_briefings b JOIN {fq}.gold_lapse_risk_forecast f USING (line_id)
ORDER BY f.projected_lapse_amount DESC LIMIT 5
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3 · Quarterly budget-performance review narrative (one per office)

# COMMAND ----------

qr = spark.sql(f"""
SELECT office_code, fiscal_quarter,
       CAST(ROUND(SUM(planned_obligations), 2) AS DOUBLE) AS planned_obligations,
       CAST(ROUND(SUM(actual_obligations), 2) AS DOUBLE) AS actual_obligations,
       CAST(ROUND(100 * SUM(actual_obligations) / NULLIF(SUM(planned_obligations), 0), 1) AS DOUBLE) AS attainment_pct,
       CAST(ROUND(SUM(actual_expenditures), 2) AS DOUBLE) AS actual_expenditures
FROM {fq}.gold_quarterly_review GROUP BY ALL ORDER BY office_code, fiscal_quarter
""").toPandas()
as_of_q = (pd.to_datetime(as_of).month + 2) % 12 // 3 + 1
office = spark.sql(f"SELECT * FROM {fq}.gold_office_execution_summary WHERE fund_status = 'Current'").toPandas()
office_facts = []
for code, g in office.groupby("office_code"):
    lines = forecast[(forecast.office_code == code) & forecast.predicted_lapse_rate.notna()]
    top_alerts = alerts[alerts.office_code == code].sort_values("amount_at_risk", ascending=False).head(6)
    office_facts.append({"office_code": code, "facts_json": json.dumps({
        "office": g.office_name.iloc[0],
        "fiscal_year_quarters_vs_approved_plan": qr[qr.office_code == code].drop(columns="office_code").to_dict("records"),
        "completed_quarters_planned": money(qr[(qr.office_code == code) & (qr.fiscal_quarter < as_of_q)].planned_obligations.sum()),
        "completed_quarters_actual": money(qr[(qr.office_code == code) & (qr.fiscal_quarter < as_of_q)].actual_obligations.sum()),
        "current_quarter": int(as_of_q),
        "current_lines_total_budget": money(g.total_budget.sum()), "obligated_to_date": money(g.obligated_to_date.sum()),
        "unobligated_balance": money(g.unobligated_balance.sum()),
        "projected_lapse_amount": money(lines.projected_lapse_amount.sum()),
        "lines_by_risk_tier": lines.risk_tier.value_counts().to_dict(),
        "top_alerts": [{"type": a.alert_type, "severity": a.severity, "detail": a.detail} for a in top_alerts.itertuples()],
    }, default=str)})

REVIEW_PROMPT = """You are preparing the quarterly budget-performance review that a program office presents to the
CFO, covering the completed quarters and the current quarter to date, measured against the approved spend plan.
Use ONLY the facts below; do not invent figures and prefer the totals given over your own arithmetic.
Write amounts as $X.XM.
Return: performance_summary (3-4 sentences on obligations vs plan by quarter and year-end outlook),
key_risks (2-4 bullets), decisions_requested (1-3 bullets for the CFO).

FACTS:
"""
spark.createDataFrame(pd.DataFrame(office_facts).assign(prompt=lambda d: REVIEW_PROMPT + d.facts_json)) \
    .createOrReplaceTempView("review_prompts")
REVIEW_SCHEMA = "STRUCT<performance_summary: STRING, key_risks: ARRAY<STRING>, decisions_requested: ARRAY<STRING>>"
reviews = spark.sql(f"""
SELECT office_code, facts_json,
       from_json(ai_query('{llm}', prompt, responseFormat => 'STRUCT<review: {REVIEW_SCHEMA}>'), '{REVIEW_SCHEMA}') AS r
FROM review_prompts
""").selectExpr("office_code", "facts_json", "r.performance_summary", "r.key_risks", "r.decisions_requested").toPandas()
reviews["ungrounded_figures"] = [ungrounded(" ".join([s, *k, *d]), f) for s, k, d, f in
                                 zip(reviews.performance_summary, reviews.key_risks, reviews.decisions_requested, reviews.facts_json)]
reviews["grounding_passed"] = reviews.ungrounded_figures.map(len) == 0
(to_spark(reviews.assign(model_endpoint=llm, generated_at=datetime.now(timezone.utc)),
          ["key_risks", "decisions_requested", "ungrounded_figures"])
 .write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{fq}.gold_quarterly_review_briefings"))
spark.sql(f"COMMENT ON TABLE {fq}.gold_quarterly_review_briefings IS 'AI-drafted quarterly budget-performance review narrative per program office, grounded in gold_quarterly_review and current risk alerts.'")
display(reviews[["office_code", "performance_summary", "key_risks", "decisions_requested", "grounding_passed"]])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4 · Automated procurement package initiation
# MAGIC For lines forecast to lapse at least $250K within 120 days, size a package to the projected gap and pick only
# MAGIC acquisition types whose historical median PALT still lands before expiration (with a 14-day buffer).

# COMMAND ----------

palt = spark.sql(f"""
SELECT acquisition_type, CAST(percentile_approx(palt_days, 0.5) AS INT) AS median_palt_days,
       CAST(percentile_approx(palt_days, 0.8) AS INT) AS p80_palt_days
FROM {fq}.gold_procurement_pipeline WHERE status = 'Awarded' GROUP BY acquisition_type
""").toPandas().set_index("acquisition_type")
incumbents = spark.sql(f"""
SELECT budget_fiscal_year, ppa_code, contract_number, MAX(vendor_name) AS vendor_name,
       MAX(object_class) AS object_class, MAX(period_of_performance_end) AS pop_end,
       SUM(obligated_amount) AS obligated
FROM {fq}.silver_obligations
WHERE period_of_performance_end >= DATE '{as_of}' AND object_class LIKE '25.%'
GROUP BY ALL
""").toPandas()
display(palt.reset_index())

candidates = forecast[(forecast.projected_lapse_amount >= 250_000) & (forecast.days_to_expiration <= 120)]
packages = []
for r in candidates.itertuples():
    must_award_by = pd.to_datetime(r.expiration_date) - pd.Timedelta(days=14)
    days_left = (must_award_by - pd.to_datetime(as_of)).days
    feasible = [a for a in ["Option Exercise", "Modification", "Task Order"]
                if a in palt.index and palt.loc[a, "p80_palt_days"] <= days_left]
    inc = incumbents[incumbents.ppa_code == r.ppa_code].sort_values("obligated", ascending=False).head(3)
    packages.append({
        "package_id": f"PKG-{r.line_id}", "line_id": r.line_id, "office_code": r.office_code,
        "ppa_code": r.ppa_code, "facts_json": json.dumps({
            "ppa": f"{r.ppa_name} ({r.ppa_code})", "fund": r.tas, "expires_on": str(r.expiration_date),
            "must_award_by": str(must_award_by.date()), "days_until_must_award": int(days_left),
            "projected_lapse_amount": money(r.projected_lapse_amount),
            "recommended_package_amount": money(round(0.8 * r.projected_lapse_amount, -3)),
            "feasible_acquisition_types": [{"type": a, "median_palt_days": int(palt.loc[a, "median_palt_days"]),
                                            "p80_palt_days": int(palt.loc[a, "p80_palt_days"])} for a in feasible],
            "active_service_contracts_on_line": [
                {"contract_number": c.contract_number, "vendor": c.vendor_name, "object_class": c.object_class,
                 "period_of_performance_end": str(c.pop_end), "obligated_to_date": money(c.obligated)}
                for c in inc.itertuples()],
            "risk_drivers": list(r.top_risk_drivers),
        })})

PACKAGE_PROMPT = """You support a federal program office's year-end acquisition planning. Draft a procurement
request package to put projected-to-lapse funds to work before they expire. Use ONLY the facts below: choose an
acquisition type from feasible_acquisition_types and, for option exercises or modifications, a contract from
active_service_contracts_on_line. Do not invent contract numbers, vendors, regulations or dollar figures.
For an option exercise or modification the amount must not exceed the selected contract's obligated_to_date (a
proxy for its priced option value), and the requirement must be a bona fide need of the current period of
availability; if no contract can absorb the recommended amount, recommend a smaller amount rather than stretch.
Return: title, recommended_acquisition_type, contract_number (or empty), amount (number),
requirement_summary (2-3 sentences of bona fide need for the current period of availability),
justification (2 sentences on why this vehicle can award in time), required_documents (list),
milestones (list of "YYYY-MM-DD: step" back-planned from must_award_by).

FACTS:
"""
package_df = pd.DataFrame(packages)
if package_df.empty:
    print("No lines meet the package-initiation criteria")
else:
    spark.createDataFrame(package_df.assign(prompt=PACKAGE_PROMPT + package_df.facts_json)) \
        .createOrReplaceTempView("package_prompts")
    PKG_SCHEMA = ("STRUCT<title: STRING, recommended_acquisition_type: STRING, contract_number: STRING, "
                  "amount: DOUBLE, requirement_summary: STRING, justification: STRING, required_documents: ARRAY<STRING>, "
                  "milestones: ARRAY<STRING>>")
    drafts = spark.sql(f"""
    SELECT package_id, line_id, office_code, ppa_code, facts_json,
           from_json(ai_query('{llm}', prompt, responseFormat => 'STRUCT<package: {PKG_SCHEMA}>'), '{PKG_SCHEMA}') AS d
    FROM package_prompts
    """).selectExpr("package_id", "line_id", "office_code", "ppa_code", "facts_json", "d.*").toPandas()

    def valid(row):
        f = json.loads(row.facts_json)
        types = {a["type"] for a in f["feasible_acquisition_types"]}
        contracts = {c["contract_number"] for c in f["active_service_contracts_on_line"]}
        issues = []
        if row.recommended_acquisition_type not in types:
            issues.append(f"acquisition type '{row.recommended_acquisition_type}' not feasible")
        if row.contract_number and row.contract_number not in contracts:
            issues.append(f"contract {row.contract_number} not on line")
        if row.amount and row.amount > f["projected_lapse_amount"] * 1.01:
            issues.append("amount exceeds projected lapse")
        contract = next((c for c in f["active_service_contracts_on_line"] if c["contract_number"] == row.contract_number), None)
        if contract and row.amount and row.amount > contract["obligated_to_date"]:
            issues.append("amount exceeds the contract's obligated value; confirm priced option value and bona fide need")
        return issues

    drafts["validation_issues"] = drafts.apply(valid, axis=1)
    drafts["status"] = np.where(drafts.validation_issues.map(len) == 0,
                                "AI Draft - Pending Program Office Review", "AI Draft - Needs Correction")
    drafts = drafts.assign(model_endpoint=llm, generated_at=datetime.now(timezone.utc))
    (to_spark(drafts, ["required_documents", "milestones", "validation_issues"]).write.mode("overwrite").option("overwriteSchema", "true")
     .saveAsTable(f"{fq}.gold_procurement_package_drafts"))
    spark.sql(f"ALTER TABLE {fq}.gold_procurement_package_drafts ALTER COLUMN package_id SET NOT NULL")
    spark.sql(f"ALTER TABLE {fq}.gold_procurement_package_drafts ADD CONSTRAINT package_drafts_pk PRIMARY KEY (package_id)")
    spark.sql(f"COMMENT ON TABLE {fq}.gold_procurement_package_drafts IS 'AI-initiated procurement request packages for lines forecast to lapse, validated against feasible PALT and active contracts. Pending program-office review.'")
    print(f"{len(drafts)} packages drafted; {int((drafts.validation_issues.map(len) == 0).sum())} passed validation")
    display(drafts[["package_id", "title", "recommended_acquisition_type", "contract_number", "amount",
                    "requirement_summary", "milestones", "status", "validation_issues"]])
