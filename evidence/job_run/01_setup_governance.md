# Setup Governance

- Job task: `setup_governance` (task run `157164303325892`)
- Result: **SUCCESS**, started 2026-10-15 13:45:59 UTC, ran 50s on serverless compute
- Notebook: `/Workspace/Users/rahul.chopra@databricks.com/.bundle/febar-budget-execution/dev/files/src/notebooks/00_setup_governance`

# 00 · Setup and governance foundations

Creates the Unity Catalog objects the rest of the build depends on **before** any data lands:

| Object | Purpose |
|---|---|
| `landing` volume | Governed drop zone for the three trackers' raw extracts |
| `office_access_map` | Entitlements: which program office(s) each principal may see, and who may see payee PII |
| `office_row_filter()` | Row filter attached to procurement and obligation tables: program offices see only their own rows |
| `mask_payee_pii()` | Column mask attached to payee TIN and bank fields on invoices |

The row filter and mask are declared on the pipeline's tables, so the policies exist from the first write.

```python
dbutils.widgets.text("catalog", "rachopra_catalog")
dbutils.widgets.text("schema", "fe_bar")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
fq = f"{catalog}.{schema}"
me = spark.sql("SELECT current_user()").first()[0]
print(f"Target schema: {fq}\nRunning as:    {me}")
```

**Output:**

```text
Target schema: rachopra_catalog.fe_bar
Running as:    rahul.chopra@databricks.com
```

```python
spark.sql(f"""
CREATE SCHEMA IF NOT EXISTS {fq}
COMMENT 'Budget execution and financial oversight (synthetic data, fictional agency): spend plans, procurement requests, obligations, invoices, execution metrics, lapse-risk forecasts.'
""")
spark.sql(f"""
CREATE VOLUME IF NOT EXISTS {fq}.landing
COMMENT 'Raw drop zone for budget authority, spend-plan spreadsheets, PR-tracker exports and invoice-register extracts. Ingested by Auto Loader.'
""")
display(spark.sql(f"DESCRIBE SCHEMA EXTENDED {fq}"))
```

**Output:**

| database_description_item | database_description_value |
|---|---|
| Catalog Name | rachopra_catalog |
| Namespace Name | fe_bar |
| Comment | Budget execution and financial oversight (synthetic data, fictional agency) |
| Location |  |
| Owner | rahul.chopra@databricks.com |
| Properties | ((unity.catalog.managed.delta.defaults.delta.parquet.format.version,2.12.0), (unity.catalog.managed.delta.defaults.delta.parquet.format.version.afe.internal,2.12.0), (unity.catalog.managed.iceberg.defaults.delta.feature.catalogManaged,supported)) |
| Predictive Optimization | ENABLE (inherited from METASTORE metastore_aws_us_east_1) |

## Entitlements table
One row per principal per office. `ALL` grants agency-wide visibility (CFO / budget office).
The program-office rows use fictional addresses to illustrate how a program analyst is scoped.

```python
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {fq}.office_access_map (
  principal STRING NOT NULL COMMENT 'User e-mail or service-principal application ID',
  office_code STRING NOT NULL COMMENT 'Program office the principal may see, or ALL for agency-wide access',
  budget_role STRING COMMENT 'Budget role (Budget Director, Budget Analyst, Program Analyst, Disbursing Officer, Application)',
  can_view_payee_pii BOOLEAN NOT NULL COMMENT 'Whether the principal may see unmasked payee TIN and bank details'
)
COMMENT 'Entitlements driving the office row filter and the payee-PII column mask.'
""")

entitlements = [
    (me, "ALL", "Budget Director", False),
    ("ots.program.analyst@dci.example.gov", "OTS", "Program Analyst", False),
    ("owd.program.analyst@dci.example.gov", "OWD", "Program Analyst", False),
    ("disbursing.officer@dci.example.gov", "ALL", "Disbursing Officer", True),
]
spark.createDataFrame(entitlements, "principal string, office_code string, budget_role string, can_view_payee_pii boolean") \
    .createOrReplaceTempView("seed_entitlements")
spark.sql(f"""
MERGE INTO {fq}.office_access_map t
USING seed_entitlements s
ON t.principal = s.principal AND t.office_code = s.office_code
WHEN MATCHED THEN UPDATE SET budget_role = s.budget_role, can_view_payee_pii = s.can_view_payee_pii
WHEN NOT MATCHED THEN INSERT *
""")
display(spark.table(f"{fq}.office_access_map"))
```

**Output:**

| principal | office_code | budget_role | can_view_payee_pii |
|---|---|---|---|
| disbursing.officer@dci.example.gov | ALL | Disbursing Officer | True |
| ots.program.analyst@dci.example.gov | OTS | Program Analyst | False |
| owd.program.analyst@dci.example.gov | OWD | Program Analyst | False |
| rahul.chopra@databricks.com | ALL | Budget Director | False |

## Row filter and column mask

```python
spark.sql(f"""
CREATE OR REPLACE FUNCTION {fq}.office_row_filter(p_office_code STRING)
RETURNS BOOLEAN
COMMENT 'Row filter: a principal sees rows for the offices granted in office_access_map (ALL = agency-wide).'
RETURN EXISTS (
  SELECT 1 FROM {fq}.office_access_map m
  WHERE m.principal = current_user() AND m.office_code IN ('ALL', p_office_code)
)
""")

spark.sql(f"""
CREATE OR REPLACE FUNCTION {fq}.mask_payee_pii(p_value STRING)
RETURNS STRING
COMMENT 'Column mask: payee TIN / bank details are visible only to principals with can_view_payee_pii; others see the last 4 characters.'
RETURN CASE
  WHEN p_value IS NULL THEN NULL
  WHEN EXISTS (
    SELECT 1 FROM {fq}.office_access_map m
    WHERE m.principal = current_user() AND m.can_view_payee_pii
  ) THEN p_value
  ELSE concat(repeat('*', greatest(length(p_value) - 4, 0)), right(p_value, 4))
END
""")

display(spark.sql(f"""
SELECT routine_name, data_type AS returns, comment
FROM {catalog}.information_schema.routines
WHERE routine_schema = '{schema}'
ORDER BY routine_name
"""))
```

**Output:**

| routine_name | returns | comment |
|---|---|---|
| mask_payee_pii | STRING | Column mask: payee TIN / bank details are visible only to principals with can_view_payee_pii; others see the last 4 characters. |
| office_row_filter | BOOLEAN | Row filter: a principal sees rows for the offices granted in office_access_map (ALL = agency-wide). |

```python
display(spark.sql(f"""
SELECT '{me}' AS principal,
       {fq}.office_row_filter('OTS') AS sees_ots_rows,
       {fq}.mask_payee_pii('12-3456789') AS tin_as_seen
"""))
```

**Output:**

| principal | sees_ots_rows | tin_as_seen |
|---|---|---|
| rahul.chopra@databricks.com | True | ******6789 |
