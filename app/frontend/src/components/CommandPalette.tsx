import { Building2, CornerDownLeft, FileText, LayoutDashboard, Search, Sparkles, Wallet } from "lucide-react";
import { ReactNode, useEffect, useMemo, useRef, useState } from "react";
import { get, money } from "../api";
import { Route, useApp } from "../app-context";
import { NAV } from "../nav";

type Item = { id: string; group: string; icon: ReactNode; label: ReactNode; sub?: ReactNode; run: () => void };

export default function CommandPalette({ onClose }: { onClose: () => void }) {
  const { go, filters, setOffice, openLine, askGenie, toast } = useApp();
  const [q, setQ] = useState("");
  const [res, setRes] = useState<{ lines: any[]; prs: any[] }>({ lines: [], prs: [] });
  const [sel, setSel] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => { input.current?.focus(); }, []);
  useEffect(() => {
    if (q.trim().length < 2) { setRes({ lines: [], prs: [] }); return; }
    const t = setTimeout(() => get("/search", { q }).then(setRes).catch(() => undefined), 180);
    return () => clearTimeout(t);
  }, [q]);

  const items = useMemo<Item[]>(() => {
    const t = q.trim().toLowerCase();
    const done = (fn: () => void) => () => { fn(); onClose(); };
    const out: Item[] = [];
    for (const n of NAV) if (!t || n.label.toLowerCase().includes(t))
      out.push({ id: `nav:${n.id}`, group: "Go to", icon: n.icon, label: n.label, run: done(() => go(n.id as Route)) });
    for (const o of filters.offices) if (t && `${o.office_code} ${o.office_name}`.toLowerCase().includes(t))
      out.push({ id: `office:${o.office_code}`, group: "Scope to office", icon: <Building2 size={15} />, label: o.office_name, sub: o.office_code,
                 run: done(() => { setOffice(o.office_code); toast(`Scoped to ${o.office_name}`, "info"); }) });
    for (const l of res.lines)
      out.push({ id: `line:${l.line_id}`, group: "Budget lines", icon: <Wallet size={15} />, label: l.ppa_name,
                 sub: `${l.line_id} · ${money(l.unobligated_balance)} unobligated · ${l.days_to_expiration}d left`, run: done(() => openLine(l.line_id)) });
    for (const p of res.prs)
      out.push({ id: `pr:${p.pr_id}`, group: "Procurement requests", icon: <FileText size={15} />, label: `${p.pr_id} · ${p.title}`,
                 sub: `${p.status} · ${money(p.estimated_amount)} · ${p.line_id}`, run: done(() => openLine(p.line_id, "procurement")) });
    if (t) out.push({ id: "genie", group: "Ask Genie", icon: <Sparkles size={15} />, label: <>Ask Genie: “{q}”</>, run: done(() => askGenie(q)) });
    if (!t) out.push({ id: "scope:all", group: "Scope to office", icon: <LayoutDashboard size={15} />, label: "All offices in my scope", run: done(() => setOffice("")) });
    return out;
  }, [q, res, filters.offices, go, setOffice, openLine, askGenie, onClose, toast]);

  useEffect(() => setSel(0), [q, res]);
  const key = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setSel((s) => Math.min(items.length - 1, s + 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setSel((s) => Math.max(0, s - 1)); }
    else if (e.key === "Enter") { e.preventDefault(); items[sel]?.run(); }
    else if (e.key === "Escape") onClose();
  };

  let last = "";
  return (
    <div className="overlay center top" onMouseDown={onClose}>
      <div className="palette" onMouseDown={(e) => e.stopPropagation()}>
        <div className="palette-input"><Search size={17} />
          <input ref={input} value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={key} placeholder="Search lines, procurement requests, offices, pages… or ask Genie" />
          <kbd>esc</kbd></div>
        <div className="palette-list">
          {items.map((it, i) => {
            const head = it.group !== last ? <div className="palette-group">{it.group}</div> : null;
            last = it.group;
            return (
              <div key={it.id}>
                {head}
                <button className={`palette-item ${i === sel ? "sel" : ""}`} onMouseEnter={() => setSel(i)} onClick={it.run}>
                  <span className="palette-icon">{it.icon}</span>
                  <span className="grow"><span>{it.label}</span>{it.sub && <span className="tiny muted block">{it.sub}</span>}</span>
                  {i === sel && <CornerDownLeft size={13} className="muted" />}
                </button>
              </div>
            );
          })}
          {items.length === 0 && <div className="palette-empty muted">No matches</div>}
        </div>
      </div>
    </div>
  );
}
