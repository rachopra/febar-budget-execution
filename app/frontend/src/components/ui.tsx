import { CircleAlert, CircleCheck, OctagonAlert, TriangleAlert, X } from "lucide-react";
import { ReactNode, useEffect, useRef, useState } from "react";
import { initials, TIER_SEVERITY } from "../api";

export function Card({ title, hint, actions, children, className = "", id }: {
  title?: ReactNode; hint?: ReactNode; actions?: ReactNode; children?: ReactNode; className?: string; id?: string;
}) {
  return (
    <section className={`card ${className}`} id={id}>
      {(title || actions) && (
        <div className="card-head">
          <div>
            {title && <h2>{title}</h2>}
            {hint && <p className="hint">{hint}</p>}
          </div>
          {actions && <div className="card-actions">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  );
}

export function Stat({ label, value, foot, tone }: { label: ReactNode; value: ReactNode; foot?: ReactNode; tone?: "accent" | "warn" }) {
  return (
    <div className={`stat ${tone ?? ""}`}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {foot && <div className="stat-foot">{foot}</div>}
    </div>
  );
}

/** Animates from the previous value to `value`. */
export function CountUp({ value, format, duration = 900 }: { value: number; format: (v: number) => string; duration?: number }) {
  const [shown, setShown] = useState(0);
  const from = useRef(0);
  useEffect(() => {
    const start = performance.now();
    const a = from.current;
    let raf = 0;
    const tick = (t: number) => {
      const k = Math.min(1, (t - start) / duration);
      const eased = 1 - Math.pow(1 - k, 3);
      setShown(a + (value - a) * eased);
      if (k < 1) raf = requestAnimationFrame(tick);
      else from.current = value;
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value, duration]);
  return <>{format(shown)}</>;
}

const SEV_ICON: Record<string, ReactNode> = {
  Critical: <OctagonAlert size={13} />,
  High: <TriangleAlert size={13} />,
  Medium: <CircleAlert size={13} />,
  Low: <CircleCheck size={13} />,
};

export function SevBadge({ severity, label }: { severity: string; label?: string }) {
  return <span className={`sev sev-${severity}`}>{SEV_ICON[severity]}{label ?? severity}</span>;
}

export function TierBadge({ tier }: { tier?: string | null }) {
  if (!tier || !TIER_SEVERITY[tier]) return <span className="pill">{tier || "Not scored"}</span>;
  return <SevBadge severity={TIER_SEVERITY[tier]} label={tier} />;
}

export function Tabs<T extends string>({ tabs, value, onChange }: {
  tabs: { id: T; label: ReactNode; count?: ReactNode }[]; value: T; onChange: (v: T) => void;
}) {
  return (
    <div className="tabs" role="tablist">
      {tabs.map((t) => (
        <button key={t.id} role="tab" aria-selected={t.id === value} className={t.id === value ? "active" : ""} onClick={() => onChange(t.id)}>
          {t.label}{t.count !== undefined && <span className="tab-count">{t.count}</span>}
        </button>
      ))}
    </div>
  );
}

export function Segmented<T extends string>({ options, value, onChange }: {
  options: { id: T; label: ReactNode }[]; value: T; onChange: (v: T) => void;
}) {
  return (
    <div className="segmented">
      {options.map((o) => (
        <button key={o.id} className={o.id === value ? "active" : ""} onClick={() => onChange(o.id)}>{o.label}</button>
      ))}
    </div>
  );
}

export function Modal({ title, onClose, children, footer, wide }: {
  title: ReactNode; onClose: () => void; children: ReactNode; footer?: ReactNode; wide?: boolean;
}) {
  useEscape(onClose);
  return (
    <div className="overlay center" onMouseDown={onClose}>
      <div className={`modal ${wide ? "wide" : ""}`} onMouseDown={(e) => e.stopPropagation()} role="dialog" aria-modal>
        <div className="modal-head"><h3>{title}</h3><button className="icon-btn" onClick={onClose} aria-label="Close"><X size={16} /></button></div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-foot">{footer}</div>}
      </div>
    </div>
  );
}

export function Drawer({ onClose, children, width = 880 }: { onClose: () => void; children: ReactNode; width?: number }) {
  useEscape(onClose);
  return (
    <div className="overlay" onMouseDown={onClose}>
      <aside className="drawer" style={{ width: `min(${width}px, 96vw)` }} onMouseDown={(e) => e.stopPropagation()}>
        {children}
      </aside>
    </div>
  );
}

export function useEscape(fn: () => void) {
  useEffect(() => {
    const h = (e: KeyboardEvent) => e.key === "Escape" && fn();
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [fn]);
}

export function Skeleton({ h = 120, className = "" }: { h?: number; className?: string }) {
  return <div className={`skeleton ${className}`} style={{ height: h }} />;
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="empty">{children}</div>;
}

export function Avatar({ email, size = 28 }: { email?: string; size?: number }) {
  return <span className="avatar" style={{ width: size, height: size, fontSize: size * 0.4 }}>{initials(email)}</span>;
}

export function Meter({ value, max, marker, tone = "accent" }: { value: number; max: number; marker?: number; tone?: string }) {
  const w = max > 0 ? Math.max(0, Math.min(1, value / max)) : 0;
  return (
    <div className="meter">
      <div className={`meter-fill ${tone}`} style={{ width: `${w * 100}%` }} />
      {marker !== undefined && max > 0 && <div className="meter-marker" style={{ left: `${Math.min(1, marker / max) * 100}%` }} />}
    </div>
  );
}

/** Dark tooltip for Recharts. */
export function ChartTip({ active, payload, label, format, labelFormat }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tip">
      {label !== undefined && <div className="chart-tip-label">{labelFormat ? labelFormat(label) : label}</div>}
      {payload.filter((p: any) => p.value !== null && p.value !== undefined).map((p: any) => (
        <div key={p.dataKey ?? p.name} className="chart-tip-row">
          <span className="swatch" style={{ background: p.color || p.stroke || p.fill }} />
          <span>{p.name}</span>
          <b>{format ? format(p.value, p) : p.value}</b>
        </div>
      ))}
    </div>
  );
}

export const axisProps = { stroke: "var(--axis)", tick: { fill: "var(--text-muted)", fontSize: 11 }, tickLine: false };
