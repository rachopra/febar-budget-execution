import { GripVertical, Search, X } from "lucide-react";
import { useMemo, useState } from "react";
import { ago, ALERT_LABEL, money, person, post, useApi } from "../api";
import { useApp } from "../app-context";
import { Drawer, Empty, Modal, Segmented, SevBadge, Skeleton } from "../components/ui";

const COLUMNS = ["Open", "Acknowledged", "Assigned", "Escalated", "Resolved"] as const;
type Col = (typeof COLUMNS)[number];
const SEVERITIES = ["All", "Critical", "High", "Medium"] as const;
const PAGE = 30;

export default function AlertsBoard() {
  const { office, version, changed, toast } = useApp();
  const alerts = useApi<any[]>("/alerts", { office }, [version]);
  const summary = useApi<any[]>("/alerts/summary", { office }, [version]);
  const [type, setType] = useState("");
  const [sev, setSev] = useState<(typeof SEVERITIES)[number]>("All");
  const [q, setQ] = useState("");
  const [local, setLocal] = useState<Record<string, { action: Col; assignee?: string }>>({});
  const [pending, setPending] = useState<{ a: any; to: Col } | null>(null);
  const [open, setOpen] = useState<any>(null);
  const [dragOver, setDragOver] = useState<Col | null>(null);
  const [limit, setLimit] = useState<Record<string, number>>({});

  const byType = useMemo(() => {
    const m: Record<string, { n: number; amt: number }> = {};
    for (const s of summary.data ?? []) {
      m[s.alert_type] ??= { n: 0, amt: 0 };
      m[s.alert_type].n += Number(s.alerts); m[s.alert_type].amt += Number(s.amount_at_risk);
    }
    return Object.entries(m).sort((a, b) => b[1].amt - a[1].amt);
  }, [summary.data]);

  const status = (a: any): Col => (local[a.alert_id]?.action ?? a.last_action ?? "Open") as Col;
  const rows = (alerts.data ?? []).filter((a) =>
    (!type || a.alert_type === type) && (sev === "All" || a.severity === sev)
    && (!q || `${a.detail} ${a.office_code} ${a.line_id ?? ""} ${a.entity_id}`.toLowerCase().includes(q.toLowerCase())));
  const cols = Object.fromEntries(COLUMNS.map((c) => [c, rows.filter((a) => status(a) === c)])) as Record<Col, any[]>;

  const commit = async (a: any, to: Col, assignee?: string, note?: string) => {
    const prev = local[a.alert_id];
    setLocal((l) => ({ ...l, [a.alert_id]: { action: to, assignee } }));
    try {
      await post(`/alerts/${a.alert_id}/actions`, { action: to, assignee, note });
      toast(`${ALERT_LABEL[a.alert_type] ?? a.alert_type} → ${to}${assignee ? ` (${person(assignee)})` : ""}`);
      changed();
    } catch (e: any) {
      setLocal((l) => { const n = { ...l }; if (prev) n[a.alert_id] = prev; else delete n[a.alert_id]; return n; });
      toast(e.message, "error");
    }
  };
  const move = (a: any, to: Col) => {
    if (to === status(a)) return;
    if (to === "Open") { toast("Alerts can't be moved back to Open; acknowledge or reassign instead", "info"); return; }
    if (to === "Acknowledged") commit(a, to);
    else setPending({ a, to });
  };

  return (
    <div className="stack">
      <div className="page-head">
        <div>
          <h1>Risk alerts</h1>
          <p className="muted">Detected by the gold pipeline as of the reporting date. Drag a card to triage it; every move is written to Lakebase and streamed to Unity Catalog.</p>
        </div>
      </div>
      <div className="type-chips">
        <button className={!type ? "active" : ""} onClick={() => setType("")}>All types <b>{(alerts.data ?? []).length}</b></button>
        {byType.map(([t, v]) => (
          <button key={t} className={type === t ? "active" : ""} onClick={() => setType(type === t ? "" : t)}>
            {ALERT_LABEL[t] ?? t} <b>{v.n}</b> <span className="muted">{money(v.amt)}</span>
          </button>
        ))}
      </div>
      <div className="toolbar">
        <Segmented value={sev} onChange={setSev} options={SEVERITIES.map((s) => ({ id: s, label: s === "All" ? "All severities" : <SevBadge severity={s} /> }))} />
        <div className="search-box"><Search size={15} /><input placeholder="Search detail, office, line, invoice…" value={q} onChange={(e) => setQ(e.target.value)} /></div>
      </div>
      {!alerts.data ? <Skeleton h={520} /> : (
        <div className="board">
          {COLUMNS.map((c) => {
            const list = cols[c];
            const total = list.reduce((s, a) => s + Number(a.amount_at_risk || 0), 0);
            const lim = limit[c] ?? PAGE;
            return (
              <div key={c} className={`column ${dragOver === c ? "drop" : ""} col-${c.toLowerCase()}`}
                   onDragOver={(e) => { e.preventDefault(); setDragOver(c); }} onDragLeave={() => setDragOver(null)}
                   onDrop={(e) => { e.preventDefault(); setDragOver(null); const a = rows.find((x) => x.alert_id === e.dataTransfer.getData("text/plain")); if (a) move(a, c); }}>
                <div className="column-head"><b>{c}</b><span className="count">{list.length}</span><span className="muted small">{money(total)}</span></div>
                <div className="column-body">
                  {list.slice(0, lim).map((a) => (
                    <div key={a.alert_id} className={`acard sev-edge-${a.severity}`} draggable
                         onDragStart={(e) => { e.dataTransfer.setData("text/plain", a.alert_id); e.dataTransfer.effectAllowed = "move"; }}
                         onClick={() => setOpen(a)}>
                      <div className="acard-top"><SevBadge severity={a.severity} /><span className="muted tiny">{a.office_code}</span><GripVertical size={13} className="grip" /></div>
                      <div className="acard-type">{ALERT_LABEL[a.alert_type] ?? a.alert_type}</div>
                      <div className="acard-detail">{a.detail}</div>
                      <div className="acard-foot"><b>{money(a.amount_at_risk)}</b>
                        {(local[a.alert_id]?.assignee ?? a.assignee) && <span className="muted tiny">→ {person(local[a.alert_id]?.assignee ?? a.assignee)}</span>}</div>
                    </div>
                  ))}
                  {list.length > lim && <button className="btn ghost sm more" onClick={() => setLimit((l) => ({ ...l, [c]: lim + PAGE }))}>Show {Math.min(PAGE, list.length - lim)} more of {list.length - lim}</button>}
                  {list.length === 0 && <div className="column-empty">Drop alerts here</div>}
                </div>
              </div>
            );
          })}
        </div>
      )}
      {pending && <ActionModal a={pending.a} to={pending.to} onClose={() => setPending(null)}
                               onSubmit={(assignee, note) => { commit(pending.a, pending.to, assignee, note); setPending(null); }} />}
      {open && <AlertPanel a={open} status={status(open)} onClose={() => setOpen(null)} onMove={(to) => move(open, to)} />}
    </div>
  );
}

function ActionModal({ a, to, onClose, onSubmit }: { a: any; to: Col; onClose: () => void; onSubmit: (assignee?: string, note?: string) => void }) {
  const [assignee, setAssignee] = useState(a.assignee ?? "");
  const [note, setNote] = useState("");
  const needs = to === "Assigned";
  return (
    <Modal title={`${to}: ${ALERT_LABEL[a.alert_type] ?? a.alert_type}`} onClose={onClose}
           footer={<><button className="btn ghost" onClick={onClose}>Cancel</button>
             <button className="btn primary" disabled={needs && !assignee.includes("@")} onClick={() => onSubmit(assignee || undefined, note || undefined)}>Save</button></>}>
      <p className="small">{a.detail}</p>
      {needs && <label className="field">Assign to (e-mail)<input value={assignee} onChange={(e) => setAssignee(e.target.value)} placeholder="budget.analyst@dci.example.gov" autoFocus /></label>}
      <label className="field">{to === "Resolved" ? "Resolution" : to === "Escalated" ? "Why escalate" : "Note"}<textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} autoFocus={!needs} /></label>
    </Modal>
  );
}

function AlertPanel({ a, status, onClose, onMove }: { a: any; status: Col; onClose: () => void; onMove: (to: Col) => void }) {
  const { version, openLine } = useApp();
  const hist = useApi<any[]>(`/alerts/${a.alert_id}/history`, {}, [version]);
  return (
    <Drawer onClose={onClose} width={560}>
      <div className="drawer-head">
        <div>
          <div className="row-center gap"><SevBadge severity={a.severity} /><span className={`status-pill ${status.toLowerCase()}`}>{status}</span></div>
          <h2>{ALERT_LABEL[a.alert_type] ?? a.alert_type}</h2>
          <div className="small muted">{a.office_code} · {a.entity_id}</div>
        </div>
        <button className="icon-btn" onClick={onClose} aria-label="Close"><X size={18} /></button>
      </div>
      <div className="drawer-body stack">
        <p>{a.detail}</p>
        <div className="stat-grid two"><div className="stat"><div className="stat-label">Amount at risk</div><div className="stat-value">{money(a.amount_at_risk)}</div></div>
          {a.line_id && <div className="stat"><div className="stat-label">Budget line</div><div className="stat-value small-value"><a onClick={() => { onClose(); openLine(a.line_id); }}>{a.line_id}</a></div></div>}</div>
        <div className="row-center gap wrap">
          {COLUMNS.filter((c) => c !== "Open" && c !== status).map((c) => <button key={c} className="btn ghost sm" onClick={() => onMove(c)}>{c === "Acknowledged" ? "Acknowledge" : c === "Assigned" ? "Assign" : c === "Escalated" ? "Escalate" : "Resolve"}</button>)}
        </div>
        <h3 className="sub-head">History</h3>
        {!hist.data ? <Skeleton h={80} /> : hist.data.length === 0 ? <Empty>No actions yet.</Empty> : (
          <ul className="timeline">
            {hist.data.map((h) => (
              <li key={h.action_id}><b>{h.action}</b>{h.assignee ? ` → ${person(h.assignee)}` : ""} <span className="muted small">by {person(h.acted_by)} · {ago(h.acted_at)}</span>
                {h.note && <div className="small">{h.note}</div>}</li>
            ))}
          </ul>
        )}
      </div>
    </Drawer>
  );
}
