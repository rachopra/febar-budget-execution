"""Foundation Model API (procurement package drafting) and Genie Conversation API."""

import json
import re
import time

import requests

from .config import GENIE_SPACE_ID, SERVING_ENDPOINT, host, workspace

PACKAGE_PROMPT = """You support a federal program office's year-end acquisition planning. Draft a procurement
request package to put projected-to-lapse funds to work before they expire. Use ONLY the facts below: choose an
acquisition type from feasible_acquisition_types and, for option exercises or modifications, a contract from
active_service_contracts_on_line. Do not invent contract numbers, vendors, regulations or dollar figures.
For an option exercise or modification the amount must not exceed the selected contract's obligated_to_date (a
proxy for its priced option value), and the requirement must be a bona fide need of the current period of
availability; if no contract can absorb the recommended amount, recommend a smaller amount rather than stretch.
Respond with a single JSON object with keys: title, recommended_acquisition_type, contract_number (or ""),
amount (number), requirement_summary, justification, required_documents (list of strings),
milestones (list of "YYYY-MM-DD: step" strings back-planned from must_award_by).

FACTS:
"""


def draft_package(facts: dict) -> dict:
    res = workspace().api_client.do(
        "POST", f"/serving-endpoints/{SERVING_ENDPOINT}/invocations",
        body={"messages": [{"role": "user", "content": PACKAGE_PROMPT + json.dumps(facts, indent=1)}],
              "max_tokens": 4000},
    )
    text = res["choices"][0]["message"]["content"]
    if isinstance(text, list):  # some endpoints return content blocks
        text = "".join(b.get("text", "") for b in text if isinstance(b, dict))
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    match = re.search(r"\{[\s\S]*\}", text)
    try:
        return json.loads(match.group(0)) if match else {"error": "Model did not return JSON", "raw": text}
    except json.JSONDecodeError:
        return {"error": "Model returned malformed JSON", "raw": text}


def _genie_headers(user_token: str | None) -> dict:
    if user_token:  # on-behalf-of-user: Genie runs with the signed-in user's UC permissions
        return {"Authorization": f"Bearer {user_token}"}
    return workspace().config.authenticate()


def ask_genie(question: str, conversation_id: str | None, user_token: str | None, timeout_s: int = 120) -> dict:
    base = f"{host()}/api/2.0/genie/spaces/{GENIE_SPACE_ID}"
    headers = _genie_headers(user_token)
    if conversation_id:
        r = requests.post(f"{base}/conversations/{conversation_id}/messages", json={"content": question},
                          headers=headers, timeout=30)
    else:
        r = requests.post(f"{base}/start-conversation", json={"content": question}, headers=headers, timeout=30)
    r.raise_for_status()
    start = r.json()
    conv = start.get("conversation_id") or conversation_id
    msg = start.get("message_id") or start.get("id")
    t0 = time.time()
    while True:
        m = requests.get(f"{base}/conversations/{conv}/messages/{msg}", headers=headers, timeout=30).json()
        if m.get("status") in ("COMPLETED", "FAILED", "CANCELLED") or time.time() - t0 > timeout_s:
            break
        time.sleep(2)
    out = {"conversation_id": conv, "status": m.get("status"), "text": None, "sql": None,
           "description": None, "columns": [], "rows": [],
           "identity": "signed-in user" if user_token else "app service principal"}
    for a in m.get("attachments") or []:
        if a.get("text"):
            out["text"] = a["text"].get("content")
        if a.get("query"):
            out["sql"] = a["query"].get("query")
            out["description"] = a["query"].get("description")
            qr = requests.get(f"{base}/conversations/{conv}/messages/{msg}/attachments/{a['attachment_id']}/query-result",
                              headers=headers, timeout=60).json()
            sr = qr.get("statement_response", {})
            out["columns"] = [c["name"] for c in sr.get("manifest", {}).get("schema", {}).get("columns", [])]
            out["rows"] = (sr.get("result", {}).get("data_array") or [])[:200]
    if m.get("status") == "FAILED":
        out["text"] = (m.get("error") or {}).get("error") or "Genie could not answer that question."
    return out
