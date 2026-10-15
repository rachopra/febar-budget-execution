export async function get<T = any>(path: string, params: Record<string, string | undefined> = {}): Promise<T> {
  const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v) as [string, string][]);
  const r = await fetch(`/api${path}${qs.toString() ? `?${qs}` : ""}`);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
  return r.json();
}

export async function post<T = any>(path: string, body: unknown = {}): Promise<T> {
  const r = await fetch(`/api${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
  return r.json();
}

const n = (v: unknown) => (v === null || v === undefined ? NaN : Number(v));

export function money(v: unknown, digits = 1): string {
  const x = n(v);
  if (Number.isNaN(x)) return "-";
  const a = Math.abs(x);
  if (a >= 1e9) return `$${(x / 1e9).toFixed(digits)}B`;
  if (a >= 1e6) return `$${(x / 1e6).toFixed(digits)}M`;
  if (a >= 1e3) return `$${(x / 1e3).toFixed(0)}K`;
  return `$${x.toFixed(0)}`;
}

export function pct(v: unknown, digits = 1): string {
  const x = n(v);
  return Number.isNaN(x) ? "-" : `${(100 * x).toFixed(digits)}%`;
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

export const SEVERITY_ICON: Record<string, string> = { Critical: "⛔", High: "▲", Medium: "●", Low: "○" };
