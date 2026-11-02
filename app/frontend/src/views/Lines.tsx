import { ArrowDown, ArrowUp, LayoutGrid, Search, Table2 } from "lucide-react";
import { useMemo, useState } from "react";
import { ResponsiveContainer, Tooltip, Treemap } from "recharts";
import { asList, money, pct, TIER_SEVERITY, useApi } from "../api";
import { useApp } from "../app-context";
import { Card, Segmented, Skeleton, TierBadge } from "../components/ui";

const COLS: { key: string; label: string; num?: boolean }[] = [
  { key: "ppa_name", label: "Budget line" },
  { key: "tas", label: "Fund" },
  { key: "days_to_expiration", label: "Days left", num: true },
  { key: "total_budget", label: "Budget", num: true },
  { key: "obligation_rate", label: "Obligated", num: true },
  { key: "burn_rate_vs_plan", label: "vs plan", num: true },
  { key: "uncommitted_balance", label: "Uncommitted", num: true },
  { key: "projected_lapse_amount", label: "Projected lapse", num: true },
  { key: "risk_tier", label: "Lapse risk" },
];
const TIER_RANK: Record<string, number> = { Critical: 0, High: 1, Moderate: 2, Low: 3 };
const STATUS = ["All", "Behind Plan", "On Plan", "Ahead of Plan", "No Plan"] as const;

export default function Lines() {
  const { office, version, openLine } = useApp();
  const [maxDays, setMaxDays] = useState("1000");
  const lines = useApi<any[]>("/lines", { office, max_days: maxDays }, [version]);
  const [view, setView] = useState<"table" | "map">("table");
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<(typeof STATUS)[number]>("All");
  const [sort, setSort] = useState<{ key: string; dir: 1 | -1 }>({ key: "projected_lapse_amount", dir: -1 });

  const rows = useMemo(() => {
    const t = q.trim().toLowerCase();
    const r = (lines.data ?? []).filter((l) =>
      (!t || `${l.ppa_name} ${l.line_id} ${l.tas} ${l.office_code}`.toLowerCase().includes(t))
      && (status === "All" || l.execution_status === status));
    const val = (l: any) => sort.key === "risk_tier" ? TIER_RANK[l.risk_tier] ?? 9 : l[sort.key];
    return [...r].sort((a, b) => {
      const x = val(a), y = val(b);
      if (x === null || x === undefined) return 1;
      if (y === null || y === undefined) return -1;
      return (typeof x === "string" ? x.localeCompare(y) : Number(x) - Number(y)) * sort.dir;
    });
  }, [lines.data, q, status, sort]);

  const total = rows.reduce((a, l) => ({ budget: a.budget + Number(l.total_budget), unobl: a.unobl + Number(l.unobligated_balance), lapse: a.lapse + Number(l.projected_lapse_amount || 0) }), { budget: 0, unobl: 0, lapse: 0 });

  return (
    <div className="stack">
      <div className="page-head">
        <div>
          <h1>Budget lines</h1>
          <p className="muted">Every current line (PPA × budget fiscal year) with execution, balances and the ML lapse forecast. Select a line for its briefing, procurements, alerts, package and notes.</p>
        </div>
      </div>
      <div className="toolbar">
        <div className="search-box"><Search size={15} /><input placeholder="Filter by name, line, fund or office" value={q} onChange={(e) => setQ(e.target.value)} /></div>
        <select value={maxDays} onChange={(e) => setMaxDays(e.target.value)} aria-label="Expiring within">
          <option value="90">Expiring ≤ 90 days</option><option value="120">Expiring ≤ 120 days</option>
          <option value="400">Expiring ≤ 13 months</option><option value="1000">Any expiration</option>
        </select>
        <Segmented value={status} onChange={setStatus} options={STATUS.map((s) => ({ id: s, label: s === "All" ? "All statuses" : s }))} />
        <div className="spacer" />
        <Segmented value={view} onChange={setView} options={[{ id: "table", label: <><Table2 size={14} /> Table</> }, { id: "map", label: <><LayoutGrid size={14} /> Map</> }]} />
      </div>
      <div className="summary-strip">
        <span><b>{rows.length}</b> lines</span><span><b>{money(total.budget)}</b> budget</span>
        <span><b>{money(total.unobl)}</b> unobligated</span><span><b>{money(total.lapse)}</b> projected lapse</span>
      </div>
      {!lines.data ? <Skeleton h={480} /> : view === "table" ? (
        <Card className="flush">
          <div className="table-wrap">
            <table className="sticky">
              <thead><tr>
                {COLS.map((c) => (
                  <th key={c.key} className={`${c.num ? "num" : ""} sortable`} onClick={() => setSort((s) => ({ key: c.key, dir: s.key === c.key ? (-s.dir as 1 | -1) : c.num ? -1 : 1 }))}>
                    {c.label}{sort.key === c.key && (sort.dir === 1 ? <ArrowUp size={12} /> : <ArrowDown size={12} />)}
                  </th>
                ))}
                <th>AI briefing</th>
              </tr></thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.line_id} className="clickable" onClick={() => openLine(r.line_id)}>
                    <td><b>{r.ppa_name}</b><div className="small muted">{r.line_id} · {r.office_code}</div></td>
                    <td className="small nowrap">{r.tas}<div className="muted">{r.fund_type}</div></td>
                    <td className="num">{r.days_to_expiration}</td>
                    <td className="num">{money(r.total_budget)}</td>
                    <td className="num">{pct(r.obligation_rate, 0)}</td>
                    <td className="num"><span className={Number(r.burn_rate_vs_plan) < 0.85 ? "warn-text" : ""}>{pct(r.burn_rate_vs_plan, 0)}</span></td>
                    <td className="num">{money(r.uncommitted_balance)}</td>
                    <td className="num">{r.projected_lapse_amount == null ? <span className="muted">-</span> : <b>{money(r.projected_lapse_amount)}</b>}
                      <div className="small muted">{r.predicted_lapse_rate == null ? "" : pct(r.predicted_lapse_rate)}</div></td>
                    <td><TierBadge tier={r.risk_tier} />
                      {asList(r.top_risk_drivers).length > 0 && <div className="tiny muted clamp1 driver-cell">{asList(r.top_risk_drivers)[0]}</div>}</td>
                    <td className="small"><div className="clamp2">{r.briefing_headline || <span className="muted">-</span>}</div></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : <LinesMap rows={rows} onPick={openLine} />}
    </div>
  );
}

const TIER_FILL: Record<string, string> = { Critical: "var(--critical)", High: "var(--serious)", Medium: "var(--warning)", Low: "var(--good)" };

function LinesMap({ rows, onPick }: { rows: any[]; onPick: (id: string) => void }) {
  const data = useMemo(() => {
    const by: Record<string, any[]> = {};
    for (const r of rows) if (Number(r.unobligated_balance) > 0) (by[r.office_code] ??= []).push(r);
    return Object.entries(by).map(([o, ls]) => ({
      name: o,
      children: ls.map((l) => ({ name: l.ppa_name, size: Number(l.unobligated_balance), line_id: l.line_id, tier: l.risk_tier, office: o,
                                 sev: TIER_SEVERITY[l.risk_tier] ?? "", lapse: l.projected_lapse_amount, days: l.days_to_expiration })),
    }));
  }, [rows]);
  return (
    <Card title="Where the unobligated money sits" hint="Tile size = unobligated balance, grouped by office; color = ML lapse-risk tier (gray = outside the forecast window). Select a tile to open the line.">
      <ResponsiveContainer width="100%" height={540}>
        <Treemap data={data} dataKey="size" stroke="var(--surface-1)" isAnimationActive={false}
                 content={<Tile />} onClick={(n: any) => n?.line_id && onPick(n.line_id)}>
          <Tooltip content={({ payload }: any) => {
            const p = payload?.[0]?.payload;
            if (!p?.line_id) return null;
            return (
              <div className="chart-tip">
                <div className="chart-tip-label">{p.name}</div>
                <div className="chart-tip-row"><span>{p.line_id}</span></div>
                <div className="chart-tip-row"><span>Unobligated</span><b>{money(p.size)}</b></div>
                <div className="chart-tip-row"><span>Projected lapse</span><b>{p.lapse == null ? "-" : money(p.lapse)}</b></div>
                <div className="chart-tip-row"><span>Risk tier</span><b>{p.tier || "not scored"}</b></div>
                <div className="chart-tip-row"><span>Days left</span><b>{p.days}</b></div>
              </div>
            );
          }} />
        </Treemap>
      </ResponsiveContainer>
      <div className="legend-row">
        {["Critical", "High", "Moderate", "Low"].map((t) => <span key={t}><TierBadge tier={t} /></span>)}
        <span><span className="swatch" style={{ background: "var(--neutral-seg)" }} />Outside forecast window</span>
      </div>
    </Card>
  );
}

function Tile(props: any) {
  const { x, y, width, height, depth, name, sev, size, line_id, office } = props;
  if (depth === 1) {
    return (
      <rect x={x} y={y} width={width} height={height} fill="none" stroke="var(--page)" strokeWidth={3} />
    );
  }
  if (depth !== 2) return null;
  const fill = TIER_FILL[sev] ?? "var(--neutral-seg)";
  const ink = sev === "Medium" ? "#0b0b0b" : "#ffffff";
  const clip = `tile-${String(line_id).replace(/[^a-zA-Z0-9-]/g, "")}`;
  return (
    <g style={{ cursor: line_id ? "pointer" : undefined }}>
      <clipPath id={clip}><rect x={x + 1} y={y + 1} width={Math.max(0, width - 10)} height={Math.max(0, height - 2)} /></clipPath>
      <rect x={x + 1} y={y + 1} width={Math.max(0, width - 2)} height={Math.max(0, height - 2)} rx={4} fill={fill} fillOpacity={0.88} stroke="none" />
      {width > 70 && height > 40 && (
        <g clipPath={`url(#${clip})`} stroke="none">
          <text x={x + 8} y={y + 20} fill={ink} fontSize={12} fontWeight={600}>{name}</text>
          <text x={x + 8} y={y + 36} fill={ink} fontSize={11} opacity={0.9}>{office} · {money(size)} unobligated</text>
        </g>
      )}
    </g>
  );
}
