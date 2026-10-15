# Land Raw Data

- Job task: `land_raw_data` (task run `695639909594735`)
- Result: **SUCCESS**, started 2026-10-15 13:46:49 UTC, ran 74s on serverless compute
- Notebook: `/Workspace/Users/rahul.chopra@databricks.com/.bundle/febar-budget-execution/dev/files/src/notebooks/01_generate_raw_data`

# 01 · Land synthetic raw feeds

Simulates four budget fiscal years (FY2023-FY2026) of execution for a **fictional** federal civilian
agency and writes the extracts its siloed trackers would produce into the governed `landing` volume:

| Feed | Format | Realistic mess the pipeline has to handle |
|---|---|---|
| PPA reference + enacted budget / apportionment | CSV | Withheld apportionment on one line |
| Spend-plan tracker (by PPA x object class x month) | CSV, two templates | Currency strings, `$K` units, lower-case PPA codes, offices that never re-plan |
| Procurement-request tracker | JSON lines, one event per status change | Nested payloads, duplicate deliveries, events missing a PR id |
| Invoice register (IPP / PMS) | CSV | Payee PII, over-billing, duplicate submissions, unknown contract numbers, late payments |

The reporting date is **2026-07-31**: early Q4, when unobligated balances on expiring funds need the most scrutiny.

```python
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
```

```python
if dbutils.widgets.get("reset_landing") == "true":
    for entry in dbutils.fs.ls(landing):
        dbutils.fs.rm(entry.path, recurse=True)
    print(f"Cleared {landing}")

summary = generate(landing, seed=seed, as_of=as_of)
truth = summary.pop("ground_truth")
for k, v in summary.items():
    print(f"{k:>24}: {v}")
```

**Output:**

```text
Cleared /Volumes/rachopra_catalog/fe_bar/landing
                   as_of: 2026-07-31
            budget_lines: 116
                    ppas: 29
        spend_plan_files: 157
         spend_plan_rows: 50244
          pr_event_files: 47
               pr_events: 21534
    procurement_requests: 4485
           invoice_files: 45
                invoices: 19736
```

## What landed

```python
rows = []
for feed in ["reference", "budget_authority", "spend_plan/budget_office_template",
             "spend_plan/legacy_office_template", "procurement_requests", "invoices"]:
    files = dbutils.fs.ls(f"{landing}/{feed}")
    rows.append((feed, len(files), round(sum(f.size for f in files) / 1e6, 2), sorted(f.name for f in files)[-1]))
display(spark.createDataFrame(rows, "feed string, files int, size_mb double, latest_file string"))
```

**Output:**

| feed | files | size_mb | latest_file |
|---|---|---|---|
| reference | 1 | 0.01 | ppa_master.csv |
| budget_authority | 4 | 0.02 | budget_authority_FY2026.csv |
| spend_plan/budget_office_template | 124 | 6.45 | spend_plan_FY2026_OWS_rev04_2026-07-10.csv |
| spend_plan/legacy_office_template | 33 | 0.6 | spend_plan_FY2026_OWD_rev04_2026-07-10.csv |
| procurement_requests | 47 | 20.96 | pr_events_2026-07.jsonl |
| invoices | 45 | 5.11 | invoices_2026-07.csv |

### The same spend plan, two templates
Budget-office template (whole dollars, currency strings) vs. legacy template (thousands of dollars, lower-case PPA codes).

```python
sp = f"{landing}/spend_plan"
a = sorted(f.path for f in dbutils.fs.ls(f"{sp}/budget_office_template"))[0]
b = sorted(f.path for f in dbutils.fs.ls(f"{sp}/legacy_office_template"))[0]
print(dbutils.fs.head(a, 600))
print("-" * 80)
print(dbutils.fs.head(b, 400))
```

**Output:**

```text
[Truncated to first 600 bytes]
Fiscal Year,PPA Code,PPA Name,Fund (TAS),Object Class,Month,Planned Obligations,Planned Expenditures,Last Updated By
2023,OCIO-OS-01,Enterprise IT Operations,999-2023-0100,25.1 Advisory and assistance services,Oct-22,"$393,409.95",$0.00,cameron.novak@dci.example.gov
2023,OCIO-OS-01,Enterprise IT Operations,999-2023-0100,25.1 Advisory and assistance services,Nov-22,"$472,091.94","$32,784.16",cameron.novak@dci.example.gov
2023,OCIO-OS-01,Enterprise IT Operations,999-2023-0100,25.1 Advisory and assistance services,Dec-22,"$472,091.94","$72,125.16",cameron.novak@dci.example.gov
2023,OCIO-OS-01,Ent
--------------------------------------------------------------------------------
[Truncated to first 400 bytes]
FY,PPA,Fund,BOC,Period,Obligation Plan ($K),Outlay Plan ($K),Owner
2023,ots-os-01,999-2023-0100,25.1,2022-10,362.6,0.0,parker.garcia@dci.example.gov
2023,ots-os-01,999-2023-0100,25.1,2022-11,435.1,30.2,parker.garcia@dci.example.gov
2023,ots-os-01,999-2023-0100,25.1,2022-12,435.1,66.5,parker.garcia@dci.example.gov
2023,ots-os-01,999-2023-0100,25.1,2023-01,507.7,102.7,parker.garcia@dci.example.gov
2
```

### A PR-tracker event (nested JSON)

```python
import json
latest = sorted(f.path for f in dbutils.fs.ls(f"{landing}/procurement_requests"))[-1]
first_award = next(l for l in dbutils.fs.head(latest, 200000).splitlines() if '"AWARD"' in l)
print(json.dumps(json.loads(first_award), indent=2))
```

**Output:**

```text
[Truncated to first 200000 bytes]
{
  "event_id": "EVT-0015469",
  "event_type": "AWARD",
  "event_ts": "2026-07-01T07:56:45",
  "source_system": "PR Tracker (SharePoint list export)",
  "status": "Awarded",
  "status_reason": null,
  "updated_by": "hayden.garcia@dci.example.gov",
  "pr": {
    "pr_id": "PR-26-OWD-0006",
    "fiscal_year": 2026,
    "ppa_code": "OWD-GA-01",
    "tas": "999-2026-0600",
    "office_code": "OWD",
    "title": "Infrastructure Workforce Grants - cooperative agreement 5",
    "description": "Infrastructure Workforce Grants - cooperative agreement 5 supporting the Infrastructure Workforce Grants PPA. Funded from 999-2026-0600 (object class 41.0 Grants, subsidies, and contributions).",
    "object_class": "41.0",
    "acquisition_type": "Grant Award",
    "contract_vehicle": "Notice of Funding Opportunity",
    "estimated_amount": 3271931.62,
    "priority": "High",
    "requested_by": "kendall.foster@dci.example.gov",
    "contracting_officer": "hayden.garcia@dci.example.gov",
    "need_by_date": "2026-07-14",
    "year_end_action": false
  },
  "award": {
    "contract_number": "DCI26G000225",
    "modification_number": "000",
    "action_date": "2026-07-01",
    "obligated_amount": 3167002.52,
    "period_of_performance_start": "2026-07-01",
    "period_of_performance_end": "2028-06-30",
    "vendor": {
      "name": "State of Idaho Department of Transportation",
      "uei": "8R0DXN17UDSE"
    }
  }
}
```

### Simulation sanity check (not landed)
Final lapse rate (unobligated share of budget authority at expiration) for lines that expired before the reporting date.
Offices with weak execution health (late PRs, long PALT) lapse more; the lapse-risk model should learn this from the data alone.

```python
expired = truth[truth.expiration <= as_of]
display(
    expired.assign(lapse_pct=lambda d: (100 * d.lapse_pct).round(2))
    .groupby("office", as_index=False)
    .agg(expired_lines=("ppa_code", "count"), median_lapse_pct=("lapse_pct", "median"),
         max_lapse_pct=("lapse_pct", "max"))
    .sort_values("median_lapse_pct", ascending=False)
)
```

**Output:**

| office | expired_lines | median_lapse_pct | max_lapse_pct |
|---|---|---|---|
| OTS | 12 | 12.965 | 56.11 |
| OWD | 11 | 5.15 | 30.59 |
| OGM | 12 | 2.6799999999999997 | 9.36 |
| OWS | 12 | 1.825 | 8.52 |
| OCIO | 11 | 1.77 | 6.81 |
| OMA | 13 | 1.4 | 4.97 |
