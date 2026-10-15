# Forecast And Ai Briefings

- Job task: `forecast_and_ai_briefings` (task run `522900452292376`)
- Result: **SUCCESS**, started 2026-10-15 14:11:47 UTC, ran 307s on serverless compute
- Notebook: `/Workspace/Users/rahul.chopra@databricks.com/.bundle/febar-budget-execution/dev/files/src/notebooks/04_forecast_and_ai_briefings`

# 04 · Forecast lapse, brief leadership, initiate procurement packages

1. **Score** every current budget line with the `@champion` lapse-risk model and explain each forecast
   (which features move it most versus a typical line).
2. **Brief**: `ai_query` turns each line's governed facts into a short execution briefing with recommended actions,
   and each office's quarter into a quarterly budget-performance review narrative.
3. **Initiate**: for lines forecast to lapse, draft a procurement package sized to the gap, using only acquisition
   types whose historical PALT can still award before the funds expire.
4. **Check**: every dollar figure and percentage the LLM writes is verified against the facts it was given.

```text
%pip install -q -U mlflow scikit-learn
%restart_python
```

```python
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
```

**Output:**

```text
Scoring with rachopra_catalog.fe_bar.lapse_risk_model v2 as of 2026-07-31; LLM endpoint databricks-claude-sonnet-4-6
```

## 1 · Score current lines

```python
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
```

**Output:**

| risk_tier | lines | budget_m | projected_lapse_m | spend_plan_implied_lapse_m |
|---|---|---|---|---|
| Critical | 4 | 165.0 | 23.44 | 23.91 |
| High | 7 | 355.8 | 23.09 | 18.73 |
| Moderate | 14 | 478.6 | 17.37 | 22.98 |
| Low | 4 | 144.2 | 1.97 | 1.96 |
| Outside forecast window | 16 | 1003.3 |  | 51.96 |

```python
display(spark.sql(f"""
SELECT line_id, ppa_name, days_to_expiration, ROUND(total_budget/1e6, 2) AS budget_m,
       ROUND(100*obligation_rate, 1) AS obligated_pct, ROUND(100*predicted_lapse_rate, 1) AS predicted_lapse_pct,
       ROUND(projected_lapse_amount/1e6, 2) AS projected_lapse_m, risk_tier, top_risk_drivers
FROM {fq}.gold_lapse_risk_forecast
WHERE risk_tier IN ('Critical', 'High')
ORDER BY projected_lapse_amount DESC LIMIT 15
"""))
```

**Output:**

| line_id | ppa_name | days_to_expiration | budget_m | obligated_pct | predicted_lapse_pct | projected_lapse_m | risk_tier | top_risk_drivers |
|---|---|---|---|---|---|---|---|---|
| OWD-GA-01-FY2026 | Infrastructure Workforce Grants | 61 | 65.76 | 41.2 | 14.1 | 9.27 | Critical | ['cancelled PR value 13% vs typical 0% (+4.2 pp)', 'obligations vs spend plan 80% vs typical 94% (+2.2 pp)', 'long-PALT pipeline (new awards/grants) 42% vs typical 8% (+2.0 pp)'] |
| OCIO-PCI-01-FY2024 | Financial System Modernization | 61 | 102.17 | 72.5 | 7.2 | 7.35 | High | ['cancelled PR value 16% vs typical 0% (+2.9 pp)', 'prior-year lapse rate 3% vs typical 1% (+1.4 pp)'] |
| OTS-PCI-01-FY2024 | Bridge Inspection Systems | 61 | 54.47 | 87.0 | 11.2 | 6.1 | Critical | ['cancelled PR value 11% vs typical 0% (+4.2 pp)', 'prior-year lapse rate 3% vs typical 1% (+2.0 pp)', 'obligations vs spend plan 92% vs typical 94% (+1.8 pp)'] |
| OTS-GA-01-FY2026 | Highway Safety Improvement Grants | 61 | 21.07 | 16.7 | 26.3 | 5.55 | Critical | ['prior-year lapse rate 23% vs typical 1% (+8.7 pp)', 'obligations vs spend plan 30% vs typical 94% (+7.8 pp)', 'long-PALT pipeline (new awards/grants) 83% vs typical 8% (+0.9 pp)'] |
| OGM-GA-01-FY2026 | State Energy Resilience Grants | 61 | 81.66 | 49.8 | 5.4 | 4.41 | High | ['cancelled PR value 4% vs typical 0% (+1.7 pp)', 'avg age of open PRs (days) 116 vs typical 56 (+0.4 pp)', 'open procurement pipeline 56% vs typical 19% (+0.3 pp)'] |
| OCIO-PCI-02-FY2024 | Cloud Migration | 61 | 66.23 | 92.0 | 5.2 | 3.46 | High | ['prior-year lapse rate 2% vs typical 1% (+0.7 pp)', 'cancelled PR value 1% vs typical 0% (+0.6 pp)'] |
| OTS-OS-01-FY2026 | Safety Inspection Operations | 61 | 38.35 | 76.6 | 8.8 | 3.37 | High | ['prior-year lapse rate 20% vs typical 1% (+4.3 pp)', 'cancelled PR value 5% vs typical 0% (+0.9 pp)'] |
| OTS-OS-02-FY2026 | Incident Investigation | 61 | 23.69 | 68.5 | 10.6 | 2.52 | Critical | ['prior-year lapse rate 26% vs typical 1% (+3.2 pp)', 'obligations vs spend plan 92% vs typical 94% (+1.7 pp)', 'cancelled PR value 9% vs typical 0% (+0.9 pp)'] |
| OTS-RD-01-FY2025 | Automated Vehicle Safety Research | 61 | 21.07 | 77.2 | 8.8 | 1.85 | High | ['obligations vs spend plan 84% vs typical 94% (+4.2 pp)', 'prior-year lapse rate 3% vs typical 1% (+3.7 pp)'] |
| OWS-OS-01-FY2026 | Drinking Water Program Operations | 61 | 22.88 | 46.0 | 6.2 | 1.42 | High | ['prior-year lapse rate 9% vs typical 1% (+1.5 pp)', 'cancelled PR value 4% vs typical 0% (+0.7 pp)'] |
| OWS-OS-02-FY2026 | Laboratory Services | 61 | 23.48 | 82.8 | 5.2 | 1.23 | High | ['prior-year lapse rate 7% vs typical 1% (+2.0 pp)'] |

## 2 · Execution briefings (one per line in the forecast window)

```python
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
```

**Output:**

```text
29 lines to brief
Generated 29 briefings
```

### Grounding check: every $ and % in the briefing must trace to a fact

```python
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
```

**Output:**

```text
Grounding check passed for 93% of briefings (27/29)
```

| line_id | ungrounded_figures | summary |
|---|---|---|
| OMA-OS-01-FY2026 | ['29%'] | OMA-OS-01 has obligated $16.0M (53.5% of the $29.9M annual budget) against a plan calling for $22.6M obligated to date, yielding a burn-rate variance of only 70.8% of plan — a Medium-severity alert. The $13.9M unobligated balance is largely covered by $13.1M in committed-but-not-yet-obligated action |
| OWD-GA-01-FY2026 | ['59%', '27.5%'] | OWD-GA-01 is executing at only 72.5% of plan, with $27.1M obligated against $37.4M planned — a $10.3M shortfall against Spend Plan Rev 4. The unobligated balance stands at $38.7M (59% of the $65.8M budget) with just 61 days remaining, and the forecast projects a $9.3M lapse (14.1%), exceeding the sp |

```python
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
```

**Output:**

| line_id | risk_tier | headline | summary | recommended_actions | grounding_passed |
|---|---|---|---|---|---|
| OWD-GA-01-FY2026 | Critical | Critical lapse risk: $9.3M projected to expire in 61 days | OWD-GA-01 is executing at only 72.5% of plan, with $27.1M obligated against $37.4M planned — a $10.3M shortfall against Spend Plan Rev 4. The unobligated balance stands at $38.7M (59% of the $65.8M budget) with just 61 days remaining, and the forecast projects a $9.3M lapse (14.1%), exceeding the sp | ['Grants Officer must expedite evaluation and award PR-26-OWD-0003 (Infrastructure Workforce Grants – Cooperative Agreement 1, $3.5M) and PR-26-OWD-0013 (Formula Allocation Region 6, $2.9M) — both currently forecast to award after the September 30 expiration — by no later than September 26 to allow  | False |
| OCIO-PCI-01-FY2024 | High | High lapse risk: $20.1M uncommitted with 61 days until fund expiration | OCIO-PCI-01 (Financial System Modernization) has obligated $74.1M (72.5%) of its $102.2M budget against a plan of $96.4M, running at only 76.9% of the approved spend plan (Revision 10, 21 days old). With 61 days remaining before the multi-year fund expires on 2026-09-30, $28.0M remains unobligated — | ['OCIO Contracting Officer must prioritize award of PR-24-OCIO-0108 (Region 4 Field Office operations center, $8.0M, currently 23 days Under Evaluation) no later than its forecast award date of 2026-08-10, as this is the single largest committed-not-obligated balance and any further slip narrows the | True |
| OTS-PCI-01-FY2024 | Critical | Critical lapse risk: $6.1M projected to expire in 61 days | Bridge Inspection Systems (OTS-PCI-01) has obligated $47.4M (87.0%) of its $54.5M budget, running at 91.9% of plan with a $7.1M unobligated balance and only 61 days before fund expiration on 2026-09-30. The forecast projects an 11.2% lapse ($6.1M) — exceeding the spend-plan-implied lapse of 9.6% — d | ['OTS Budget Officer should immediately refresh the Spend Plan (currently Rev 2, aged 839 days since 2024-04-13) to reflect current committed-not-obligated balances ($5.9M) and the $1.2M uncommitted balance, and resubmit to the CFO no later than this Friday to support accurate lapse forecasting befo | True |
| OTS-GA-01-FY2026 | Critical | Critical lapse risk: $5.6M projected to expire with only 16.7% obligated | OTS-GA-01 is severely behind plan with only $3.5M obligated (16.7%) against a planned $11.7M to date — a burn-rate variance of 30.2% vs. plan — with 61 days remaining before fund expiration on 2026-09-30. The unobligated balance stands at $17.6M, of which $17.4M is committed-not-obligated, leaving o | ["OTS Grants Officer must immediately escalate PR-26-OTS-0200 ($5.6M, 'competitive awards cohort 1') through the evaluation panel to compress the award timeline ahead of the 2026-09-30 expiration; if a pre-expiration award is not achievable, the Grants Officer must notify the Budget Director no late | True |
| OGM-GA-01-FY2026 | High | High lapse risk: $4.4M projected to expire with commitments exceeding available funds | OGM-GA-01 (State Energy Resilience Grants) has obligated $40.7M (49.8%) of its $81.7M annual appropriation against a plan of $45.6M, running at 89.1% of planned burn rate with 61 days remaining before the fund expires on September 30, 2026. The forecast projects a $4.4M lapse (5.4% of budget), drive | ['IMMEDIATE (by COB today) — Budget Officer and Contracting Officer must conduct a funds-control review of all open PRs: the $45.3M in certified commitments exceeds the $40.9M unobligated balance by $4.3M. No additional PR certifications or awards may proceed until the over-commitment is resolved, p | True |

## 3 · Quarterly budget-performance review narrative (one per office)

```python
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
```

**Output:**

| office_code | performance_summary | key_risks | decisions_requested | grounding_passed |
|---|---|---|---|---|
| OCIO | Through the first three completed quarters, the Office of the Chief Information Officer obligated $141.3M against a planned $151.3M, achieving 93.4% of the cumulative spend plan. Q1 ran 16.6% over plan at $29.1M obligated vs. $25.0M planned, while Q2 and Q3 came in under plan at 92.7% ($48.8M vs. $5 | ['CRITICAL – Potential Antideficiency Act (ADA) Violation: Financial System Modernization obligations of $33.9M have exceeded the apportioned amount of $32.5M by $1.4M. Footnote B indicates the balance is withheld pending congressional spend-plan notification; immediate remediation and legal review  | ['IMMEDIATE ACTION REQUIRED – Authorize the program office to engage the Office of General Counsel and OMB to assess and remediate the potential Antideficiency Act violation on Financial System Modernization, where obligations of $33.9M have exceeded the apportioned level of $32.5M by $1.4M.', 'Appr | False |
| OGM | The Office of Grid Modernization closed Q1–Q3 at $137.5M obligated against a $149.7M plan (91.8% attainment), masking significant quarter-to-quarter volatility: Q1 came in at only 46.2% of plan ($10.8M vs. $23.4M), Q2 surged to 153.3% ($74.7M vs. $48.8M), and Q3 fell back to 67.0% ($51.9M vs. $77.5M | ['HIGH – Commitments Exceed Available Funds (State Energy Resilience Grants): $45.3M in certified open procurement requests exceeds the $41.0M unobligated balance by approximately $4.3M; a funds-control breach is imminent if additional requests are certified or awarded before a corrective review is  | ['DECISION REQUIRED – Funds Control Hold (State Energy Resilience Grants): Authorize an immediate suspension of new procurement certifications and awards against the State Energy Resilience Grants line until a funds-control review reconciles the $4.3M excess commitment ($45.3M certified vs. $40.1M u | False |
| OMA | Through the first three completed quarters, the Office of Management and Administration obligated $114.8M against a plan of $117.8M (97.4% attainment), reflecting a modest under-obligation of $3.0M. Quarter 1 came in significantly below plan at 67.2% ($16.7M actual vs. $24.8M planned), while Quarter | ['INVOICE EXCEEDS OBLIGATION (High): Invoices against contract DCI24F001882-000 total $2.8M, exceeding the $1.4M obligated — a $1.4M shortfall that poses immediate Anti-Deficiency Act exposure and requires urgent resolution.', 'POTENTIAL DUPLICATE INVOICE (High): Vendor invoice RED-00203 from Redlin | ['AUTHORIZE IMMEDIATE CONTRACT REVIEW AND OBLIGATION CORRECTION: Direct the Contracting Officer to reconcile the obligation on DCI24F001882-000 and halt payment processing on the potential duplicate Redline Federal Group invoice (RED-00203) pending verification, to prevent an improper payment of up  | False |
| OTS | The Office of Transportation Safety has consistently obligated below its approved spend plan across all completed quarters. In Q1, obligations reached only $9.4M against a plan of $17.8M (52.7% attainment), improving modestly to $25.5M of $33.1M planned in Q2 (77.1%) and $36.1M of $47.4M planned in  | ['Projected lapse of $19.4M at fiscal year-end signals a structural execution gap that could jeopardize future-year funding levels and program continuity.', 'Bridge Inspection Systems is a critical burn-rate outlier, obligating only 59% of its approved spend plan to date ($14.9M vs. $25.2M planned), | ['Approve an immediate spend plan revision cycle for all lines with plans not updated in the past 90 days — particularly Bridge Inspection Systems, Highway Safety Improvement Grants, Automated Vehicle Safety Research, and Safety Inspection Operations — to establish reliable Q4 forecasts before the f | True |
| OWD | The Office of Workforce Development closed Q1 significantly under plan at 44.1% attainment ($3.5M obligated vs. $7.9M planned), recovered strongly in Q2 with 138.5% attainment ($25.9M vs. $18.7M planned), and returned near plan in Q3 at 92.5% attainment ($35.4M vs. $38.3M planned). Through the three | ['LAPSE RISK – Infrastructure Workforce Grants (999-2026-0600): $5.3M (8.0% of line budget) is neither obligated nor committed, with funds expiring 2026-09-30. Two grant awards under this line (PR-26-OWD-0003 at $3.5M and PR-26-OWD-0013 at $2.9M) are currently Under Evaluation with forecast award da | ['AUTHORIZE EXPEDITED AWARD ACTION: Direct the contracting office to prioritize and accelerate evaluation of PR-26-OWD-0003 ($3.5M) and PR-26-OWD-0013 ($2.9M) to achieve award before 2026-09-30; if award cannot be confirmed by that date, CFO should decide whether to de-obligate and reprogram the $6. | False |
| OWS | The Office of Water Systems closed Q1 at 82.6% of plan ($12.1M obligated vs. $14.7M planned) and surged to 146.5% in Q2 ($44.5M vs. $30.3M planned), reflecting accelerated award activity mid-year. Q3 pulled back sharply to 70.2% attainment ($33.8M vs. $48.1M planned), and Q4 to date stands at only 2 | ['HIGH – Drinking Water Program Operations is obligating at only 62% of plan ($10.5M obligated vs. $17.0M planned) and carries $1.7M in funds (7.4% of budget) that are neither obligated nor committed, with only 61 days until the September 30, 2026 expiration date, creating a direct lapse risk.', 'HI | ['APPROVE or DIRECT a funds-control hold on Laboratory Services procurement certifications and awards until a funds-control review reconciles the $920K shortfall between certified commitments ($5.0M) and available unobligated balance ($4.0M).', 'APPROVE an expedited acquisition strategy or authorize | True |

## 4 · Automated procurement package initiation
For lines forecast to lapse at least $250K within 120 days, size a package to the projected gap and pick only
acquisition types whose historical median PALT still lands before expiration (with a 14-day buffer).

```python
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
```

**Output:**

| acquisition_type | median_palt_days | p80_palt_days |
|---|---|---|
| Task Order | 59 | 82 |
| New Award (Simplified) | 51 | 118 |
| Option Exercise | 21 | 29 |
| New Award | 155 | 189 |
| Modification | 26 | 32 |
| Grant Award | 153 | 186 |

```text
26 packages drafted; 26 passed validation
```

| package_id | title | recommended_acquisition_type | contract_number | amount | requirement_summary | milestones | status | validation_issues |
|---|---|---|---|---|---|---|---|---|
| PKG-OTS-GA-01-FY2026 | Year-End Option Exercise – Highway Safety Improvement Grants Research & Technical Support (OTS-GA-01) | Option Exercise | DCI25F000963 | 1183004.96 | The Highway Safety Improvement Grants program (OTS-GA-01) has a bona fide need in the current FY 2026 period of availability for continued research and technical support services under object class 25.1 to sustain ongoing highway safety data analysis, grant performance monitoring, and stakeholder te | ['2026-08-01: Program office initiates package; drafts updated SOW/PWS and IGCE', '2026-08-05: COR submits signed Purchase Request and Funds Availability Certification to Contracting Officer', '2026-08-08: Contracting Officer reviews package for completeness; requests any missing documents', '2026-0 | AI Draft - Pending Program Office Review | [] |
| PKG-OGM-RD-01-FY2025 | FY2026 Year-End Option Exercise – Advanced Transmission Research Support Services (DCI26C000243) | Option Exercise | DCI26C000243 | 793000.0 | The Advanced Transmission Research program (OGM-RD-01) requires continued research and engineering support services in FY2026 to sustain active laboratory testing, data analysis, and technical reporting tasks that are scoped to and executable within the current 2025/2026 period of availability endin | ['2026-07-31: Program office initiates requirement package; drafts bona fide need memo and updated PWS', '2026-08-05: IGCE completed and signed by Program Manager', '2026-08-07: PR submitted to Budget/Finance for funds certification and PR creation', '2026-08-11: Certified PR and complete package tr | AI Draft - Pending Program Office Review | [] |
| PKG-OCIO-PCI-01-FY2024 | FY2026 Financial System Modernization – Year-End IT Professional Services Modification (DCI26F001274) | Modification | DCI26F001274 | 1903840.14 | The OCIO Financial System Modernization program (OCIO-PCI-01) requires continued IT professional services support during the current period of availability (FY2024–2026, expiring 30 September 2026) to sustain active modernization workstreams including system integration testing, data migration valid | ['2026-08-01: Program office initiates requirement; PM signs Bona Fide Need Determination memo', '2026-08-05: IGCE completed and certified by COR', '2026-08-07: Updated SOW/PWS drafted and reviewed by program office', '2026-08-11: Acquisition package (IGCE, SOW, FAC, Acquisition Plan) submitted to C | AI Draft - Pending Program Office Review | [] |
| PKG-OGM-PCI-01-FY2024 | Substation Hardening – Option Exercise / Modification to Obligate Projected-to-Lapse FY2024/2026 Funds (OGM-PCI-01) | Option Exercise | DCI26F000285 | 2325000.0 | The Substation Hardening program (OGM-PCI-01) has a bona fide need within the current FY2024/2026 period of availability to accelerate physical and cyber hardening of electrical substations identified in the agency's current-year capital improvement plan. Scope includes installation of protective re | ['2026-08-01: Program office initiates PR and IGCE; COR confirms bona fide need memo', '2026-08-06: PR package (PWS, IGCE, funding doc) submitted to Contracting Officer', '2026-08-11: Contracting Officer reviews package; issues RFI/clarifications to vendor if needed', '2026-08-15: FAR 17.207 option  | AI Draft - Pending Program Office Review | [] |
| PKG-OGM-OS-02-FY2026 | OGM-OS-02 Outage Analytics and Monitoring — FY2026 Year-End Scope Expansion (Modification) | Modification | DCI26C000080 | 548000.0 | The Outage Analytics and Monitoring program (OGM-OS-02) requires additional analytical services and monitoring support capacity within FY2026 to address a documented backlog of outage event correlation studies and dashboard enhancement work identified during the current period of availability. Expan | ['2026-08-01: Program office initiates requirement; drafts delta SOW/PWS and IGCE', '2026-08-06: Bona Fide Need memo drafted and routed to Program Manager for signature', '2026-08-08: Complete package (SOW, IGCE, Bona Fide Need memo, funds cert) submitted to Contracting Officer', '2026-08-13: Contra | AI Draft - Pending Program Office Review | [] |
| PKG-OMA-PCI-01-FY2024 | FY2026 Headquarters Consolidation – Option Exercise to Obligate Projected-to-Lapse OMA Funds | Option Exercise | DCI24C001302 | 817000.0 | The Headquarters Consolidation program (OMA-PCI-01) requires continued facility support and infrastructure services through the current period of availability ending 30 September 2026 to sustain ongoing consolidation activities at the headquarters site. Exercising the next priced option on contract  | ['2026-07-31: Program office submits signed Requirements Document, SOW, and IGCE to Contracting Officer', '2026-08-05: Contracting Officer opens PR in acquisition system; Funds Availability Certification obtained', '2026-08-08: Option Exercise D&F drafted and routed for legal/policy review', '2026-0 | AI Draft - Pending Program Office Review | [] |
| PKG-OTS-PCI-01-FY2024 | Bridge Inspection Systems – Year-End Option Exercise (OTS-PCI-01) | Option Exercise | DCI25C000558 | 1039509.21 | The Bridge Inspection Systems program (OTS-PCI-01) requires continued professional and technical services under Object Class 25.1 to sustain active bridge inspection data collection, analysis, and reporting activities through the current period of availability ending 30 September 2026. Exercising th | ['2026-07-31: Program Office initiates PR package and drafts Bona Fide Need memo', '2026-08-05: IGCE completed and signed by Program Office', '2026-08-07: PR package (PR, IGCE, Bona Fide Need memo) submitted to Contracting', '2026-08-12: Contracting Officer reviews package; requests any corrections' | AI Draft - Pending Program Office Review | [] |
| PKG-OCIO-OS-01-FY2026 | FY2026 Year-End Option Exercise – Enterprise IT Operations Support (DCI23F000984) | Option Exercise | DCI23F000984 | 1077000.0 | The Enterprise IT Operations program office (OCIO-OS-01) requires continued IT support services under object class 25.1 to sustain mission-critical system operations, help desk support, and infrastructure maintenance through the end of FY2026. These services represent a bona fide need of the current | ['2026-08-01: Program office initiates procurement request and drafts Bona Fide Need memo', '2026-08-05: Budget Officer certifies funds availability against fund 999-2026-0100', '2026-08-08: IGCE completed and signed by Program Manager', "2026-08-11: Contracting Officer's Option Exercise D&F drafted | AI Draft - Pending Program Office Review | [] |
| PKG-OMA-OS-02-FY2026 | FY2026 Year-End Option Exercise – Human Capital Services (OMA-OS-02) | Option Exercise | DCI25F001642 | 843000.0 | The Human Capital Services program office has a bona fide need within the current FY2026 period of availability (fund 999-2026-0100, expiring 2026-09-30) to sustain uninterrupted delivery of human capital support services currently performed under DCI25F001642 with Apex Technologies Group. Exercisin | ['2026-08-01: Program office initiates requirement; PM signs Bona Fide Need Determination memo', '2026-08-05: Budget Officer certifies funds availability; PR package assembled', '2026-08-08: IGCE completed and reviewed by Contracting Officer', "2026-08-12: Contracting Officer's D&F and Option Exerci | AI Draft - Pending Program Office Review | [] |
| PKG-OWD-OS-01-FY2026 | Year-End Option Exercise – Training Program Administration Support (OWD-OS-01) | Option Exercise | DCI24C000961 | 354000.0 | The Training Program Administration office (OWD-OS-01) requires continued professional and management support services through the end of FY 2026 to sustain ongoing curriculum development, instructor coordination, and learner-management system administration activities that are bona fide needs of th | ['2026-07-31: Program office confirms bona fide need and initiates procurement request package', '2026-08-05: IGCE completed and signed by Program Office lead', '2026-08-08: Bona fide need determination memorandum drafted and routed for legal review', '2026-08-12: Complete procurement request packag | AI Draft - Pending Program Office Review | [] |
| PKG-OWS-OS-02-FY2026 | FY 2026 Year-End Option Exercise – Laboratory Services (OWS-OS-02) | Option Exercise | DCI26F000482 | 981000.0 | The Laboratory Services program (OWS-OS-02) requires continued research and technical support services through the current period of availability ending September 30, 2026. Exercising this option funds ongoing laboratory operations, data analysis, and scientific support tasks that constitute a bona  | ['2026-07-31: Program Manager initiates requirement package and drafts updated SOW confirming FY 2026 bona fide need', '2026-08-05: IGCE completed and signed by Government cost estimator', '2026-08-07: Funds Availability Certification obtained from Budget Officer (fund 999-2026-0100)', '2026-08-11:  | AI Draft - Pending Program Office Review | [] |
| PKG-OWD-GA-01-FY2026 | Year-End Option Exercise – Infrastructure Workforce Services (OWD-GA-01) | Option Exercise | DCI26C000954 | 4207034.66 | The Infrastructure Workforce Grants program office (OWD-GA-01) requires continued professional and technical services under object class 25.1 to support active grant administration, workforce development program delivery, and compliance monitoring activities through the current period of availabilit | ['2026-07-30: Program office initiates requirement; COR drafts scope confirmation memo and bona fide needs determination', '2026-08-01: IGCE completed and certified by program office', '2026-08-04: Funding availability certified by Budget/Finance; PR package assembled', '2026-08-06: PR submitted to  | AI Draft - Pending Program Office Review | [] |
| PKG-OWD-GA-02-FY2026 | Apprenticeship Expansion Grants – Year-End Option Exercise (FY 2026) | Option Exercise | DCI25F001418 | 1328000.0 | The Apprenticeship Expansion Grants program (OWD-GA-02) requires continued technical and support services through the current period of availability ending September 30, 2026, to sustain grant administration, employer outreach, and apprentice enrollment activities already underway. Exercising this o | ['2026-07-31: Program office issues internal tasking memo and initiates package assembly', '2026-08-05: IGCE completed and signed by COR', '2026-08-07: Bona Fide Need memorandum drafted and approved by program manager', '2026-08-11: Acquisition package (IGCE, D&F, Funds Cert, Bona Fide Need memo) su | AI Draft - Pending Program Office Review | [] |
| PKG-OCIO-PCI-02-FY2024 | Cloud Migration Support Services – FY2026 Year-End Option Exercise (OCIO-PCI-02) | Option Exercise | DCI26F001397 | 2091257.36 | The OCIO Cloud Migration program (OCIO-PCI-02) requires continued IT professional services support under object class 25.1 to sustain active cloud infrastructure migration workstreams within the current FY2024–2026 period of availability, which expires September 30, 2026. Exercising the next priced  | ['2026-07-31: Program Manager initiates bona fide need memo and IGCE; COR confirms scope is executable within option period', '2026-08-05: Budget Officer certifies funds availability ($2,091,257.36 from fund 999-2024/2026-0400) and signs PR', '2026-08-08: Complete procurement package (PR, IGCE, bona | AI Draft - Pending Program Office Review | [] |
| PKG-OMA-OS-04-FY2026 | FY2026 Year-End Financial Management Services — Option Exercise (DCI23C001213) | Option Exercise | DCI23C001213 | 709000.0 | The Financial Management Services program office (PPA OMA-OS-04) requires continued financial management support services through the current period of availability ending September 30, 2026. Exercising this option will sustain mission-critical financial operations, reporting, and analytical support | ['2026-08-01: Program office initiates bona fide need determination and drafts requirement summary', '2026-08-05: Budget Officer certifies funds availability for $709,000 against fund 999-2026-0100', '2026-08-07: Program Manager signs Bona Fide Need Determination memo', '2026-08-11: IGCE completed a | AI Draft - Pending Program Office Review | [] |
| PKG-OTS-OS-01-FY2026 | Year-End Option Exercise – Safety Inspection Operations Support (OTS-OS-01) | Option Exercise | DCI25C000456 | 2697000.0 | The Safety Inspection Operations program (OTS-OS-01) requires continued facility and equipment inspection support services through the remainder of FY 2026 to maintain uninterrupted operational safety compliance across monitored sites. Demand for inspection labor and associated operational support h | ['2026-08-01: Program office initiates requirement and drafts bona fide need statement', '2026-08-05: IGCE completed and signed by Program Office', '2026-08-07: Procurement Request (PR) submitted to Contracting Office with funding document', '2026-08-11: Contracting Officer reviews PR package and co | AI Draft - Pending Program Office Review | [] |
| PKG-OTS-OS-02-FY2026 | FY2026 Year-End Option Exercise – Incident Investigation Support Services (OTS-OS-02) | Option Exercise | DCI26F000816 | 2016000.0 | The Incident Investigation program (OTS-OS-02) has a bona fide need for continued investigative support services through the current period of availability ending September 30, 2026. Elevated risk indicators—including a prior-year lapse rate of 26%, a cancelled PR value of 9%, and obligations tracki | ['2026-07-31: Program office initiates Procurement Request and Bona Fide Need Memo; COR confirms active deliverables requiring FY2026 funding', '2026-08-05: IGCE completed and signed by Program Manager', '2026-08-08: PR package (PR, IGCE, Bona Fide Need Memo, Funds Cert) submitted to Contracting Off | AI Draft - Pending Program Office Review | [] |
| PKG-OCIO-OS-02-FY2026 | FY2026 Year-End Cybersecurity Operations Support — Option Exercise (DCI24C000706) | Option Exercise | DCI24C000706 | 783000.0 | The OCIO Cybersecurity Operations program (PPA OCIO-OS-02) requires continued professional and technical support services under object class 25.2 to sustain active threat monitoring, vulnerability management, and security operations center (SOC) functions through the current period of availability e | ['2026-07-31: Program office initiates package; COR drafts Bona Fide Need memo and IGCE', '2026-08-05: Acquisition Plan and PWS/SOW scope-alignment review completed by COR and Program Manager', '2026-08-08: Funding document (999-2026-0100) certified by Budget Officer', '2026-08-12: Option Exercise D | AI Draft - Pending Program Office Review | [] |
| PKG-OMA-OS-01-FY2026 | FY2026 Year-End Facilities and Logistics Support Services — Option Exercise (OMA-OS-01) | Option Exercise | DCI24F001517 | 836000.0 | The Facilities and Logistics program office (PPA OMA-OS-01) has a bona fide need in the current FY2026 period of availability for continued facilities operations and maintenance support services under Object Class 25.2. Ongoing facility sustainment activities — including preventive maintenance, cust | ['2026-08-01: Program office initiates package; COR drafts updated PWS/SOW and IGCE', '2026-08-08: Bona fide need determination and funds certification completed by Budget Officer', '2026-08-13: Acquisition package (IGCE, SOW, funding doc, justification memo) submitted to Contracting Officer', '2026 | AI Draft - Pending Program Office Review | [] |
| PKG-OWS-OS-01-FY2026 | FY2026 Year-End Option Exercise – Drinking Water Program Operations IT/Technical Services (DCI26F000423) | Option Exercise | DCI26F000423 | 1136000.0 | The Drinking Water Program Operations office (OWS-OS-01) requires continued information technology and technical support services under object class 25.1 to sustain mission-critical drinking water monitoring, data management, and regulatory compliance activities through the end of FY2026. These serv | ['2026-07-31: Program office initiates and submits Procurement Request package with IGCE and requirements document to Contracting Officer', '2026-08-05: Contracting Officer confirms option is exercisable and reviews Bona Fide Need Determination and D&F', '2026-08-08: Legal/policy review completed; a | AI Draft - Pending Program Office Review | [] |
| PKG-OGM-GA-01-FY2026 | State Energy Resilience Grants – Year-End Research & Analytical Support Services | Option Exercise | DCI24F000356 | 1077536.35 | The State Energy Resilience Grants program (OGM-GA-01) requires continued research and analytical support services during the current FY 2026 period of availability to complete grant recipient technical assessments, data validation, and performance reporting obligations that are bona fide needs of t | ['2026-08-01: Program office initiates requirement; drafts SOW and IGCE', '2026-08-06: Bona Fide Need memo and Funds Availability Certification signed by Program Manager and Budget Officer', '2026-08-08: Complete PR package (PR, SOW, IGCE, D&F, COR letter) submitted to Contracting Officer', '2026-08 | AI Draft - Pending Program Office Review | [] |
| PKG-OWS-GA-01-FY2026 | FY2026 Year-End Option Exercise – Tribal and Rural Water Infrastructure Technical Support Services | Option Exercise | DCI26F000623 | 1722667.14 | The Office of Water Systems (OWS) requires continued technical support services for Tribal and Rural Water Grant recipients under PPA OWS-GA-01 during the current FY2026 period of availability (fund 999-2026-0600, expiring 2026-09-30). These services include grant compliance monitoring, engineering  | ['2026-07-31: Program Office initiates Procurement Request (PR) and submits IGCE and SOW to Contracting Officer', '2026-08-04: Contracting Officer confirms funds availability with Budget; FAC obtained', '2026-08-06: Bona Fide Need Determination memo drafted and signed by Program Officer', '2026-08-0 | AI Draft - Pending Program Office Review | [] |
| PKG-OWS-PCI-01-FY2024 | Water Infrastructure Modernization – Option Exercise to Obligate FY2024/2026 Projected-Lapse Funds (OWS-PCI-01) | Option Exercise | DCI25C000362 | 1589000.0 | The Water Infrastructure Modernization program (OWS-PCI-01) has a bona fide need in the current FY2024/2026 period of availability for continued professional and technical services supporting the design, assessment, and modernization of aging water infrastructure systems. Work to be performed under  | ['2026-08-01: Program office initiates bona fide need determination and drafts option-period SOW/PWS', '2026-08-06: IGCE completed and signed by Program Manager', '2026-08-08: Funding document (PR) submitted to Budget/Finance for funds certification against 999-2024/2026-0400', '2026-08-12: Certifie | AI Draft - Pending Program Office Review | [] |
| PKG-OTS-RD-01-FY2025 | FY2026 Year-End Option Exercise – Automated Vehicle Safety Research Support Services | Option Exercise | DCI25C000599 | 1476000.0 | The Automated Vehicle Safety Research program (OTS-RD-01) requires continued research and technical support services through the end of the current period of availability (September 30, 2026) to sustain active workstreams in vehicle safety data analysis, test protocol development, and findings docum | ['2026-08-01: Program office initiates procurement request and drafts Bona Fide Need Memorandum', '2026-08-05: IGCE completed and signed by Program Manager', '2026-08-07: Funding document and Funds Availability Certification submitted to Contracting Officer', '2026-08-11: Contracting Officer complet | AI Draft - Pending Program Office Review | [] |
| PKG-OWD-RD-01-FY2025 | FY 2026 Year-End Option Exercise – Workforce Outcomes Evaluation Research & Data Support | Option Exercise | DCI25C001002 | 791000.0 | The Workforce Outcomes Evaluation program (OWD-RD-01) requires continued research and analytical support services through the current period of availability ending September 30, 2026, to sustain active data collection, longitudinal cohort tracking, and interim findings reporting that are already und | ['2026-07-31: Program Manager issues bona fide need memo and finalizes SOW/PWS deliverable list for FY 2026 option period', '2026-08-05: IGCE completed and signed by Program Office; funds availability certification obtained from Finance', '2026-08-08: Acquisition package (SOW, IGCE, bona fide need m | AI Draft - Pending Program Office Review | [] |
| PKG-OGM-OS-01-FY2026 | Grid Resilience Program Operations – FY2026 Year-End Capacity Augmentation | Option Exercise | DCI25C000034 | 558000.0 | The Grid Resilience Program Operations office (OGM-OS-01) requires additional engineering and technical services capacity under Object Class 25.2 to sustain grid resilience analysis, field assessment support, and program operations activities through the current period of availability ending Septemb | ['2026-07-30: Program office initiates requirement; drafts SOW/PWS and IGCE', '2026-08-01: Bona Fide Need Determination memo signed by Program Manager', '2026-08-04: Procurement Request (PR) and Funding Document submitted to Contracting', '2026-08-06: Contracting Officer confirms option availability | AI Draft - Pending Program Office Review | [] |
