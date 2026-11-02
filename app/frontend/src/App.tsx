import { CircleCheck, Info, Search, Sparkles, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { longDate } from "./api";
import { AppProvider, useApp } from "./app-context";
import CommandPalette from "./components/CommandPalette";
import GeniePanel from "./components/GeniePanel";
import { Avatar } from "./components/ui";
import { NAV } from "./nav";
import AlertsBoard from "./views/AlertsBoard";
import CommandCenter from "./views/CommandCenter";
import LineDetail from "./views/LineDetail";
import Lines from "./views/Lines";
import Procurement from "./views/Procurement";
import Quarterly from "./views/Quarterly";
import YearEndPlan from "./views/YearEndPlan";

export default function App() {
  return <AppProvider><Shell /></AppProvider>;
}

function Shell() {
  const { route, go, me, filters, office, setOffice, line, closeLine, askGenie, genie, toasts } = useApp();
  const [palette, setPalette] = useState(false);
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setPalette((p) => !p); }
      const typing = ["INPUT", "TEXTAREA", "SELECT"].includes((e.target as HTMLElement)?.tagName);
      if (!typing && e.key === "/") { e.preventDefault(); setPalette(true); }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);
  const officeName = filters.offices.find((o) => o.office_code === office)?.office_name;

  return (
    <div className={`shell ${genie.open ? "genie-open" : ""}`}>
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark" aria-hidden>
            <svg viewBox="0 0 32 32" width="30" height="30"><rect width="32" height="32" rx="8" fill="url(#bg)" />
              <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#3987e5" /><stop offset="1" stopColor="#184f95" /></linearGradient></defs>
              <path d="M8 22V14M13 22V10M18 22V16M23 22V12" stroke="#fff" strokeWidth="2.6" strokeLinecap="round" /></svg>
          </div>
          <div><div className="brand-name">Budget Execution</div><div className="brand-sub">Office of the CFO</div></div>
        </div>
        <nav>
          {NAV.map((n) => (
            <button key={n.id} className={route === n.id ? "active" : ""} onClick={() => go(n.id)}>
              {n.icon}<span><span className="nav-label">{n.label}</span><span className="nav-hint">{n.hint}</span></span>
            </button>
          ))}
        </nav>
        <button className="nav-genie" onClick={() => askGenie()}><Sparkles size={16} /> Ask Genie</button>
        <div className="sidebar-foot">
          <div>Department of Civic Infrastructure</div>
          <div className="muted">Fictional agency · synthetic data</div>
        </div>
      </aside>

      <div className="main-col">
        <header className="topbar">
          <button className="search-trigger" onClick={() => setPalette(true)}>
            <Search size={15} /><span>Search lines, requests, offices or ask Genie</span><kbd>⌘K</kbd>
          </button>
          <div className="spacer" />
          <select className="scope" value={office} onChange={(e) => setOffice(e.target.value)} aria-label="Office scope">
            <option value="">All offices in my scope</option>
            {filters.offices.map((o) => <option key={o.office_code} value={o.office_code}>{o.office_code} · {o.office_name}</option>)}
          </select>
          <span className="asof" title="Reporting date of the gold tables">Data as of {filters.as_of_date ? longDate(filters.as_of_date) : "…"}</span>
          <div className="me">
            <Avatar email={me?.email} />
            <div><div className="me-name">{me?.email ?? "…"}</div><div className="tiny muted">{me?.role}{me ? ` · ${me.offices ? me.offices.join(", ") : "agency-wide"}` : ""}</div></div>
          </div>
        </header>
        {office && (
          <div className="scope-banner">Scoped to <b>{officeName}</b> <button className="link" onClick={() => setOffice("")}>Show all offices</button></div>
        )}
        <main>
          {route === "home" && <CommandCenter />}
          {route === "plan" && <YearEndPlan />}
          {route === "lines" && <Lines />}
          {route === "alerts" && <AlertsBoard />}
          {route === "procurement" && <Procurement />}
          {route === "quarterly" && <Quarterly />}
        </main>
      </div>

      <GeniePanel />
      {line && <LineDetail lineId={line.id} initialTab={line.tab} onClose={closeLine} />}
      {palette && <CommandPalette onClose={() => setPalette(false)} />}
      <div className="toasts" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast ${t.kind}`}>
            {t.kind === "ok" ? <CircleCheck size={16} /> : t.kind === "error" ? <TriangleAlert size={16} /> : <Info size={16} />}
            <span>{t.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
