import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from "react";
import { get } from "./api";

export type Route = "home" | "plan" | "lines" | "alerts" | "procurement" | "quarterly";
export type Toast = { id: number; kind: "ok" | "error" | "info"; text: string };

type Ctx = {
  me: any;
  filters: { offices: { office_code: string; office_name: string }[]; as_of_date?: string };
  office: string;
  setOffice: (o: string) => void;
  route: Route;
  query: URLSearchParams;
  go: (route: Route, query?: Record<string, string>) => void;
  openLine: (lineId: string, tab?: string) => void;
  line: { id: string; tab?: string } | null;
  closeLine: () => void;
  genie: { open: boolean; question?: string; nonce: number };
  askGenie: (question?: string) => void;
  closeGenie: () => void;
  toast: (text: string, kind?: Toast["kind"]) => void;
  toasts: Toast[];
  /** Bumped after every write so views refetch. */
  version: number;
  changed: () => void;
};

const AppCtx = createContext<Ctx>(null as unknown as Ctx);
export const useApp = () => useContext(AppCtx);

const ROUTES: Route[] = ["home", "plan", "lines", "alerts", "procurement", "quarterly"];

function parseHash(): { route: Route; query: URLSearchParams } {
  const [path, q] = window.location.hash.replace(/^#\/?/, "").split("?");
  const route = (ROUTES.includes(path as Route) ? path : "home") as Route;
  return { route, query: new URLSearchParams(q || "") };
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<any>(null);
  const [filters, setFilters] = useState<Ctx["filters"]>({ offices: [] });
  const [office, setOfficeState] = useState(() => localStorage.getItem("office") || "");
  const [loc, setLoc] = useState(parseHash);
  const [line, setLine] = useState<Ctx["line"]>(null);
  const [genie, setGenie] = useState<Ctx["genie"]>({ open: false, nonce: 0 });
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    get("/me").then(setMe).catch(() => setMe({ email: "unknown", role: "No access", offices: [] }));
    get("/filters").then(setFilters).catch(() => undefined);
    const onHash = () => setLoc(parseHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const toast = useCallback((text: string, kind: Toast["kind"] = "ok") => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, kind, text }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), kind === "error" ? 7000 : 4200);
  }, []);

  const setOffice = useCallback((o: string) => {
    setOfficeState(o);
    localStorage.setItem("office", o);
  }, []);

  const go = useCallback((route: Route, query?: Record<string, string>) => {
    const q = query ? new URLSearchParams(query).toString() : "";
    window.location.hash = `/${route === "home" ? "" : route}${q ? `?${q}` : ""}`;
    window.scrollTo({ top: 0 });
  }, []);

  const value: Ctx = {
    me, filters, office, setOffice, route: loc.route, query: loc.query, go,
    line, openLine: (id, tab) => setLine({ id, tab }), closeLine: () => setLine(null),
    genie, askGenie: (question) => setGenie((g) => ({ open: true, question, nonce: g.nonce + 1 })),
    closeGenie: () => setGenie((g) => ({ ...g, open: false })),
    toast, toasts, version, changed: () => setVersion((v) => v + 1),
  };
  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>;
}
