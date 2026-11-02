import { useLayoutEffect, useMemo, useRef, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ago, asList, longDate, money, person, shortDate, useApi } from "../api";
import { useApp } from "../app-context";
import { axisProps, Card, ChartTip, Empty, Segmented, SevBadge, Skeleton, Tabs } from "../components/ui";
import { monthStarts } from "./CommandCenter";

const STAGES = ["Draft", "Submitted", "Funds Certified", "In Solicitation", "Under Evaluation"];
type Tab = "timeline" | "pipeline" | "packages";

export default function Procurement() {
  const { office, version, query, go } = useApp();
  const d = useApi("/procurement", { office }, [version]);
  const [tab, setTab] = useState<Tab>((query.get("tab") as Tab) || "timeline");
  const type = query.get("type") || "";
  const setType = (t: string) => go("procurement", { ...(t ? { type: t } : {}), tab });
  const types = useMemo(() => Array.from(new Set((d.data?.open ?? []).map((p: any) => p.acquisition_type))).sort() as string[], [d.data]);

  return (
    <div className="stack">
      <div className="page-head">
        <div>
          <h1>Procurement</h1>
          <p className="muted">Procurement-cycle visibility from the PR tracker: where requests sit, how long each acquisition type takes, and which open requests will award after their funds expire.</p>
        </div>
      </div>
      <div className="toolbar">
        <Tabs value={tab} onChange={(t) => { setTab(t); go("procurement", { ...(type ? { type } : {}), tab: t }); }} tabs={[
          { id: "timeline", label: "Award timeline" }, { id: "pipeline", label: "Pipeline" }, { id: "packages", label: "Packages" },
        ]} />
        <div className="spacer" />
        {tab !== "packages" && (
          <select value={type} onChange={(e) => setType(e.target.value)} aria-label="Acquisition type">
            <option value="">All acquisition types</option>{types.map((t) => <option key={t}>{t}</option>)}
          </select>
        )}
      </div>
      {!d.data ? <Skeleton h={480} /> : tab === "timeline" ? <Timeline d={d.data} type={type} />
        : tab === "pipeline" ? <Pipeline d={d.data} type={type} /> : <Packages />}
    </div>
  );
}

// ------------------------------------------------------------------------------------- timeline
function Timeline({ d, type }: { d: any; type: string }) {
  const { filters, openLine } = useApp();
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(1000);
  const [hover, setHover] = useState<any>(null);
  const [onlyMiss, setOnlyMiss] = useState<"all" | "miss">("all");
  const [showAll, setShowAll] = useState(false);
  useLayoutEffect(() => {
    if (!ref.current) return;
    const ro = new ResizeObserver(([e]) => setWidth(e.contentRect.width));
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, []);
  const asOf = filters.as_of_date ?? "2026-07-31";
  const fy = Number(asOf.slice(0, 4)) + (Number(asOf.slice(5, 7)) >= 10 ? 1 : 0);
  const fyEnd = `${fy}-09-30`;
  const awardBy = new Date(new Date(`${fyEnd}T12:00:00`).getTime() - 14 * 86400000).toISOString().slice(0, 10);
  const all = (d.open as any[]).filter((p) => p.expiration_date <= fyEnd && (!type || p.acquisition_type === type) && p.started_at);
  const misses = all.filter((p) => p.at_risk_of_missing_expiration);
  const rows = (onlyMiss === "miss" ? misses : all)
    .sort((a, b) => Number(b.at_risk_of_missing_expiration) - Number(a.at_risk_of_missing_expiration) || b.forecast_award_date.localeCompare(a.forecast_award_date))
    .slice(0, showAll ? 400 : 30);
  const t = (s: string) => new Date(`${String(s).slice(0, 10)}T12:00:00`).getTime();
  const lo = Math.min(t(asOf) - 120 * 86400000, ...rows.map((r) => t(r.started_at)));
  const hi = Math.max(t(fyEnd) + 20 * 86400000, ...rows.map((r) => t(r.forecast_award_date) + 10 * 86400000));
  const L = 300, R = 24, plotW = Math.max(300, width - L - R), rowH = 26, top = 44, H = top + rows.length * rowH + 28;
  const x = (s: string) => L + ((t(s) - lo) / (hi - lo)) * plotW;
  const months = monthStarts(lo, hi);
  return (
    <Card title={`${misses.length} open requests on expiring funds are forecast to award after ${longDate(fyEnd)}`}
          hint="Each bar runs from submission to forecast award (submission + median PALT for the type); the solid part has elapsed. Requests that cross the expiration line need a faster vehicle or will leave the funds to lapse."
          actions={<Segmented value={onlyMiss} onChange={setOnlyMiss} options={[{ id: "all", label: `All ${all.length}` }, { id: "miss", label: `Will miss ${misses.length}` }]} />}>
      <div ref={ref} className="gantt">
        {rows.length === 0 ? <Empty>No open requests on expiring funds for this filter.</Empty> : (
          <svg width="100%" height={H}>
            {months.map((m) => (
              <g key={m}><line x1={x(m)} x2={x(m)} y1={top - 6} y2={H - 24} className="grid-line" />
                <text x={x(m)} y={H - 8} className="tick" textAnchor="middle">{new Date(`${m}T12:00:00`).toLocaleDateString("en-US", { month: "short" })}</text></g>
            ))}
            {rows.map((p, i) => {
              const y = top + i * rowH, miss = p.at_risk_of_missing_expiration;
              const xs = x(p.started_at), xn = x(asOf), xe = x(p.forecast_award_date);
              return (
                <g key={p.pr_id} className={`g-row ${hover?.pr_id === p.pr_id ? "hover" : ""}`} onMouseEnter={() => setHover({ ...p, i })} onMouseLeave={() => setHover(null)}
                   onClick={() => openLine(p.line_id, "procurement")} style={{ cursor: "pointer" }}>
                  <rect x={0} y={y} width="100%" height={rowH} className="win-hit" />
                  <text x={8} y={y + 17} className="g-label"><tspan className="g-id">{p.pr_id}</tspan> {String(p.title).slice(0, 34)}{String(p.title).length > 34 ? "…" : ""}</text>
                  <rect x={xs} y={y + 8} width={Math.max(2, Math.min(xn, xe) - xs)} height={10} rx={3} className={`g-bar done ${miss ? "miss" : ""}`} />
                  {xe > xn && <rect x={xn} y={y + 8} width={xe - xn} height={10} rx={3} className={`g-bar todo ${miss ? "miss" : ""}`} />}
                  <circle cx={xe} cy={y + 13} r={4} className={`g-end ${miss ? "miss" : ""}`} />
                </g>
              );
            })}
            {[{ d: asOf, l: "Today", c: "today", a: "end", dx: -4, dy: -24 }, { d: awardBy, l: "Must award", c: "award", a: "end", dx: -4, dy: -10 }, { d: fyEnd, l: "Funds expire", c: "expire", a: "start", dx: 4, dy: -24 }].map((m) => (
              <g key={m.l} className={`marker ${m.c}`}><line x1={x(m.d)} x2={x(m.d)} y1={top + m.dy - 10} y2={H - 24} /><text x={x(m.d) + m.dx} y={top + m.dy} textAnchor={m.a as "start" | "middle" | "end"}>{m.l} {shortDate(m.d)}</text></g>
            ))}
          </svg>
        )}
        {hover && (
          <div className="svg-tip" style={{ left: Math.min(width - 300, x(hover.forecast_award_date) + 12), top: top + hover.i * rowH + 26 }}>
            <b>{hover.pr_id}</b> · {hover.acquisition_type}
            <div>{hover.title}</div>
            <div className="muted">{hover.status} for {hover.days_in_status} days · {money(hover.estimated_amount)}</div>
            <div>Forecast award {longDate(hover.forecast_award_date)} · funds expire {longDate(hover.expiration_date)}</div>
            {hover.at_risk_of_missing_expiration && <SevBadge severity="Critical" label="awards after the funds expire" />}
          </div>
        )}
      </div>
      <div className="legend-row">
        <span><span className="swatch" style={{ background: "var(--series-1)" }} />On track</span>
        <span><SevBadge severity="Critical" label="Forecast after expiration" /></span>
        <span className="muted">Solid = elapsed · light = remaining forecast PALT</span>
        {!showAll && (onlyMiss === "miss" ? misses.length : all.length) > 30 && <button className="btn ghost sm" onClick={() => setShowAll(true)}>Show all {(onlyMiss === "miss" ? misses.length : all.length)}</button>}
      </div>
    </Card>
  );
}

// ------------------------------------------------------------------------------------- pipeline
function Pipeline({ d, type }: { d: any; type: string }) {
  const { openLine } = useApp();
  const open = (d.open as any[]).filter((p) => !type || p.acquisition_type === type);
  const stages = STAGES.map((s) => {
    const ps = open.filter((p) => p.status === s);
    return { stage: s, value: ps.reduce((a, p) => a + Number(p.estimated_amount), 0), prs: ps.length };
  });
  return (
    <div className="stack">
      <div className="grid cols-3-2">
        <Card title="Open pipeline by stage" hint={`Dollar value of open procurement requests${type ? ` (${type})` : ""}`}>
          <ResponsiveContainer width="100%" height={230}>
            <BarChart data={stages} layout="vertical" margin={{ left: 8, right: 56 }}>
              <CartesianGrid stroke="var(--grid)" horizontal={false} />
              <XAxis type="number" {...axisProps} tickFormatter={(v) => money(v, 0)} />
              <YAxis type="category" dataKey="stage" {...axisProps} width={116} axisLine={false} />
              <Tooltip content={<ChartTip format={(v: number, p: any) => `${money(v)} · ${p.payload.prs} requests`} />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
              <Bar dataKey="value" name="Open value" fill="var(--series-1)" radius={[0, 4, 4, 0]} barSize={18}
                   label={{ position: "right", fontSize: 11, fill: "var(--text-secondary)", formatter: (v: number) => money(v, 0) }} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Procurement administrative lead time" hint="Submission to award, historical awards">
          <table>
            <thead><tr><th>Acquisition type</th><th className="num">Awards</th><th className="num">Median days</th><th className="num">p80 days</th></tr></thead>
            <tbody>{d.palt.map((p: any) => (
              <tr key={p.acquisition_type} className={type === p.acquisition_type ? "row-on" : ""}><td>{p.acquisition_type}</td><td className="num">{p.awards}</td>
                <td className="num">{Math.round(p.median_palt_days)}</td><td className="num">{Math.round(p.p80_palt_days)}</td></tr>))}
            </tbody>
          </table>
        </Card>
      </div>
      <Card title="Open procurement requests" hint="Requests forecast to award after their funds expire are listed first" className="flush">
        <div className="table-wrap">
          <table className="sticky">
            <thead><tr><th>Request</th><th>Budget line</th><th>Type / vehicle</th><th>Status</th><th className="num">Days in status</th><th className="num">Amount</th><th>Forecast award</th><th>Funds expire</th></tr></thead>
            <tbody>{open.map((p) => (
              <tr key={p.pr_id} className="clickable" onClick={() => openLine(p.line_id, "procurement")}>
                <td><b>{p.pr_id}</b><div className="small muted">{p.title}</div></td>
                <td className="small">{p.ppa_name}<div className="muted">{p.office_code}</div></td>
                <td className="small">{p.acquisition_type}<div className="muted">{p.contract_vehicle}</div></td>
                <td className="small">{p.status}</td><td className="num">{p.days_in_status}</td>
                <td className="num">{money(p.estimated_amount)}</td>
                <td className="small">{longDate(p.forecast_award_date)}{p.at_risk_of_missing_expiration && <div><SevBadge severity="Critical" label="misses expiration" /></div>}</td>
                <td className="small">{longDate(p.expiration_date)}</td>
              </tr>))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

// ------------------------------------------------------------------------------------- packages
function Packages() {
  const { version, openLine } = useApp();
  const p = useApi("/packages", {}, [version]);
  if (!p.data) return <Skeleton h={300} />;
  const submittedLines = new Set(p.data.submitted.map((s: any) => s.line_id));
  return (
    <div className="stack">
      <Card title={`Submitted to acquisition (${p.data.submitted.length})`} hint="Written by the app to Lakebase and streamed to Unity Catalog" className="flush">
        {p.data.submitted.length === 0 ? <Empty>No packages submitted yet.</Empty> : (
          <div className="table-wrap"><table>
            <thead><tr><th>Request</th><th>Line</th><th>Type</th><th className="num">Amount</th><th>Status</th><th>Submitted</th></tr></thead>
            <tbody>{p.data.submitted.map((s: any) => (
              <tr key={s.package_id} className="clickable" onClick={() => openLine(s.line_id, "package")}>
                <td><b>{s.package_id}</b><div className="small muted">{s.title}</div></td><td className="small">{s.line_id}</td>
                <td className="small">{s.acquisition_type}<div className="muted">{s.contract_number}</div></td><td className="num">{money(s.amount)}</td>
                <td className="small">{s.status}<div className="muted">{s.source}</div></td>
                <td className="small">{person(s.created_by)}<div className="muted">{ago(s.created_at)}</div></td>
              </tr>))}</tbody>
          </table></div>
        )}
      </Card>
      <Card title={`AI package drafts (${p.data.ai_drafts.length})`} hint="Drafted in batch by ai_query and validated against PALT, active contracts, projected lapse and contract value" className="flush">
        <div className="table-wrap"><table>
          <thead><tr><th>Draft</th><th>Type / contract</th><th className="num">Amount</th><th>Validation</th><th></th></tr></thead>
          <tbody>{p.data.ai_drafts.map((a: any) => (
            <tr key={a.package_id} className="clickable" onClick={() => openLine(a.line_id, "package")}>
              <td><b>{a.title}</b><div className="small muted">{a.line_id} · {a.office_code}</div></td>
              <td className="small">{a.recommended_acquisition_type}<div className="muted">{a.contract_number}</div></td>
              <td className="num">{money(a.amount)}</td>
              <td className="small">{asList(a.validation_issues).length ? <span className="warn-text">{asList(a.validation_issues).join("; ")}</span> : <span className="ok-text">passes</span>}</td>
              <td className="small">{submittedLines.has(a.line_id) ? <span className="status-pill approved">submitted</span> : <span className="status-pill pending">ready</span>}</td>
            </tr>))}</tbody>
        </table></div>
      </Card>
    </div>
  );
}
