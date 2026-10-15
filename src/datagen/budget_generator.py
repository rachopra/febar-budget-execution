"""Synthetic budget-execution data for a fictional federal civilian agency.

The agency ("Department of Civic Infrastructure", DCI, Treasury agency code 999) is
invented. Nothing here is derived from real agency or customer data.

The generator simulates the full execution lifecycle of every budget line
(PPA x budget fiscal year x Treasury Account Symbol) and then emits only what the
agency's three siloed trackers would have recorded by ``as_of``:

  reference/ppa_master.csv                       PPA / office / appropriation reference
  budget_authority/budget_authority_FY{bfy}.csv  enacted budget + apportionment (formulation)
  spend_plan/{template}/spend_plan_FY{bfy}_{office}_rev{nn}_{date}.csv
                                                 program-office spend-plan spreadsheets; the
                                                 budget-office template and a legacy template
                                                 in $K; some offices never revise after enactment
  procurement_requests/pr_events_{yyyy-mm}.jsonl PR-tracker change events (nested JSON)
  invoices/invoices_{yyyy-mm}.csv                invoice register from the payment system

Behaviours baked in so the downstream analytics and ML have real signal:
  * Continuing resolutions delay new starts until full-year enactment.
  * Spend plans and obligations are back-loaded; offices run a Q4 "sweep".
  * Offices differ in execution health: late PR submission, longer PALT, more cancellations.
  * PRs that cannot award before the funds expire are cancelled and the funds lapse.
  * Deobligations, an apportionment shortfall (ADA risk), over-billed and duplicate
    invoices, unknown contract numbers, Prompt Payment Act late payments, and messy
    spreadsheet values (currency strings, $K units, inconsistent PPA codes).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

AGENCY_CODE = "999"
AGENCY_NAME = "Department of Civic Infrastructure (fictional)"
EMAIL_DOMAIN = "dci.example.gov"
BUDGET_FISCAL_YEARS = [2023, 2024, 2025, 2026]
DEFAULT_AS_OF = date(2026, 7, 31)

# Illustrative full-year enactment dates. Before enactment the agency runs under a CR,
# which blocks new starts.
ENACTMENT_DATES = {
    2023: date(2022, 12, 29),
    2024: date(2024, 3, 23),
    2025: date(2025, 3, 15),
    2026: date(2026, 1, 30),
}

# code, name, execution-health bias, spend-plan template, revises plan after enactment
OFFICES = [
    ("OGM", "Office of Grid Modernization", 0.30, "A", True),
    ("OWS", "Office of Water Systems", 0.05, "A", True),
    ("OTS", "Office of Transportation Safety", -0.65, "B", False),
    ("OCIO", "Office of the Chief Information Officer", 0.15, "A", True),
    ("OWD", "Office of Workforce Development", -0.30, "B", True),
    ("OMA", "Office of Management and Administration", 0.45, "A", True),
]

# code -> name, fund type, years of availability, main account, enacted range ($M), BOC mix
APPROPRIATIONS = {
    "OS": ("Operations and Support", "annual", 1, "0100", (6, 38),
           {"25.1": 0.25, "25.2": 0.40, "25.7": 0.10, "26.0": 0.05, "31.0": 0.20}),
    "PCI": ("Procurement, Construction, and Improvements", "multi-year", 3, "0400", (25, 110),
            {"32.0": 0.55, "31.0": 0.30, "25.1": 0.15}),
    "RD": ("Research and Development", "multi-year", 2, "0800", (8, 36),
           {"25.5": 0.70, "25.1": 0.15, "31.0": 0.15}),
    "GA": ("Grants and Assistance", "annual", 1, "0600", (18, 85),
           {"41.0": 0.94, "25.1": 0.06}),
}

OBJECT_CLASSES = {
    "25.1": ("Advisory and assistance services", "services"),
    "25.2": ("Other services from non-Federal sources", "services"),
    "25.5": ("Research and development contracts", "research"),
    "25.7": ("Operation and maintenance of equipment", "services"),
    "26.0": ("Supplies and materials", "supplies"),
    "31.0": ("Equipment", "equipment"),
    "32.0": ("Land and structures", "construction"),
    "41.0": ("Grants, subsidies, and contributions", "grants"),
}

# office, appropriation, PPA name
PPAS = [
    ("OGM", "OS", "Grid Resilience Program Operations"),
    ("OGM", "OS", "Outage Analytics and Monitoring"),
    ("OGM", "PCI", "Substation Hardening"),
    ("OGM", "RD", "Advanced Transmission Research"),
    ("OGM", "GA", "State Energy Resilience Grants"),
    ("OWS", "OS", "Drinking Water Program Operations"),
    ("OWS", "OS", "Laboratory Services"),
    ("OWS", "PCI", "Water Infrastructure Modernization"),
    ("OWS", "RD", "Water Quality Sensor Research"),
    ("OWS", "GA", "Tribal and Rural Water Grants"),
    ("OTS", "OS", "Safety Inspection Operations"),
    ("OTS", "OS", "Incident Investigation"),
    ("OTS", "PCI", "Bridge Inspection Systems"),
    ("OTS", "RD", "Automated Vehicle Safety Research"),
    ("OTS", "GA", "Highway Safety Improvement Grants"),
    ("OCIO", "OS", "Enterprise IT Operations"),
    ("OCIO", "OS", "Cybersecurity Operations"),
    ("OCIO", "OS", "Data and Analytics Platform"),
    ("OCIO", "PCI", "Financial System Modernization"),
    ("OCIO", "PCI", "Cloud Migration"),
    ("OWD", "GA", "Infrastructure Workforce Grants"),
    ("OWD", "GA", "Apprenticeship Expansion Grants"),
    ("OWD", "OS", "Training Program Administration"),
    ("OWD", "RD", "Workforce Outcomes Evaluation"),
    ("OMA", "OS", "Facilities and Logistics"),
    ("OMA", "OS", "Human Capital Services"),
    ("OMA", "OS", "Acquisition Management"),
    ("OMA", "OS", "Financial Management Services"),
    ("OMA", "PCI", "Headquarters Consolidation"),
]

# Monthly obligation-plan curves over a fiscal year (Oct..Sep), by spend category.
PLAN_CURVES = {
    "services": [5, 6, 6, 7, 8, 8, 8, 9, 10, 10, 11, 12],
    "research": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 12, 13],
    "supplies": [7, 7, 8, 8, 8, 8, 8, 8, 9, 9, 10, 10],
    "equipment": [2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 15],
    "construction": [1, 2, 3, 5, 7, 9, 10, 11, 12, 13, 13, 14],
    "grants": [0, 0, 1, 2, 3, 4, 6, 9, 13, 17, 21, 24],
}
MULTI_YEAR_SHARE = {1: [1.0], 2: [0.72, 0.28], 3: [0.55, 0.32, 0.13]}

# Typical single-requirement size range by category ($)
REQUIREMENT_SIZE = {
    "services": (300_000, 3_000_000),
    "research": (500_000, 4_000_000),
    "supplies": (40_000, 300_000),
    "equipment": (150_000, 2_500_000),
    "construction": (2_000_000, 14_000_000),
    "grants": (1_000_000, 7_000_000),
}

ACQUISITION_MIX = {
    "services": {"Option Exercise": 0.35, "Task Order": 0.40, "New Award": 0.25},
    "research": {"Task Order": 0.30, "New Award": 0.70},
    "supplies": {"Task Order": 0.60, "New Award": 0.40},
    "equipment": {"Task Order": 0.65, "New Award": 0.35},
    "construction": {"New Award": 1.0},
    "grants": {"Grant Award": 1.0},
}

PALT_MEDIAN_DAYS = {
    "Option Exercise": 20,
    "Modification": 25,
    "Task Order": 55,
    "New Award (Simplified)": 40,
    "New Award": 140,
    "Grant Award": 150,
}

REQUIREMENT_TITLES = {
    "25.1": ["Program management support services", "Technical assistance for {ppa}",
             "Independent verification and validation", "Acquisition support services",
             "Program evaluation support"],
    "25.2": ["Service desk and end-user support", "Enterprise software license renewal",
             "Cloud hosting services", "Training delivery services", "Data analytics support"],
    "25.5": ["Applied research task order: {ppa}", "Prototype evaluation study",
             "Field pilot and test campaign", "Modeling and simulation research"],
    "25.7": ["Equipment maintenance agreement", "Laboratory instrument service contract",
             "Fleet maintenance services"],
    "26.0": ["Field supplies", "Laboratory consumables", "Safety equipment and PPE"],
    "31.0": ["Sensor equipment procurement", "Network hardware refresh",
             "Field inspection vehicles", "End-user device refresh", "Test instrumentation"],
    "32.0": ["Facility renovation - {site}", "Substation retrofit - {site}",
             "Construction of {site} operations center", "Site preparation - {site}"],
    "41.0": ["{ppa} - competitive awards cohort {n}", "{ppa} - formula allocation region {n}",
             "{ppa} - cooperative agreement {n}"],
}
SITES = ["Denver Federal Center", "Region 4 Field Office", "Kansas City Annex", "Atlanta Campus",
         "Seattle Field Station", "Albuquerque Test Range", "Region 7 Depot", "Headquarters East"]

FIRST_NAMES = ["Avery", "Jordan", "Morgan", "Taylor", "Riley", "Casey", "Jamie", "Quinn", "Drew",
               "Reese", "Rowan", "Skyler", "Parker", "Hayden", "Emerson", "Logan", "Dakota",
               "Sasha", "Cameron", "Alexis", "Kendall", "Peyton", "Blake", "Harper"]
LAST_NAMES = ["Nguyen", "Okafor", "Patel", "Garcia", "Kim", "Johnson", "Silva", "Cohen", "Reyes",
              "Murphy", "Adeyemi", "Larsen", "Brooks", "Chen", "Haddad", "Novak", "Ortiz",
              "Walsh", "Iyer", "Foster", "Mendez", "Tanaka", "Hughes", "Sato"]
VENDOR_PREFIX = ["Apex", "Bluewater", "Cardinal", "Summit", "Ironwood", "Keystone", "Meridian",
                 "Northstar", "Pinnacle", "Redline", "Sentinel", "Trident", "Vantage", "Liberty",
                 "Granite", "Harbor", "Cobalt", "Evergreen", "Patriot", "Horizon"]
VENDOR_CORE = ["Federal", "Engineering", "Systems", "Analytics", "Technologies", "Infrastructure",
               "Consulting", "Integrators", "Solutions", "Research"]
VENDOR_SUFFIX = ["LLC", "Inc.", "Group", "Corp.", "Partners", "JV"]
GRANTEES = ["State of {s} Department of Transportation", "{s} Water Resources Authority",
            "{s} Energy Office", "University of {s}", "{s} Workforce Development Board",
            "{s} Tribal Utilities Commission"]
STATES = ["Colorado", "Ohio", "Arizona", "Georgia", "Michigan", "Oregon", "Kansas", "Virginia",
          "New Mexico", "Montana", "Iowa", "Alabama", "Nevada", "Maine", "Utah", "Idaho"]

UEI_ALPHABET = list("ABCDEFGHJKLMNPQRSTUVWXYZ0123456789")
PROMPT_PAY_RATE = 0.045  # illustrative Prompt Payment Act interest rate


@dataclass
class BudgetLine:
    bfy: int
    ppa_code: str
    ppa_name: str
    office: str
    approp: str
    fund_type: str
    years: int
    tas: str
    start: date
    expiration: date
    pb_request: float
    enacted: float
    health: float
    boc_mix: dict
    monthly_plan: dict = field(default_factory=dict)  # boc -> np.array of planned obligations
    prs: list = field(default_factory=list)
    obligations: list = field(default_factory=list)  # (date, amount, pr_id, contract, mod)


def _month_start(start: date, i: int) -> date:
    y = start.year + (start.month - 1 + i) // 12
    m = (start.month - 1 + i) % 12 + 1
    return date(y, m, 1)


def _month_end(d: date) -> date:
    nxt = _month_start(d.replace(day=1), 1)
    return nxt - timedelta(days=1)


def _fy_of(d: date) -> int:
    return d.year + 1 if d.month >= 10 else d.year


class Generator:
    def __init__(self, seed: int = 42, as_of: date = DEFAULT_AS_OF):
        self.rng = np.random.default_rng(seed)
        self.as_of = as_of
        self.as_of_ts = datetime.combine(as_of, time(23, 59, 59))
        self.lines: list[BudgetLine] = []
        self.ppa_master: list[dict] = []
        self.staff = self._make_staff()
        self.vendors = self._make_vendors(140)
        self.grantees = self._make_grantees()
        self.seq = {}
        self.events: list[dict] = []
        self.invoices: list[dict] = []
        self.awards: list[dict] = []
        self.incumbents: dict[str, list[dict]] = {}

    # ------------------------------------------------------------------ reference data
    def _uei(self) -> str:
        return "".join(self.rng.choice(UEI_ALPHABET, 12))

    def _person(self):
        f = self.rng.choice(FIRST_NAMES)
        l = self.rng.choice(LAST_NAMES)
        return {"name": f"{f} {l}", "email": f"{f.lower()}.{l.lower()}@{EMAIL_DOMAIN}"}

    def _make_staff(self):
        return {o[0]: [self._person() for _ in range(4)] for o in OFFICES} | {
            "ACQ": [self._person() for _ in range(8)]}

    def _make_vendors(self, n):
        seen, out = set(), []
        while len(out) < n:
            name = (f"{self.rng.choice(VENDOR_PREFIX)} {self.rng.choice(VENDOR_CORE)} "
                    f"{self.rng.choice(VENDOR_SUFFIX)}")
            if name in seen:
                continue
            seen.add(name)
            out.append(self._payee(name))
        return out

    def _make_grantees(self):
        out = []
        for s in STATES:
            for t in self.rng.choice(GRANTEES, 2, replace=False):
                out.append(self._payee(t.format(s=s)))
        return out

    def _payee(self, name):
        tin = f"{self.rng.integers(10, 99)}-{self.rng.integers(1_000_000, 9_999_999)}"
        return {"name": name, "uei": self._uei(), "tin": tin,
                "routing": f"{self.rng.integers(100_000_000, 999_999_999)}",
                "account": f"{self.rng.integers(10**9, 10**11)}"}

    def _next(self, key: str) -> int:
        self.seq[key] = self.seq.get(key, 0) + 1
        return self.seq[key]

    # ------------------------------------------------------------------ budget lines
    def build_lines(self):
        office_bias = {o[0]: o[2] for o in OFFICES}
        counters = {}
        for office, approp, name in PPAS:
            counters[(office, approp)] = counters.get((office, approp), 0) + 1
            ppa_code = f"{office}-{approp}-{counters[(office, approp)]:02d}"
            a_name, fund_type, years, main_acct, (lo, hi), mix = APPROPRIATIONS[approp]
            ppa_bias = float(self.rng.normal(0, 0.25))
            base = float(self.rng.uniform(lo, hi)) * 1e6
            pm, analyst = self.rng.choice(self.staff[office], 2, replace=False)
            self.ppa_master.append({
                "ppa_code": ppa_code, "ppa_name": name, "office_code": office,
                "office_name": next(o[1] for o in OFFICES if o[0] == office),
                "appropriation_code": approp, "appropriation_name": a_name,
                "main_account": f"{AGENCY_CODE}-{main_acct}", "fund_type": fund_type,
                "years_of_availability": years, "program_manager": pm["name"],
                "program_manager_email": pm["email"], "budget_analyst": analyst["name"],
                "budget_analyst_email": analyst["email"],
            })
            for bfy in BUDGET_FISCAL_YEARS:
                epoa = bfy + years - 1
                tas = (f"{AGENCY_CODE}-{bfy}-{main_acct}" if years == 1
                       else f"{AGENCY_CODE}-{bfy}/{epoa}-{main_acct}")
                enacted = round(base * (1 + 0.04 * (bfy - 2023)) * self.rng.uniform(0.92, 1.08), -3)
                pb_request = round(enacted * self.rng.uniform(0.95, 1.15), -3)
                health = office_bias[office] + ppa_bias + float(self.rng.normal(0, 0.3))
                mix_perturbed = self.rng.dirichlet(np.array(list(mix.values())) * 40)
                self.lines.append(BudgetLine(
                    bfy=bfy, ppa_code=ppa_code, ppa_name=name, office=office, approp=approp,
                    fund_type=fund_type, years=years, tas=tas,
                    start=date(bfy - 1, 10, 1), expiration=date(epoa, 9, 30),
                    pb_request=pb_request, enacted=enacted, health=health,
                    boc_mix=dict(zip(mix.keys(), mix_perturbed)),
                ))

    def _curve(self, category: str, years: int) -> np.ndarray:
        base = np.array(PLAN_CURVES[category], float)
        base = base / base.sum()
        return np.concatenate([base * s for s in MULTI_YEAR_SHARE[years]])

    # ------------------------------------------------------------------ simulation
    def simulate(self):
        for line in self.lines:
            self._simulate_line(line)

    def _simulate_line(self, line: BudgetLine):
        rng = self.rng
        h = line.health
        plan_total = line.enacted * rng.uniform(0.975, 0.995)
        n_months = 12 * line.years
        requirements = []
        for boc, share in line.boc_mix.items():
            category = OBJECT_CLASSES[boc][1]
            curve = self._curve(category, line.years)
            amount = plan_total * share
            line.monthly_plan[boc] = amount * curve
            lo, hi = REQUIREMENT_SIZE[category]
            n = max(1, int(round(amount / math.sqrt(lo * hi))))
            sizes = amount * rng.dirichlet(np.full(n, 2.0))
            months = rng.choice(n_months, size=n, p=curve)
            for size, m in zip(sizes, months):
                ms = _month_start(line.start, int(m))
                planned_award = ms + timedelta(days=int(rng.integers(0, 28)))
                requirements.append((boc, category, float(size), planned_award, False))

        prs = [self._make_pr(line, *r) for r in requirements]

        # Q4 sweep: offices look at the projected unobligated balance ~70-110 days before
        # expiration and push short-PALT actions (options, mods, task orders).
        checkpoint = line.expiration - timedelta(days=int(rng.integers(70, 110)))
        projected = sum(p["award_amount"] for p in prs
                        if p["award_date"] and p["award_date"] <= line.expiration)
        gap = line.enacted - projected
        if gap / line.enacted > 0.02:
            frac = float(np.clip(0.65 + 0.25 * h + rng.normal(0, 0.12), 0.15, 0.95))
            sweep_total = gap * frac
            k = int(rng.integers(1, 5))
            service_bocs = [b for b in line.boc_mix if OBJECT_CLASSES[b][1] in
                            ("services", "equipment", "research", "supplies")] or list(line.boc_mix)
            for amt in sweep_total * rng.dirichlet(np.full(k, 2.0)):
                boc = str(rng.choice(service_bocs))
                submit = checkpoint + timedelta(days=int(rng.integers(0, 25)))
                prs.append(self._make_pr(line, boc, OBJECT_CLASSES[boc][1], float(amt),
                                         submit, True))

        # Funds control: certify in award order and never exceed enacted authority.
        prs.sort(key=lambda p: p["award_date"] or date.max)
        cumulative = 0.0
        for p in prs:
            if not p["award_date"] or p["cancel_date"]:
                continue
            if p["award_date"] > line.expiration:
                p["cancel_date"] = line.expiration - timedelta(days=int(rng.integers(0, 8)))
                p["cancel_reason"] = "Funds expiring - unable to award before expiration"
                p["award_date"] = None
                continue
            remaining = line.enacted - cumulative
            if p["award_amount"] > remaining:
                if remaining > 0.25 * p["award_amount"]:
                    p["award_amount"] = round(remaining * 0.999, 2)
                else:
                    p["cancel_date"] = p["award_date"]
                    p["cancel_reason"] = "Insufficient funds available on line"
                    p["award_date"] = None
                    continue
            cumulative += p["award_amount"]
            self._record_award(line, p)
        line.prs = prs

    def _make_pr(self, line, boc, category, amount, anchor, is_sweep):
        rng = self.rng
        h = line.health
        mix = ACQUISITION_MIX[category]
        acq = str(rng.choice(list(mix.keys()), p=list(mix.values())))
        if is_sweep:
            acq = str(rng.choice(["Option Exercise", "Modification", "Task Order"],
                                 p=[0.4, 0.3, 0.3]))
        if acq == "New Award" and amount < 250_000:
            acq = "New Award (Simplified)"
        median = PALT_MEDIAN_DAYS[acq]
        if acq == "New Award":
            median += 12 * max(0.0, math.log10(amount / 1e6) * 2)
        palt = median * float(rng.lognormal(0, 0.25)) * (1 + 0.25 * max(0.0, -h))

        if is_sweep:
            submit = anchor
        else:
            slip = float(rng.gamma(2.0, 4 + 12 * max(0.0, -h))) - 15 * max(0.0, h) - 20
            submit = anchor - timedelta(days=int(median - slip))
        earliest = line.start + timedelta(days=int(rng.integers(0, 20)))
        submit = max(submit, earliest)
        award = submit + timedelta(days=int(palt))

        enacted_on = ENACTMENT_DATES.get(line.bfy)
        if (enacted_on and award < enacted_on and line.start < enacted_on
                and (acq in ("New Award", "Grant Award", "New Award (Simplified)")
                     or rng.random() < 0.5)):
            award = enacted_on + timedelta(days=int(rng.integers(7, 45)))

        cancel_date, cancel_reason = None, None
        if rng.random() < 0.02 + 0.04 * max(0.0, -h):
            cancel_date = submit + timedelta(days=int(max(1, palt * rng.uniform(0.2, 0.9))))
            cancel_reason = str(rng.choice([
                "Requirement withdrawn by program office", "Requirement consolidated",
                "No acceptable offers received"]))
            award = None

        if acq == "Grant Award":
            vehicle = "Notice of Funding Opportunity"
        elif acq in ("Option Exercise", "Modification"):
            vehicle = "Existing contract"
        elif acq == "Task Order":
            vehicle = {"equipment": "NASA SEWP V", "supplies": "GSA MAS"}.get(
                category, str(rng.choice(["DCI Professional Services IDIQ", "GSA MAS"])))
        elif category == "research":
            vehicle = "Broad Agency Announcement"
        elif acq == "New Award (Simplified)":
            vehicle = "Open Market - Simplified Acquisition"
        else:
            vehicle = "Open Market - Full and Open Competition"

        title = str(rng.choice(REQUIREMENT_TITLES[boc])).format(
            ppa=line.ppa_name, site=rng.choice(SITES), n=int(rng.integers(1, 9)))
        if is_sweep:
            title = f"{title} (year-end)"
        requester = self.staff[line.office][int(rng.integers(0, 4))]
        co = self.staff["ACQ"][int(rng.integers(0, 8))]
        pr_id = f"PR-{line.bfy % 100:02d}-{line.office}-{self._next(('pr', line.bfy, line.office)):04d}"
        estimate = round(amount, 2)
        return {
            "pr_id": pr_id, "line": line, "boc": boc, "category": category,
            "acquisition_type": acq, "vehicle": vehicle, "title": title,
            "estimated_amount": estimate,
            "award_amount": round(estimate * float(rng.uniform(0.94, 1.03)), 2),
            "priority": str(rng.choice(["High", "Medium", "Low"], p=[0.25, 0.55, 0.2])),
            "requested_by": requester, "contracting_officer": co,
            "created_date": submit - timedelta(days=int(rng.integers(1, 15))),
            "submit_date": submit, "award_date": award, "palt_days": int(palt),
            "cancel_date": cancel_date, "cancel_reason": cancel_reason,
            "need_by_date": anchor if not is_sweep else line.expiration - timedelta(days=15),
            "is_sweep": is_sweep,
        }

    def _record_award(self, line, p):
        rng = self.rng
        if p["acquisition_type"] in ("Option Exercise", "Modification"):
            pool = self.incumbents.get(line.ppa_code) or []
            if pool:
                parent = pool[int(rng.integers(0, len(pool)))]
                contract, vendor = parent["contract_number"], parent["vendor"]
                parent["mods"] += 1
                mod = f"P{parent['mods']:05d}"
            else:
                p["acquisition_type"] = "Task Order"
                p["vehicle"] = "GSA MAS"
                contract, vendor, mod = None, None, "000"
        else:
            contract, vendor, mod = None, None, "000"
        if contract is None:
            letter = {"Grant Award": "G", "Task Order": "F"}.get(p["acquisition_type"], "C")
            contract = f"DCI{line.bfy % 100:02d}{letter}{self._next(('piid', letter)):06d}"
            pool_src = self.grantees if p["category"] == "grants" else self.vendors
            vendor = pool_src[int(rng.integers(0, len(pool_src)))]
            if p["category"] in ("services", "research"):
                self.incumbents.setdefault(line.ppa_code, []).append(
                    {"contract_number": contract, "vendor": vendor, "mods": 0})
        p["contract_number"], p["modification_number"], p["vendor"] = contract, mod, vendor
        line.obligations.append((p["award_date"], p["award_amount"], p["pr_id"], contract, mod))
        self.awards.append(p)

        # Occasional deobligation at closeout / descoping.
        if rng.random() < 0.06:
            d = p["award_date"] + timedelta(days=int(rng.integers(150, 420)))
            amt = -round(p["award_amount"] * float(rng.uniform(0.03, 0.15)), 2)
            p.setdefault("deobligations", []).append((d, amt))
            line.obligations.append((d, amt, p["pr_id"], contract, "DEOB"))

    # ------------------------------------------------------------------ emitters
    def _ts(self, d: date) -> datetime:
        return datetime.combine(d, time(int(self.rng.integers(7, 19)), int(self.rng.integers(0, 60)),
                                        int(self.rng.integers(0, 60))))

    def _pr_header(self, p):
        line = p["line"]
        ppa = line.ppa_code
        if self.rng.random() < 0.015:  # free-text entry errors in the tracker
            ppa = f" {ppa.lower()} "
        return {
            "pr_id": p["pr_id"], "fiscal_year": line.bfy, "ppa_code": ppa, "tas": line.tas,
            "office_code": line.office, "title": p["title"],
            "description": (f"{p['title']} supporting the {line.ppa_name} PPA. Funded from "
                            f"{line.tas} (object class {p['boc']} "
                            f"{OBJECT_CLASSES[p['boc']][0]})."),
            "object_class": p["boc"], "acquisition_type": p["acquisition_type"],
            "contract_vehicle": p["vehicle"], "estimated_amount": p["estimated_amount"],
            "priority": p["priority"], "requested_by": p["requested_by"]["email"],
            "contracting_officer": p["contracting_officer"]["email"],
            "need_by_date": p["need_by_date"].isoformat(), "year_end_action": p["is_sweep"],
        }

    def build_pr_events(self):
        for line in self.lines:
            for p in line.prs:
                self._emit_pr(p)
        # export overlap: a handful of events are delivered twice
        dupes = self.rng.choice(len(self.events), size=len(self.events) // 250, replace=False)
        self.events.extend(dict(self.events[i]) for i in dupes)
        # a few malformed events with no PR id
        for i in self.rng.choice(len(self.events), size=6, replace=False):
            bad = json.loads(json.dumps(self.events[i], default=str))
            bad["pr"]["pr_id"] = None
            bad["event_id"] = f"EVT-X{i:07d}"
            self.events.append(bad)

    def _emit_pr(self, p):
        rng = self.rng
        end = p["award_date"] or p["cancel_date"] or p["line"].expiration
        steps = [("Draft", p["created_date"]), ("Submitted", p["submit_date"])]
        span = max((end - p["submit_date"]).days, 4)
        certify = p["submit_date"] + timedelta(days=int(min(rng.integers(2, 12), span * 0.3)))
        steps.append(("Funds Certified", certify))
        if p["acquisition_type"] not in ("Option Exercise", "Modification"):
            sol = certify + timedelta(days=int(min(rng.integers(3, 15), span * 0.2)))
            steps.append(("In Solicitation", sol))
            if p["acquisition_type"] in ("New Award", "Grant Award"):
                steps.append(("Under Evaluation", sol + timedelta(days=int((end - sol).days * 0.55))))
        if p["award_date"]:
            steps.append(("Awarded", p["award_date"]))
        elif p["cancel_date"]:
            steps = [s for s in steps if s[1] < p["cancel_date"]]
            steps.append(("Cancelled", p["cancel_date"]))

        header = self._pr_header(p)
        for status, d in steps:
            ts = self._ts(d)
            if ts > self.as_of_ts:
                break
            award = None
            if status == "Awarded":
                award = self._award_payload(p, p["award_date"], p["award_amount"],
                                            p["modification_number"])
            self.events.append({
                "event_id": f"EVT-{self._next('evt'):07d}",
                "event_type": "AWARD" if status == "Awarded" else "PR_STATUS_CHANGE",
                "event_ts": ts.isoformat(), "source_system": "PR Tracker (SharePoint list export)",
                "status": status,
                "status_reason": p["cancel_reason"] if status == "Cancelled" else None,
                "updated_by": (p["contracting_officer"] if status in
                               ("In Solicitation", "Under Evaluation", "Awarded")
                               else p["requested_by"])["email"],
                "pr": header, "award": award,
            })
        for d, amt in p.get("deobligations", []):
            ts = self._ts(d)
            if ts > self.as_of_ts:
                continue
            self.events.append({
                "event_id": f"EVT-{self._next('evt'):07d}", "event_type": "MODIFICATION",
                "event_ts": ts.isoformat(), "source_system": "PR Tracker (SharePoint list export)",
                "status": "Awarded", "status_reason": "Deobligation - descoped / closeout",
                "updated_by": p["contracting_officer"]["email"], "pr": header,
                "award": self._award_payload(p, d, amt, f"D{self._next(('deob', p['pr_id'])):04d}"),
            })

    def _award_payload(self, p, d, amount, mod):
        pop_months = {"services": 12, "research": 18, "supplies": 3, "equipment": 6,
                      "construction": 18, "grants": 24}[p["category"]]
        return {
            "contract_number": p["contract_number"], "modification_number": mod,
            "action_date": d.isoformat(), "obligated_amount": amount,
            "period_of_performance_start": d.isoformat(),
            "period_of_performance_end": (_month_start(d, pop_months) - timedelta(days=1)).isoformat(),
            "vendor": {"name": p["vendor"]["name"], "uei": p["vendor"]["uei"]},
        }

    def build_invoices(self):
        rng = self.rng
        for p in self.awards:
            if p["award_date"] > self.as_of:
                continue
            amt, cat, d0 = p["award_amount"], p["category"], p["award_date"]
            if cat in ("services", "research"):
                n = 12 if cat == "services" else 6
                gap = 30 if cat == "services" else 90
                sched = [(d0 + timedelta(days=gap * (i + 1)), amt / n * rng.uniform(0.85, 1.08))
                         for i in range(n)]
            elif cat in ("supplies", "equipment"):
                first = d0 + timedelta(days=int(rng.integers(30, 120)))
                if rng.random() < 0.6:
                    sched = [(first, amt)]
                else:
                    sched = [(first, amt * 0.7), (first + timedelta(days=45), amt * 0.3)]
            elif cat == "construction":
                n = int(rng.integers(9, 18))
                sched = [(d0 + timedelta(days=30 * (i + 1)), amt * 0.9 / n) for i in range(n)]
                sched.append((d0 + timedelta(days=30 * (n + 2)), amt * 0.1))
            else:  # grant drawdowns, quarterly over two years
                sched = [(d0 + timedelta(days=91 * (i + 1)), amt / 8 * rng.uniform(0.7, 1.2))
                         for i in range(8)]
            billed = 0.0
            for inv_date, a in sched:
                a = round(min(a, amt - billed), 2)
                if a <= 0:
                    break
                if rng.random() < 0.0012:  # over-billing beyond the obligated amount
                    a = round(a * rng.uniform(1.8, 3.0), 2)
                billed += a
                self._emit_invoice(p, inv_date, a)
        # duplicates: same vendor invoice resubmitted under a new system id
        for i in rng.choice(len(self.invoices), size=len(self.invoices) // 900, replace=False):
            dup = dict(self.invoices[i])
            dup["invoice_id"] = f"INV-{self._next('inv'):08d}"
            dup["received_date"] = (date.fromisoformat(dup["received_date"])
                                    + timedelta(days=int(rng.integers(2, 20)))).isoformat()
            if date.fromisoformat(dup["received_date"]) <= self.as_of:
                dup["status"], dup["approved_date"], dup["paid_date"] = "Received", None, None
                dup["paid_amount"], dup["interest_penalty"] = None, None
                self.invoices.append(dup)
        # unknown contract numbers (keying errors at intake)
        for i in rng.choice(len(self.invoices), size=12, replace=False):
            inv = self.invoices[i]
            bad = inv["contract_number"][:-2] + "XX"
            inv["obligation_document"] = inv["obligation_document"].replace(inv["contract_number"], bad)
            inv["contract_number"] = bad

    def _emit_invoice(self, p, inv_date, amount):
        rng = self.rng
        received = inv_date + timedelta(days=int(rng.integers(0, 6)))
        if received > self.as_of:
            return
        h = p["line"].health
        due = received + timedelta(days=30)
        status, approved, paid, paid_amt, interest = "Received", None, None, None, 0.0
        if rng.random() < 0.02:
            status = "Rejected"
        else:
            approve_lag = int(rng.integers(3, 18) * (1 + 0.5 * max(0.0, -h)))
            pay_lag = int(rng.integers(2, 10))
            if rng.random() < 0.03 + 0.04 * max(0.0, -h):
                pay_lag += int(rng.integers(20, 60))
            a_d = received + timedelta(days=approve_lag)
            p_d = a_d + timedelta(days=pay_lag)
            if a_d <= self.as_of:
                status, approved = "Approved", a_d
            if p_d <= self.as_of:
                status, paid, paid_amt = "Paid", p_d, amount
                late = (p_d - due).days
                if late > 0:
                    interest = round(amount * PROMPT_PAY_RATE * late / 360, 2)
        vendor = p["vendor"]
        amount_str = f"${amount:,.2f}" if rng.random() < 0.06 else f"{amount:.2f}"
        self.invoices.append({
            "invoice_id": f"INV-{self._next('inv'):08d}",
            "vendor_invoice_number": f"{vendor['name'][:3].upper()}-{self._next(('vinv', vendor['uei'])):05d}",
            "contract_number": p["contract_number"],
            "obligation_document": f"{p['contract_number']}-{p['modification_number']}",
            "invoice_type": "Grant Drawdown" if p["category"] == "grants" else "Vendor Invoice",
            "vendor_name": vendor["name"], "vendor_uei": vendor["uei"], "vendor_tin": vendor["tin"],
            "remit_routing_number": vendor["routing"], "remit_account_number": vendor["account"],
            "invoice_date": inv_date.isoformat(), "received_date": received.isoformat(),
            "invoice_amount": amount_str, "status": status,
            "approved_date": approved.isoformat() if approved else None,
            "paid_date": paid.isoformat() if paid else None,
            "paid_amount": round(paid_amt, 2) if paid_amt else None,
            "prompt_pay_due_date": due.isoformat(), "interest_penalty": interest or None,
            "submitted_via": ("Payment Management System" if p["category"] == "grants"
                              else "Invoice Processing Platform"),
            "extract_date": self.as_of.isoformat(),
        })

    # ------------------------------------------------------------------ spend plans
    def _actual_by_month(self, line: BudgetLine) -> dict:
        """Actual obligations by (boc, month index) for re-forecast revisions."""
        out = {b: np.zeros(12 * line.years) for b in line.boc_mix}
        for p in line.prs:
            if p.get("award_date"):
                m = (p["award_date"].year - line.start.year) * 12 + p["award_date"].month - 10
                if 0 <= m < 12 * line.years:
                    out[p["boc"]][m] += p["award_amount"]
        return out

    def build_spend_plans(self) -> list[tuple[str, pd.DataFrame]]:
        files = []
        offices = {o[0]: o for o in OFFICES}
        for bfy in BUDGET_FISCAL_YEARS:
            for office, (_, _, _, template, revises) in offices.items():
                lines = [l for l in self.lines if l.bfy == bfy and l.office == office]
                years = max(l.years for l in lines)
                start = date(bfy - 1, 10, 1)
                rev_dates = [start - timedelta(days=20),
                             ENACTMENT_DATES[bfy] + timedelta(days=21)]
                if revises:
                    for k in range(years):
                        rev_dates += [date(bfy + k, 4, 15), date(bfy + k, 7, 10)]
                        if k + 1 < years:
                            rev_dates.append(date(bfy + k, 10, 20))
                rev_dates = sorted(set(d for d in rev_dates if d <= self.as_of))
                for rev, rd in enumerate(rev_dates, start=1):
                    rows = []
                    for line in lines:
                        rows += self._plan_rows(line, rev, rd)
                    df = self._format_plan(pd.DataFrame(rows), template, office)
                    folder = "budget_office_template" if template == "A" else "legacy_office_template"
                    files.append((f"{folder}/spend_plan_FY{bfy}_{office}_rev{rev:02d}_{rd.isoformat()}.csv", df))
        return files

    def _plan_rows(self, line: BudgetLine, rev: int, rev_date: date) -> list[dict]:
        rows = []
        n = 12 * line.years
        scale = (line.pb_request / line.enacted) if rev == 1 else 1.0
        actual = self._actual_by_month(line) if rev > 2 else None
        cur_m = (rev_date.year - line.start.year) * 12 + rev_date.month - 10
        for boc, plan in line.monthly_plan.items():
            p = plan * scale
            if actual is not None and cur_m > 0:
                past = actual[boc][:min(cur_m, n)]
                remaining_target = plan.sum() - past.sum()
                fut_w = plan[min(cur_m, n):]
                fut = (fut_w / fut_w.sum() * max(remaining_target, 0)) if fut_w.sum() > 0 else fut_w
                p = np.concatenate([past, fut])
            cat = OBJECT_CLASSES[boc][1]
            lag = {"services": 1, "research": 2, "supplies": 1, "equipment": 3,
                   "construction": 4, "grants": 3}[cat]
            spread = {"services": 12, "research": 12, "supplies": 1, "equipment": 2,
                      "construction": 12, "grants": 12}[cat]
            outlay = np.zeros(n)
            for m in range(n):
                for k in range(spread):
                    j = m + lag + k
                    if j < n:
                        outlay[j] += p[m] / spread
            for m in range(n):
                rows.append({"bfy": line.bfy, "ppa_code": line.ppa_code, "ppa_name": line.ppa_name,
                             "tas": line.tas, "boc": boc, "month": _month_start(line.start, m),
                             "obligations": round(float(p[m]), 2),
                             "outlays": round(float(outlay[m]), 2),
                             "updated_by": line.ppa_code})
        return rows

    def _format_plan(self, df: pd.DataFrame, template: str, office: str) -> pd.DataFrame:
        analyst = self.staff[office][0]["email"]
        if template == "A":
            return pd.DataFrame({
                "Fiscal Year": df["bfy"],
                "PPA Code": df["ppa_code"],
                "PPA Name": df["ppa_name"],
                "Fund (TAS)": df["tas"],
                "Object Class": df["boc"].map(lambda b: f"{b} {OBJECT_CLASSES[b][0]}"),
                "Month": df["month"].map(lambda d: d.strftime("%b-%y")),
                "Planned Obligations": df["obligations"].map(lambda v: f"${v:,.2f}"),
                "Planned Expenditures": df["outlays"].map(lambda v: f"${v:,.2f}"),
                "Last Updated By": analyst,
            })
        # Template B: different headers, $K units, ISO periods, lower-case PPA codes
        return pd.DataFrame({
            "FY": df["bfy"],
            "PPA": df["ppa_code"].str.lower(),
            "Fund": df["tas"],
            "BOC": df["boc"],
            "Period": df["month"].map(lambda d: d.strftime("%Y-%m")),
            "Obligation Plan ($K)": (df["obligations"] / 1000).round(1),
            "Outlay Plan ($K)": (df["outlays"] / 1000).round(1),
            "Owner": analyst,
        })

    # ------------------------------------------------------------------ budget authority
    def build_budget_authority(self) -> dict[int, pd.DataFrame]:
        out = {}
        withheld_line = next(l for l in self.lines
                             if l.bfy == 2026 and l.ppa_code == "OCIO-PCI-01")
        for bfy in BUDGET_FISCAL_YEARS:
            rows = []
            for l in (x for x in self.lines if x.bfy == bfy):
                q = [0.30, 0.55, 0.80, 1.0] if l.years == 1 else [0.35, 0.60, 0.85, 1.0]
                appr = [round(l.enacted * s, -3) for s in q]
                note = None
                if l is withheld_line:
                    # OMB footnote withholds part of the line pending a spend-plan notification;
                    # obligations already exceed the apportioned amount (ADA exposure).
                    ob = sum(a for d, a, *_ in l.obligations if d <= self.as_of)
                    appr = [min(a, round(ob * 0.96, -3)) for a in appr]
                    note = "Footnote B: balance withheld pending congressional spend-plan notification"
                rows.append({
                    "budget_fiscal_year": bfy, "ppa_code": l.ppa_code, "tas": l.tas,
                    "fund_type": l.fund_type, "beginning_poa": bfy,
                    "ending_poa": bfy + l.years - 1, "expiration_date": l.expiration.isoformat(),
                    "presidents_budget_request": l.pb_request, "enacted_amount": l.enacted,
                    "enactment_date": ENACTMENT_DATES[bfy].isoformat(),
                    "apportioned_q1": appr[0], "apportioned_q2": appr[1],
                    "apportioned_q3": appr[2], "apportioned_q4": appr[3],
                    "apportionment_footnote": note,
                })
            out[bfy] = pd.DataFrame(rows)
        return out

    # ------------------------------------------------------------------ ground truth
    def ground_truth(self) -> pd.DataFrame:
        """Simulated final outcome per line (not landed; used only to sanity-check the build)."""
        rows = []
        for l in self.lines:
            final = sum(a for d, a, *_ in l.obligations if d <= l.expiration)
            rows.append({"bfy": l.bfy, "ppa_code": l.ppa_code, "office": l.office,
                         "expiration": l.expiration, "enacted": l.enacted, "health": l.health,
                         "final_obligated": final, "lapse_pct": 1 - final / l.enacted})
        return pd.DataFrame(rows)


def generate(output_dir: str, seed: int = 42, as_of: date = DEFAULT_AS_OF) -> dict:
    """Generate all raw feeds under ``output_dir`` and return file counts."""
    g = Generator(seed=seed, as_of=as_of)
    g.build_lines()
    g.simulate()
    g.build_pr_events()
    g.build_invoices()

    root = Path(output_dir)
    for sub in ("reference", "budget_authority", "spend_plan/budget_office_template",
                "spend_plan/legacy_office_template", "procurement_requests", "invoices"):
        (root / sub).mkdir(parents=True, exist_ok=True)

    pd.DataFrame(g.ppa_master).to_csv(root / "reference" / "ppa_master.csv", index=False)
    for bfy, df in g.build_budget_authority().items():
        df.to_csv(root / "budget_authority" / f"budget_authority_FY{bfy}.csv", index=False)

    plans = g.build_spend_plans()
    for name, df in plans:
        df.to_csv(root / "spend_plan" / name, index=False)

    by_month: dict[str, list[dict]] = {}
    for e in g.events:
        by_month.setdefault(e["event_ts"][:7], []).append(e)
    for month, evs in by_month.items():
        evs.sort(key=lambda e: e["event_ts"])
        with open(root / "procurement_requests" / f"pr_events_{month}.jsonl", "w") as f:
            for e in evs:
                f.write(json.dumps(e, default=str) + "\n")

    inv = pd.DataFrame(g.invoices)
    inv["_month"] = inv["received_date"].str[:7]
    for month, df in inv.groupby("_month"):
        df.drop(columns="_month").to_csv(root / "invoices" / f"invoices_{month}.csv", index=False)

    return {
        "as_of": as_of.isoformat(),
        "budget_lines": len(g.lines),
        "ppas": len(g.ppa_master),
        "spend_plan_files": len(plans),
        "spend_plan_rows": int(sum(len(df) for _, df in plans)),
        "pr_event_files": len(by_month),
        "pr_events": len(g.events),
        "procurement_requests": int(sum(len(l.prs) for l in g.lines)),
        "invoice_files": int(inv["_month"].nunique()),
        "invoices": len(inv),
        "ground_truth": g.ground_truth(),
    }
