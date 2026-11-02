import { ClipboardCheck, Gauge, Kanban, Target, Wallet, Workflow } from "lucide-react";
import { ReactNode } from "react";
import { Route } from "./app-context";

export const NAV: { id: Route; label: string; icon: ReactNode; hint: string }[] = [
  { id: "home", label: "Command center", icon: <Gauge size={17} />, hint: "Year-end at a glance" },
  { id: "plan", label: "Year-end plan", icon: <Target size={17} />, hint: "Recover projected lapse" },
  { id: "lines", label: "Budget lines", icon: <Wallet size={17} />, hint: "Execution by PPA" },
  { id: "alerts", label: "Risk alerts", icon: <Kanban size={17} />, hint: "Triage board" },
  { id: "procurement", label: "Procurement", icon: <Workflow size={17} />, hint: "PR pipeline and PALT" },
  { id: "quarterly", label: "Quarterly review", icon: <ClipboardCheck size={17} />, hint: "Narratives and sign-off" },
];
