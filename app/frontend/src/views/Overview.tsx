import { useEffect, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { get, money, pct } from "../api";

const axis = { stroke: "var(--axis)", tick: { fill: "var(--text-muted)", fontSize: 11 } };

function Tile({ label, value, foot }: { label: string; value: string; foot?: string }) {
  return (
    <div className="card tile">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      {foot && <div className="foot">{foot}</div>}
    </div>
  );
}

export default function Overview({ office }: { office?: string }) {
  const [data, setData] = useState<any>(null);
  const [burn, setBurn] = useState<any[]>([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    setData(null);
    get("/overview", { office }).then(setData).catch((e) => setErr(e.message));
    get("/burn", { office }).then(setBurn).catch(() => setBurn([]));
  }, [office]);

  if (err) return <div className="error">{err}</div>;
  if (!data) return <div className="muted">Loading…</div>;
  const k = data.kpis;
  const burnRows = burn.map((r) => ({
    month: String(r.month).slice(0, 7),
    "Planned obligations": r.cumulative_planned_obligations,
    "Actual obligations": r.is_actualized ? r.cumulative_actual_obligations : null,
  }));
  const offices = data.by_office.map((o: any) => ({ office: o.office_code, burn: Number(o.burn_rate_vs_plan) * 100 }));

  return (
    <div className="grid">
      <div className="grid kpis">
        <Tile label="Total budget (current funds)" value={money(k.total_budget)} foot={`${k.budget_lines} budget lines`} />
        <Tile label="Planned obligations to date" value={money(k.planned_obligations_to_date)} foot="approved baseline spend plan" />
        <Tile label="Obligated to date" value={money(k.obligated_to_date)} foot={`obligation rate ${pct(k.obligation_rate)}`} />
        <Tile label="Burn rate vs plan" value={pct(k.burn_rate_vs_plan, 0)} foot="obligated ÷ planned to date" />
        <Tile label="Expended / invoiced to date" value={money(k.expended_to_date)} foot={`expenditure rate ${pct(k.expenditure_rate)}`} />
        <Tile label="Remaining (unobligated) balance" value={money(k.unobligated_balance)} foot={`${money(k.committed_not_obligated)} committed, not obligated`} />
        <Tile label="Unobligated, expiring ≤ 90 days" value={money(k.unobligated_expiring_90d)} foot="balances approaching deadline" />
        <Tile label="Projected year-end lapse" value={money(k.projected_lapse)} foot={`${k.high_risk_lines} high/critical-risk lines (ML forecast)`} />
      </div>

      <div className="grid two">
        <div className="card">
          <h2>Cumulative obligations vs spend plan</h2>
          <p className="hint">Funds expiring at the end of the current fiscal year · monthly, cumulative</p>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={burnRows} margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
              <CartesianGrid stroke="var(--grid)" vertical={false} />
              <XAxis dataKey="month" {...axis} />
              <YAxis {...axis} tickFormatter={(v) => money(v, 0)} width={64} />
              <Tooltip formatter={(v: any) => money(v)} contentStyle={{ fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line type="monotone" dataKey="Planned obligations" stroke="var(--series-2)" strokeWidth={2} strokeDasharray="5 4" dot={false} />
              <Line type="monotone" dataKey="Actual obligations" stroke="var(--series-1)" strokeWidth={2} dot={false} connectNulls={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h2>Burn rate vs plan by office</h2>
          <p className="hint">Obligated ÷ planned to date, current funds · 100% = on plan</p>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={offices} layout="vertical" margin={{ top: 4, right: 24, left: 4, bottom: 0 }}>
              <CartesianGrid stroke="var(--grid)" horizontal={false} />
              <XAxis type="number" {...axis} tickFormatter={(v) => `${v}%`} domain={[0, "dataMax + 10"]} />
              <YAxis type="category" dataKey="office" {...axis} width={48} />
              <Tooltip formatter={(v: any) => `${Number(v).toFixed(1)}%`} contentStyle={{ fontSize: 12 }} />
              <ReferenceLine x={100} stroke="var(--text-secondary)" strokeDasharray="3 3" />
              <Bar dataKey="burn" name="Burn rate vs plan" fill="var(--series-1)" radius={[0, 4, 4, 0]} barSize={16}
                   label={{ position: "right", fontSize: 11, fill: "var(--text-secondary)", formatter: (v: number) => `${v.toFixed(0)}%` }} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid two">
        <div className="card">
          <h2>Funding by program office</h2>
          <table>
            <thead><tr><th>Office</th><th className="num">Budget</th><th className="num">Obligated</th><th className="num">Expended</th><th className="num">Remaining</th><th className="num">Obligation rate</th><th className="num">vs plan</th></tr></thead>
            <tbody>
              {data.by_office.map((o: any) => (
                <tr key={o.office_code}>
                  <td>{o.office_name}</td>
                  <td className="num">{money(o.total_budget)}</td><td className="num">{money(o.obligated)}</td>
                  <td className="num">{money(o.expended)}</td><td className="num">{money(o.unobligated)}</td>
                  <td className="num">{pct(o.obligation_rate)}</td><td className="num">{pct(o.burn_rate_vs_plan, 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="card">
          <h2>Funding by appropriation</h2>
          <table>
            <thead><tr><th>Appropriation</th><th className="num">Budget</th><th className="num">Remaining</th><th className="num">Obligation rate</th></tr></thead>
            <tbody>
              {data.by_appropriation.map((a: any) => (
                <tr key={a.appropriation_name + a.fund_type}>
                  <td>{a.appropriation_name} <span className="pill">{a.fund_type}</span></td>
                  <td className="num">{money(a.total_budget)}</td><td className="num">{money(a.unobligated)}</td>
                  <td className="num">{pct(a.obligation_rate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
