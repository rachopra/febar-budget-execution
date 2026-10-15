# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Land synthetic raw feeds
# MAGIC
# MAGIC Simulates four budget fiscal years (FY2023-FY2026) of execution for a **fictional** federal civilian
# MAGIC agency and writes the extracts its siloed trackers would produce into the governed `landing` volume:
# MAGIC
# MAGIC | Feed | Format | Realistic mess the pipeline has to handle |
# MAGIC |---|---|---|
# MAGIC | PPA reference + enacted budget / apportionment | CSV | Withheld apportionment on one line |
# MAGIC | Spend-plan tracker (by PPA x object class x month) | CSV, two templates | Currency strings, `$K` units, lower-case PPA codes, offices that never re-plan |
# MAGIC | Procurement-request tracker | JSON lines, one event per status change | Nested payloads, duplicate deliveries, events missing a PR id |
# MAGIC | Invoice register (IPP / PMS) | CSV | Payee PII, over-billing, duplicate submissions, unknown contract numbers, late payments |
# MAGIC
# MAGIC The reporting date is **2026-07-31**: early Q4, when unobligated balances on expiring funds need the most scrutiny.

# COMMAND ----------

dbutils.widgets.text("catalog", "rachopra_catalog")
dbutils.widgets.text("schema", "fe_bar")
dbutils.widgets.text("as_of_date", "2026-07-31")
dbutils.widgets.text("seed", "42")
dbutils.widgets.dropdown("reset_landing", "false", ["true", "false"])

import os
import sys
from datetime import date

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
as_of = date.fromisoformat(dbutils.widgets.get("as_of_date"))
seed = int(dbutils.widgets.get("seed"))
landing = f"/Volumes/{catalog}/{schema}/landing"

sys.path.append(os.path.abspath(".."))
from datagen.budget_generator import generate

# COMMAND ----------

if dbutils.widgets.get("reset_landing") == "true":
    for entry in dbutils.fs.ls(landing):
        dbutils.fs.rm(entry.path, recurse=True)
    print(f"Cleared {landing}")

summary = generate(landing, seed=seed, as_of=as_of)
truth = summary.pop("ground_truth")
for k, v in summary.items():
    print(f"{k:>24}: {v}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## What landed

# COMMAND ----------

rows = []
for feed in ["reference", "budget_authority", "spend_plan/budget_office_template",
             "spend_plan/legacy_office_template", "procurement_requests", "invoices"]:
    files = dbutils.fs.ls(f"{landing}/{feed}")
    rows.append((feed, len(files), round(sum(f.size for f in files) / 1e6, 2), sorted(f.name for f in files)[-1]))
display(spark.createDataFrame(rows, "feed string, files int, size_mb double, latest_file string"))

# COMMAND ----------

# MAGIC %md
# MAGIC ### The same spend plan, two templates
# MAGIC Budget-office template (whole dollars, currency strings) vs. legacy template (thousands of dollars, lower-case PPA codes).

# COMMAND ----------

sp = f"{landing}/spend_plan"
a = sorted(f.path for f in dbutils.fs.ls(f"{sp}/budget_office_template"))[0]
b = sorted(f.path for f in dbutils.fs.ls(f"{sp}/legacy_office_template"))[0]
print(dbutils.fs.head(a, 600))
print("-" * 80)
print(dbutils.fs.head(b, 400))

# COMMAND ----------

# MAGIC %md
# MAGIC ### A PR-tracker event (nested JSON)

# COMMAND ----------

import json
latest = sorted(f.path for f in dbutils.fs.ls(f"{landing}/procurement_requests"))[-1]
first_award = next(l for l in dbutils.fs.head(latest, 200000).splitlines() if '"AWARD"' in l)
print(json.dumps(json.loads(first_award), indent=2))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Simulation sanity check (not landed)
# MAGIC Final lapse rate (unobligated share of budget authority at expiration) for lines that expired before the reporting date.
# MAGIC Offices with weak execution health (late PRs, long PALT) lapse more; the lapse-risk model should learn this from the data alone.

# COMMAND ----------

expired = truth[truth.expiration <= as_of]
display(
    expired.assign(lapse_pct=lambda d: (100 * d.lapse_pct).round(2))
    .groupby("office", as_index=False)
    .agg(expired_lines=("ppa_code", "count"), median_lapse_pct=("lapse_pct", "median"),
         max_lapse_pct=("lapse_pct", "max"))
    .sort_values("median_lapse_pct", ascending=False)
)
