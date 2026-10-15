"""Silver: typed, conformed, quality-checked records that connect the three trackers.

* Spend plans: two spreadsheet templates are normalised into one table by two append flows.
* PR tracker: change events are de-duplicated, then AUTO CDC builds the current state of every
  procurement request (SCD1) and its full status history (SCD2).
* Obligations and invoices are keyed by obligation document so payments roll up to the
  budget line that funded them.

Row filters (office scoping) and column masks (payee PII) are UC functions created by the
governance setup notebook before the pipeline runs.
"""

from pyspark import pipelines as dp
from pyspark.sql import Window
from pyspark.sql import functions as F

GOV = spark.conf.get("governance_schema")
OFFICE_FILTER = f"ROW FILTER {GOV}.office_row_filter ON (office_code)"
PII_MASK = f"MASK {GOV}.mask_payee_pii"
PPA_CODE_RE = "^[A-Z]+-[A-Z]+-[0-9]{2}$"


def _money(col):
    """'$1,234.50' / '1234.5' -> DECIMAL(18,2)."""
    return F.regexp_replace(F.col(col), r"[$,\s]", "").cast("decimal(18,2)")


def _latest(df, keys, order_cols):
    w = Window.partitionBy(*keys).orderBy(*[F.col(c).desc() for c in order_cols])
    return df.withColumn("_rn", F.row_number().over(w)).filter("_rn = 1").drop("_rn")


# --------------------------------------------------------------------------- reference
@dp.materialized_view(comment="Conformed PPA reference: one row per Program/Project/Activity with owning office and appropriation.")
@dp.expect_or_fail("valid_ppa_code", f"ppa_code RLIKE '{PPA_CODE_RE}'")
def silver_ppa():
    df = spark.read.table("bronze_ppa_master").withColumn("ppa_code", F.upper(F.trim("ppa_code")))
    return _latest(df, ["ppa_code"], ["_file_modified_at", "_ingested_at"]).select(
        "ppa_code", "ppa_name", "office_code", "office_name", "appropriation_code",
        "appropriation_name", "main_account", "fund_type",
        F.col("years_of_availability").cast("int").alias("years_of_availability"),
        "program_manager", "program_manager_email", "budget_analyst", "budget_analyst_email",
    )


@dp.materialized_view(comment="Budget lines (PPA x budget fiscal year) with enacted authority, OMB apportionment and period of availability.")
@dp.expect_or_fail("positive_enacted_amount", "enacted_amount > 0")
@dp.expect("apportionment_within_enacted", "apportioned_q4 <= enacted_amount")
def silver_budget_lines():
    ba = spark.read.table("bronze_budget_authority").withColumn("ppa_code", F.upper(F.trim("ppa_code")))
    ba = _latest(ba, ["budget_fiscal_year", "ppa_code"], ["_file_modified_at", "_ingested_at"])
    ppa = spark.read.table("silver_ppa")
    return (
        ba.join(ppa.select("ppa_code", "ppa_name", "office_code", "office_name",
                           "appropriation_code", "appropriation_name"), "ppa_code", "left")
        .select(
            F.concat("ppa_code", F.lit("-FY"), "budget_fiscal_year").alias("line_id"),
            F.col("budget_fiscal_year").cast("int").alias("budget_fiscal_year"),
            "ppa_code", "ppa_name", "office_code", "office_name", "appropriation_code",
            "appropriation_name", "tas", "fund_type",
            F.col("beginning_poa").cast("int").alias("beginning_poa"),
            F.col("ending_poa").cast("int").alias("ending_poa"),
            F.to_date("expiration_date").alias("expiration_date"),
            _money("presidents_budget_request").alias("presidents_budget_request"),
            _money("enacted_amount").alias("enacted_amount"),
            F.to_date("enactment_date").alias("enactment_date"),
            *[_money(f"apportioned_q{q}").alias(f"apportioned_q{q}") for q in range(1, 5)],
            "apportionment_footnote",
        )
    )


# --------------------------------------------------------------------------- spend plans
SPEND_PLAN_RULES = {
    "valid_ppa_code": f"ppa_code RLIKE '{PPA_CODE_RE}'",
    "valid_plan_month": "plan_month IS NOT NULL",
    "valid_planned_obligations": "planned_obligations IS NOT NULL AND planned_obligations >= 0",
    "valid_revision": "revision_no IS NOT NULL AND revision_date IS NOT NULL",
}
_REV = r"rev(\d+)_(\d{4}-\d{2}-\d{2})"
_OFFICE = r"spend_plan_FY\d{4}_([A-Z]+)_rev"

dp.create_streaming_table(
    "silver_spend_plan",
    comment="Every spend-plan revision from every office, normalised to whole dollars by PPA, object class and month.",
    expect_all_or_drop=SPEND_PLAN_RULES,
)


def _with_revision(df):
    return (
        df.withColumn("revision_no", F.regexp_extract("_source_file", _REV, 1).cast("int"))
        .withColumn("revision_date", F.to_date(F.regexp_extract("_source_file", _REV, 2)))
        .withColumn("office_code", F.regexp_extract("_source_file", _OFFICE, 1))
    )


@dp.append_flow(target="silver_spend_plan", name="spend_plan_from_budget_office_template")
def spend_plan_budget_office():
    df = _with_revision(spark.readStream.table("bronze_spend_plan_budget_office"))
    return df.select(
        F.col("fiscal_year").cast("int").alias("budget_fiscal_year"),
        F.upper(F.trim("ppa_code")).alias("ppa_code"),
        F.trim("fund_tas").alias("tas"),
        F.split(F.trim("object_class"), " ").getItem(0).alias("object_class"),
        F.to_date("month", "MMM-yy").alias("plan_month"),
        _money("planned_obligations").alias("planned_obligations"),
        _money("planned_expenditures").alias("planned_expenditures"),
        "revision_no", "revision_date", "office_code",
        F.lit("budget_office_template").alias("source_template"),
        F.col("last_updated_by").alias("submitted_by"),
        "_source_file", "_ingested_at",
    )


@dp.append_flow(target="silver_spend_plan", name="spend_plan_from_legacy_template")
def spend_plan_legacy():
    df = _with_revision(spark.readStream.table("bronze_spend_plan_legacy"))
    thousands = lambda c: (F.col(c).cast("decimal(18,4)") * 1000).cast("decimal(18,2)")
    return df.select(
        F.col("fy").cast("int").alias("budget_fiscal_year"),
        F.upper(F.trim("ppa")).alias("ppa_code"),
        F.trim("fund").alias("tas"),
        F.trim("boc").alias("object_class"),
        F.to_date(F.concat(F.col("period"), F.lit("-01"))).alias("plan_month"),
        thousands("obligation_plan_k").alias("planned_obligations"),
        thousands("outlay_plan_k").alias("planned_expenditures"),
        "revision_no", "revision_date", "office_code",
        F.lit("legacy_office_template").alias("source_template"),
        F.col("owner").alias("submitted_by"),
        "_source_file", "_ingested_at",
    )


@dp.materialized_view(comment="Current spend plan (re-forecast): the latest revision each office has submitted for each budget fiscal year.")
def silver_spend_plan_current():
    sp = spark.read.table("silver_spend_plan")
    latest = sp.groupBy("budget_fiscal_year", "office_code").agg(F.max("revision_no").alias("revision_no"))
    return sp.join(latest, ["budget_fiscal_year", "office_code", "revision_no"])


@dp.materialized_view(comment="Baseline (approved operating) spend plan: the first revision each office submitted after full-year enactment. Execution is measured against this plan; later revisions re-forecast and true past months up to actuals.")
def silver_spend_plan_baseline():
    sp = spark.read.table("silver_spend_plan")
    enacted = (spark.read.table("silver_budget_lines")
               .groupBy("budget_fiscal_year").agg(F.min("enactment_date").alias("enactment_date")))
    baseline = (sp.join(enacted, "budget_fiscal_year")
                .filter(F.col("revision_date") >= F.col("enactment_date"))
                .groupBy("budget_fiscal_year", "office_code").agg(F.min("revision_no").alias("revision_no")))
    return sp.join(baseline, ["budget_fiscal_year", "office_code", "revision_no"])


# --------------------------------------------------------------------------- PR tracker
PR_STATUSES = ("Draft", "Submitted", "Funds Certified", "In Solicitation", "Under Evaluation",
               "Awarded", "Cancelled")


@dp.table(comment="PR-tracker events, flattened, typed and de-duplicated (the export re-delivers some events).")
@dp.expect_or_drop("has_pr_id", "pr_id IS NOT NULL")
@dp.expect_or_drop("has_event_ts", "event_ts IS NOT NULL")
@dp.expect("known_status", f"status IN {PR_STATUSES}")
@dp.expect("valid_ppa_code", f"ppa_code RLIKE '{PPA_CODE_RE}'")
def silver_pr_events():
    ev = (spark.readStream.table("bronze_pr_events")
          .withWatermark("_ingested_at", "10 minutes")
          .dropDuplicatesWithinWatermark(["event_id"]))
    return ev.select(
        "event_id", "event_type",
        F.to_timestamp("event_ts").alias("event_ts"),
        "status", "status_reason", "updated_by",
        F.col("pr.pr_id").alias("pr_id"),
        F.col("pr.fiscal_year").cast("int").alias("budget_fiscal_year"),
        F.upper(F.trim("pr.ppa_code")).alias("ppa_code"),
        F.col("pr.tas").alias("tas"),
        F.col("pr.office_code").alias("office_code"),
        F.col("pr.title").alias("title"),
        F.col("pr.description").alias("description"),
        F.col("pr.object_class").alias("object_class"),
        F.col("pr.acquisition_type").alias("acquisition_type"),
        F.col("pr.contract_vehicle").alias("contract_vehicle"),
        F.col("pr.estimated_amount").cast("decimal(18,2)").alias("estimated_amount"),
        F.col("pr.priority").alias("priority"),
        F.col("pr.requested_by").alias("requested_by"),
        F.col("pr.contracting_officer").alias("contracting_officer"),
        F.to_date("pr.need_by_date").alias("need_by_date"),
        F.col("pr.year_end_action").cast("boolean").alias("year_end_action"),
        F.col("award.contract_number").alias("contract_number"),
        F.col("award.modification_number").alias("modification_number"),
        F.to_date("award.action_date").alias("action_date"),
        F.col("award.obligated_amount").cast("decimal(18,2)").alias("obligated_amount"),
        F.to_date("award.period_of_performance_start").alias("period_of_performance_start"),
        F.to_date("award.period_of_performance_end").alias("period_of_performance_end"),
        F.col("award.vendor.name").alias("vendor_name"),
        F.col("award.vendor.uei").alias("vendor_uei"),
        "_source_file", "_ingested_at",
    )


@dp.temporary_view(comment="Status-change and award events that drive procurement-request state.")
def pr_status_changes():
    return spark.readStream.table("silver_pr_events").filter("event_type IN ('PR_STATUS_CHANGE', 'AWARD')")


dp.create_streaming_table(
    "silver_procurement_requests",
    comment="Current state of every procurement request (AUTO CDC, SCD type 1). Row-filtered by office.",
    row_filter=OFFICE_FILTER,
)
dp.create_auto_cdc_flow(
    target="silver_procurement_requests",
    source="pr_status_changes",
    keys=["pr_id"],
    sequence_by=F.col("event_ts"),
    stored_as_scd_type=1,
    except_column_list=["event_type", "event_id", "action_date", "_source_file", "_ingested_at"],
)

dp.create_streaming_table(
    "silver_pr_status_history",
    comment="Full status history of every procurement request (AUTO CDC, SCD type 2) for procurement-cycle (PALT) analysis.",
    row_filter=OFFICE_FILTER,
)
dp.create_auto_cdc_flow(
    target="silver_pr_status_history",
    source="pr_status_changes",
    keys=["pr_id"],
    sequence_by=F.col("event_ts"),
    stored_as_scd_type=2,
    column_list=["pr_id", "budget_fiscal_year", "ppa_code", "office_code", "acquisition_type",
                 "status", "status_reason", "updated_by", "event_ts"],
    track_history_column_list=["status"],
)


@dp.table(
    comment="Obligations recorded against each budget line: awards, option exercises, modifications and deobligations. Row-filtered by office.",
    row_filter=OFFICE_FILTER,
)
@dp.expect_or_drop("has_obligation_document", "contract_number IS NOT NULL AND modification_number IS NOT NULL")
@dp.expect("nonzero_obligation", "obligated_amount <> 0")
def silver_obligations():
    return (
        spark.readStream.table("silver_pr_events")
        .filter("event_type IN ('AWARD', 'MODIFICATION')")
        .select(
            F.concat_ws("-", "contract_number", "modification_number").alias("obligation_document"),
            "event_id", "pr_id", "budget_fiscal_year", "ppa_code", "office_code", "tas",
            "object_class", "acquisition_type", "contract_number", "modification_number",
            F.when(F.col("obligated_amount") < 0, "Deobligation")
             .when(F.col("acquisition_type").isin("Option Exercise", "Modification"), F.col("acquisition_type"))
             .otherwise("New Obligation").alias("action_type"),
            F.col("action_date").alias("obligation_date"),
            "obligated_amount", "vendor_name", "vendor_uei",
            "period_of_performance_start", "period_of_performance_end", "year_end_action",
        )
    )


# --------------------------------------------------------------------------- invoices
INVOICE_SCHEMA = f"""
  invoice_id STRING NOT NULL,
  vendor_invoice_number STRING,
  contract_number STRING,
  obligation_document STRING,
  invoice_type STRING,
  vendor_name STRING,
  vendor_uei STRING,
  vendor_tin STRING {PII_MASK} COMMENT 'Payee taxpayer identification number (masked)',
  remit_routing_number STRING {PII_MASK} COMMENT 'Payee bank routing number (masked)',
  remit_account_number STRING {PII_MASK} COMMENT 'Payee bank account number (masked)',
  invoice_date DATE,
  received_date DATE,
  invoice_amount DECIMAL(18,2),
  status STRING,
  approved_date DATE,
  paid_date DATE,
  paid_amount DECIMAL(18,2),
  prompt_pay_due_date DATE,
  interest_penalty DECIMAL(18,2),
  submitted_via STRING,
  extract_date DATE
"""


@dp.temporary_view(comment="Typed invoice register rows with intake quality checks.")
@dp.expect_or_drop("has_invoice_id", "invoice_id IS NOT NULL")
@dp.expect_or_drop("positive_invoice_amount", "invoice_amount > 0")
@dp.expect("well_formed_contract_number", "contract_number RLIKE '^DCI[0-9]{2}[CFG][0-9]{6}$'")
def invoices_clean():
    return spark.readStream.table("bronze_invoices").select(
        "invoice_id", "vendor_invoice_number", "contract_number", "obligation_document",
        "invoice_type", "vendor_name", "vendor_uei", "vendor_tin", "remit_routing_number",
        "remit_account_number",
        F.to_date("invoice_date").alias("invoice_date"),
        F.to_date("received_date").alias("received_date"),
        _money("invoice_amount").alias("invoice_amount"),
        "status",
        F.to_date("approved_date").alias("approved_date"),
        F.to_date("paid_date").alias("paid_date"),
        _money("paid_amount").alias("paid_amount"),
        F.to_date("prompt_pay_due_date").alias("prompt_pay_due_date"),
        _money("interest_penalty").alias("interest_penalty"),
        "submitted_via",
        F.to_date("extract_date").alias("extract_date"),
    )


dp.create_streaming_table(
    "silver_invoices",
    comment="Latest status of every invoice / grant drawdown (AUTO CDC on invoice_id). Payee TIN and bank details are masked.",
    schema=INVOICE_SCHEMA,
)
dp.create_auto_cdc_flow(
    target="silver_invoices",
    source="invoices_clean",
    keys=["invoice_id"],
    sequence_by=F.col("extract_date"),
    stored_as_scd_type=1,
)
