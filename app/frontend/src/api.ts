import { useCallback, useEffect, useRef, useState } from "react";

type Params = Record<string, string | number | undefined | null>;

function qs(params: Params) {
  const p = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "").map(([k, v]) => [k, String(v)]),
  );
  return p.toString() ? `?${p}` : "";
}

export async function get<T = any>(path: string, params: Params = {}): Promise<T> {
  const r = await fetch(`/api${path}${qs(params)}`);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
  return r.json();
}

export async function post<T = any>(path: string, body: unknown = {}): Promise<T> {
  const r = await fetch(`/api${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const detail = (await r.json().catch(() => ({}))).detail;
    throw new Error(typeof detail === "string" ? detail : Array.isArray(detail) ? detail.map((d) => d.msg).join("; ") : r.statusText);
  }
  return r.json();
}

/** Fetch `path` whenever its params or `deps` change; keeps the previous data while reloading. */
export function useApi<T = any>(path: string | null, params: Params = {}, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const key = path ? path + qs(params) : "";
  const seq = useRef(0);
  const load = useCallback(() => {
    if (!path) return;
    const n = ++seq.current;
    setLoading(true);
    get<T>(path, params)
      .then((d) => { if (n === seq.current) { setData(d); setError(""); } })
      .catch((e) => { if (n === seq.current) setError(e.message); })
      .finally(() => { if (n === seq.current) setLoading(false); });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  useEffect(load, [load, ...deps]);
  return { data, error, loading, reload: load };
}

const n = (v: unknown) => (v === null || v === undefined || v === "" ? NaN : Number(v));

export function money(v: unknown, digits = 1): string {
  const x = n(v);
  if (Number.isNaN(x)) return "-";
  const a = Math.abs(x);
  const sign = x < 0 ? "-" : "";
  if (a >= 1e9) return `${sign}$${(a / 1e9).toFixed(digits)}B`;
  if (a >= 1e6) return `${sign}$${(a / 1e6).toFixed(digits)}M`;
  if (a >= 1e3) return `${sign}$${(a / 1e3).toFixed(0)}K`;
  return `${sign}$${a.toFixed(0)}`;
}

export function moneyFull(v: unknown): string {
  const x = n(v);
  return Number.isNaN(x) ? "-" : `$${Math.round(x).toLocaleString("en-US")}`;
}

export function pct(v: unknown, digits = 1): string {
  const x = n(v);
  return Number.isNaN(x) ? "-" : `${(100 * x).toFixed(digits)}%`;
}

export function shortDate(v: unknown): string {
  if (!v) return "-";
  const d = new Date(String(v).length === 10 ? `${v}T12:00:00` : String(v));
  return d.toLocaleDateString("en-US", { day: "numeric", month: "short" });
}

export function longDate(v: unknown): string {
  if (!v) return "-";
  const d = new Date(String(v).length === 10 ? `${v}T12:00:00` : String(v));
  return d.toLocaleDateString("en-US", { day: "numeric", month: "short", year: "numeric" });
}

export function ago(v: unknown): string {
  if (!v) return "";
  const s = (Date.now() - new Date(String(v)).getTime()) / 1000;
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

export function daysBetween(a: string, b: string): number {
  return Math.round((new Date(`${b}T12:00:00`).getTime() - new Date(`${a}T12:00:00`).getTime()) / 86400000);
}

export function asList(v: unknown): string[] {
  if (Array.isArray(v)) return v as string[];
  if (typeof v === "string") {
    try {
      const p = JSON.parse(v);
      return Array.isArray(p) ? p : [v];
    } catch {
      return v ? [v] : [];
    }
  }
  return [];
}

export function initials(email?: string): string {
  if (!email) return "?";
  const name = email.split("@")[0].split(/[._-]/).filter(Boolean);
  return (name[0]?.[0] ?? "?").toUpperCase() + (name[1]?.[0] ?? "").toUpperCase();
}

export function person(email?: string | null): string {
  if (!email) return "";
  return email.split("@")[0].split(/[._-]/).filter(Boolean).map((p) => p[0].toUpperCase() + p.slice(1)).join(" ");
}

export const TIER_SEVERITY: Record<string, string> = { Critical: "Critical", High: "High", Moderate: "Medium", Low: "Low" };

export const ALERT_LABEL: Record<string, string> = {
  LAPSE_RISK: "Lapse risk",
  APPORTIONMENT_EXCEEDED: "Apportionment exceeded (ADA)",
  COMMITMENTS_EXCEED_AVAILABLE: "Commitments exceed available",
  BURN_RATE_VARIANCE: "Burn-rate variance",
  STALE_SPEND_PLAN: "Stale spend plan",
  PROCUREMENT_WILL_MISS_EXPIRATION: "Procurement will miss expiration",
  STALLED_PROCUREMENT: "Stalled procurement",
  INVOICE_EXCEEDS_OBLIGATION: "Invoice exceeds obligation",
  POTENTIAL_DUPLICATE_INVOICE: "Potential duplicate invoice",
  UNMATCHED_INVOICE: "Unmatched invoice",
  PROMPT_PAY_RISK: "Prompt Payment risk",
};
