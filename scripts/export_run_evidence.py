"""Export a job run's executed notebooks (code + outputs) to Markdown under evidence/.

Usage: python scripts/export_run_evidence.py <job_run_id> [--profile PROFILE]

Each notebook task is exported with `jobs export-run`, the embedded notebook model is decoded,
and every cell is written as Markdown: source, then its rendered output (tables as Markdown
tables, text as code blocks, errors verbatim). Pipeline tasks are summarised from the run.
"""

import argparse
import base64
import html
import json
import re
import subprocess
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

MAX_TABLE_ROWS = 30
MAX_TEXT_CHARS = 6000


def cli(*args, profile):
    out = subprocess.run(["databricks", *args, "-p", profile, "-o", "json"], capture_output=True, text=True)
    if out.returncode:
        raise RuntimeError(out.stderr)
    return json.loads(out.stdout)


def notebook_model(view_html: str) -> dict:
    m = re.search(r"__DATABRICKS_NOTEBOOK_MODEL = '([^']+)'", view_html)
    if not m:
        raise ValueError("notebook model not found in export")
    return json.loads(urllib.parse.unquote(base64.b64decode(m.group(1)).decode("utf-8")))


def cell(v) -> str:
    s = "" if v is None else str(v)
    return s.replace("|", "\\|").replace("\n", " ")[:300]


def md_table(schema, rows) -> str:
    cols = [c.get("name", "") for c in schema]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows[:MAX_TABLE_ROWS]:
        vals = r if isinstance(r, list) else [r.get(c) for c in cols]
        lines.append("| " + " | ".join(cell(v) for v in vals) + " |")
    if len(rows) > MAX_TABLE_ROWS:
        lines.append(f"\n_{len(rows) - MAX_TABLE_ROWS} more rows not shown_")
    return "\n".join(lines)


def strip_html(s: str) -> str:
    s = re.sub(r"<(script|style)[\s\S]*?</\1>", "", s)
    s = re.sub(r"<br\s*/?>|</p>|</div>|</tr>", "\n", s)
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def render_results(res) -> str:
    if not res:
        return ""
    t, data = res.get("type"), res.get("data")
    if t == "table":
        return md_table(res.get("schema") or [], data or [])
    if t in ("text", "ansi"):
        text = re.sub(r"\x1b\[[0-9;]*m", "", str(data or "")).strip()
        return f"```text\n{text[:MAX_TEXT_CHARS]}\n```" if text else ""
    if t == "html":
        text = strip_html(str(data or ""))
        return f"```text\n{text[:MAX_TEXT_CHARS]}\n```" if text else ""
    if t == "error":
        summary = res.get("summary") or ""
        cause = re.sub(r"\x1b\[[0-9;]*m", "", str(res.get("cause") or data or ""))
        return f"**Error:** {strip_html(summary)}\n```text\n{cause[:3000]}\n```"
    if t == "listResults":
        return "\n\n".join(filter(None, (render_results(r) for r in data or [])))
    return ""


def notebook_markdown(model: dict, title: str, task: dict) -> str:
    st = task["state"]
    start = datetime.fromtimestamp(task["start_time"] / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    out = [f"# {title}", "",
           f"- Job task: `{task['task_key']}` (task run `{task['run_id']}`)",
           f"- Result: **{st.get('result_state')}**, started {start}, "
           f"ran {round((task.get('end_time', 0) - task['start_time']) / 1000)}s on serverless compute",
           f"- Notebook: `{task.get('notebook_task', {}).get('notebook_path', '')}`", ""]
    for c in sorted(model.get("commands", []), key=lambda c: c.get("position", 0)):
        src = c.get("command", "")
        if src.lstrip().startswith("%md"):
            out += [re.sub(r"^\s*%md\s?", "", src, count=1).strip(), ""]
            continue
        if src.lstrip().startswith(("%pip", "%restart_python")):
            out += [f"```text\n{src.strip()}\n```", ""]
            continue
        out += ["```python", src.rstrip(), "```", ""]
        rendered = render_results(c.get("results"))
        if rendered:
            out += ["**Output:**", "", rendered, ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id")
    ap.add_argument("--profile", default="fe-vm-rachopra-cyber-demo")
    ap.add_argument("--out", default="evidence/job_run")
    a = ap.parse_args()

    run = cli("jobs", "get-run", a.run_id, profile=a.profile)
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    latest = {}
    for t in sorted(run["tasks"], key=lambda t: t.get("start_time", 0)):
        latest[t["task_key"]] = t  # a repaired run keeps earlier attempts; report the final one
    tasks = sorted(latest.values(), key=lambda t: t.get("start_time", 0))
    repaired = {t["task_key"] for t in run["tasks"]} and {
        k for k in latest if sum(1 for t in run["tasks"] if t["task_key"] == k) > 1}
    index = [f"# Job run {a.run_id}: `{run.get('run_name')}`", "",
             f"Run page: {run.get('run_page_url')}", "",
             f"Overall result: **{run.get('state', {}).get('result_state')}**. "
             + (f"Tasks {', '.join(sorted(repaired))} were re-run in a repair of this run after a guardrail was added "
                "to procurement package drafting; their final attempt is shown." if repaired else ""), "",
             "| # | Task | Type | Result | Duration (s) | Evidence |", "|---|---|---|---|---|---|"]
    for i, t in enumerate(tasks, 1):
        kind = "notebook" if "notebook_task" in t else "pipeline" if "pipeline_task" in t else "other"
        dur = round((t.get("end_time", 0) - t.get("start_time", 0)) / 1000)
        fname = f"{i:02d}_{t['task_key']}.md"
        if kind == "notebook":
            exp = cli("jobs", "export-run", str(t["run_id"]), "--views-to-export", "CODE", profile=a.profile)
            model = notebook_model(exp["views"][0]["content"])
            (out_dir / fname).write_text(notebook_markdown(model, t["task_key"].replace("_", " ").title(), t))
        else:
            (out_dir / fname).write_text(
                f"# {t['task_key']}\n\n- Type: {kind}\n- Result: **{t['state'].get('result_state')}**\n"
                f"- Duration: {dur}s\n- Pipeline: `{t.get('pipeline_task', {}).get('pipeline_id', '')}`\n\n"
                "Pipeline evidence: `../sql/00_pipeline_update.md` (update lifecycle), `../sql/00_pipeline_expectations.md` "
                "(data-quality results), `../sql/02_row_counts.md`, and the flow metrics and bronze-to-silver "
                "reconciliation in `04_govern_and_document.md`.\n")
        index.append(f"| {i} | `{t['task_key']}` | {kind} | {t['state'].get('result_state')} | {dur} | [{fname}]({fname}) |")
        print(f"exported {fname}")
    (out_dir / "README.md").write_text("\n".join(index) + "\n")


if __name__ == "__main__":
    main()
