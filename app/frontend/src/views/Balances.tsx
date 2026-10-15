import { useEffect, useState } from "react";
import { asList, get, money, pct, SEVERITY_ICON } from "../api";
import LineDetail from "./LineDetail";

const TIER_SEV: Record<string, string> = { Critical: "Critical", High: "High", Moderate: "Medium", Low: "Low" };

export default function Balances({ office }: { office?: string }) {
  const [rows, setRows] = useState<any[] | null>(null);
  const [maxDays, setMaxDays] = useState("120");
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    setRows(null);
    get("/lines", { office, max_days: maxDays }).then(setRows);
  }, [office, maxDays]);

  return (
    <div className="card">
      <h2>Unobligated balances approaching expiration</h2>
      <p className="hint">Current budget lines ranked by ML-projected year-end lapse. Select a line for the AI briefing, open procurements and package initiation.</p>
      <div className="filters">
        Expiring within
        <select value={maxDays} onChange={(e) => setMaxDays(e.target.value)}>
          <option value="90">90 days</option><option value="120">120 days</option>
          <option value="400">13 months</option><option value="1000">any time</option>
        </select>
      </div>
      {!rows ? <div className="muted">Loading…</div> : (
        <table>
          <thead><tr>
            <th>Budget line</th><th>Fund</th><th className="num">Days left</th><th className="num">Budget</th>
            <th className="num">Obligated</th><th className="num">Uncommitted</th><th className="num">vs plan</th>
            <th className="num">Projected lapse</th><th>Lapse risk</th><th>AI briefing</th>
          </tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.line_id} className="clickable" onClick={() => setOpen(r.line_id)}>
                <td><b>{r.ppa_name}</b><div className="small muted">{r.line_id}</div></td>
                <td className="small">{r.tas}<div className="muted">{r.fund_type}</div></td>
                <td className="num">{r.days_to_expiration}</td>
                <td className="num">{money(r.total_budget)}</td>
                <td className="num">{pct(r.obligation_rate, 0)}</td>
                <td className="num">{money(r.uncommitted_balance)}</td>
                <td className="num">{pct(r.burn_rate_vs_plan, 0)}</td>
                <td className="num">{r.projected_lapse_amount == null ? "-" : money(r.projected_lapse_amount)}<div className="small muted">{r.predicted_lapse_rate == null ? "" : pct(r.predicted_lapse_rate)}</div></td>
                <td>
                  {TIER_SEV[r.risk_tier] ? <span className={`sev ${TIER_SEV[r.risk_tier]}`}><span className="dot">{SEVERITY_ICON[TIER_SEV[r.risk_tier]]}</span>{r.risk_tier}</span>
                    : <span className="small muted">{r.risk_tier || "-"}</span>}
                  {asList(r.top_risk_drivers).length > 0 && <ul className="drivers">{asList(r.top_risk_drivers).slice(0, 2).map((d) => <li key={d}>{d}</li>)}</ul>}
                </td>
                <td className="small">{r.briefing_headline || <span className="muted">-</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {open && <LineDetail lineId={open} onClose={() => setOpen(null)} />}
    </div>
  );
}
