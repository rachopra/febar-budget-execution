"""Runtime configuration and Databricks auth (app service principal remotely, CLI profile locally)."""

import os
from functools import lru_cache

from databricks.sdk import WorkspaceClient

IS_APP = bool(os.environ.get("DATABRICKS_APP_NAME"))
LAKEBASE_ENDPOINT = os.environ.get("LAKEBASE_ENDPOINT", "projects/fe-bar-budget/branches/production/endpoints/primary")
PG_SCHEMA = os.environ.get("PG_SCHEMA", "fe_bar")
PG_DATABASE = os.environ.get("PGDATABASE", "budget_ops")
SERVING_ENDPOINT = os.environ.get("SERVING_ENDPOINT", "databricks-claude-sonnet-5-5")
GENIE_SPACE_ID = os.environ.get("GENIE_SPACE_ID", "")
DEFAULT_OFFICE_SCOPE = os.environ.get("DEFAULT_OFFICE_SCOPE", "ALL")
LOCAL_USER = os.environ.get("LOCAL_USER_EMAIL", "")


@lru_cache
def workspace() -> WorkspaceClient:
    if IS_APP:
        return WorkspaceClient()
    return WorkspaceClient(profile=os.environ.get("DATABRICKS_PROFILE", "fe-vm-rachopra-cyber-demo"))


def host() -> str:
    h = workspace().config.host
    return h if h.startswith("http") else f"https://{h}"
