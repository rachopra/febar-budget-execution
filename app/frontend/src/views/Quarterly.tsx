import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { asList, get, money, post } from "../api";

const axis = { stroke: "var(--axis)", tick: { fill: "var(--text-muted)", fontSize: 11 } };

export default function Quarterly({ asOf }: { asOf?: string }) {
  const [d, setD] = useState<any>(null);
  const [office, setOffice] = useState("");
  const [busy, setBusy] = useState(false);
  const load = () => get("/quarterly").then((x) => { setD(x); if (!office && x.reviews.length) setOffice(x.reviews[0].office_code); });
  useEffect(() => { load(); }, []);
  if (!d) return <div className="muted">Loading…</div>;

  const fy = asOf ? Number(asOf.slice(0, 4)) + (Number(asOf.slice(5, 7)) >= 10 ? 1 : 0) : 0;
  const quarter = asOf ? Math.floor(((Number(asOf.slice(5, 7)) + 2) % 12) / 3) + 1 : 0;
  const review = d.reviews.find((r: any) => r.office_code === office);
  const q = d.quarters.filter((r: any) => r.office_code === office).map((r: any) => ({
    quarter: `Q${r.fiscal_quarter}`, Planned: Number(r.planned_obligations), Actual: Number(r.actual_obligations),
  }));
  const signoffs = d.signoffs.filter((s: any) => s.office_code === office);

  const sign = async (decision: string) => {
    const comment = prompt(`${decision}: comment for the record (optional)`) ?? undefined;
    setBusy(true);
    await post(`/quarterly/${office}/signoff`, { fiscal_year: fy, fiscal_quarter: quarter - 1 || 4, decision, comment });
    setBusy(false);
    load();
  };

  return (
    <div className="grid">
      <div className="filters">
        Program office
        <select value={office} onChange={(e) => setOffice(e.target.value)}>
          {d.reviews.map((r: any) => <option key={r.office_code}>{r.office_code}</option>)}
        </select>
        <span className="muted">FY{fy} quarterly budget-performance review</span>
      </div>
      <div className="grid two">
        <div className="card">
          <h2>Obligations vs plan by fiscal quarter</h2>
          <p className="hint">All current lines for the office, FY{fy} activity</p>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={q} barGap={2}>
              <CartesianGrid stroke="var(--grid)" vertical={false} />
              <XAxis dataKey="quarter" {...axis} /><YAxis {...axis} tickFormatter={(v) => money(v, 0)} width={60} />
              <Tooltip formatter={(v: any) => money(v)} contentStyle={{ fontSize: 12 }} /><Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="Planned" fill="var(--series-2)" radius={[4, 4, 0, 0]} barSize={22} />
              <Bar dataKey="Actual" fill="var(--series-1)" radius={[4, 4, 0, 0]} barSize={22} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h2>Review narrative</h2>
          {review ? (
            <div className="ai">
              <div className="tag">AI-drafted for the program office · grounding {review.grounding_passed ? "passed" : "flagged"}</div>
              <p>{review.performance_summary}</p>
              <b className="small">Key risks</b><ul className="small">{asList(review.key_risks).map((k) => <li key={k}>{k}</li>)}</ul>
              <b className="small">Decisions requested</b><ul className="small">{asList(review.decisions_requested).map((k) => <li key={k}>{k}</li>)}</ul>
            </div>
          ) : <div className="muted">No narrative for this office.</div>}
          <div style={{ display: "flex", gap: 8 }}>
            <button className="primary" disabled={busy} onClick={() => sign("Approved")}>Approve</button>
            <button className="ghost" disabled={busy} onClick={() => sign("Approved with conditions")}>Approve with conditions</button>
            <button className="ghost" disabled={busy} onClick={() => sign("Returned")}>Return</button>
          </div>
          {signoffs.length > 0 && (
            <table style={{ marginTop: 12 }}>
              <thead><tr><th>Decision</th><th>By</th><th>Comment</th></tr></thead>
              <tbody>{signoffs.map((s: any) => <tr key={s.signoff_id}><td className="small">{s.decision}<div className="muted">FY{s.fiscal_year} Q{s.fiscal_quarter}</div></td><td className="small">{s.signed_by}<div className="muted">{String(s.signed_at).slice(0, 16)}</div></td><td className="small">{s.comment}</td></tr>)}</tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
