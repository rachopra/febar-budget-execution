"""Budget Execution & Financial Oversight - Databricks App entry point."""

import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server import yearend
from server.routes import router

app = FastAPI(title="Budget Execution & Financial Oversight")
app.include_router(router)
app.include_router(yearend.router)

dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.isdir(dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist, "assets")), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        return FileResponse(os.path.join(dist, "index.html"))
