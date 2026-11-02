import { BarChart3, Plus, Send, Sparkles, Table2, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { money, pct, post } from "../api";
import { useApp } from "../app-context";
import { axisProps, ChartTip, useEscape } from "./ui";

const SUGGESTED = [
  "Which offices are furthest behind their spend plan?",
  "What is the projected lapse by office?",
  "Which budget lines have more than $1M unobligated and expire in the next 90 days?",
  "Which open procurements will miss their fund expiration?",
  "Show critical and high financial risk alerts",
];

type Turn = { q: string; a?: any; error?: string; view?: "chart" | "table" };

const isNum = (v: unknown) => v !== null && v !== "" && !Number.isNaN(Number(v));

const MONEY_COL = /(lapse|amount|budget|obligat|balance|value|spend|expend|unobl|commit|dollar|usd|total)/;

function formatFor(col: string, values: number[]) {
  const c = col.toLowerCase();
  const max = Math.max(...values.map(Math.abs));
  if (/(_m$|_mm$|million)/.test(c)) return (v: number) => `$${v.toFixed(1)}M`;
  if (/(rate|pct|percent|ratio|burn)/.test(c) && max <= 2) return (v: number) => pct(v);
  if (MONEY_COL.test(c)) return (v: number) => money(v);
  return (v: number) => new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(v);
}

function chartable(a: any) {
  if (!a?.columns?.length || a.rows.length < 2 || a.rows.length > 25) return null;
  const numIdx = a.columns.map((_: string, i: number) => a.rows.every((r: any[]) => isNum(r[i])));
  const label = numIdx.indexOf(false);
  const nums = numIdx.map((n: boolean, i: number) => (n ? i : -1)).filter((i: number) => i >= 0);
  if (label < 0 || !nums.length) return null;
  // prefer a dollar / lapse column over counts, else the column with the largest values
  const value = nums.find((i: number) => MONEY_COL.test(a.columns[i].toLowerCase()))
    ?? nums.reduce((b: number, i: number) => (Math.max(...a.rows.map((r: any[]) => Math.abs(Number(r[i])))) > Math.max(...a.rows.map((r: any[]) => Math.abs(Number(r[b])))) ? i : b), nums[0]);
  const data = a.rows.map((r: any[]) => ({ label: String(r[label]), value: Number(r[value]) }));
  return { data, col: a.columns[value], fmt: formatFor(a.columns[value], data.map((d: any) => d.value)) };
}

/** Genie answers use light markdown: paragraphs, "- " bullets and **bold**. */
function Markdown({ text }: { text: string }) {
  const inline = (s: string) => s.split(/(\*\*[^*]+\*\*)/g).map((p, i) => p.startsWith("**") && p.endsWith("**") ? <b key={i}>{p.slice(2, -2)}</b> : p);
  const blocks: JSX.Element[] = [];
  let items: string[] = [];
  const flush = () => { if (items.length) blocks.push(<ul key={blocks.length}>{items.map((x, i) => <li key={i}>{inline(x)}</li>)}</ul>); items = []; };
  for (const line of text.replace(/ - (?=\*\*)/g, "\n- ").split("\n")) {
    const m = line.match(/^\s*[-*•]\s+(.*)/);
    if (m) { items.push(m[1]); continue; }
    flush();
    if (line.trim()) blocks.push(<p key={blocks.length}>{inline(line)}</p>);
  }
  flush();
  return <>{blocks}</>;
}

export default function GeniePanel() {
  const { genie, closeGenie } = useApp();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [q, setQ] = useState("");
  const [conv, setConv] = useState<string | undefined>();
  const [busy, setBusy] = useState(false);
  const end = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLInputElement>(null);
  useEscape(() => genie.open && closeGenie());

  const ask = async (question: string) => {
    if (!question.trim() || busy) return;
    setQ(""); setBusy(true);
    setTurns((t) => [...t, { q: question }]);
    try {
      const a = await post("/genie", { question, conversation_id: conv });
      setConv(a.conversation_id);
      setTurns((t) => t.map((x, i) => (i === t.length - 1 ? { ...x, a, view: chartable(a) ? "chart" : "table" } : x)));
    } catch (e: any) {
      setTurns((t) => t.map((x, i) => (i === t.length - 1 ? { ...x, error: e.message } : x)));
    }
    setBusy(false);
  };

  useEffect(() => {
    if (genie.open) {
      if (genie.question) ask(genie.question);
      setTimeout(() => input.current?.focus(), 200);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [genie.nonce]);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [turns]);

  return (
    <aside className={`genie ${genie.open ? "open" : ""}`} aria-hidden={!genie.open}>
      <div className="genie-head">
        <div className="row-center gap"><span className="genie-mark"><Sparkles size={16} /></span>
          <div><b>Ask Genie</b><div className="tiny muted">Governed SQL over gold tables and the metric view · runs as you</div></div></div>
        <div className="row-center gap">
          {conv && <button className="icon-btn" title="New conversation" onClick={() => { setConv(undefined); setTurns([]); }}><Plus size={16} /></button>}
          <button className="icon-btn" onClick={closeGenie} aria-label="Close"><X size={18} /></button>
        </div>
      </div>
      <div className="genie-body">
        {turns.length === 0 && (
          <div className="genie-empty">
            <p className="muted">Ask about obligations, balances, lapse risk, alerts or procurements. Answers respect your Unity Catalog permissions.</p>
            <div className="chips col">{SUGGESTED.map((s) => <button key={s} className="chip-btn" onClick={() => ask(s)}>{s}</button>)}</div>
          </div>
        )}
        {turns.map((t, i) => {
          const ch = t.a ? chartable(t.a) : null;
          return (
            <div key={i} className="turn">
              <div className="msg user">{t.q}</div>
              <div className="msg bot">
                {t.error ? <div className="error">{t.error}</div> : !t.a ? <div className="thinking"><span /><span /><span /> Genie is writing SQL…</div> : (
                  <>
                    {t.a.description && <p>{t.a.description}</p>}
                    {t.a.text && <Markdown text={t.a.text} />}
                    {t.a.columns.length > 0 && (
                      <>
                        {ch && (
                          <div className="segmented mini">
                            <button className={t.view === "chart" ? "active" : ""} onClick={() => setTurns((x) => x.map((y, j) => j === i ? { ...y, view: "chart" } : y))}><BarChart3 size={13} /> Chart</button>
                            <button className={t.view === "table" ? "active" : ""} onClick={() => setTurns((x) => x.map((y, j) => j === i ? { ...y, view: "table" } : y))}><Table2 size={13} /> Table</button>
                          </div>
                        )}
                        {ch && t.view === "chart" ? (
                          <ResponsiveContainer width="100%" height={Math.max(140, ch.data.length * 30 + 30)}>
                            <BarChart data={ch.data} layout="vertical" margin={{ left: 4, right: 56, top: 4, bottom: 0 }}>
                              <CartesianGrid stroke="var(--grid)" horizontal={false} />
                              <XAxis type="number" {...axisProps} tickFormatter={(v) => ch.fmt(v)} />
                              <YAxis type="category" dataKey="label" {...axisProps} width={130} axisLine={false} />
                              <Tooltip content={<ChartTip format={(v: number) => ch.fmt(v)} />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
                              <Bar dataKey="value" name={ch.col} fill="var(--series-1)" radius={[0, 4, 4, 0]} barSize={16}
                                   label={{ position: "right", fontSize: 11, fill: "var(--text-secondary)", formatter: (v: number) => ch.fmt(v) }} />
                            </BarChart>
                          </ResponsiveContainer>
                        ) : (
                          <div className="table-wrap small-table">
                            <table><thead><tr>{t.a.columns.map((c: string) => <th key={c}>{c}</th>)}</tr></thead>
                              <tbody>{t.a.rows.slice(0, 25).map((r: any[], j: number) => <tr key={j}>{r.map((v, k) => <td key={k}>{v}</td>)}</tr>)}</tbody></table>
                          </div>
                        )}
                      </>
                    )}
                    {t.a.sql && <details><summary className="tiny muted">SQL generated by Genie · ran as {t.a.identity}</summary><pre className="sql">{t.a.sql}</pre></details>}
                  </>
                )}
              </div>
            </div>
          );
        })}
        <div ref={end} />
      </div>
      <form className="genie-input" onSubmit={(e) => { e.preventDefault(); ask(q); }}>
        <input ref={input} value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ask a question…" disabled={busy} />
        <button className="btn primary" disabled={busy || !q.trim()} aria-label="Ask"><Send size={15} /></button>
      </form>
    </aside>
  );
}
