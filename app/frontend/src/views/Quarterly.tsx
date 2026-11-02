import { CircleCheck, ShieldCheck, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ago, asList, money, pct, person, post, useApi } from "../api";
import { useApp } from "../app-context";
import { axisProps, Card, ChartTip, Empty, Modal, Skeleton } from "../components/ui";

const DECISIONS = ["Approved", "Approved with conditions", "Returned"] as const;

export default function Quarterly() {
  const { version, filters, changed, toast } = useApp();
  const d = useApi("/quarterly", {}, [version]);
  const [office, setOffice] = useState("");
  const [signing, setSigning] = useState(false);
  useEffect(() => { if (!office && d.data?.reviews.length) setOffice(d.data.reviews[0].office_code); }, [d.data, office]);
  if (!d.data) return <Skeleton h={480} />;

  const asOf = filters.as_of_date ?? "";
  const fy = asOf ? Number(asOf.slice(0, 4)) + (Number(asOf.slice(5, 7)) >= 10 ? 1 : 0) : 0;
  const quarter = asOf ? Math.floor(((Number(asOf.slice(5, 7)) + 2) % 12) / 3) + 1 : 0;
  const review = { fy: quarter > 1 ? fy : fy - 1, q: quarter > 1 ? quarter - 1 : 4 };
  const signed = (o: string) => d.data.signoffs.find((s: any) => s.office_code === o && s.fiscal_year === review.fy && s.fiscal_quarter === review.q);
  const r = d.data.reviews.find((x: any) => x.office_code === office);
  const quarters = d.data.quarters.filter((x: any) => x.office_code === office).map((x: any) => ({
    quarter: `Q${x.fiscal_quarter}`, Plan: Number(x.planned_obligations), Obligated: Number(x.actual_obligations),
  }));
  const done = quarters.filter((x: any) => Number(x.quarter.slice(1)) <= review.q);
  const att = done.reduce((a: number, x: any) => a + x.Obligated, 0) / Math.max(1, done.reduce((a: number, x: any) => a + x.Plan, 0));
  const history = d.data.signoffs.filter((s: any) => s.office_code === office);

  return (
    <div className="stack">
      <div className="page-head">
        <div>
          <h1>Quarterly budget-performance review</h1>
          <p className="muted">FY{review.fy} Q{review.q} review by program office: obligations against the approved spend plan, an AI-drafted narrative checked against the governed numbers, and the CFO's sign-off.</p>
        </div>
      </div>
      <div className="office-tabs">
        {d.data.reviews.map((x: any) => (
          <button key={x.office_code} className={x.office_code === office ? "active" : ""} onClick={() => setOffice(x.office_code)}>
            {x.office_code}{signed(x.office_code) ? <CircleCheck size={14} className="ok-text" /> : <span className="dot-pending" />}
          </button>
        ))}
      </div>
      <div className="grid cols-3-2">
        <Card title={`${office}: obligations vs approved plan by quarter`} hint={`Completed quarters through Q${review.q}: ${pct(att, 0)} of plan obligated`}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={quarters} barGap={3} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="var(--grid)" vertical={false} />
              <XAxis dataKey="quarter" {...axisProps} />
              <YAxis {...axisProps} tickFormatter={(v) => money(v, 0)} width={60} axisLine={false} />
              <Tooltip content={<ChartTip format={(v: number) => money(v)} />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="Plan" name="Approved plan" fill="var(--series-2)" radius={[4, 4, 0, 0]} barSize={26} />
              <Bar dataKey="Obligated" fill="var(--series-1)" radius={[4, 4, 0, 0]} barSize={26} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Review narrative" actions={signed(office)
          ? <span className="status-pill approved"><CircleCheck size={12} /> {signed(office).decision}</span>
          : <button className="btn primary" onClick={() => setSigning(true)}>Sign off Q{review.q}</button>}>
          {r ? (
            <div className="ai-block flat">
              <div className="ai-tag"><Sparkles size={13} /> AI-drafted for the program office ·
                {r.grounding_passed ? <span className="ok-text"> <ShieldCheck size={12} /> grounded</span> : <span className="warn-text"> a figure was not found in the facts; analyst review needed</span>}</div>
              <p>{r.performance_summary}</p>
              <b className="small">Key risks</b><ul className="small">{asList(r.key_risks).map((k) => <li key={k}>{k}</li>)}</ul>
              <b className="small">Decisions requested</b><ul className="small">{asList(r.decisions_requested).map((k) => <li key={k}>{k}</li>)}</ul>
            </div>
          ) : <Empty>No narrative for this office.</Empty>}
        </Card>
      </div>
      <Card title="Sign-off history">
        {history.length === 0 ? <Empty>No sign-offs for {office} yet.</Empty> : (
          <table>
            <thead><tr><th>Quarter</th><th>Decision</th><th>Signed by</th><th>Comment</th></tr></thead>
            <tbody>{history.map((s: any) => (
              <tr key={s.signoff_id}><td>FY{s.fiscal_year} Q{s.fiscal_quarter}</td><td>{s.decision}</td>
                <td className="small">{person(s.signed_by)}<div className="muted">{ago(s.signed_at)}</div></td><td className="small">{s.comment}</td></tr>))}
            </tbody>
          </table>
        )}
      </Card>
      {signing && <SignModal office={office} fy={review.fy} q={review.q} onClose={() => setSigning(false)}
                             onDone={(dec) => { setSigning(false); toast(`${office} FY${review.fy} Q${review.q} review: ${dec.toLowerCase()}`); changed(); }} />}
    </div>
  );
}

function SignModal({ office, fy, q, onClose, onDone }: { office: string; fy: number; q: number; onClose: () => void; onDone: (d: string) => void }) {
  const [decision, setDecision] = useState<(typeof DECISIONS)[number]>("Approved");
  const [comment, setComment] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async () => {
    setBusy(true); setErr("");
    try { await post(`/quarterly/${office}/signoff`, { fiscal_year: fy, fiscal_quarter: q, decision, comment: comment || undefined }); onDone(decision); }
    catch (e: any) { setErr(e.message); setBusy(false); }
  };
  return (
    <Modal title={`Sign off ${office} · FY${fy} Q${q}`} onClose={onClose}
           footer={<><button className="btn ghost" onClick={onClose}>Cancel</button><button className="btn primary" disabled={busy} onClick={submit}>{busy ? "Saving…" : "Record decision"}</button></>}>
      <div className="radio-group">
        {DECISIONS.map((x) => (
          <label key={x} className={decision === x ? "on" : ""}><input type="radio" checked={decision === x} onChange={() => setDecision(x)} />{x}</label>
        ))}
      </div>
      <label className="field">Comment for the record<textarea rows={4} value={comment} onChange={(e) => setComment(e.target.value)}
        placeholder={decision === "Returned" ? "What the office needs to revise" : "Conditions or follow-ups"} /></label>
      {err && <div className="error">{err}</div>}
    </Modal>
  );
}
