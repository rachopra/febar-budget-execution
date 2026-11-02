import { ArrowRight, ArrowRightLeft, Check, CircleCheck, FileText, Info, Landmark, Plus, Send, ShieldCheck, Undo2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { ago, asList, longDate, money, moneyFull, pct, person, post, useApi } from "../api";
import { useApp } from "../app-context";
import { Card, CountUp, Empty, Modal, Segmented, Skeleton, Tabs, TierBadge } from "../components/ui";

type Sugg = any;
const key = (s: Sugg) => `${s.from_line_id}>${s.to_line_id}`;
const TIERS = ["All", "Critical", "High", "Moderate", "Low"] as const;

export default function YearEndPlan() {
  const { office, version, query, go } = useApp();
  const plan = useApi("/plan", { office }, [version]);
  const [tab, setTab] = useState<"lines" | "reprogramming">(query.get("tab") === "reprogramming" ? "reprogramming" : "lines");
  const [tier, setTier] = useState<(typeof TIERS)[number]>((query.get("tier") as any) || "All");
  const [pkg, setPkg] = useState<Record<string, number>>({});
  const [rpg, setRpg] = useState<Record<string, number>>({});
  const [review, setReview] = useState(false);
  useEffect(() => { if (query.get("tab")) setTab(query.get("tab") === "reprogramming" ? "reprogramming" : "lines"); }, [query]);

  const d = plan.data;
  const lines: any[] = d?.lines ?? [];
  const suggestions: Sugg[] = d?.suggestions ?? [];
  const byLine = useMemo(() => Object.fromEntries(lines.map((l) => [l.line_id, l])), [lines]);

  const totals = useMemo(() => {
    const lapse = lines.reduce((a, l) => a + Number(l.projected_lapse_amount), 0);
    const inFlight = lines.reduce((a, l) => a + Number(l.recovered), 0);
    let selected = 0;
    for (const l of lines) {
      const room = Math.max(0, Number(l.projected_lapse_amount) - Number(l.recovered));
      const s = (pkg[l.line_id] ?? 0) + suggestions.filter((x) => x.from_line_id === l.line_id).reduce((a, x) => a + (rpg[key(x)] ?? 0), 0);
      selected += Math.min(room, s);
    }
    return { lapse, inFlight, selected, remaining: Math.max(0, lapse - inFlight - selected) };
  }, [lines, suggestions, pkg, rpg]);

  if (plan.error) return <div className="error">{plan.error}</div>;
  if (!d) return <div className="stack"><Skeleton h={150} /><Skeleton h={500} /></div>;

  const actions = Object.keys(pkg).length + Object.keys(rpg).length;
  const shown = lines.filter((l) => tier === "All" || l.risk_tier === tier);
  const validDrafts = shown.filter((l) => l.draft_amount && asList(l.draft_issues).length === 0 && Number(l.recovered) < Number(l.projected_lapse_amount));

  return (
    <div className="stack">
      <div className="page-head">
        <div>
          <h1>Year-end plan</h1>
          <p className="muted">Put projected-to-lapse funds to work before {longDate(d.calendar.fiscal_year_end)}: submit validated AI procurement packages and reprogram within the same account. Nothing is sent until you submit the plan.</p>
        </div>
      </div>

      <section className="plan-summary">
        <div className="plan-figures">
          <Figure label="Projected lapse (ML)" value={totals.lapse} />
          <ArrowRight className="muted" size={18} />
          <Figure label="Covered by actions in flight" value={totals.inFlight} tone="flight" />
          <span className="op">+</span>
          <Figure label="Selected in this plan" value={totals.selected} tone="selected" />
          <span className="op">=</span>
          <Figure label="Still projected to lapse" value={totals.remaining} tone="remain" big />
        </div>
        <div className="plan-bar" aria-label="Projected lapse coverage">
          <div className="pb flight" style={{ width: `${(totals.inFlight / totals.lapse) * 100}%` }} />
          <div className="pb selected" style={{ width: `${(totals.selected / totals.lapse) * 100}%` }} />
          <div className="pb remain" style={{ flex: 1 }} />
        </div>
        <div className="plan-cta">
          <span className="muted small">{actions ? `${actions} action${actions > 1 ? "s" : ""} selected · recovers ${pct(totals.selected / totals.lapse, 0)} more of the projected lapse` : "Select packages and reprogramming moves below"}</span>
          <div className="row-center gap">
            {actions > 0 && <button className="btn ghost" onClick={() => { setPkg({}); setRpg({}); }}><Undo2 size={14} /> Clear</button>}
            <button className="btn primary" disabled={!actions} onClick={() => setReview(true)}><Send size={15} /> Review and submit plan</button>
          </div>
        </div>
      </section>

      <Tabs value={tab} onChange={(t) => { setTab(t); go("plan", t === "reprogramming" ? { tab: t } : {}); }} tabs={[
        { id: "lines", label: "Lines at risk", count: lines.length },
        { id: "reprogramming", label: "Reprogramming", count: `${suggestions.length} matches · ${d.requests.filter((r: any) => r.status === "Pending").length} pending` },
      ]} />

      {tab === "lines" && (
        <>
          <div className="toolbar">
            <Segmented value={tier} onChange={setTier} options={TIERS.map((t) => ({ id: t, label: t === "All" ? `All tiers` : t }))} />
            <div className="spacer" />
            <button className="btn ghost" disabled={!validDrafts.length}
                    onClick={() => setPkg((p) => ({ ...p, ...Object.fromEntries(validDrafts.map((l) => [l.line_id, Math.min(Number(l.draft_amount), Number(l.projected_lapse_amount) - Number(l.recovered))])) }))}>
              <Check size={14} /> Select all {validDrafts.length} validated AI packages
            </button>
          </div>
          <div className="plan-list">
            {shown.map((l) => (
              <PlanLine key={l.line_id} l={l} suggestions={suggestions.filter((s) => s.from_line_id === l.line_id)}
                        pkg={pkg[l.line_id]} setPkg={(v) => setPkg((p) => { const n = { ...p }; if (v === undefined) delete n[l.line_id]; else n[l.line_id] = v; return n; })}
                        rpg={rpg} toggleRpg={(s, on) => setRpg((r) => { const n = { ...r }; if (on) n[key(s)] = s.amount; else delete n[key(s)]; return n; })} />
            ))}
            {shown.length === 0 && <Empty>No lines in this tier.</Empty>}
          </div>
        </>
      )}

      {tab === "reprogramming" && (
        <Reprogramming d={d} byLine={byLine} rpg={rpg}
                       toggleRpg={(s, on) => setRpg((r) => { const n = { ...r }; if (on) n[key(s)] = s.amount; else delete n[key(s)]; return n; })} />
      )}

      {review && <ReviewModal lines={byLine} pkg={pkg} rpg={rpg} suggestions={suggestions} totals={totals}
                              onClose={() => setReview(false)} onDone={() => { setPkg({}); setRpg({}); setReview(false); }} />}
    </div>
  );
}

function Figure({ label, value, tone = "", big }: { label: string; value: number; tone?: string; big?: boolean }) {
  return (
    <div className={`figure ${tone} ${big ? "big" : ""}`}>
      <div className="figure-label">{tone && <span className={`swatch ${tone}`} />}{label}</div>
      <div className="figure-value"><CountUp value={value} format={(v) => money(v)} duration={600} /></div>
    </div>
  );
}

function PlanLine({ l, suggestions, pkg, setPkg, rpg, toggleRpg }: {
  l: any; suggestions: Sugg[]; pkg?: number; setPkg: (v?: number) => void; rpg: Record<string, number>; toggleRpg: (s: Sugg, on: boolean) => void;
}) {
  const { openLine } = useApp();
  const lapse = Number(l.projected_lapse_amount), recovered = Number(l.recovered);
  const room = Math.max(0, lapse - recovered);
  const issues = asList(l.draft_issues);
  const selected = (pkg ?? 0) + suggestions.reduce((a, s) => a + (rpg[key(s)] ?? 0), 0);
  const over = selected > room + 1;
  const covered = room <= 1;
  return (
    <div className={`plan-line ${selected ? "has-sel" : ""} ${covered ? "covered" : ""}`}>
      <div className="pl-head">
        <TierBadge tier={l.risk_tier} />
        <button className="link-title" onClick={() => openLine(l.line_id)}>{l.ppa_name}</button>
        <span className="muted small">{l.line_id} · {l.office_code} · {l.tas} · {l.days_to_expiration} days left</span>
        <div className="spacer" />
        <div className="pl-lapse">
          <span className="muted small">projected lapse</span>
          <b>{money(lapse)}</b>
        </div>
      </div>
      <div className="pl-progress">
        <div className="pb flight" style={{ width: `${Math.min(100, (recovered / lapse) * 100)}%` }} />
        <div className="pb selected" style={{ width: `${Math.min(100 - (recovered / lapse) * 100, (selected / lapse) * 100)}%` }} />
      </div>
      <div className="pl-meta small">
        {recovered > 0 && <span className="ok-text"><CircleCheck size={13} /> {money(recovered)} covered by {l.packaged > 0 ? "submitted packages" : ""}{l.packaged > 0 && l.reprogrammed > 0 ? " and " : ""}{l.reprogrammed > 0 ? "reprogramming requests" : ""}</span>}
        {asList(l.top_risk_drivers).slice(0, 2).map((x) => <span key={x} className="driver">{x}</span>)}
      </div>
      <div className="pl-actions">
        {l.draft_amount ? (
          <label className={`action ${pkg !== undefined ? "on" : ""} ${covered || issues.length ? "disabled" : ""}`}>
            <input type="checkbox" checked={pkg !== undefined} disabled={covered || issues.length > 0}
                   onChange={(e) => setPkg(e.target.checked ? Math.min(Number(l.draft_amount), room) : undefined)} />
            <FileText size={15} />
            <span className="action-main">
              <b>{l.draft_type}{l.draft_contract ? ` on ${l.draft_contract}` : ""}</b>
              <span className="muted small">{l.draft_title}</span>
            </span>
            {issues.length ? <span className="sev sev-High">{issues.join("; ")}</span>
              : <span className="validated"><ShieldCheck size={13} /> validated</span>}
            {pkg !== undefined ? (
              <span className="amount-edit" onClick={(e) => e.preventDefault()}>
                <input type="range" min={10000} max={Math.min(Number(l.draft_amount), Math.max(room, 10000))} step={10000} value={pkg}
                       onChange={(e) => setPkg(Number(e.target.value))} />
                <b className="num">{money(pkg)}</b>
              </span>
            ) : <b className="num">{money(l.draft_amount)}</b>}
          </label>
        ) : (
          <div className="action disabled"><FileText size={15} /><span className="muted small">No batch AI draft for this line. Open the line to draft one on demand.</span>
            <button className="btn ghost sm" onClick={() => openLine(l.line_id, "package")}>Draft with AI</button></div>
        )}
        {suggestions.map((s) => (
          <label key={key(s)} className={`action ${rpg[key(s)] ? "on" : ""} ${covered ? "disabled" : ""}`}>
            <input type="checkbox" checked={!!rpg[key(s)]} disabled={covered} onChange={(e) => toggleRpg(s, e.target.checked)} />
            <ArrowRightLeft size={15} />
            <span className="action-main">
              <b>Reprogram to {s.to_ppa_name}</b>
              <span className="muted small">{s.to_line_id} · {s.reason}</span>
            </span>
            {s.notification_required && <span className="tag"><Landmark size={12} /> notification</span>}
            <b className="num">{money(s.amount)}</b>
          </label>
        ))}
      </div>
      {over && <div className="warn-text small"><Info size={13} /> Selected actions exceed the remaining projected lapse on this line by {money(selected - room)}; only {money(room)} counts toward recovery.</div>}
    </div>
  );
}

// ------------------------------------------------------------------------------------ reprogramming
function Reprogramming({ d, byLine, rpg, toggleRpg }: { d: any; byLine: Record<string, any>; rpg: Record<string, number>; toggleRpg: (s: Sugg, on: boolean) => void }) {
  const { me, changed, toast } = useApp();
  const [deciding, setDeciding] = useState<{ r: any; decision: string } | null>(null);
  const [creating, setCreating] = useState(false);
  const t = d.notification_threshold;
  return (
    <div className="stack">
      <Card title="Suggested moves within the same account"
            hint={`Lines projected to lapse matched with lines short of funds in the same TAS (same appropriation and period of availability). Moving funds across appropriations needs transfer authority and is never suggested. "Notification" flags moves above the illustrative threshold (lesser of ${money(t.amount)} or ${pct(t.pct, 0)} of either PPA).`}
            actions={<button className="btn ghost sm" onClick={() => setCreating(true)}><Plus size={14} /> New request</button>}>
        {d.suggestions.length === 0 ? <Empty>No same-account matches right now.</Empty> : (
          <table>
            <thead><tr><th></th><th>From (projected to lapse)</th><th></th><th>To (short of funds)</th><th>Account</th><th className="num">Amount</th><th>Why</th></tr></thead>
            <tbody>
              {d.suggestions.map((s: Sugg) => (
                <tr key={key(s)} className={rpg[key(s)] ? "row-on" : ""}>
                  <td><input type="checkbox" checked={!!rpg[key(s)]} onChange={(e) => toggleRpg(s, e.target.checked)} aria-label="Add to plan" /></td>
                  <td><b>{s.from_ppa_name}</b><div className="small muted">{s.from_line_id} · lapse {money(s.from_projected_lapse)}</div></td>
                  <td><ArrowRight size={14} className="muted" /></td>
                  <td><b>{s.to_ppa_name}</b><div className="small muted">{s.to_line_id} · needs {money(s.to_need)}</div></td>
                  <td className="small">{s.tas}</td>
                  <td className="num"><b>{money(s.amount)}</b>{s.notification_required && <div><span className="tag"><Landmark size={11} /> notification</span></div>}</td>
                  <td className="small muted">{s.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <Card title="Reprogramming requests" hint="Approval needs an agency-wide Budget Director other than the requester (separation of duties).">
        {d.requests.length === 0 ? <Empty>No reprogramming requests yet.</Empty> : (
          <table>
            <thead><tr><th>Request</th><th>From → To</th><th className="num">Amount</th><th>Status</th><th>Requested</th><th>Decision</th><th></th></tr></thead>
            <tbody>
              {d.requests.map((r: any) => {
                const mine = r.requested_by === me?.email;
                return (
                  <tr key={r.request_id}>
                    <td><b>{r.request_id}</b><div className="small muted">{r.tas}</div></td>
                    <td className="small">{r.from_ppa_name} <span className="muted">({r.from_line_id})</span><br />→ {r.to_ppa_name} <span className="muted">({r.to_line_id})</span>
                      {r.justification && <div className="muted">{r.justification}</div>}</td>
                    <td className="num"><b>{money(r.amount)}</b>{r.notification_required && <div><span className="tag"><Landmark size={11} /> notification</span></div>}</td>
                    <td><span className={`status-pill ${r.status.toLowerCase()}`}>{r.status}</span></td>
                    <td className="small">{person(r.requested_by)}<div className="muted">{ago(r.requested_at)}</div></td>
                    <td className="small">{r.decided_by ? <>{person(r.decided_by)}<div className="muted">{r.decision_note}</div></> : <span className="muted">-</span>}</td>
                    <td className="nowrap">
                      {r.status === "Pending" && (
                        <>
                          <button className="btn sm primary" disabled={!me?.can_approve_reprogramming || mine}
                                  title={mine ? "Separation of duties: a second Budget Director must approve a request you made" : !me?.can_approve_reprogramming ? "Only an agency-wide Budget Director can approve" : ""}
                                  onClick={() => setDeciding({ r, decision: "Approved" })}>Approve</button>{" "}
                          <button className="btn sm ghost" disabled={!me?.can_approve_reprogramming || mine} onClick={() => setDeciding({ r, decision: "Rejected" })}>Reject</button>{" "}
                          {mine && <button className="btn sm ghost" onClick={() => setDeciding({ r, decision: "Withdrawn" })}>Withdraw</button>}
                          {mine && <div className="tiny muted">awaiting a second approver</div>}
                        </>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </Card>

      {deciding && (
        <DecisionModal r={deciding.r} decision={deciding.decision} onClose={() => setDeciding(null)}
                       onDone={(msg) => { setDeciding(null); toast(msg); changed(); }} />
      )}
      {creating && <NewRequestModal byLine={byLine} onClose={() => setCreating(false)} onDone={(r) => { setCreating(false); toast(`${r.request_id} submitted for approval`); changed(); }} />}
    </div>
  );
}

function DecisionModal({ r, decision, onClose, onDone }: { r: any; decision: string; onClose: () => void; onDone: (msg: string) => void }) {
  const [note, setNote] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async () => {
    setBusy(true); setErr("");
    try {
      await post(`/reprogramming/${r.request_id}/decision`, { decision, note: note || undefined });
      onDone(`${r.request_id} ${decision.toLowerCase()}`);
    } catch (e: any) { setErr(e.message); setBusy(false); }
  };
  return (
    <Modal title={`${decision === "Withdrawn" ? "Withdraw" : decision === "Approved" ? "Approve" : "Reject"} ${r.request_id}`} onClose={onClose}
           footer={<><button className="btn ghost" onClick={onClose}>Cancel</button><button className="btn primary" disabled={busy} onClick={submit}>{busy ? "Saving…" : "Confirm"}</button></>}>
      <p>{money(r.amount)} from <b>{r.from_ppa_name}</b> to <b>{r.to_ppa_name}</b> within {r.tas}.</p>
      <label className="field">Note for the record<textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} /></label>
      {err && <div className="error">{err}</div>}
    </Modal>
  );
}

function NewRequestModal({ byLine, onClose, onDone }: { byLine: Record<string, any>; onClose: () => void; onDone: (r: any) => void }) {
  const all = useApi<any[]>("/lines", { max_days: 1000 });
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [amount, setAmount] = useState("");
  const [why, setWhy] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const src = (all.data ?? []).find((l) => l.line_id === from);
  const targets = (all.data ?? []).filter((l) => src && l.tas === src.tas && l.line_id !== from);
  const submit = async () => {
    setBusy(true); setErr("");
    try { onDone(await post("/reprogramming", { from_line_id: from, to_line_id: to, amount: Number(amount), justification: why || undefined })); }
    catch (e: any) { setErr(e.message); setBusy(false); }
  };
  return (
    <Modal title="New reprogramming request" onClose={onClose}
           footer={<><button className="btn ghost" onClick={onClose}>Cancel</button><button className="btn primary" disabled={busy || !from || !to || !Number(amount)} onClick={submit}>{busy ? "Submitting…" : "Submit for approval"}</button></>}>
      <label className="field">From line
        <select value={from} onChange={(e) => { setFrom(e.target.value); setTo(""); }}>
          <option value="">Select a line…</option>
          {(all.data ?? []).filter((l) => Number(l.uncommitted_balance) > 0).map((l) => (
            <option key={l.line_id} value={l.line_id}>{l.line_id} · {l.ppa_name} · {money(l.uncommitted_balance)} uncommitted{byLine[l.line_id] ? ` · lapse ${money(byLine[l.line_id].projected_lapse_amount)}` : ""}</option>
          ))}
        </select>
      </label>
      <label className="field">To line (same account {src?.tas ?? ""})
        <select value={to} onChange={(e) => setTo(e.target.value)} disabled={!src}>
          <option value="">Select a line…</option>
          {targets.map((l) => <option key={l.line_id} value={l.line_id}>{l.line_id} · {l.ppa_name}</option>)}
        </select>
      </label>
      <label className="field">Amount (USD)<input type="number" min={1000} step={1000} value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="e.g. 250000" /></label>
      <label className="field">Justification<textarea rows={3} value={why} onChange={(e) => setWhy(e.target.value)} /></label>
      {err && <div className="error">{err}</div>}
    </Modal>
  );
}

// --------------------------------------------------------------------------------------- review
function ReviewModal({ lines, pkg, rpg, suggestions, totals, onClose, onDone }: {
  lines: Record<string, any>; pkg: Record<string, number>; rpg: Record<string, number>; suggestions: Sugg[]; totals: any; onClose: () => void; onDone: () => void;
}) {
  const { toast, changed } = useApp();
  const [status, setStatus] = useState<Record<string, "pending" | "ok" | string>>({});
  const [running, setRunning] = useState(false);
  const items = [
    ...Object.entries(pkg).map(([lid, amount]) => ({ id: `pkg:${lid}`, kind: "pkg" as const, l: lines[lid], amount })),
    ...suggestions.filter((s) => rpg[key(s)]).map((s) => ({ id: `rpg:${key(s)}`, kind: "rpg" as const, s, amount: rpg[key(s)] })),
  ];
  const done = items.length > 0 && items.every((i) => status[i.id] && status[i.id] !== "pending");
  const run = async () => {
    setRunning(true);
    let ok = 0;
    for (const it of items) {
      if (status[it.id] === "ok") continue;
      setStatus((s) => ({ ...s, [it.id]: "pending" }));
      try {
        if (it.kind === "pkg") {
          const l = it.l;
          await post(`/packages/${l.line_id}`, {
            title: l.draft_title, acquisition_type: l.draft_type, contract_number: l.draft_contract, amount: it.amount,
            requirement_summary: l.draft_requirement_summary, justification: l.draft_justification,
            required_documents: asList(l.draft_documents), milestones: asList(l.draft_milestones), source: "Year-end plan - batch AI draft",
          });
        } else {
          const s = it.s;
          await post("/reprogramming", {
            from_line_id: s.from_line_id, to_line_id: s.to_line_id, amount: it.amount,
            justification: `Year-end reprogramming within ${s.tas}: ${s.from_ppa_name} is projected to lapse ${moneyFull(s.from_projected_lapse)}; ${s.to_ppa_name}: ${s.reason}.`,
          });
        }
        ok++;
        setStatus((s) => ({ ...s, [it.id]: "ok" }));
      } catch (e: any) {
        setStatus((s) => ({ ...s, [it.id]: e.message }));
      }
    }
    setRunning(false);
    changed();
    toast(`${ok} of ${items.length} plan actions submitted`, ok === items.length ? "ok" : "error");
  };
  return (
    <Modal wide title="Review the year-end plan" onClose={onClose}
           footer={done
             ? <button className="btn primary" onClick={onDone}>Done</button>
             : <><button className="btn ghost" onClick={onClose} disabled={running}>Back</button>
                 <button className="btn primary" onClick={run} disabled={running}><Send size={14} /> {running ? "Submitting…" : `Submit ${items.length} actions`}</button></>}>
      <p className="muted">Recovers <b>{money(totals.selected)}</b> of the remaining projected lapse. Packages go to the acquisition office; reprogramming requests go to a second Budget Director for approval. Every action is written to Lakebase and streamed to Unity Catalog.</p>
      <ul className="review-list">
        {items.map((it) => (
          <li key={it.id}>
            {it.kind === "pkg" ? <FileText size={15} /> : <ArrowRightLeft size={15} />}
            <span className="grow">
              {it.kind === "pkg"
                ? <><b>{it.l.draft_type}</b> · {it.l.ppa_name} <span className="muted">({it.l.line_id}{it.l.draft_contract ? `, ${it.l.draft_contract}` : ""})</span></>
                : <><b>Reprogram</b> {it.s.from_ppa_name} → {it.s.to_ppa_name} <span className="muted">({it.s.tas})</span></>}
            </span>
            <b className="num">{money(it.amount)}</b>
            <span className="review-status">
              {status[it.id] === "ok" ? <span className="ok-text"><Check size={14} /> submitted</span>
                : status[it.id] === "pending" ? <span className="muted">sending…</span>
                : status[it.id] ? <span className="error small">{status[it.id]}</span> : null}
            </span>
          </li>
        ))}
      </ul>
    </Modal>
  );
}

