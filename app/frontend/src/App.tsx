import { useEffect, useState } from "react";
import { get } from "./api";
import Alerts from "./views/Alerts";
import Balances from "./views/Balances";
import Genie from "./views/Genie";
import Overview from "./views/Overview";
import Procurement from "./views/Procurement";
import Quarterly from "./views/Quarterly";

const TABS = ["Budget execution", "Expiring balances", "Risk alerts", "Procurement", "Quarterly review", "Ask the data"] as const;

export default function App() {
  const [tab, setTab] = useState<(typeof TABS)[number]>("Budget execution");
  const [me, setMe] = useState<any>(null);
  const [filters, setFilters] = useState<any>({ offices: [] });
  const [office, setOffice] = useState("");

  useEffect(() => {
    get("/me").then(setMe);
    get("/filters").then(setFilters);
  }, []);

  const scoped = tab !== "Quarterly review" && tab !== "Ask the data";
  return (
    <>
      <header>
        <div>
          <h1>Budget Execution &amp; Financial Oversight</h1>
          <div className="sub">Office of the CFO · Department of Civic Infrastructure (fictional, synthetic data) · as of {filters.as_of_date ?? "…"}</div>
        </div>
        <div className="spacer" />
        {scoped && (
          <select value={office} onChange={(e) => setOffice(e.target.value)}>
            <option value="">All offices in my scope</option>
            {filters.offices.map((o: any) => <option key={o.office_code} value={o.office_code}>{o.office_name}</option>)}
          </select>
        )}
        <div className="who">{me?.email}<br />{me?.role} · {me?.offices ? me.offices.join(", ") : "agency-wide"}</div>
      </header>
      <nav>{TABS.map((t) => <button key={t} className={t === tab ? "active" : ""} onClick={() => setTab(t)}>{t}</button>)}</nav>
      <main>
        {tab === "Budget execution" && <Overview office={office || undefined} />}
        {tab === "Expiring balances" && <Balances office={office || undefined} />}
        {tab === "Risk alerts" && <Alerts office={office || undefined} />}
        {tab === "Procurement" && <Procurement office={office || undefined} />}
        {tab === "Quarterly review" && <Quarterly asOf={filters.as_of_date} />}
        {tab === "Ask the data" && <Genie />}
      </main>
    </>
  );
}
