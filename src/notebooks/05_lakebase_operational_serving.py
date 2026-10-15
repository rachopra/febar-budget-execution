# Databricks notebook source
# MAGIC %md
# MAGIC # 05 · Lakebase: operational serving and write-back
# MAGIC
# MAGIC The app needs millisecond reads and transactional writes, which is a Postgres workload, not a warehouse one.
# MAGIC
# MAGIC ```
# MAGIC  UC gold tables ──synced tables (snapshot)──▶ Lakebase Postgres `budget_ops.fe_bar.*`   (read path for the app)
# MAGIC                                             Lakebase Postgres `budget_ops.workflow.*`  (app writes: alert actions,
# MAGIC                                                                                           package requests, sign-offs)
# MAGIC  UC Delta `fe_bar.app_*` ◀──change data feed (CDF config)─────────┘                     (back to the lakehouse)
# MAGIC ```
# MAGIC
# MAGIC Program-office scoping in the app uses the same `office_access_map` entitlements that drive the UC row filter
# MAGIC (synced alongside the gold tables), so there is one source of truth for who sees which office.

# COMMAND ----------

# MAGIC %pip install -q -U databricks-sdk "psycopg[binary]"
# MAGIC %restart_python

# COMMAND ----------

dbutils.widgets.text("catalog", "rachopra_catalog")
dbutils.widgets.text("schema", "fe_bar")
dbutils.widgets.text("lakebase_project", "fe-bar-budget")

import time

import pandas as pd
import psycopg
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.postgres import (CdfConfig, NewPipelineSpec, SyncedTable,
                                             SyncedTableSyncedTableSpec,
                                             SyncedTableSyncedTableSpecSyncedTableSchedulingPolicy)

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
project = dbutils.widgets.get("lakebase_project")
fq = f"{catalog}.{schema}"
PG_DB = "budget_ops"

w = WorkspaceClient()
me = w.current_user.me().user_name
branch = f"projects/{project}/branches/production"
endpoint = next(iter(w.postgres.list_endpoints(parent=branch)))
host = endpoint.status.hosts.host
print(f"Project {project}  endpoint {endpoint.name}  state {endpoint.status.current_state}\nhost {host}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Synced tables: gold → Postgres

# COMMAND ----------

SYNCS = {
    "gold_budget_execution": ["line_id"],
    "gold_monthly_execution": ["line_id", "month"],
    "gold_office_execution_summary": ["office_code", "budget_fiscal_year", "fund_status"],
    "gold_financial_risk_alerts": ["alert_id"],
    "gold_procurement_pipeline": ["pr_id"],
    "gold_lapse_risk_forecast": ["line_id"],
    "gold_execution_briefings": ["line_id"],
    "gold_quarterly_review_briefings": ["office_code"],
    "gold_procurement_package_drafts": ["package_id"],
    "office_access_map": ["principal", "office_code"],
}


def synced_name(source):
    return f"{fq}.lb_{source.removeprefix('gold_')}"


existing = {}
for source in SYNCS:
    try:
        existing[source] = w.postgres.get_synced_table(name=f"synced_tables/{synced_name(source)}")
    except Exception:
        pass

def create_sync(source, pk):
    w.postgres.create_synced_table(
        synced_table_id=synced_name(source),
        synced_table=SyncedTable(spec=SyncedTableSyncedTableSpec(
            source_table_full_name=f"{fq}.{source}",
            primary_key_columns=pk,
            branch=branch,
            postgres_database=PG_DB,
            create_database_objects_if_missing=True,
            scheduling_policy=SyncedTableSyncedTableSpecSyncedTableSchedulingPolicy.SNAPSHOT,
            new_pipeline_spec=NewPipelineSpec(storage_catalog=catalog, storage_schema=schema),
        )),
    )
    print(f"created synced table {synced_name(source)}  <-  {fq}.{source}")


for source, pk in SYNCS.items():
    if source not in existing:
        create_sync(source, pk)

# Re-snapshot tables that already existed so Postgres reflects this run's gold data
for source, st in existing.items():
    if st.status and st.status.pipeline_id:
        w.pipelines.start_update(pipeline_id=st.status.pipeline_id, full_refresh=True)
        print(f"refreshing {synced_name(source)}")
if existing:
    time.sleep(90)

# COMMAND ----------

def sync_states():
    rows = []
    for source in SYNCS:
        st = w.postgres.get_synced_table(name=f"synced_tables/{synced_name(source)}")
        s = st.status
        state = s.detailed_state.value if s and s.detailed_state else "UNKNOWN"
        rows.append({"synced_table": synced_name(source).split(".")[-1], "source": source,
                     "state": state.removeprefix("SYNCED_TABLE_"), "message": (s.message or "")[:90] if s else ""})
    return pd.DataFrame(rows)


def wait_for_syncs(minutes=25):
    deadline = time.time() + minutes * 60
    while True:
        states = sync_states()
        settled = states.state.str.contains("ONLINE|FAILED", regex=True) & ~states.state.str.contains("UPDATING|TRIGGERED", regex=True)
        if settled.all() or time.time() > deadline:
            return states
        time.sleep(30)


states = wait_for_syncs()
failed = states[states.state.str.contains("FAILED")]
for row in failed.itertuples():  # e.g. the gold schema changed: recreate the synced table
    print(f"recreating {row.synced_table} ({row.state}: {row.message})")
    w.postgres.delete_synced_table(name=f"synced_tables/{synced_name(row.source)}")
    time.sleep(20)
    create_sync(row.source, SYNCS[row.source])
if not failed.empty:
    states = wait_for_syncs()
display(states)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Workflow tables the app writes to

# COMMAND ----------

def connect(dbname=PG_DB):
    cred = w.postgres.generate_database_credential(endpoint=endpoint.name)
    return psycopg.connect(host=host, port=5432, dbname=dbname, user=me, password=cred.token,
                           sslmode="require", autocommit=True)


WORKFLOW_DDL = """
CREATE SCHEMA IF NOT EXISTS workflow;

CREATE TABLE IF NOT EXISTS workflow.app_alert_actions (
  action_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  alert_id      TEXT NOT NULL,
  alert_type    TEXT,
  line_id       TEXT,
  office_code   TEXT,
  action        TEXT NOT NULL CHECK (action IN ('Acknowledged', 'Assigned', 'Escalated', 'Resolved')),
  assignee      TEXT,
  note          TEXT,
  acted_by      TEXT NOT NULL,
  acted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workflow.app_procurement_packages (
  package_id          TEXT PRIMARY KEY,
  line_id             TEXT NOT NULL,
  office_code         TEXT NOT NULL,
  title               TEXT NOT NULL,
  acquisition_type    TEXT,
  contract_number     TEXT,
  amount              NUMERIC(18, 2),
  requirement_summary TEXT,
  justification       TEXT,
  required_documents  JSONB,
  milestones          JSONB,
  status              TEXT NOT NULL DEFAULT 'Submitted to Acquisition',
  source              TEXT NOT NULL,
  model_endpoint      TEXT,
  created_by          TEXT NOT NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workflow.app_review_signoffs (
  signoff_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  office_code    TEXT NOT NULL,
  fiscal_year    INT NOT NULL,
  fiscal_quarter INT NOT NULL,
  decision       TEXT NOT NULL CHECK (decision IN ('Approved', 'Approved with conditions', 'Returned')),
  comment        TEXT,
  signed_by      TEXT NOT NULL,
  signed_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- the change data feed to Unity Catalog needs full before/after images of each row
ALTER TABLE workflow.app_alert_actions REPLICA IDENTITY FULL;
ALTER TABLE workflow.app_procurement_packages REPLICA IDENTITY FULL;
ALTER TABLE workflow.app_review_signoffs REPLICA IDENTITY FULL;
"""
with connect() as conn:
    conn.execute(WORKFLOW_DDL)
    tables = conn.execute("""
        SELECT table_schema, table_name,
               (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from %I.%I', table_schema, table_name), false, true, '')))[1]::text::bigint AS row_count
        FROM information_schema.tables
        WHERE table_schema IN ('fe_bar', 'workflow') AND table_type = 'BASE TABLE'
        ORDER BY 1, 2""").fetchall()
display(pd.DataFrame(tables, columns=["pg_schema", "table", "rows"]))

# COMMAND ----------

# MAGIC %md
# MAGIC ## App access: least privilege for the app's service principal
# MAGIC Read-only on the synced serving tables; read/insert/update (no delete) on the workflow tables.

# COMMAND ----------

APP_NAME = "febar-budget-execution"
APP_GRANTS = """
GRANT USAGE ON SCHEMA fe_bar TO "{sp}";
GRANT SELECT ON ALL TABLES IN SCHEMA fe_bar TO "{sp}";
GRANT USAGE ON SCHEMA workflow TO "{sp}";
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA workflow TO "{sp}";
GRANT USAGE ON ALL SEQUENCES IN SCHEMA workflow TO "{sp}";
"""
try:
    app_sp = w.apps.get(APP_NAME).service_principal_client_id
except Exception:
    app_sp = None
if app_sp:
    with connect() as conn:
        conn.execute(APP_GRANTS.format(sp=app_sp))
        grants = conn.execute("""
            SELECT table_schema, privilege_type, COUNT(*) AS tables
            FROM information_schema.role_table_grants WHERE grantee = %s
            GROUP BY 1, 2 ORDER BY 1, 2""", (app_sp,)).fetchall()
    display(pd.DataFrame(grants, columns=["pg_schema", "privilege", "tables"]))
else:
    print(f"App {APP_NAME} not deployed yet; run `databricks bundle run budget_execution_app`, then re-run this cell.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Change data feed: workflow tables → Unity Catalog Delta

# COMMAND ----------

database = next(d for d in w.postgres.list_databases(parent=branch)
                if (getattr(d.status, "postgres_database", None) or d.name.split("/")[-1]) in (PG_DB, PG_DB.replace("_", "-")))
cdf_parent = database.name
try:
    cdf = w.postgres.get_cdf_config(name=f"{cdf_parent}/cdf-configs/workflow")
    print("CDF config exists:", cdf.name)
except Exception:
    op = w.postgres.create_cdf_config(parent=cdf_parent, cdf_config_id="workflow",
                                      cdf_config=CdfConfig(catalog=catalog, schema=schema, postgres_schema="workflow"))
    print("Created CDF config for workflow schema ->", fq)

time.sleep(60)
statuses = [{"postgres_table": st.postgres_table, "state": str(st.state.value if st.state else ""),
             "detail": st.status_detail, "last_sync_time": str(st.last_sync_time)}
            for st in w.postgres.list_cdf_statuses(parent=f"{cdf_parent}/cdf-configs/workflow")]
display(pd.DataFrame(statuses))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read-path check: what the app's overview query returns from Postgres

# COMMAND ----------

with connect() as conn:
    t0 = time.perf_counter()
    rows = conn.execute("""
        SELECT office_name,
               round(sum(total_budget) / 1e6, 1) AS budget_m,
               round(sum(obligated_to_date) / 1e6, 1) AS obligated_m,
               round(100 * sum(obligated_to_date) / sum(total_budget), 1) AS obligation_rate_pct,
               round(100 * sum(obligated_to_date) / nullif(sum(planned_obligations_to_date), 0), 1) AS burn_vs_plan_pct
        FROM fe_bar.lb_budget_execution
        WHERE fund_status = 'Current'
        GROUP BY office_name ORDER BY burn_vs_plan_pct""").fetchall()
    ms = (time.perf_counter() - t0) * 1000
display(pd.DataFrame(rows, columns=["office", "budget_m", "obligated_m", "obligation_rate_pct", "burn_vs_plan_pct"]))
print(f"Postgres round trip: {ms:.1f} ms")
