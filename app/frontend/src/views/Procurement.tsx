import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { get, money } from "../api";

const STAGES = ["Draft", "Submitted", "Funds Certified", "In Solicitation", "Under Evaluation"];
const axis = { stroke: "var(--axis)", tick: { fill: "var(--text-muted)", fontSize: 11 } };

export default function Procurement({ office }: { office?: string }) {
  const [d, setD] = useState<any>(null);
  useEffect(() => { setD(null); get("/procurement", { office }).then(setD); }, [office]);
  if (!d) return <div className="muted">Loading…</div>;

  const stages = STAGES.map((s) => {
    const r = d.by_stage.find((x: any) => x.status === s);
    return { stage: s, value: r ? Number(r.value) : 0, prs: r ? r.prs : 0 };
  });
  return (
    <div className="grid">
      <div className="grid two">
        <div className="card">
          <h2>Open procurement pipeline by stage</h2>
          <p className="hint">Dollar value of open procurement requests</p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={stages} layout="vertical" margin={{ left: 8, right: 40 }}>
              <CartesianGrid stroke="var(--grid)" horizontal={false} />
              <XAxis type="number" {...axis} tickFormatter={(v) => money(v, 0)} />
              <YAxis type="category" dataKey="stage" {...axis} width={110} />
              <Tooltip formatter={(v: any, _n, p: any) => [`${money(v)} (${p.payload.prs} PRs)`, "Open value"]} contentStyle={{ fontSize: 12 }} />
              <Bar dataKey="value" fill="var(--series-1)" radius={[0, 4, 4, 0]} barSize={16}
                   label={{ position: "right", fontSize: 11, fill: "var(--text-secondary)", formatter: (v: number) => money(v, 0) }} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h2>Procurement administrative lead time</h2>
          <p className="hint">Submission to award, historical awards</p>
          <table>
            <thead><tr><th>Acquisition type</th><th className="num">Awards</th><th className="num">Median days</th><th className="num">80th pct days</th></tr></thead>
            <tbody>{d.palt.map((p: any) => (
              <tr key={p.acquisition_type}><td>{p.acquisition_type}</td><td className="num">{p.awards}</td>
                <td className="num">{Math.round(p.median_palt_days)}</td><td className="num">{Math.round(p.p80_palt_days)}</td></tr>))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="card">
        <h2>Open procurement requests</h2>
        <p className="hint">Forecast award = submission + median PALT for the acquisition type. Requests forecast to award after their funds expire are listed first.</p>
        <table>
          <thead><tr><th>PR</th><th>Budget line</th><th>Type / vehicle</th><th>Status</th><th className="num">Days in status</th><th className="num">Amount</th><th>Forecast award</th><th>Funds expire</th></tr></thead>
          <tbody>{d.open.map((p: any) => (
            <tr key={p.pr_id}>
              <td>{p.pr_id}<div className="small muted">{p.title}</div></td>
              <td className="small">{p.ppa_name}<div className="muted">{p.office_code}</div></td>
              <td className="small">{p.acquisition_type}<div className="muted">{p.contract_vehicle}</div></td>
              <td className="small">{p.status}</td><td className="num">{p.days_in_status}</td>
              <td className="num">{money(p.estimated_amount)}</td>
              <td className="small">{String(p.forecast_award_date)}{p.at_risk_of_missing_expiration && <div><span className="sev Critical"><span className="dot">⛔</span>misses expiration</span></div>}</td>
              <td className="small">{String(p.expiration_date)}</td>
            </tr>))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
