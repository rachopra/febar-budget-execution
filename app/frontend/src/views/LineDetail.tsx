import { ArrowRightLeft, MessageSquare, RefreshCw, Send, ShieldCheck, Sparkles, X } from "lucide-react";
import { useEffect, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ago, ALERT_LABEL, asList, longDate, money, pct, person, post, useApi } from "../api";
import { useApp } from "../app-context";
import { Avatar, axisProps, ChartTip, Drawer, Empty, SevBadge, Skeleton, Stat, Tabs, TierBadge } from "../components/ui";

type Tab = "overview" | "procurement" | "alerts" | "package" | "notes";

export default function LineDetail({ lineId, initialTab, onClose }: { lineId: string; initialTab?: string; onClose: () => void }) {
  const { version, changed, toast } = useApp();
  const detail = useApi(`/lines/${lineId}`, {}, [version]);
  const burn = useApi<any[]>("/burn", { line_id: lineId });
  const notes = useApi<any[]>(`/lines/${lineId}/notes`, {}, [version]);
  const [tab, setTab] = useState<Tab>((initialTab as Tab) || "overview");
  useEffect(() => setTab((initialTab as Tab) || "overview"), [lineId, initialTab]);
  const d = detail.data;
  const l = d?.line;

  return (
    <Drawer onClose={onClose}>
      <div className="drawer-head">
        <div>
          {l ? <>
            <div className="row-center gap"><TierBadge tier={l.risk_tier} /><span className="muted small">{l.office_name}</span></div>
            <h2>{l.ppa_name}</h2>
            <div className="small muted">{l.line_id} · {l.tas} · {l.appropriation_name} · expires {longDate(l.expiration_date)} ({l.days_to_expiration} days)</div>
          </> : <Skeleton h={60} />}
        </div>
        <button className="icon-btn" onClick={onClose} aria-label="Close"><X size={18} /></button>
      </div>
      {detail.error && <div className="error">{detail.error}</div>}
      {d && (
        <>
          <Tabs value={tab} onChange={setTab} tabs={[
            { id: "overview", label: "Overview" },
            { id: "procurement", label: "Procurement", count: d.open_procurements.length },
            { id: "alerts", label: "Alerts", count: d.alerts.length },
            { id: "package", label: "AI package", count: d.submitted_packages.length || undefined },
            { id: "notes", label: "Notes", count: (notes.data?.length ?? 0) + d.reprogramming.length || undefined },
          ]} />
          <div className="drawer-body">
            {tab === "overview" && <Overview d={d} burn={burn.data ?? []} />}
            {tab === "procurement" && <Procurements rows={d.open_procurements} />}
            {tab === "alerts" && <LineAlerts rows={d.alerts} />}
            {tab === "package" && <Package d={d} lineId={lineId} onSubmitted={() => { toast("Package submitted to the acquisition office"); changed(); }} />}
            {tab === "notes" && <Notes lineId={lineId} notes={notes.data ?? []} reprogramming={d.reprogramming}
                                       onAdded={() => { toast("Note added"); changed(); }} />}
          </div>
        </>
      )}
    </Drawer>
  );
}

function Overview({ d, burn }: { d: any; burn: any[] }) {
  const l = d.line;
  const label = (v: string) => new Date(`${v}-15`).toLocaleDateString("en-US", { month: "short", year: "2-digit" });
  return (
    <div className="stack">
      <div className="stat-grid">
        <Stat label="Total budget" value={money(l.total_budget)} foot={`apportioned ${money(l.apportioned_to_date)}`} />
        <Stat label="Obligated" value={pct(l.obligation_rate, 0)} foot={`${money(l.obligated_to_date)} · ${pct(l.burn_rate_vs_plan, 0)} of plan`} />
        <Stat label="Uncommitted balance" value={money(l.uncommitted_balance)} foot={`${money(l.committed_not_obligated)} committed`} />
        <Stat label={`Projected lapse (model v${l.model_version ?? "-"})`} tone="warn"
              value={l.projected_lapse_amount == null ? "-" : money(l.projected_lapse_amount)}
              foot={l.spend_plan_implied_lapse_rate == null ? undefined : `spend plan implies ${pct(l.spend_plan_implied_lapse_rate)}`} />
      </div>
      {d.briefing && (
        <div className="ai-block">
          <div className="ai-tag"><Sparkles size={13} /> AI execution briefing · {d.briefing.model_endpoint} ·
            {d.briefing.grounding_passed ? <span className="ok-text"> <ShieldCheck size={12} /> every figure grounded</span> : <span className="warn-text"> flagged for analyst review</span>}</div>
          <h3>{d.briefing.headline}</h3>
          <p>{d.briefing.summary}</p>
          <ul>{asList(d.briefing.recommended_actions).map((a) => <li key={a}>{a}</li>)}</ul>
        </div>
      )}
      {asList(l.top_risk_drivers).length > 0 && (
        <div className="drivers-box"><b className="small">What drives the lapse forecast</b>
          <ul>{asList(l.top_risk_drivers).map((x) => <li key={x}>{x}</li>)}</ul></div>
      )}
      <div className="panel">
        <h3 className="sub-head">Cumulative obligations vs approved plan</h3>
        {burn.length === 0 ? <Skeleton h={210} /> : (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={burn.map((r) => ({ month: String(r.month).slice(0, 7), Plan: r.cumulative_planned_obligations, Obligated: r.is_actualized ? r.cumulative_actual_obligations : null }))}
                       margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="var(--grid)" vertical={false} />
              <XAxis dataKey="month" {...axisProps} tickFormatter={label} />
              <YAxis {...axisProps} tickFormatter={(v) => money(v, 0)} width={58} axisLine={false} />
              <Tooltip content={<ChartTip format={(v: number) => money(v)} labelFormat={label} />} />
              <Legend wrapperStyle={{ fontSize: 12 }} iconType="plainline" />
              <Line dataKey="Plan" name="Approved plan" stroke="var(--series-2)" strokeWidth={2} strokeDasharray="6 4" dot={false} />
              <Line dataKey="Obligated" stroke="var(--series-1)" strokeWidth={2.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

function Procurements({ rows }: { rows: any[] }) {
  if (!rows.length) return <Empty>No open procurement requests on this line.</Empty>;
  return (
    <table>
      <thead><tr><th>Request</th><th>Type</th><th>Status</th><th className="num">Days in status</th><th className="num">Amount</th><th>Forecast award</th></tr></thead>
      <tbody>{rows.map((p) => (
        <tr key={p.pr_id}>
          <td><b>{p.pr_id}</b><div className="small muted">{p.title}</div></td>
          <td className="small">{p.acquisition_type}<div className="muted">{p.contract_vehicle}</div></td>
          <td className="small">{p.status}</td><td className="num">{p.days_in_status}</td>
          <td className="num">{money(p.estimated_amount)}</td>
          <td className="small">{longDate(p.forecast_award_date)}{p.at_risk_of_missing_expiration && <div><SevBadge severity="Critical" label="after expiration" /></div>}</td>
        </tr>))}
      </tbody>
    </table>
  );
}

function LineAlerts({ rows }: { rows: any[] }) {
  const { go } = useApp();
  if (!rows.length) return <Empty>No alerts on this line.</Empty>;
  return (
    <div className="stack">
      {rows.map((a) => (
        <div key={a.alert_id} className="alert-row">
          <SevBadge severity={a.severity} />
          <div className="grow"><b>{ALERT_LABEL[a.alert_type] ?? a.alert_type}</b><div className="small">{a.detail}</div></div>
          <b className="num">{money(a.amount_at_risk)}</b>
        </div>
      ))}
      <button className="btn ghost sm" onClick={() => go("alerts")}>Triage on the alerts board</button>
    </div>
  );
}

function Package({ d, lineId, onSubmitted }: { d: any; lineId: string; onSubmitted: () => void }) {
  const [draft, setDraft] = useState<any>(null);
  const [busy, setBusy] = useState("");
  const [err, setErr] = useState("");
  const generate = async () => {
    setBusy("generate"); setErr("");
    try { setDraft(await post(`/packages/${lineId}/draft`)); } catch (e: any) { setErr(e.message); }
    setBusy("");
  };
  const submit = async (p: any, source: string) => {
    setBusy("submit"); setErr("");
    try {
      await post(`/packages/${lineId}`, {
        title: p.title, acquisition_type: p.recommended_acquisition_type, contract_number: p.contract_number,
        amount: Number(p.amount), requirement_summary: p.requirement_summary, justification: p.justification,
        required_documents: asList(p.required_documents), milestones: asList(p.milestones), source,
      });
      setDraft(null); onSubmitted();
    } catch (e: any) { setErr(e.message); }
    setBusy("");
  };
  const pkg = draft?.draft || d.package_draft;
  const issues = asList(draft ? draft.validation_issues : d.package_draft?.validation_issues);
  return (
    <div className="stack">
      <p className="muted small">Puts projected-to-lapse funds to work using only acquisition types whose historical PALT can still award before expiration, an active contract on the line, and no more than the contract's obligated value (bona fide need).</p>
      {pkg && !pkg.error ? (
        <div className="ai-block">
          <div className="ai-tag"><Sparkles size={13} /> {draft ? `On-demand draft · ${draft.model_endpoint}` : `Batch AI draft · ${d.package_draft.status}`}
            {issues.length === 0 ? <span className="ok-text"> · <ShieldCheck size={12} /> passes validation</span> : null}</div>
          <h3>{pkg.title}</h3>
          <div className="pkg-facts">
            <span><b>{pkg.recommended_acquisition_type}</b></span>
            {pkg.contract_number && <span>{pkg.contract_number}</span>}
            <span className="pkg-amt">{money(pkg.amount)}</span>
          </div>
          <p>{pkg.requirement_summary}</p>
          <p className="small muted">{pkg.justification}</p>
          <div className="small"><b>Documents</b><div className="chips">{asList(pkg.required_documents).map((x) => <span key={x} className="chip">{x}</span>)}</div></div>
          <ol className="milestones">{asList(pkg.milestones).map((m) => <li key={m}>{m}</li>)}</ol>
          {issues.length > 0 && <div className="error">Validation: {issues.join("; ")}</div>}
          <div className="row-center gap">
            <button className="btn primary" disabled={!!busy || issues.length > 0} onClick={() => submit(pkg, draft ? "App - on-demand AI draft" : "Batch AI draft")}>
              <Send size={14} /> {busy === "submit" ? "Submitting…" : "Submit to acquisition"}</button>
            <button className="btn ghost" disabled={!!busy} onClick={generate}><RefreshCw size={14} /> {busy === "generate" ? "Drafting with Claude…" : "Redraft on demand"}</button>
          </div>
        </div>
      ) : (
        <div className="empty">
          {pkg?.error && <div className="error">{pkg.error}</div>}
          <button className="btn primary" disabled={!!busy} onClick={generate}><Sparkles size={14} /> {busy === "generate" ? "Drafting with Claude…" : "Draft a package with AI"}</button>
        </div>
      )}
      {err && <div className="error">{err}</div>}
      {d.submitted_packages.length > 0 && (
        <>
          <h3 className="sub-head">Submitted to acquisition</h3>
          <table>
            <thead><tr><th>Request</th><th>Status</th><th className="num">Amount</th><th>Submitted by</th></tr></thead>
            <tbody>{d.submitted_packages.map((p: any) => (
              <tr key={p.package_id}><td><b>{p.package_id}</b><div className="small muted">{p.title}</div></td>
                <td className="small">{p.status}<div className="muted">{p.source}</div></td><td className="num">{money(p.amount)}</td>
                <td className="small">{person(p.created_by)}<div className="muted">{ago(p.created_at)}</div></td></tr>
            ))}</tbody>
          </table>
        </>
      )}
    </div>
  );
}

function Notes({ lineId, notes, reprogramming, onAdded }: { lineId: string; notes: any[]; reprogramming: any[]; onAdded: () => void }) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const add = async () => {
    setBusy(true); setErr("");
    try { await post(`/lines/${lineId}/notes`, { note: text }); setText(""); onAdded(); } catch (e: any) { setErr(e.message); }
    setBusy(false);
  };
  return (
    <div className="stack">
      <div className="note-form">
        <textarea rows={3} placeholder="Add a note for the program office and budget analysts (saved to Lakebase, streamed to Unity Catalog)…"
                  value={text} onChange={(e) => setText(e.target.value)} />
        <button className="btn primary" disabled={busy || !text.trim()} onClick={add}><MessageSquare size={14} /> {busy ? "Saving…" : "Add note"}</button>
      </div>
      {err && <div className="error">{err}</div>}
      {reprogramming.length > 0 && (
        <div className="panel">
          <h3 className="sub-head">Reprogramming involving this line</h3>
          {reprogramming.map((r) => (
            <div key={r.request_id} className="alert-row">
              <ArrowRightLeft size={15} />
              <div className="grow small"><b>{r.request_id}</b> {r.from_line_id} → {r.to_line_id}<div className="muted">{r.justification}</div></div>
              <b className="num">{money(r.amount)}</b>
              <span className={`status-pill ${r.status.toLowerCase()}`}>{r.status}</span>
            </div>
          ))}
        </div>
      )}
      {notes.length === 0 ? <Empty>No notes yet.</Empty> : (
        <ul className="feed">
          {notes.map((n) => (
            <li key={n.note_id}><Avatar email={n.author} size={26} />
              <div><div className="feed-line"><b>{person(n.author)}</b> <span className="muted small">{ago(n.created_at)}</span></div>
                <div className="note-text">{n.note}</div></div></li>
          ))}
        </ul>
      )}
    </div>
  );
}

