"""Bronze: land every raw feed as-is with Auto Loader.

Each source keeps its own streaming table so the authoritative source of every record is
preserved (file path, modification time, ingest time). Column names are normalised to
snake_case so spreadsheet headers like "Fund (TAS)" become valid Delta columns; values stay
raw strings and are typed in silver.
"""

import re

from pyspark import pipelines as dp
from pyspark.sql import functions as F

LANDING = spark.conf.get("landing_path")


def _snake(name: str) -> str:
    if name.startswith("_"):
        return name
    return re.sub(r"[^0-9a-zA-Z]+", "_", name).strip("_").lower()


def _autoload(subdir: str, fmt: str, **options):
    reader = (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", fmt)
        .option("cloudFiles.inferColumnTypes", "false")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
    )
    for key, value in options.items():
        reader = reader.option(key, value)
    raw = reader.load(f"{LANDING}/{subdir}")
    return raw.select(
        *[F.col(f"`{c}`").alias(_snake(c)) for c in raw.columns],
        F.col("_metadata.file_path").alias("_source_file"),
        F.col("_metadata.file_modification_time").alias("_file_modified_at"),
        F.current_timestamp().alias("_ingested_at"),
    )


@dp.table(comment="Raw PPA / office / appropriation reference list from the budget office.")
def bronze_ppa_master():
    return _autoload("reference", "csv", header="true")


@dp.table(comment="Raw enacted budget authority and OMB apportionment by PPA and budget fiscal year.")
def bronze_budget_authority():
    return _autoload("budget_authority", "csv", header="true")


@dp.table(comment="Raw spend-plan spreadsheets submitted on the budget-office template (whole dollars).")
def bronze_spend_plan_budget_office():
    return _autoload("spend_plan/budget_office_template", "csv", header="true")


@dp.table(comment="Raw spend-plan spreadsheets submitted on the legacy office template (thousands of dollars).")
def bronze_spend_plan_legacy():
    return _autoload("spend_plan/legacy_office_template", "csv", header="true")


@dp.table(comment="Raw procurement-request tracker change events (nested JSON, one event per status change or award action).")
def bronze_pr_events():
    # Infer types so the nested pr / award / vendor objects arrive as structs.
    return _autoload("procurement_requests", "json", **{"cloudFiles.inferColumnTypes": "true"})


@dp.table(comment="Raw invoice register extracts from the payment systems (IPP / PMS). Contains payee PII.")
def bronze_invoices():
    return _autoload("invoices", "csv", header="true")
