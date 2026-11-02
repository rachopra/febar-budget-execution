import {
  Activity, ArrowRight, ArrowRightLeft, Bell, ClipboardCheck, FileText, Lock, MessageSquare, Send, Sparkles, StickyNote, Timer,
} from "lucide-react";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import {
  CartesianGrid, ComposedChart, Legend, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { ago, ALERT_LABEL, longDate, money, pct, person, shortDate, TIER_SEVERITY, useApi } from "../api";
import { useApp } from "../app-context";
import { Avatar, axisProps, Card, ChartTip, CountUp, Empty, Meter, SevBadge, Skeleton, TierBadge } from "../components/ui";

export default function CommandCenter() {
  const { office, version } = useApp();
  const cc = useApi("/command-center", { office }, [version]);
  const burn = useApi<any[]>("/burn", { office }, [version]);
  if (cc.error) return <div className="error">{cc.error}</div>;
  if (!cc.data) return <div className="stack"><Skeleton h={300} /><Skeleton h={260} /><Skeleton h={320} /></div>;
  const d = cc.data;
  return (
    <div className="stack">
      <Hero d={d} />
      <WindowsCard d={d} />
      <div className="grid cols-3-2">
        <BurnCard d={d} burn={burn.data ?? []} />
        <CompositionCard d={d} />
      </div>
      <OfficesCard d={d} />
      <div className="grid cols-3-2">
        <TopLinesCard d={d} />
        <div className="stack">
          <QueueCard q={d.queue} />
          <ActivityCard />
        </div>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------------------------------ hero
function Hero({ d }: { d: any }) {
  const { go, askGenie } = useApp();
  const [q, setQ] = useState("");
  const c = d.calendar, f = d.forecast, e = d.expiring;
  const covered = f.projected_lapse > 0 ? f.recovery_in_flight / f.projected_lapse : 0;
  const awardDays = Math.round((new Date(c.must_award_by).getTime() - new Date(c.as_of_date).getTime()) / 86400000);
  return (
    <section className="hero">
      <div className="hero-glow" />
      <div className="hero-main">
        <div className="eyebrow"><span className="live-dot" />FY{c.fiscal_year} year-end · data as of {longDate(c.as_of_date)}</div>
        <div className="hero-figure">
          <span className="hero-number"><CountUp value={f.projected_lapse} format={(v) => money(v)} duration={1400} /></span>
          <span className="hero-caption">is projected to lapse when annual and expiring multi-year funds expire on {longDate(c.fiscal_year_end)}</span>
        </div>
        <div className="recovery">
          <div className="recovery-bar">
            <div className="recovery-fill" style={{ width: `${Math.min(100, covered * 100)}%` }} />
          </div>
          <div className="recovery-legend">
            <span><span className="swatch" style={{ background: "var(--series-1)" }} />Covered by actions in flight <b><CountUp value={f.recovery_in_flight} format={(v) => money(v)} /></b> ({pct(covered, 0)})</span>
            <span><span className="swatch" style={{ background: "var(--neutral-seg)" }} />No action yet <b>{money(f.remaining_after_actions)}</b></span>
          </div>
        </div>
        <div className="hero-facts">
          <div><b>{money(e.unobligated)}</b><span>unobligated on {e.lines} expiring lines</span></div>
          <div><b>{money(f.high_risk_lapse)}</b><span>of the lapse sits on {f.high_risk_lines} critical / high-risk lines</span></div>
          <div><b>{shortDate(c.must_award_by)}</b><span>last safe award date ({awardDays} days)</span></div>
        </div>
        <div className="hero-actions">
          <button className="btn primary lg" onClick={() => go("plan")}>Build the year-end plan <ArrowRight size={16} /></button>
          <form className="ask" onSubmit={(ev) => { ev.preventDefault(); askGenie(q || undefined); setQ(""); }}>
            <Sparkles size={16} />
            <input value={q} onChange={(ev) => setQ(ev.target.value)} placeholder="Ask Genie: which offices are furthest behind plan?" />
            <button className="btn ghost sm" type="submit">Ask</button>
          </form>
        </div>
      </div>
      <Countdown days={c.days_left} elapsed={c.fiscal_year_elapsed} fy={c.fiscal_year} />
    </section>
  );
}

function Countdown({ days, elapsed, fy }: { days: number; elapsed: number; fy: number }) {
  const r = 78, circ = 2 * Math.PI * r;
  const [shown, setShown] = useState(0);
  useEffect(() => { const t = setTimeout(() => setShown(elapsed), 80); return () => clearTimeout(t); }, [elapsed]);
  return (
    <div className="countdown" aria-label={`${days} days left in FY${fy}`}>
      <svg viewBox="0 0 200 200" width="200" height="200">
        <defs>
          <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#6da7ec" /><stop offset="100%" stopColor="#2a78d6" />
          </linearGradient>
        </defs>
        <circle cx="100" cy="100" r={r} className="ring-track" />
        <circle cx="100" cy="100" r={r} className="ring-arc" stroke="url(#ring)"
                strokeDasharray={circ} strokeDashoffset={circ * (1 - shown)} transform="rotate(-90 100 100)" />
      </svg>
      <div className="countdown-center">
        <div className="countdown-days"><CountUp value={days} format={(v) => String(Math.round(v))} duration={1200} /></div>
        <div className="countdown-label">days left in FY{fy}</div>
      </div>
      <div className="countdown-foot"><Timer size={13} /> {pct(elapsed, 0)} of the fiscal year elapsed</div>
    </div>
  );
}

// ------------------------------------------------------------------------------- acquisition windows
function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [w, setW] = useState(900);
  useLayoutEffect(() => {
    if (!ref.current) return;
    const ro = new ResizeObserver(([e]) => setW(e.contentRect.width));
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, []);
  return [ref, w] as const;
}

/** First-of-month dates (YYYY-MM-DD) strictly inside (lo, hi]. */
export function monthStarts(lo: number, hi: number): string[] {
  const out: string[] = [];
  const d = new Date(lo);
  for (let y = d.getFullYear(), m = d.getMonth() + 1; ; m++) {
    if (m > 11) { y++; m = 0; }
    const s = `${y}-${String(m + 1).padStart(2, "0")}-01`;
    if (new Date(`${s}T12:00:00`).getTime() > hi) return out;
    out.push(s);
  }
}

const STATUS_TEXT: Record<string, string> = { open: "Open", closing: "Closing", closed: "Closed" };

function WindowsCard({ d }: { d: any }) {
  const { go } = useApp();
  const [ref, width] = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);
  const c = d.calendar, ws: any[] = d.windows;
  const open = ws.filter((w) => w.status !== "closed");
  const t = (s: string) => new Date(`${s}T12:00:00`).getTime();
  const lo = Math.min(...ws.map((w) => t(w.last_submit_conservative))) - 12 * 86400000;
  const hi = t(c.fiscal_year_end) + 6 * 86400000;
  const L = 190, R = 250, plotW = Math.max(200, width - L - R), rowH = 40, top = 42, H = top + ws.length * rowH + 26;
  const x = (s: string) => L + ((t(s) - lo) / (hi - lo)) * plotW;
  const months = monthStarts(lo, hi);
  const markers = [
    { date: c.as_of_date, label: "Today", cls: "today", anchor: "end", dx: -4, dy: -24 },
    { date: c.must_award_by, label: "Must award", cls: "award", anchor: "end", dx: -4, dy: -10 },
    { date: c.fiscal_year_end, label: "Funds expire", cls: "expire", anchor: "start", dx: 4, dy: -24 },
  ];
  return (
    <Card
      title={open.length ? `Only ${open.map((w) => w.acquisition_type.toLowerCase() + "s").join(" and ")} can still award before the funds expire` : "Every acquisition window has closed"}
      hint={`Last day to submit a request and still award by ${longDate(c.must_award_by)}, from historical procurement lead time (bar ends at the 80th-percentile PALT, fades out at the median). Select a row to see its open requests.`}
    >
      <div ref={ref} className="windows">
        <svg width="100%" height={H} role="img" aria-label="Acquisition windows timeline">
          {months.map((m) => (
            <g key={m}>
              <line x1={x(m)} x2={x(m)} y1={top - 6} y2={H - 22} className="grid-line" />
              <text x={x(m)} y={H - 6} className="tick" textAnchor="middle">{new Date(`${m}T12:00:00`).toLocaleDateString("en-US", { month: "short" })}</text>
            </g>
          ))}
          {ws.map((w, i) => {
            const y = top + i * rowH;
            const cy = y + rowH / 2;
            const x0 = L, x1 = x(w.last_submit_conservative), x2 = x(w.last_submit_typical);
            return (
              <g key={w.acquisition_type} className={`win-row ${w.status} ${hover === i ? "hover" : ""}`}
                 onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}
                 onClick={() => go("procurement", { type: w.acquisition_type })} style={{ cursor: "pointer" }}>
                <rect x={0} y={y + 2} width="100%" height={rowH - 4} className="win-hit" rx={6} />
                <text x={10} y={cy - 3} className="win-name">{w.acquisition_type}</text>
                <text x={10} y={cy + 12} className="win-sub">median {w.median_palt_days}d · p80 {w.p80_palt_days}d</text>
                <defs>
                  <linearGradient id={`fade${i}`} x1="0" x2="1">
                    <stop offset="0%" className={`win-stop ${w.status}`} stopOpacity={0.95} />
                    <stop offset="100%" className={`win-stop ${w.status}`} stopOpacity={0.12} />
                  </linearGradient>
                </defs>
                <rect x={x0} y={cy - 5} width={Math.max(0, x1 - x0)} height={10} rx={4} className={`win-bar ${w.status}`} />
                <rect x={x1 + 2} y={cy - 5} width={Math.max(0, x2 - x1 - 2)} height={10} rx={4} fill={`url(#fade${i})`} />
                <text x={L + plotW + 16} y={cy - 3} className={`win-status ${w.status}`}>
                  {STATUS_TEXT[w.status]}{w.status === "closed" ? ` ${-w.days_to_close}d ago` : ` · ${w.days_to_close}d left`}
                </text>
                <text x={L + plotW + 16} y={cy + 12} className="win-sub">
                  {w.open_prs} open requests · {money(w.open_value)}{w.will_miss ? ` · ${w.will_miss} will miss` : ""}
                </text>
              </g>
            );
          })}
          {markers.map((m) => (
            <g key={m.label} className={`marker ${m.cls}`}>
              <line x1={x(m.date)} x2={x(m.date)} y1={top + m.dy - 10} y2={H - 22} />
              <text x={x(m.date) + m.dx} y={top + m.dy} textAnchor={m.anchor as "start" | "middle" | "end"}>{m.label} {shortDate(m.date)}</text>
            </g>
          ))}
        </svg>
        {hover !== null && (() => {
          const w = ws[hover];
          return (
            <div className="svg-tip" style={{ left: Math.min(width - 280, x(w.last_submit_typical) + 10), top: top + hover * rowH + rowH }}>
              <b>{w.acquisition_type}</b>
              <div>Submit by {longDate(w.last_submit_conservative)} to be safe (p80), {longDate(w.last_submit_typical)} at the latest (median).</div>
              <div className="muted">{w.open_prs} open requests on expiring funds ({money(w.open_value)}).</div>
            </div>
          );
        })()}
      </div>
      <div className="legend-row">
        <span><span className="swatch" style={{ background: "var(--good)" }} />Open window</span>
        <span><span className="swatch" style={{ background: "var(--warning)" }} />Closing (past p80, before median)</span>
        <span><Lock size={12} />Closed</span>
      </div>
    </Card>
  );
}

// ------------------------------------------------------------------------------------------ burn
function BurnCard({ d, burn }: { d: any; burn: any[] }) {
  const f = d.forecast, budget = d.expiring.total_budget;
  // cumulative totals include multi-year funds' earlier years; show the current fiscal year
  const rows = burn.filter((r) => String(r.month) >= d.calendar.fiscal_year_start).map((r) => ({
    month: String(r.month).slice(0, 7),
    Plan: r.cumulative_planned_obligations,
    Actual: r.is_actualized ? r.cumulative_actual_obligations : null,
    Forecast: null as number | null,
  }));
  const last = rows.map((r) => r.Actual !== null).lastIndexOf(true);
  if (last >= 0 && rows.length) {
    rows[last].Forecast = rows[last].Actual;
    rows[rows.length - 1].Forecast = f.projected_year_end_obligations;
  }
  const label = (v: string) => new Date(`${v}-15`).toLocaleDateString("en-US", { month: "short", year: "2-digit" });
  return (
    <Card title="Obligations are tracking below the approved spend plan"
          hint={`Cumulative obligations on funds expiring ${longDate(d.calendar.fiscal_year_end)} vs the baseline operating plan, with the ML year-end forecast`}>
      {rows.length === 0 ? <Skeleton h={290} /> : (
        <ResponsiveContainer width="100%" height={290}>
          <ComposedChart data={rows} margin={{ top: 18, right: 28, left: 4, bottom: 0 }}>
            <CartesianGrid stroke="var(--grid)" vertical={false} />
            <XAxis dataKey="month" {...axisProps} tickFormatter={label} />
            <YAxis {...axisProps} tickFormatter={(v) => money(v, 0)} width={60} axisLine={false} />
            <Tooltip content={<ChartTip format={(v: number) => money(v)} labelFormat={label} />} cursor={{ stroke: "var(--axis)" }} />
            <Legend wrapperStyle={{ fontSize: 12, color: "var(--text-secondary)" }} iconType="plainline" />
            <ReferenceLine y={budget} stroke="var(--text-muted)" strokeDasharray="2 4"
                           label={{ value: `Budget ${money(budget)}`, position: "insideTopLeft", fill: "var(--text-secondary)", fontSize: 11 }} />
            <Line type="monotone" dataKey="Plan" name="Approved plan" stroke="var(--series-2)" strokeWidth={2} strokeDasharray="6 4" dot={false} />
            <Line type="monotone" dataKey="Actual" name="Obligated" stroke="var(--series-1)" strokeWidth={2.5} dot={false} activeDot={{ r: 5, stroke: "var(--surface-1)", strokeWidth: 2 }} />
            <Line type="linear" dataKey="Forecast" name="ML forecast to year end" stroke="var(--series-1)" strokeWidth={2} strokeDasharray="2 4"
                  dot={{ r: 4, fill: "var(--series-1)", stroke: "var(--surface-1)", strokeWidth: 2 }} connectNulls
                  label={({ x, y, index }: any) => index === rows.length - 1
                    ? <text x={x - 8} y={y + 20} textAnchor="end" fontSize={11} fill="var(--text-secondary)">forecast {money(f.projected_year_end_obligations, 2)} · {money(f.projected_lapse)} lapses</text>
                    : <g />} />
          </ComposedChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}

// ---------------------------------------------------------------------------------- composition
const SEG_COLORS = ["var(--ramp-1)", "var(--ramp-2)", "var(--ramp-3)", "var(--neutral-seg)"];

function CompositionCard({ d }: { d: any }) {
  const { go } = useApp();
  const e = d.expiring, f = d.forecast;
  const maxTier = Math.max(...f.by_tier.map((t: any) => Number(t.lapse)), 1);
  return (
    <Card title="Where every expiring dollar stands" hint={`${money(e.total_budget)} on ${e.lines} lines that expire ${longDate(d.calendar.fiscal_year_end)}`}>
      <div className="seg-bar">
        {e.composition.map((s: any, i: number) => (
          <div key={s.stage} className="seg" style={{ flexGrow: Math.max(s.amount, 0), background: SEG_COLORS[i] }}
               title={`${s.stage}: ${money(s.amount)} (${pct(s.amount / e.total_budget)})`} />
        ))}
      </div>
      <div className="seg-legend">
        {e.composition.map((s: any, i: number) => (
          <div key={s.stage}>
            <span className="swatch" style={{ background: SEG_COLORS[i] }} />
            <span>{s.stage}</span>
            <b>{money(s.amount)}</b>
            <span className="muted num">{pct(s.amount / e.total_budget)}</span>
          </div>
        ))}
      </div>
      <h3 className="sub-head">Projected lapse by risk tier</h3>
      <div className="tier-bars">
        {f.by_tier.map((t: any) => (
          <button key={t.risk_tier} className="tier-row" onClick={() => go("plan", { tier: t.risk_tier })}>
            <span className="tier-label"><TierBadge tier={t.risk_tier} /></span>
            <span className="tier-track"><span className={`tier-fill sev-bg-${TIER_SEVERITY[t.risk_tier]}`} style={{ width: `${(Number(t.lapse) / maxTier) * 100}%` }} /></span>
            <b className="num">{money(t.lapse)}</b>
            <span className="muted small num">{t.lines} lines</span>
          </button>
        ))}
      </div>
    </Card>
  );
}

// -------------------------------------------------------------------------------------- offices
function OfficesCard({ d }: { d: any }) {
  const { office, setOffice, toast } = useApp();
  return (
    <Card title="Program offices" hint="Burn rate vs approved spend plan (current funds). Select an office to scope the whole workspace to it.">
      <div className="office-grid">
        {d.offices.map((o: any, i: number) => {
          const burn = Number(o.burn_rate_vs_plan);
          const active = office === o.office_code;
          return (
            <button key={o.office_code} className={`office ${active ? "active" : ""}`}
                    onClick={() => { setOffice(active ? "" : o.office_code); toast(active ? "Showing all offices in your scope" : `Scoped to ${o.office_name}`, "info"); }}>
              <div className="office-head">
                <span className="office-code">{o.office_code}</span>
                {i === 0 && d.offices.length > 1 && <span className="tag warn">Furthest behind</span>}
              </div>
              <div className="office-name">{o.office_name}</div>
              <div className="office-burn"><b>{pct(burn, 0)}</b><span>of plan obligated</span></div>
              <Meter value={burn} max={1.15} marker={1} tone={burn < 0.85 ? "warn" : "accent"} />
              <div className="office-stats">
                <span>Lapse <b>{money(o.projected_lapse)}</b></span>
                <span>{o.open_critical > 0 ? <SevBadge severity="Critical" label={`${o.open_critical}`} /> : null}
                  {o.open_high > 0 ? <SevBadge severity="High" label={`${o.open_high}`} /> : null}
                  {!o.open_critical && !o.open_high && <span className="muted">no high alerts</span>}</span>
              </div>
              {o.recovery_in_flight > 0 && <div className="office-foot">{money(o.recovery_in_flight)} covered by actions in flight</div>}
            </button>
          );
        })}
      </div>
    </Card>
  );
}

// ------------------------------------------------------------------------------------ top lines
function TopLinesCard({ d }: { d: any }) {
  const { openLine, go } = useApp();
  return (
    <Card title="Lines to act on this week" hint="Ranked by ML-projected lapse; bar shows how much is covered by actions in flight"
          actions={<button className="btn ghost sm" onClick={() => go("plan")}>Open year-end plan <ArrowRight size={14} /></button>}>
      <div className="rank-list">
        {d.top_lines.map((l: any, i: number) => (
          <button key={l.line_id} className="rank" onClick={() => openLine(l.line_id)}>
            <span className="rank-n">{i + 1}</span>
            <span className="rank-main">
              <span className="rank-title">{l.ppa_name}</span>
              <span className="rank-sub">{l.line_id} · {l.days_to_expiration} days left · {pct(l.burn_rate_vs_plan, 0)} of plan</span>
            </span>
            <TierBadge tier={l.risk_tier} />
            <span className="rank-amt">
              <b>{money(l.projected_lapse_amount)}</b>
              <Meter value={l.recovered} max={Number(l.projected_lapse_amount)} />
            </span>
            <span className="rank-hint">{l.draft_amount ? <><FileText size={12} /> AI draft {money(l.draft_amount)}</> : <span className="muted">no draft</span>}</span>
          </button>
        ))}
        {d.top_lines.length === 0 && <Empty>No lines are projected to lapse in this scope.</Empty>}
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------------------- queue
function QueueCard({ q }: { q: any }) {
  const { go } = useApp();
  const items = [
    { n: q.untriaged_alerts, label: "critical / high alerts not yet triaged", icon: <Bell size={16} />, to: () => go("alerts") },
    { n: q.drafts_ready, label: "validated AI packages ready to submit", icon: <Send size={16} />, to: () => go("plan") },
    { n: q.reprogramming_suggestions, label: "reprogramming matches in the same account", icon: <ArrowRightLeft size={16} />, to: () => go("plan", { tab: "reprogramming" }) },
    { n: q.reprogramming_pending, label: "reprogramming requests awaiting decision", icon: <ClipboardCheck size={16} />, to: () => go("plan", { tab: "reprogramming" }) },
    { n: q.reviews_pending, label: "quarterly reviews awaiting sign-off", icon: <FileText size={16} />, to: () => go("quarterly") },
  ];
  return (
    <Card title="Your queue">
      <div className="queue">
        {items.map((it) => (
          <button key={it.label} className={`queue-item ${it.n ? "" : "done"}`} onClick={it.to}>
            <span className="queue-icon">{it.icon}</span>
            <b>{it.n}</b>
            <span>{it.label}</span>
            <ArrowRight size={14} className="queue-go" />
          </button>
        ))}
      </div>
    </Card>
  );
}

// ------------------------------------------------------------------------------------- activity
const KIND_ICON: Record<string, JSX.Element> = {
  alert: <Bell size={13} />, package: <Send size={13} />, signoff: <ClipboardCheck size={13} />,
  reprogramming: <ArrowRightLeft size={13} />, note: <StickyNote size={13} />,
};

export function ActivityCard({ lineId, limit = 12 }: { lineId?: string; limit?: number }) {
  const { version, openLine } = useApp();
  const a = useApi<any[]>("/activity", { limit: 60 }, [version]);
  useEffect(() => { const t = setInterval(a.reload, 20000); return () => clearInterval(t); }, [a.reload]);
  const rows = (a.data ?? []).filter((r) => !lineId || r.line_id === lineId || r.target === lineId).slice(0, limit);
  return (
    <Card title={<span className="row-center"><Activity size={15} /> Live activity <span className="live-dot" /></span>}
          hint="Every action is written to Lakebase and streamed to Unity Catalog">
      {!a.data ? <Skeleton h={160} /> : rows.length === 0 ? <Empty>No activity yet.</Empty> : (
        <ul className="feed">
          {rows.map((r, i) => (
            <li key={i}>
              <Avatar email={r.actor} size={26} />
              <div>
                <div className="feed-line">
                  <b>{person(r.actor)}</b> {r.verb} <span className="feed-subject">{ALERT_LABEL[r.subject] ?? r.subject}</span>
                  {r.target && r.kind === "alert" && <> → {person(r.target)}</>}
                  {r.target && r.kind === "reprogramming" && <> → {r.target}</>}
                  {r.amount != null && <> · <b>{money(r.amount)}</b></>}
                </div>
                {r.detail && <div className="feed-detail">{r.detail}</div>}
                <div className="feed-meta">
                  <span className="feed-kind">{KIND_ICON[r.kind]}{r.office_code}</span>
                  {r.line_id && <a onClick={() => openLine(r.line_id)}>{r.line_id}</a>}
                  <span>{ago(r.at)}</span>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
      {lineId === undefined && <div className="feed-foot muted small"><MessageSquare size={12} /> Notes, alert actions, packages, reprogramming and sign-offs</div>}
    </Card>
  );
}
