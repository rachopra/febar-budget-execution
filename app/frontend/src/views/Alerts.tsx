import { useEffect, useState } from "react";
import { get, money, post, SEVERITY_ICON } from "../api";

export default function Alerts({ office }: { office?: string }) {
  const [summary, setSummary] = useState<any[]>([]);
  const [rows, setRows] = useState<any[] | null>(null);
  const [severity, setSeverity] = useState("");
  const [type, setType] = useState("");
  const [busy, setBusy] = useState("");

  const load = () => {
    get("/alerts/summary", { office }).then(setSummary);
    get("/alerts", { office, severity, alert_type: type }).then(setRows);
  };
  useEffect(load, [office, severity, type]);

  const act = async (alertId: string, action: string) => {
    setBusy(alertId);
    const note = action === "Assigned" ? prompt("Assign to (e-mail):") : null;
    if (action === "Assigned" && !note) { setBusy(""); return; }
    await post(`/alerts/${alertId}/actions`, { action, assignee: note || undefined });
    setBusy("");
    load();
  };

  const types = Array.from(new Set(summary.map((s) => s.alert_type))).sort();
  return (
    <div className="grid">
      <div className="card">
        <h2>Financial risk and variance alerts</h2>
        <p className="hint">Detected by the gold pipeline as of the reporting date. Actions are written to Lakebase and streamed back to Unity Catalog.</p>
        <table>
          <thead><tr><th>Alert type</th><th>Severity</th><th className="num">Alerts</th><th className="num">Amount at risk</th></tr></thead>
          <tbody>{summary.map((s) => (
            <tr key={s.alert_type + s.severity} className="clickable" onClick={() => { setType(s.alert_type); setSeverity(s.severity); }}>
              <td>{s.alert_type}</td>
              <td><span className={`sev ${s.severity}`}><span className="dot">{SEVERITY_ICON[s.severity]}</span>{s.severity}</span></td>
              <td className="num">{s.alerts}</td><td className="num">{money(s.amount_at_risk)}</td>
            </tr>))}
          </tbody>
        </table>
      </div>
      <div className="card">
        <div className="filters">
          <select value={type} onChange={(e) => setType(e.target.value)}>
            <option value="">All alert types</option>{types.map((t) => <option key={t}>{t}</option>)}
          </select>
          <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
            <option value="">All severities</option><option>Critical</option><option>High</option><option>Medium</option>
          </select>
        </div>
        {!rows ? <div className="muted">Loading…</div> : (
          <table>
            <thead><tr><th>Severity</th><th>Type</th><th>Office</th><th>Detail</th><th className="num">At risk</th><th>Status</th><th></th></tr></thead>
            <tbody>{rows.map((a) => (
              <tr key={a.alert_id}>
                <td><span className={`sev ${a.severity}`}><span className="dot">{SEVERITY_ICON[a.severity]}</span>{a.severity}</span></td>
                <td className="small">{a.alert_type}</td><td className="small">{a.office_code}</td>
                <td className="small">{a.detail}</td><td className="num">{money(a.amount_at_risk)}</td>
                <td className="small">{a.last_action ? <>{a.last_action}{a.assignee ? ` → ${a.assignee}` : ""}<div className="muted">{a.acted_by}</div></> : <span className="muted">Open</span>}</td>
                <td style={{ whiteSpace: "nowrap" }}>
                  {["Acknowledged", "Assigned", "Resolved"].map((x) => (
                    <button key={x} className="ghost" style={{ marginRight: 4, padding: "3px 8px", fontSize: 11 }} disabled={busy === a.alert_id} onClick={() => act(a.alert_id, x)}>
                      {x === "Acknowledged" ? "Ack" : x === "Assigned" ? "Assign" : "Resolve"}
                    </button>))}
                </td>
              </tr>))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
