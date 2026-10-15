import { useEffect, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { asList, get, money, pct, post, SEVERITY_ICON } from "../api";

const axis = { stroke: "var(--axis)", tick: { fill: "var(--text-muted)", fontSize: 11 } };

export default function LineDetail({ lineId, onClose }: { lineId: string; onClose: () => void }) {
  const [d, setD] = useState<any>(null);
  const [burn, setBurn] = useState<any[]>([]);
  const [draft, setDraft] = useState<any>(null);
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState("");

  const load = () => get(`/lines/${lineId}`).then(setD);
  useEffect(() => {
    load();
    get("/burn", { line_id: lineId }).then(setBurn);
  }, [lineId]);

  const generate = async () => {
    setBusy("generate"); setMsg("");
    try { setDraft(await post(`/packages/${lineId}/draft`)); } catch (e: any) { setMsg(e.message); }
    setBusy("");
  };
  const submit = async (p: any, source: string) => {
    setBusy("submit");
    try {
      await post(`/packages/${lineId}`, {
        title: p.title, acquisition_type: p.recommended_acquisition_type, contract_number: p.contract_number,
        amount: Number(p.amount), requirement_summary: p.requirement_summary, justification: p.justification,
        required_documents: asList(p.required_documents), milestones: asList(p.milestones), source,
      });
      setMsg("Package submitted to the acquisition office (written to Lakebase)."); setDraft(null); load();
    } catch (e: any) { setMsg(e.message); }
    setBusy("");
  };

  const l = d?.line;
  const pkg = draft?.draft || d?.package_draft;
  return (
    <div className="drawer-bg" onClick={onClose}>
      <div className="drawer" onClick={(e) => e.stopPropagation()}>
        <button className="ghost" style={{ float: "right" }} onClick={onClose}>Close</button>
        {!d ? <div className="muted">Loading…</div> : (
          <>
            <h2>{l.ppa_name}</h2>
            <div className="small muted">{l.line_id} · {l.office_name} · {l.tas} · expires {String(l.expiration_date)} ({l.days_to_expiration} days)</div>

            <div className="grid kpis" style={{ marginTop: 14 }}>
              <div className="card tile"><div className="label">Total budget</div><div className="value">{money(l.total_budget)}</div></div>
              <div className="card tile"><div className="label">Obligated</div><div className="value">{pct(l.obligation_rate, 0)}</div><div className="foot">{money(l.obligated_to_date)} · {pct(l.burn_rate_vs_plan, 0)} of plan</div></div>
              <div className="card tile"><div className="label">Uncommitted balance</div><div className="value">{money(l.uncommitted_balance)}</div></div>
              <div className="card tile"><div className="label">Projected lapse (model v{l.model_version})</div><div className="value">{l.projected_lapse_amount == null ? "-" : money(l.projected_lapse_amount)}</div><div className="foot">spend plan implies {pct(l.spend_plan_implied_lapse_rate)}</div></div>
            </div>

            {d.briefing && (
              <div className="ai">
                <div className="tag">AI execution briefing · {d.briefing.model_endpoint} · grounding {d.briefing.grounding_passed ? "passed" : "flagged"}</div>
                <b>{d.briefing.headline}</b>
                <p style={{ margin: "6px 0" }}>{d.briefing.summary}</p>
                <ul>{asList(d.briefing.recommended_actions).map((a) => <li key={a}>{a}</li>)}</ul>
              </div>
            )}
            {asList(l.top_risk_drivers).length > 0 && (
              <div className="small"><b>Lapse-risk drivers:</b><ul className="drivers">{asList(l.top_risk_drivers).map((x) => <li key={x}>{x}</li>)}</ul></div>
            )}

            <div className="card" style={{ marginTop: 14 }}>
              <h2>Cumulative obligations vs plan</h2>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={burn.map((r) => ({ month: String(r.month).slice(0, 7), Planned: r.cumulative_planned_obligations, Actual: r.is_actualized ? r.cumulative_actual_obligations : null }))}>
                  <CartesianGrid stroke="var(--grid)" vertical={false} />
                  <XAxis dataKey="month" {...axis} /><YAxis {...axis} tickFormatter={(v) => money(v, 0)} width={60} />
                  <Tooltip formatter={(v: any) => money(v)} contentStyle={{ fontSize: 12 }} /><Legend wrapperStyle={{ fontSize: 12 }} />
                  <Line dataKey="Planned" stroke="var(--series-2)" strokeWidth={2} strokeDasharray="5 4" dot={false} />
                  <Line dataKey="Actual" stroke="var(--series-1)" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="card" style={{ marginTop: 14 }}>
              <h2>Open procurement requests</h2>
              <table>
                <thead><tr><th>PR</th><th>Type</th><th>Status</th><th className="num">Days in status</th><th className="num">Amount</th><th>Forecast award</th></tr></thead>
                <tbody>{d.open_procurements.map((p: any) => (
                  <tr key={p.pr_id}>
                    <td>{p.pr_id}<div className="small muted">{p.title}</div></td><td className="small">{p.acquisition_type}</td>
                    <td className="small">{p.status}</td><td className="num">{p.days_in_status}</td><td className="num">{money(p.estimated_amount)}</td>
                    <td className="small">{String(p.forecast_award_date)} {p.at_risk_of_missing_expiration && <span className="sev Critical"><span className="dot">⛔</span>after expiration</span>}</td>
                  </tr>))}
                  {d.open_procurements.length === 0 && <tr><td colSpan={6} className="muted">No open procurement requests</td></tr>}
                </tbody>
              </table>
            </div>

            {d.alerts.length > 0 && (
              <div className="card" style={{ marginTop: 14 }}>
                <h2>Alerts on this line</h2>
                {d.alerts.map((a: any) => (
                  <div key={a.alert_id} className="small" style={{ margin: "6px 0" }}>
                    <span className={`sev ${a.severity}`}><span className="dot">{SEVERITY_ICON[a.severity]}</span>{a.severity}</span> <b>{a.alert_type}</b> - {a.detail}
                  </div>
                ))}
              </div>
            )}

            <div className="card" style={{ marginTop: 14 }}>
              <h2>Procurement package initiation</h2>
              <p className="hint">Puts projected-to-lapse funds to work using only acquisition types whose historical PALT can still award before expiration.</p>
              {pkg ? (
                <div className="ai">
                  <div className="tag">{draft ? `On-demand AI draft · ${draft.model_endpoint}` : `Batch AI draft · ${d.package_draft.status}`}</div>
                  <b>{pkg.title}</b>
                  <div className="small">{pkg.recommended_acquisition_type} {pkg.contract_number ? `· ${pkg.contract_number}` : ""} · {money(pkg.amount)}</div>
                  <p>{pkg.requirement_summary}</p>
                  <p className="small muted">{pkg.justification}</p>
                  <div className="small"><b>Documents:</b> {asList(pkg.required_documents).join(" · ")}</div>
                  <ul className="small">{asList(pkg.milestones).map((m) => <li key={m}>{m}</li>)}</ul>
                  {asList(draft?.validation_issues || d.package_draft?.validation_issues).length > 0 &&
                    <div className="error">Validation: {asList(draft?.validation_issues || d.package_draft?.validation_issues).join("; ")}</div>}
                  <button className="primary" disabled={!!busy} onClick={() => submit(pkg, draft ? "App - on-demand AI draft" : "Batch AI draft")}>
                    {busy === "submit" ? "Submitting…" : "Submit to acquisition"}
                  </button>{" "}
                  <button className="ghost" disabled={!!busy} onClick={generate}>{busy === "generate" ? "Drafting…" : "Regenerate"}</button>
                </div>
              ) : (
                <button className="primary" disabled={!!busy} onClick={generate}>{busy === "generate" ? "Drafting…" : "Draft a package with AI"}</button>
              )}
              {msg && <p className="small">{msg}</p>}
              {d.submitted_packages.length > 0 && (
                <table style={{ marginTop: 10 }}>
                  <thead><tr><th>Request</th><th>Status</th><th className="num">Amount</th><th>Submitted by</th></tr></thead>
                  <tbody>{d.submitted_packages.map((p: any) => (
                    <tr key={p.package_id}><td>{p.package_id}<div className="small muted">{p.title}</div></td><td className="small">{p.status}</td><td className="num">{money(p.amount)}</td><td className="small">{p.created_by}<div className="muted">{String(p.created_at).slice(0, 16)}</div></td></tr>
                  ))}</tbody>
                </table>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
