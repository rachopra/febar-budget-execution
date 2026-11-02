# Databricks App API evidence: `febar-budget-execution`

- URL: https://febar-budget-execution-7474648312380302.aws.databricksapps.com
- App status: RUNNING / compute ACTIVE
- Active deployment: `01f1d6e8164911d781b6ce29f79f7150` (SUCCEEDED)
- Resources: lakebase (postgres), genie (genie_space), llm (serving_endpoint), warehouse (sql_warehouse)
- User API scopes (on-behalf-of-user): dashboards.genie, iam.access-control:read, iam.current-user:read
- Captured 2026-11-02 18:06 UTC

## Health (Lakebase connectivity)

`GET /api/health` → **HTTP 200** in 751 ms

Response:
```json
{
 "status": "ok",
 "today": "2026-11-02"
}
```

## Signed-in user, office scope (from office_access_map) and approval rights

`GET /api/me` → **HTTP 200** in 28 ms

Response:
```json
{
 "email": "rahul.chopra@databricks.com",
 "role": "Budget Director",
 "offices": null,
 "genie_on_behalf_of_user": true,
 "can_approve_reprogramming": true
}
```

## Command center: year-end countdown, projected lapse vs actions in flight, acquisition windows, expiring-dollar composition, offices, top lines, work queue

`GET /api/command-center` → **HTTP 200** in 227 ms

Response:
```json
{
 "calendar": {
  "as_of_date": "2026-07-31",
  "fiscal_year": 2026,
  "fiscal_year_start": "2025-10-01",
  "fiscal_year_end": "2026-09-30",
  "must_award_by": "2026-09-16",
  "days_left": 61,
  "fiscal_year_elapsed": 0.8324,
  "fiscal_quarter": 4,
  "last_completed_quarter": {
   "fiscal_year": 2026,
   "fiscal_quarter": 3
  }
 },
 "expiring": {
  "lines": 29,
  "total_budget": 1143720000.0,
  "unobligated": 306004573.34,
  "uncommitted": 46622100.27,
  "composition": [
   {
    "stage": "Obligated",
    "amount": 837715426.66
   },
   {
    "stage": "Committed (certified PRs)",
    "amount": 259382473.07
   },
   {
    "stage": "Requested (draft / submitted PRs)",
    "amount": 30059547.54
   },
   {
    "stage": "No action yet",
    "amount": 16562552.730000041
   }
  ]
 },
 "forecast": {
  "projected_lapse": 65866932.370000005,
  "lines": 29,
  "high_risk_lines": 11,
  "high_risk_lapse": 46526171.25,
  "projected_year_end_obligations": 1077853067.63,
  "forecast_budget": 1143720000.0,
  "by_tier": [
   {
    "risk_tier": "Critical",
    "lines": 4,
    "lapse": 23440695.42,
    "year_end_obligations": 141546304.58,
    "budget": 164987000.0
   },
   {
    "risk_tier": "High",
    "lines": 7,
    "lapse": 23085475.83,
    "year_end_obligations": 332752524.17,
    "budget": 355838000.0
   },
   {
    "risk_tier": "Moderate",
    "lines": 14,
    "lapse": 17373636.59,
    "year_end_obligations": 461275363.4100001,
    "budget": 478649000.0
   },
   {
    "risk_tier": "Low",
    "lines": 4,
    "lapse": 1967124.5299999998,
    "year_end_obligations": 142278875.47,
    "budget": 144246000.0
   }
  ],
  "recovery_in_flight": 12095124.850000001,
  "packaged": 11175124.850000001,
  "remaining_after_actions": 53771807.52
 },
 "windows": [
  {
   "acquisition_type": "Option Exercise",
   "median_palt_days": 21,
   "p80_palt_days": 29,
   "last_submit_conservative": "2026-08-18",
   "last_submit_typical": "2026-08-26",
   "status": "open",
   "days_to_close": 26,
   "open_prs": 24,
   "open_value": 18824582.24,
   "will_miss": 0
  },
  {
   "acquisition_type": "Modification",
   "median_palt_days": 26,
   "p80_palt_days": 32,
   "last_submit_conservative": "2026-08-15",
   "last_submit_typical": "2026-08-21",
   "status": "open",
   "days_to_close": 21,
   "open_prs": 21,
   "open_value": 33158039.38,
   "will_miss": 0
  },
  {
   "acquisition_type": "New Award (Simplified)",
   "median_palt_days": 51,
   "p80_palt_days": 118,
   "last_submit_conservative": "2026-05-21",
   "last_submit_typical": "2026-07-27",
   "status": "closed",
   "days_to_close": -4,
   "open_prs": 10,
   "open_value": 1112042.94,
   "will_miss": 0
  },
  {
   "acquisition_type": "Task Order",
   "median_palt_days": 59,
   "p80_palt_days": 82,
   "last_submit_conservative": "2026-06-26",
   "last_submit_typical": "2026-07-19",
   "status": "closed",
   "days_to_close": -12,
   "open_prs": 91,
   "open_value": 70744253.69,
   "will_miss": 1
  },
  {
   "acquisition_type": "Grant Award",
   "median_palt_days": 153,
   "p80_palt_days": 186,
   "last_submit_conservative": "2026-03-14",
   "last_submit_typical": "2026-04-16",
   "status": "closed",
   "days_to_close": -106,
   "open_prs": 42,
   "open_value": 116698372.88,
   "will_miss": 4
  },
  {
   "acquisition_type": "New Award",
   "median_palt_days": 155,
   "p80_palt_days": 189,
   "last_submit_conservative": "2026-03-11",
   "last_submit_typical": "2026-04-14",
   "status": "closed",
   "days_to_close": -108,
   "open_prs": 40,
   "open_value": 48904729.48,
   "will_miss": 5
  }
 ],
 "offices": [
  {
   "office_code": "OTS",
   "office_name": "Office of Transportation Safety",
   "total_budget": 304063000.0,
   "obligated": 176219742.52,
   "planned_to_date": 212135200.0,
   "burn_rate_vs_plan": 0.8306954363066572,
   "obligation_rate": 0.579550101525013,
   "unobligated_expiring": 45859296.01,
   "projected_lapse": 19386268.369999997,
   "open_critical": 0,
   "open_high": 16,
   "open_alerts": 27,
   "recovery_in_flight": 920000.0
  },
  {
   "office_code": "OWD",
   "office_name": "Office of Workforce Development",
   "total_budget": 165619000.0,
   "obligated": 95013158.46,
   "planned_to_date": 103978900.0,
   "burn_rate_vs_plan": 0.9137734526908825,
   "obligation_rate": 0.5736851355218906,
   "unobligated_expiring": 58205454.03,
   "projected_lapse": 12362037.120000001,
   "open_critical": 0,
   "open_high": 6,
   "open_alerts": 7,
   "recovery_in_flight": 9271284.71
  },
  {
   "office_code": "OGM",
   "office_name": "Office of Grid Modernization",
   "total_budget": 492585000.0,
   "obligated": 309543024.69,
   "planned_to_date": 337690850.79,
   "burn_rate_vs_plan": 0.9166461690207168,
   "obligation_rate": 0.6284052999786839,
   "unobligated_expiring": 65678015.5,
   "projected_lapse": 9690055.53,
   "open_critical": 0,
   "open_high": 17,
   "open_alerts": 26,
   "recovery_in_flight": 0.0
  },
  {
   "office_code": "OCIO",
   "office_name": "Office of the Chief Information Officer",
   "total_budget": 595446000.0,
   "obligated": 384930249.37,
   "planned_to_date": 418523015.98,
   "burn_rate_vs_plan": 0.9197349600204417,
   "obligation_rate": 0.6464570244321064,
   "unobligated_expiring": 47553796.75,
   "projected_lapse": 13385797.26,
   "open_critical": 1,
   "open_high": 7,
   "open_alerts": 12,
   "recovery_in_flight": 1903840.14
  },
  {
   "office_code": "OWS",
   "office_name": "Office of Water Systems",
   "total_budget": 297723000.0,
   "obligated": 190826633.76,
   "planned_to_date": 203165213.16,
   "burn_rate_vs_plan": 0.9392682477079237,
   "obligation_rate": 0.6409536171542004,
   "unobligated_expiring": 47725910.72,
   "projected_lapse": 6951438.730000001,
   "open_critical": 0,
   "open_high": 12,
   "open_alerts": 15,
   "recovery_in_flight": 0.0
  },
  {
   "office_code": "OMA",
   "office_name": "Office of Management and Administration",
   "total_budget": 291595000.0,
   "obligated": 199604608.08,
   "planned_to_date": 210395365.49,
 
```

## Cumulative obligations vs approved plan (burn curve)

`GET /api/burn` → **HTTP 200** in 58 ms

Response:
```json
[
 {
  "month": "2023-10-01",
  "is_actualized": true,
  "cumulative_planned_obligations": 4556923.12,
  "cumulative_actual_obligations": 0.0,
  "cumulative_planned_expenditures": 0.0,
  "cumulative_actual_expenditures": 0.0
 },
 {
  "month": "2023-11-01",
  "is_actualized": true,
  "cumulative_planned_obligations": 11431841.55,
  "cumulative_actual_obligations": 1366177.05,
  "cumulative_planned_expenditures": 163723.84,
  "cumulative_actual_expenditures": 0.0
 },
 {
  "month": "2023-12-01",
  "is_actualized": true,
  "cumulative_planned_obligations": 20231818.11,
  "cumulative_actual_obligations": 3397475.82,
  "cumulative_planned_expenditures": 523916.27,
  "cumulative_actual_expenditures": 63282.26
 },
 {
  "month": "2024-01-01",
  "is_actualized": true,
  "cumulative_planned_obligations": 33275048.09,
  "cumulative_actual_obligations": 7596595.67,
  "cumulative_planned_expenditures": 1747756.28,
  "cumulative_actual_expenditures": 430875.42
 },
 {
  "month": "2024-02-01",
  "is_actualized": true,
  "cumulative_planned_obligations": 49894052.51,
  "cumulative_actual_obligations": 10793083.44,
  "cumulative_planned_expenditures": 4306551.44,
  "cumulative_actual_expenditures": 1938264.94
 },
 {
  "month": "2024-03-01",
  "is_actualized": true,
  "cumulative_planned_obligations": 69695994.15,
  "cumulative_actual_obligations": 22895847.91,
  "cumulative_planned_expenditures": 8004330.26,
  "cumulative_actual_expenditures": 3272340.75
 },
 "... 30 more items"
]
```

## Budget execution KPIs, funding by office and appropriation

`GET /api/overview` → **HTTP 200** in 80 ms

Response:
```json
{
 "kpis": {
  "budget_lines": 45,
  "total_budget": 2147031000.0,
  "planned_obligations_to_date": 1485888545.42,
  "committed_not_obligated": 398885264.76,
  "obligated_to_date": 1356137416.88,
  "expended_to_date": 758243975.69,
  "unobligated_balance": 790893583.12,
  "obligation_rate": 0.631633831500337,
  "burn_rate_vs_plan": 0.912677751679333,
  "expenditure_rate": 0.35315930496113007,
  "unobligated_expiring_90d": 306004573.34,
  "projected_lapse": 65866932.37000001,
  "high_risk_lines": 11
 },
 "by_office": [
  {
   "office_code": "OTS",
   "office_name": "Office of Transportation Safety",
   "total_budget": 304063000.0,
   "obligated": 176219742.52,
   "expended": 103927579.69,
   "unobligated": 127843257.48,
   "obligation_rate": 0.579550101525013,
   "burn_rate_vs_plan": 0.8306954363066572
  },
  {
   "office_code": "OWD",
   "office_name": "Office of Workforce Development",
   "total_budget": 165619000.0,
   "obligated": 95013158.46,
   "expended": 23864443.73,
   "unobligated": 70605841.54,
   "obligation_rate": 0.5736851355218906,
   "burn_rate_vs_plan": 0.9137734526908825
  },
  {
   "office_code": "OGM",
   "office_name": "Office of Grid Modernization",
   "total_budget": 492585000.0,
   "obligated": 309543024.69,
   "expended": 153534307.28,
   "unobligated": 183041975.31,
   "obligation_rate": 0.6284052999786839,
   "burn_rate_vs_plan": 0.9166461690207168
  },
  {
   "office_code": "OCIO",
   "office_name": "Office of the Chief Information Officer",
   "total_budget": 595446000.0,
   "obligated": 384930249.37,
   "expended": 268996191.58,
   "unobligated": 210515750.63,
   "obligation_rate": 0.6464570244321064,
   "burn_rate_vs_plan": 0.9197349600204417
  },
  {
   "office_code": "OWS",
   "office_name": "Office of Water Systems",
   "total_budget": 297723000.0,
   "obligated": 190826633.76,
   "expended": 104605269.91,
   "unobligated": 106896366.24,
   "obligation_rate": 0.6409536171542004,
   "burn_rate_vs_plan": 0.9392682477079237
  },
  {
   "office_code": "OMA",
   "office_name": "Office of Management and Administration",
   "total_budget": 291595000.0,
   "obligated": 199604608.08,
   "expended": 103316183.5,
   "unobligated": 91990391.92,
   "obligation_rate": 0.6845268543013426,
   "burn_rate_vs_plan": 0.9487120004527244
  }
 ],
 "by_appropriation": [
  {
   "appropriation_name": "Procurement, Construction, and Improvements",
   "fund_type": "multi-year",
   "total_budget": 1344220000.0,
   "obligated": 845552699.9,
   "unobligated": 498667300.1,
   "obligation_rate": 0.6290285071640059
  },
  {
   "appropriation_name": "Operations and Support",
   "fund_type": "annual",
   "total_budget": 382238000.0,
   "obligated": 281465000.27,
   "unobligated": 100772999.73,
   "obligation_rate": 0.7363605927982042
  },
  {
   "appropriation_name": "Grants and Assistance",
   "fund_type": "annual",
   "total_budget": 249605000.0,
   "obligated": 110263782.05,
   "unobligated": 139341217.95,
   "obligation_rate": 0.4417530980949901
  },
  {
   "appropriation_name": "Research and Development",
   "fund_type": "multi-year",
   "total_budget": 170968000.0,
   "obligated": 118855934.66,
   "unobligated": 52112065.34,
   "obligation_rate": 0.6951940401712601
  }
 ]
}
```

## Global search (command palette)

`GET /api/search?q=grant` → **HTTP 200** in 58 ms

Response:
```json
{
 "lines": [
  {
   "line_id": "OGM-GA-01-FY2026",
   "ppa_name": "State Energy Resilience Grants",
   "office_code": "OGM",
   "tas": "999-2026-0600",
   "days_to_expiration": 61,
   "unobligated_balance": 40995906.13
  },
  {
   "line_id": "OWD-GA-01-FY2026",
   "ppa_name": "Infrastructure Workforce Grants",
   "office_code": "OWD",
   "tas": "999-2026-0600",
   "days_to_expiration": 61,
   "unobligated_balance": 38662242.55
  },
  {
   "line_id": "OWS-GA-01-FY2026",
   "ppa_name": "Tribal and Rural Water Grants",
   "office_code": "OWS",
   "tas": "999-2026-0600",
   "days_to_expiration": 61,
   "unobligated_balance": 29212969.59
  },
  {
   "line_id": "OWD-GA-02-FY2026",
   "ppa_name": "Apprenticeship Expansion Grants",
   "office_code": "OWD",
   "tas": "999-2026-0600",
   "days_to_expiration": 61,
   "unobligated_balance": 12919103.46
  },
  {
   "line_id": "OTS-GA-01-FY2026",
   "ppa_name": "Highway Safety Improvement Grants",
   "office_code": "OTS",
   "tas": "999-2026-0600",
   "days_to_expiration": 61,
   "unobligated_balance": 17550996.22
  }
 ],
 "prs": [
  {
   "pr_id": "PR-26-OWS-0157",
   "title": "Tribal and Rural Water Grants - formula allocation region 6",
   "line_id": "OWS-GA-01-FY2026",
   "office_code": "OWS",
   "status": "Under Evaluation",
   "estimated_amount": 6899266.29
  },
  {
   "pr_id": "PR-26-OGM-0204",
   "title": "State Energy Resilience Grants - cooperative agreement 2",
   "line_id": "OGM-GA-01-FY2026",
   "office_code": "OGM",
   "status": "Under Evaluation",
   "estimated_amount": 5859768.48
  },
  {
   "pr_id": "PR-26-OGM-0184",
   "title": "State Energy Resilience Grants - cooperative agreement 3",
   "line_id": "OGM-GA-01-FY2026",
   "office_code": "OGM",
   "status": "Under Evaluation",
   "estimated_amount": 5716704.86
  },
  {
   "pr_id": "PR-26-OTS-0200",
   "title": "Highway Safety Improvement Grants - competitive awards cohort 1",
   "line_id": "OTS-GA-01-FY2026",
   "office_code": "OTS",
   "status": "Under Evaluation",
   "estimated_amount": 5579292.96
  },
  {
   "pr_id": "PR-26-OWS-0154",
   "title": "Tribal and Rural Water Grants - cooperative agreement 1",
   "line_id": "OWS-GA-01-FY2026",
   "office_code": "OWS",
   "status": "Under Evaluation",
   "estimated_amount": 5575489.65
  },
  {
   "pr_id": "PR-26-OWD-0020",
   "title": "Infrastructure Workforce Grants - competitive awards cohort 8",
   "line_id": "OWD-GA-01-FY2026",
   "office_code": "OWD",
   "status": "Under Evaluation",
   "estimated_amount": 5421626.66
  },
  "... 2 more items"
 ]
}
```

## Year-end plan: lines projected to lapse, validated AI package drafts, what is already in flight, and same-account reprogramming matches

`GET /api/plan` → **HTTP 200** in 131 ms

Response:
```json
{
 "calendar": {
  "as_of_date": "2026-07-31",
  "fiscal_year": 2026,
  "fiscal_year_start": "2025-10-01",
  "fiscal_year_end": "2026-09-30",
  "must_award_by": "2026-09-16",
  "days_left": 61,
  "fiscal_year_elapsed": 0.8324,
  "fiscal_quarter": 4,
  "last_completed_quarter": {
   "fiscal_year": 2026,
   "fiscal_quarter": 3
  }
 },
 "lines": [
  {
   "line_id": "OWD-GA-01-FY2026",
   "ppa_name": "Infrastructure Workforce Grants",
   "office_code": "OWD",
   "office_name": "Office of Workforce Development",
   "tas": "999-2026-0600",
   "appropriation_name": "Grants and Assistance",
   "expiration_date": "2026-09-30",
   "days_to_expiration": 61,
   "total_budget": 65761000.0,
   "unobligated_balance": 38662242.55,
   "uncommitted_balance": 5293180.78,
   "burn_rate_vs_plan": 0.7253,
   "projected_lapse_amount": 9271284.71,
   "predicted_lapse_rate": 0.14098454568336033,
   "risk_tier": "Critical",
   "top_risk_drivers": [
    "cancelled PR value 13% vs typical 0% (+4.2 pp)",
    "obligations vs spend plan 80% vs typical 94% (+2.2 pp)",
    "long-PALT pipeline (new awards/grants) 42% vs typical 8% (+2.0 pp)"
   ],
   "draft_id": "PKG-OWD-GA-01-FY2026",
   "draft_title": "Year-End Option Exercise \u2013 Infrastructure Workforce Services (OWD-GA-01)",
   "draft_type": "Option Exercise",
   "draft_contract": "DCI26C000954",
   "draft_amount": 4207034.66,
   "draft_status": "AI Draft - Pending Program Office Review",
   "draft_issues": [],
   "draft_requirement_summary": "The Infrastructure Workforce Grants program office (OWD-GA-01) requires continued professional and technical services under object class 25.1 to support active grant administration, workforce development program delivery, and compliance monitoring activities through the current period of availability ending September 30, 2026. These services represent a bona fide need of FY 2026, as ongoing grant ...",
   "draft_justification": "Option exercises on existing contracts carry a median PALT of 21 days and a P80 PALT of 29 days, well within the 47 days remaining before the must-award date of September 16, 2026, providing substantial schedule margin even under adverse conditions. Contract DCI26C000954 with Cobalt Technologies Partners is already in place, fully executed, and priced for this option period, eliminating the need f...",
   "draft_documents": [
    "Signed Option Exercise Memorandum / Contracting Officer Determination",
    "Funding Cite / Fiscal Law Bona Fide Needs Determination (FY 2026 funds, period ending 2026-09-30)",
    "Certified Funds Availability Certification (Fund 999-2026-0600, $4,207,034.66)",
    "Independent Government Cost Estimate (IGCE) confirming option price reasonableness",
    "Contractor Performance Assessment Repository (CPARS) / Past Performance Review",
    "Scope Confirmation Memo from Contracting Officer's Representative (COR)",
    "... 3 more items"
   ],
   "draft_milestones": [
    "2026-07-30: Program office initiates requirement; COR drafts scope confirmation memo and bona fide needs determination",
    "2026-08-01: IGCE completed and certified by program office",
    "2026-08-04: Funding availability certified by Budget/Finance; PR package assembled",
    "2026-08-06: PR submitted to Contracting Officer; legal/policy review initiated",
    "2026-08-11: Contracting Officer completes review; any clarifications resolved with COR",
    "2026-08-13: Option Exercise Memorandum drafted and routed for CO signature",
    "... 4 more items"
   ],
   "packaged": 11617000.0,
   "reprogrammed": 0.0,
   "recovered": 9271284.71
  },
  {
   "line_id": "OCIO-PCI-01-FY2024",
   "ppa_name": "Financial System Modernization",
   "office_code": "OCIO",
   "office_name": "Office of the Chief Information Officer",
   "tas": "999-2024/2026-0400",
   "appropriation_name": "Procurement, Construction, and Improvements",
   "expiration_date": "2026-09-30",
   "days_to_expiration": 61,
   "total_budget": 102170000.0,
   "unobligated_balance": 28048367.82,
   "uncommitted_balance": 20062036.3,
   "burn_rate_vs_plan": 0.7686,
   "projected_lapse_amount": 7350824.6,
   "predicted_lapse_rate": 0.07194699615561008,
   "risk_tier": "High",
   "top_risk_drivers": [
    "cancelled PR value 16% vs typical 0% (+2.9 pp)",
    "prior-year lapse rate 3% vs typical 1% (+1.4 pp)"
   ],
   "draft_id": "PKG-OCIO-PCI-01-FY2024",
   "draft_title": "FY2026 Financial System Modernization \u2013 Year-End IT Professional Services Modification (DCI26F001274)",
   "draft_type": "Modification",
   "draft_contract": "DCI26F001274",
   "draft_amount": 1903840.14,
   "draft_status": "AI Draft - Pending Program Office Review",
   "draft_issues": [],
   "draft_requirement_summary": "The OCIO Financial System Modernization program (OCIO-PCI-01) requires continued IT professional services support during the current period of availability (FY2024\u20132026, expiring 30 September 2026) to sustain active modernization workstreams including system integration testing, data migration validation, and configuration management activities. These services represent a bona fide need of the cur...",
   "draft_justification": "Contract DCI26F001274 with Ironwood Solutions Corp. is an active service contract with a period of performance extending through 27 March 2027, providing a ready vehicle to absorb additional scope via modification well within the 47-day award window; the median modification PALT of 26 days (P80: 32 days) provides sufficient schedule margin against the 16 September 2026 must-award date. The existin...",
   "draft_documents": [
    "Independent Government Cost Estimate (IGCE)",
    "Statement of Work (SOW) / Performance Work Statement (PWS) \u2013 updated scope narrative",
    "Contracting Officer's Representative (COR) Designation Letter",
    "Bona Fide Need Determination memorandum signed by Program Manager",
    "Funds Availability Certification (FAC) / Fiscal Law Review",
    "Acquisition Plan or Simplified Acquisition Plan update"
```

## Line detail for OTS-PCI-01-FY2024: briefing, open PRs, alerts, package draft, reprogramming

`GET /api/lines/OTS-PCI-01-FY2024` → **HTTP 200** in 121 ms

Response:
```json
{
 "line": {
  "line_id": "OTS-PCI-01-FY2024",
  "budget_fiscal_year": 2024,
  "ppa_code": "OTS-PCI-01",
  "ppa_name": "Bridge Inspection Systems",
  "office_code": "OTS",
  "office_name": "Office of Transportation Safety",
  "appropriation_code": "PCI",
  "appropriation_name": "Procurement, Construction, and Improvements",
  "tas": "999-2024/2026-0400",
  "fund_type": "multi-year",
  "expiration_date": "2026-09-30",
  "as_of_date": "2026-07-31",
  "days_to_expiration": 61,
  "fund_status": "Current",
  "total_budget": 54467000.0,
  "apportioned_to_date": 54467000.0,
  "apportionment_footnote": null,
  "planned_obligations_total": 53385800.0,
  "planned_obligations_to_date": 51541900.0,
  "planned_expenditures_to_date": 46539100.0,
  "requested_not_certified": 0.0,
  "committed_not_obligated": 5891338.0,
  "obligated_to_date": 47378969.73,
  "deobligated_to_date": 231185.37,
  "obligated_last_30_days": 6952014.35,
  "invoiced_to_date": 38323639.51,
  "expended_to_date": 37694574.9,
  "invoices_pending_payment": 629064.61,
  "open_procurement_requests": 2,
  "spend_plan_revision": 2,
  "spend_plan_revised_on": "2024-04-13",
  "spend_plan_template": "legacy_office_template",
  "spend_plan_age_days": 839,
  "unobligated_balance": 7088030.27,
  "uncommitted_balance": 1196692.27,
  "undelivered_orders": 9684394.83,
  "obligation_rate": 0.8699,
  "expenditure_rate": 0.6921,
  "burn_rate_vs_plan": 0.9192,
  "expenditure_burn_vs_plan": 0.81,
  "obligation_variance_to_plan": -4162930.27,
  "execution_status": "On Plan",
  "baseline_plan_revision": 2,
  "reforecast_obligations_remaining": 1843900.0,
  "predicted_lapse_rate": 0.11198626172728568,
  "projected_lapse_amount": 6099555.72,
  "risk_tier": "Critical",
  "top_risk_drivers": [
   "cancelled PR value 11% vs typical 0% (+4.2 pp)",
   "prior-year lapse rate 3% vs typical 1% (+2.0 pp)",
   "obligations vs spend plan 92% vs typical 94% (+1.8 pp)"
  ],
  "spend_plan_implied_lapse_rate": 0.09628087229999996,
  "model_version": "2"
 },
 "briefing": {
  "headline": "Critical lapse risk: $6.1M projected to expire in 61 days",
  "summary": "Bridge Inspection Systems (OTS-PCI-01) has obligated $47.4M (87.0%) of its $54.5M budget, running at 91.9% of plan with a $7.1M unobligated balance and only 61 days before fund expiration on 2026-09-30. The forecast projects an 11.2% lapse ($6.1M) \u2014 exceeding the spend-plan-implied lapse of 9.6% \u2014 driven primarily by an abnormally high cancelled-PR rate (11% vs. 0% typical), an elevated prior-year...",
  "recommended_actions": [
   "OTS Budget Officer should immediately refresh the Spend Plan (currently Rev 2, aged 839 days since 2024-04-13) to reflect current committed-not-obligated balances ($5.9M) and the $1.2M uncommitted balance, and resubmit to the CFO no later than this Friday to support accurate lapse forecasting before the 2026-09-30 expiration.",
   "OTS Contracting Officer should confirm award timelines for PR-24-OTS-0113 (Albuquerque Test Range renovation, $5.3M, 52 days under evaluation) and PR-24-OTS-0141 (Network hardware refresh, $636.6K, 57 days in solicitation) \u2014 both forecast to award by 2026-08-01 \u2014 and provide written schedule certification to the Budget Director by end of week to validate that the $5.9M committed-not-obligated bala...",
   "The Disbursing/Accounts Payable Officer must resolve the duplicate invoice flag on Meridian Consulting LLC invoice MER-00119 ($64.1K, appearing as both INV-00009069 and INV-00019717) no later than today, and process or reject INV-00019717 immediately, as it was due 2026-04-01 and is actively accruing Prompt Payment Act interest."
  ],
  "grounding_passed": true,
  "model_endpoint": "databricks-claude-sonnet-4-6"
 },
 "open_procurements": [
  {
   "pr_id": "PR-24-OTS-0113",
   "title": "Facility renovation - Albuquerque Test Range",
   "acquisition_type": "New Award",
   "contract_vehicle": "Open Market - Full and Open Competition",
   "estimated_amount": 5254716.77,
   "status": "Under Evaluation",
   "days_in_status": 52,
   "forecast_award_date": "2026-08-01",
   "at_risk_of_missing_expiration": false
  },
  {
   "pr_id": "PR-24-OTS-0141",
   "title": "Network hardware refresh",
   "acquisition_type": "Task Order",
   "contract_vehicle": "NASA SEWP V",
   "estimated_amount": 636621.23,
   "status": "In Solicitation",
   "days_in_status": 57,
   "forecast_award_date": "2026-08-01",
   "at_risk_of_missing_expiration": false
  }
 ],
 "alerts": [
  {
   "alert_id": "09b56049fb3595d00a8cedbd06c536a669e3fcf5e5442b1fa61f969d5e4d2b01",
   "alert_type": "STALE_SPEND_PLAN",
   "severity": "Medium",
   "amount_at_risk": 7088030.27,
   "detail": "Bridge Inspection Systems spend plan was last revised 839 days ago (rev 2 on 2024-04-13); balances may be mis-forecast."
  },
  {
   "alert_id": "4124c112d40bc332f6b2603a0cd6236368698226d8f5223bbe68e01870016eb7",
   "alert_type": "PROMPT_PAY_RISK",
   "severity": "High",
   "amount_at_risk": 64094.65,
   "detail": "Invoice INV-00019717 ($64,095, Meridian Consulting LLC) is Received and was due on 2026-04-01; Prompt Payment Act interest accrues after the due date."
  },
  {
   "alert_id": "8bbf16a1ced5c3fa9338382f6755a80c8caee24a7f1b771e3bac88ffdf5fd5c5",
   "alert_type": "POTENTIAL_DUPLICATE_INVOICE",
   "severity": "High",
   "amount_at_risk": 64094.65,
   "detail": "Vendor invoice MER-00119 from Meridian Consulting LLC ($64,095) was received 2 times (INV-00009069, INV-00019717)."
  }
 ],
 "package_draft": {
  "package_id": "PKG-OTS-PCI-01-FY2024",
  "line_id": "OTS-PCI-01-FY2024",
  "office_code": "OTS",
  "ppa_code": "OTS-PCI-01",
  "facts_json": "{\"ppa\": \"Bridge Inspection Systems (OTS-PCI-01)\", \"fund\": \"999-2024/2026-0400\", \"expires_on\": \"2026-09-30\", \"must_award_by\": \"2026-09-16\", \"days_until_must_award\": 47, \"projected_lapse_amount\": 6099555.72, \"recommended_package_amount\": 4880000.0, \"feasible_acquisition_types\": [{\"type\": \"Option Exercise\", \"median_palt_days\": 21, 
```

## On-demand AI package redraft for OTS-PCI-01-FY2024 (real-time model, validated)

`POST /api/packages/OTS-PCI-01-FY2024/draft` → **HTTP 200** in 22718 ms

Response:
```json
{
 "line_id": "OTS-PCI-01-FY2024",
 "office_code": "OTS",
 "facts": {
  "ppa": "Bridge Inspection Systems (OTS-PCI-01)",
  "fund": "999-2024/2026-0400",
  "expires_on": "2026-09-30",
  "must_award_by": "2026-09-16",
  "days_until_must_award": 47,
  "projected_lapse_amount": 6099555.72,
  "recommended_package_amount": 4880000.0,
  "feasible_acquisition_types": [
   {
    "type": "Modification",
    "median_palt_days": 26,
    "p80_palt_days": 32
   },
   {
    "type": "Option Exercise",
    "median_palt_days": 21,
    "p80_palt_days": 29
   }
  ],
  "active_service_contracts_on_line": [
   {
    "contract_number": "DCI25C000558",
    "vendor": "Horizon Consulting Corp.",
    "object_class": "25.1",
    "obligated_to_date": 1039509.21
   },
   {
    "contract_number": "DCI26F000900",
    "vendor": "Vantage Integrators LLC",
    "object_class": "25.1",
    "obligated_to_date": 1014507.93
   },
   {
    "contract_number": "DCI23F000850",
    "vendor": "Apex Integrators JV",
    "object_class": "25.1",
    "obligated_to_date": 946285.34
   }
  ],
  "risk_drivers": [
   "cancelled PR value 11% vs typical 0% (+4.2 pp)",
   "prior-year lapse rate 3% vs typical 1% (+2.0 pp)",
   "obligations vs spend plan 92% vs typical 94% (+1.8 pp)"
  ]
 },
 "draft": {
  "title": "Year-End Option Exercise, Bridge Inspection Systems (OTS-PCI-01), Contract DCI25C000558",
  "recommended_acquisition_type": "Option Exercise",
  "contract_number": "DCI25C000558",
  "amount": 1039509.21,
  "requirement_summary": "Exercise the next option on contract DCI25C000558 (Horizon Consulting Corp., object class 25.1) to continue Bridge Inspection Systems services under PPA OTS-PCI-01. The services must be performed in the current period of availability, and fund 999-2024/2026-0400 expires 2026-09-30. The amount is capped at the contract's obligated_to_date ($1,039,509.21), which is used as a proxy for the priced opt...",
  "justification": "Projected lapse is $6,099,555.72, and the full recommended package amount was $4,880,000.00. None of the three active 25.1 service contracts can absorb that amount: DCI25C000558 at $1,039,509.21, DCI26F000900 at $1,014,507.93, and DCI23F000850 at $946,285.34. Stretching an option exercise or modification beyond a contract's priced value would risk an out-of-scope action and a non-bona-fide use of ...",
  "required_documents": [
   "Approved purchase request with certified funding on fund 999-2024/2026-0400",
   "Bona fide need statement confirming the services are performed in the current period of availability",
   "Option exercise request memo to the contracting officer",
   "Confirmation of option terms and priced option value from the contract file, with the amount not exceeding $1,039,509.21",
   "Statement of work or performance work statement consistent with the existing contract scope",
   "Independent government cost estimate or price reasonableness support against the option price",
   "... 4 more items"
  ],
  "milestones": [
   "2026-07-31: Decision to proceed with Option Exercise on DCI25C000558 at no more than $1,039,509.21; notify the contracting officer",
   "2026-08-05: Contracting officer confirms the option is unexercised, still within its exercise window, and its actual priced value; program office confirms in-period bona fide need",
   "2026-08-10: Finalize the SOW/PWS and the cost estimate or price reasonableness support",
   "2026-08-14: Purchase request approved and funds certified on 999-2024/2026-0400; the amount is set to the lesser of the priced option value or $1,039,509.21",
   "2026-08-18: Complete package submitted to contracting, which starts the 29-day p80 PALT clock",
   "2026-09-01: Contracting officer review complete and any contractor confirmation of option price and terms received",
   "... 4 more items"
  ]
 },
 "validation_issues": [],
 "model_endpoint": "databricks-claude-sonnet-5-5"
}
```

## Write-back: submit the validated batch AI package for OTS-PCI-01-FY2024 as part of the year-end plan

`POST /api/packages/OTS-PCI-01-FY2024` → **HTTP 200** in 71 ms

Request body:
```json
{
 "title": "Bridge Inspection Systems \u2013 Year-End Option Exercise (OTS-PCI-01)",
 "acquisition_type": "Option Exercise",
 "contract_number": "DCI25C000558",
 "amount": 1039509.21,
 "requirement_summary": "The Bridge Inspection Systems program (OTS-PCI-01) requires continued professional and technical services under Object Class 25.1 to sustain active bridge inspection data collection, analysis, and reporting activities through the current period of availability ending 30 September 2026. Exercising this option now ensures uninterrupted delivery of inspection system support services that constitute a bona fide need of FY 2024\u20132026 multi-year funds before they expire. Failure to obligate these funds prior to the 16 September 2026 award deadline would result in lapse of resources already planned and budgeted for this program year's inspection workload.",
 "justification": "Option exercises carry a median PALT of 21 days and a P80 PALT of 29 days, well within the 47 days remaining before the 16 September 2026 must-award date, providing sufficient schedule margin even under adverse conditions. Contract DCI25C000558 with Horizon Consulting Corp. is an active, in-scope vehicle with a period of performance extending through 28 February 2027, meaning the option can be exercised and work performed without a scope gap or period-of-performance conflict.",
 "required_documents": [
  "Procurement Request (PR) / Funding Document signed by Budget Officer",
  "Contracting Officer's Option Exercise Determination and Findings (D&F)",
  "Bona Fide Need Determination memorandum citing fund citation 999-2024/2026-0400",
  "Independent Government Cost Estimate (IGCE) validating $1,039,509.21 option value",
  "Contractor Performance Assessment (CPARS) review for DCI25C000558",
  "Legal / Policy Review checklist",
  "Contracting Officer Representative (COR) Nomination or Reaffirmation letter",
  "Signed Option Exercise modification (SF-30) ready for CO signature"
 ],
 "milestones": [
  "2026-07-31: Program Office initiates PR package and drafts Bona Fide Need memo",
  "2026-08-05: IGCE completed and signed by Program Office",
  "2026-08-07: PR package (PR, IGCE, Bona Fide Need memo) submitted to Contracting",
  "2026-08-12: Contracting Officer reviews package; requests any corrections",
  "2026-08-18: D&F and Option Exercise determination drafted and routed for legal review",
  "2026-08-22: Legal / Policy review complete; D&F approved",
  "2026-08-26: SF-30 modification drafted and reviewed by COR",
  "2026-09-02: Final package cleared; SF-30 routed to CO for signature",
  "2026-09-10: Contracting Officer signs and awards option exercise (target)",
  "2026-09-16: HARD DEADLINE \u2013 Option exercise must be awarded and obligation recorded"
 ],
 "source": "Year-end plan - batch AI draft"
}
```
Response:
```json
{
 "package_id": "REQ-OTS-PCI-01-FY2024-01",
 "line_id": "OTS-PCI-01-FY2024",
 "office_code": "OTS",
 "title": "Bridge Inspection Systems \u2013 Year-End Option Exercise (OTS-PCI-01)",
 "acquisition_type": "Option Exercise",
 "contract_number": "DCI25C000558",
 "amount": 1039509.21,
 "requirement_summary": "The Bridge Inspection Systems program (OTS-PCI-01) requires continued professional and technical services under Object Class 25.1 to sustain active bridge inspection data collection, analysis, and reporting activities through the current period of availability ending 30 September 2026. Exercising this option now ensures uninterrupted delivery of inspection system support services that constitute a...",
 "justification": "Option exercises carry a median PALT of 21 days and a P80 PALT of 29 days, well within the 47 days remaining before the 16 September 2026 must-award date, providing sufficient schedule margin even under adverse conditions. Contract DCI25C000558 with Horizon Consulting Corp. is an active, in-scope vehicle with a period of performance extending through 28 February 2027, meaning the option can be exe...",
 "required_documents": [
  "Procurement Request (PR) / Funding Document signed by Budget Officer",
  "Contracting Officer's Option Exercise Determination and Findings (D&F)",
  "Bona Fide Need Determination memorandum citing fund citation 999-2024/2026-0400",
  "Independent Government Cost Estimate (IGCE) validating $1,039,509.21 option value",
  "Contractor Performance Assessment (CPARS) review for DCI25C000558",
  "Legal / Policy Review checklist",
  "... 2 more items"
 ],
 "milestones": [
  "2026-07-31: Program Office initiates PR package and drafts Bona Fide Need memo",
  "2026-08-05: IGCE completed and signed by Program Office",
  "2026-08-07: PR package (PR, IGCE, Bona Fide Need memo) submitted to Contracting",
  "2026-08-12: Contracting Officer reviews package; requests any corrections",
  "2026-08-18: D&F and Option Exercise determination drafted and routed for legal review",
  "2026-08-22: Legal / Policy review complete; D&F approved",
  "... 4 more items"
 ],
 "status": "Submitted to Acquisition",
 "source": "Year-end plan - batch AI draft",
 "model_endpoint": "databricks-claude-sonnet-5-5",
 "created_by": "rahul.chopra@databricks.com",
 "created_at": "2026-11-02T18:07:08.023644+00:00",
 "updated_at": "2026-11-02T18:07:08.023644+00:00"
}
```

## Write-back: analyst note on OTS-PCI-01-FY2024

`POST /api/lines/OTS-PCI-01-FY2024/notes` → **HTTP 200** in 54 ms

Request body:
```json
{
 "note": "Option exercise submitted from the year-end plan; program office to confirm the bona fide need memo by 7 Aug."
}
```
Response:
```json
{
 "note_id": 2,
 "line_id": "OTS-PCI-01-FY2024",
 "office_code": "OTS",
 "note": "Option exercise submitted from the year-end plan; program office to confirm the bona fide need memo by 7 Aug.",
 "author": "rahul.chopra@databricks.com",
 "created_at": "2026-11-02T18:07:08.081312+00:00"
}
```

## Notes on OTS-PCI-01-FY2024

`GET /api/lines/OTS-PCI-01-FY2024/notes` → **HTTP 200** in 41 ms

Response:
```json
[
 {
  "note_id": 2,
  "line_id": "OTS-PCI-01-FY2024",
  "office_code": "OTS",
  "note": "Option exercise submitted from the year-end plan; program office to confirm the bona fide need memo by 7 Aug.",
  "author": "rahul.chopra@databricks.com",
  "created_at": "2026-11-02T18:07:08.081312+00:00"
 }
]
```

## Write-back: reprogramming request OWS-GA-01-FY2026 -> OGM-GA-01-FY2026 within 999-2026-0600

`POST /api/reprogramming` → **HTTP 200** in 61 ms

Request body:
```json
{
 "from_line_id": "OWS-GA-01-FY2026",
 "to_line_id": "OGM-GA-01-FY2026",
 "amount": 433000.0,
 "justification": "Year-end reprogramming within 999-2026-0600: Tribal and Rural Water Grants is projected to lapse; State Energy Resilience Grants: commitments exceed available funds by $4,343,489."
}
```
Response:
```json
{
 "request_id": "RPG-0002",
 "tas": "999-2026-0600",
 "from_line_id": "OWS-GA-01-FY2026",
 "from_office_code": "OWS",
 "to_line_id": "OGM-GA-01-FY2026",
 "to_office_code": "OGM",
 "amount": 433000.0,
 "justification": "Year-end reprogramming within 999-2026-0600: Tribal and Rural Water Grants is projected to lapse; State Energy Resilience Grants: commitments exceed available funds by $4,343,489.",
 "notification_required": false,
 "status": "Pending",
 "requested_by": "rahul.chopra@databricks.com",
 "requested_at": "2026-11-02T18:07:08.183120+00:00",
 "decided_by": null,
 "decided_at": null,
 "decision_note": null
}
```

## Control: the requester tries to approve their own request (separation of duties, expect 403)

`POST /api/reprogramming/RPG-0002/decision` → **HTTP 403** in 50 ms

Request body:
```json
{
 "decision": "Approved",
 "note": "self-approval attempt"
}
```
Response:
```json
{
 "detail": "Separation of duties: a second Budget Director must decide on a request you made"
}
```

## Control: a move between different appropriations is refused (expect 400)

`POST /api/reprogramming` → **HTTP 400** in 50 ms

Request body:
```json
{
 "from_line_id": "OWS-GA-01-FY2026",
 "to_line_id": "OCIO-PCI-01-FY2024",
 "amount": 10000
}
```
Response:
```json
{
 "detail": "999-2026-0600 and 999-2024/2026-0400 are different accounts; moving funds between appropriations needs transfer authority, not a reprogramming"
}
```

## Reprogramming requests in scope

`GET /api/reprogramming` → **HTTP 200** in 46 ms

Response:
```json
[
 {
  "request_id": "RPG-0002",
  "tas": "999-2026-0600",
  "from_line_id": "OWS-GA-01-FY2026",
  "from_office_code": "OWS",
  "to_line_id": "OGM-GA-01-FY2026",
  "to_office_code": "OGM",
  "amount": 433000.0,
  "justification": "Year-end reprogramming within 999-2026-0600: Tribal and Rural Water Grants is projected to lapse; State Energy Resilience Grants: commitments exceed available funds by $4,343,489.",
  "notification_required": false,
  "status": "Pending",
  "requested_by": "rahul.chopra@databricks.com",
  "requested_at": "2026-11-02T18:07:08.183120+00:00",
  "decided_by": null,
  "decided_at": null,
  "decision_note": null,
  "from_ppa_name": "Tribal and Rural Water Grants",
  "to_ppa_name": "State Energy Resilience Grants"
 },
 {
  "request_id": "RPG-0001",
  "tas": "999-2026-0100",
  "from_line_id": "OTS-OS-02-FY2026",
  "from_office_code": "OTS",
  "to_line_id": "OWS-OS-02-FY2026",
  "to_office_code": "OWS",
  "amount": 920000.0,
  "justification": "Year-end reprogramming within 999-2026-0100: Incident Investigation is projected to lapse; Laboratory Services: commitments exceed available funds by $920,379.",
  "notification_required": true,
  "status": "Pending",
  "requested_by": "rahul.chopra@databricks.com",
  "requested_at": "2026-11-02T18:04:22.562623+00:00",
  "decided_by": null,
  "decided_at": null,
  "decision_note": null,
  "from_ppa_name": "Incident Investigation",
  "to_ppa_name": "Laboratory Services"
 }
]
```

## Risk alert summary

`GET /api/alerts/summary` → **HTTP 200** in 35 ms

Response:
```json
[
 {
  "alert_type": "STALE_SPEND_PLAN",
  "severity": "Medium",
  "alerts": 8,
  "amount_at_risk": 127843257.48
 },
 {
  "alert_type": "BURN_RATE_VARIANCE",
  "severity": "Medium",
  "alerts": 12,
  "amount_at_risk": 86981149.17
 },
 {
  "alert_type": "BURN_RATE_VARIANCE",
  "severity": "High",
  "alerts": 7,
  "amount_at_risk": 47674964.16
 },
 {
  "alert_type": "LAPSE_RISK",
  "severity": "High",
  "alerts": 5,
  "amount_at_risk": 33248868.35
 },
 {
  "alert_type": "PROCUREMENT_WILL_MISS_EXPIRATION",
  "severity": "High",
  "alerts": 4,
  "amount_at_risk": 15409376.45
 },
 {
  "alert_type": "LAPSE_RISK",
  "severity": "Medium",
  "alerts": 6,
  "amount_at_risk": 12804075.89
 },
 "... 8 more items"
]
```

## High-severity alerts (board cards)

`GET /api/alerts?severity=High` → **HTTP 200** in 64 ms

Response:
```json
[
 {
  "alert_id": "8915b868e77ef3bfc7350acfdb5e44900fa237d00b869a4c75f46b4df3750019",
  "alert_type": "LAPSE_RISK",
  "severity": "High",
  "line_id": "OCIO-PCI-01-FY2024",
  "office_code": "OCIO",
  "ppa_code": "OCIO-PCI-01",
  "entity_id": "OCIO-PCI-01-FY2024",
  "amount_at_risk": 20062036.3,
  "detail": "Financial System Modernization (999-2024/2026-0400) has $20,062,036 (19.6% of budget) neither obligated nor committed, with 61 days until the funds expire on 2026-09-30.",
  "last_action": "Assigned",
  "assignee": "budget.analyst@dci.example.gov",
  "acted_by": "rahul.chopra@databricks.com",
  "acted_at": "2026-11-02T18:04:22.932530+00:00"
 },
 {
  "alert_id": "0dff95d8fd2266f732ee5e8b8cbc6e7aae95ac0adc3e1dd75e3b2a9aabd6df09",
  "alert_type": "BURN_RATE_VARIANCE",
  "severity": "High",
  "line_id": "OCIO-PCI-02-FY2026",
  "office_code": "OCIO",
  "ppa_code": "OCIO-PCI-02",
  "entity_id": "OCIO-PCI-02-FY2026",
  "amount_at_risk": 12696108.18,
  "detail": "Cloud Migration obligations are 53% of the approved spend plan to date ($14,491,845 obligated vs $27,187,953 planned in baseline rev 2).",
  "last_action": null,
  "assignee": null,
  "acted_by": null,
  "acted_at": null
 },
 {
  "alert_id": "2f458085da0d8ac8c7a16c6b0d579ebbbb13ef1c9f1c70b8a0086b8ef34b3e84",
  "alert_type": "BURN_RATE_VARIANCE",
  "severity": "High",
  "line_id": "OTS-PCI-01-FY2026",
  "office_code": "OTS",
  "ppa_code": "OTS-PCI-01",
  "entity_id": "OTS-PCI-01-FY2026",
  "amount_at_risk": 10269793.03,
  "detail": "Bridge Inspection Systems obligations are 59% of the approved spend plan to date ($14,935,707 obligated vs $25,205,500 planned in baseline rev 2).",
  "last_action": null,
  "assignee": null,
  "acted_by": null,
  "acted_at": null
 },
 {
  "alert_id": "9c475af02fdfd347e832494211852cd122816e274d8b7feccaa617a9af046b21",
  "alert_type": "BURN_RATE_VARIANCE",
  "severity": "High",
  "line_id": "OTS-GA-01-FY2026",
  "office_code": "OTS",
  "ppa_code": "OTS-GA-01",
  "entity_id": "OTS-GA-01-FY2026",
  "amount_at_risk": 8141296.22,
  "detail": "Highway Safety Improvement Grants obligations are 30% of the approved spend plan to date ($3,522,004 obligated vs $11,663,300 planned in baseline rev 2).",
  "last_action": null,
  "assignee": null,
  "acted_by": null,
  "acted_at": null
 },
 {
  "alert_id": "718dd65b4f89ce1b8fc734951f083264d025491330eed9ea7d90e57e8f8be35a",
  "alert_type": "BURN_RATE_VARIANCE",
  "severity": "High",
  "line_id": "OWS-OS-01-FY2026",
  "office_code": "OWS",
  "ppa_code": "OWS-OS-01",
  "entity_id": "OWS-OS-01-FY2026",
  "amount_at_risk": 6490320.49,
  "detail": "Drinking Water Program Operations obligations are 62% of the approved spend plan to date ($10,515,343 obligated vs $17,005,664 planned in baseline rev 2).",
  "last_action": null,
  "assignee": null,
  "acted_by": null,
  "acted_at": null
 },
 {
  "alert_id": "46dcafc20f3f5a535df53d722bd9db895649fcb06da6714265609ed5a7c40804",
  "alert_type": "PROCUREMENT_WILL_MISS_EXPIRATION",
  "severity": "High",
  "line_id": "OTS-GA-01-FY2026",
  "office_code": "OTS",
  "ppa_code": "OTS-GA-01",
  "entity_id": "PR-26-OTS-0200",
  "amount_at_risk": 5579292.96,
  "detail": "PR-26-OTS-0200 \"Highway Safety Improvement Grants - competitive awards cohort 1\" ($5,579,293, Grant Award) is Under Evaluation; forecast award 2026-10-07 is after the funds expire on 2026-09-30.",
  "last_action": null,
  "assignee": null,
  "acted_by": null,
  "acted_at": null
 },
 "... 78 more items"
]
```

## Write-back: board move Open -> Acknowledged (BURN_RATE_VARIANCE)

`POST /api/alerts/0dff95d8fd2266f732ee5e8b8cbc6e7aae95ac0adc3e1dd75e3b2a9aabd6df09/actions` → **HTTP 200** in 48 ms

Request body:
```json
{
 "action": "Acknowledged"
}
```
Response:
```json
{
 "action_id": 7,
 "alert_id": "0dff95d8fd2266f732ee5e8b8cbc6e7aae95ac0adc3e1dd75e3b2a9aabd6df09",
 "alert_type": "BURN_RATE_VARIANCE",
 "line_id": "OCIO-PCI-02-FY2026",
 "office_code": "OCIO",
 "action": "Acknowledged",
 "assignee": null,
 "note": null,
 "acted_by": "rahul.chopra@databricks.com",
 "acted_at": "2026-11-02T18:07:08.475828+00:00"
}
```

## Write-back: board move Acknowledged -> Assigned

`POST /api/alerts/0dff95d8fd2266f732ee5e8b8cbc6e7aae95ac0adc3e1dd75e3b2a9aabd6df09/actions` → **HTTP 200** in 49 ms

Request body:
```json
{
 "action": "Assigned",
 "assignee": "budget.analyst@dci.example.gov",
 "note": "Confirm obligation plan for the uncommitted balance before the option-exercise window closes."
}
```
Response:
```json
{
 "action_id": 8,
 "alert_id": "0dff95d8fd2266f732ee5e8b8cbc6e7aae95ac0adc3e1dd75e3b2a9aabd6df09",
 "alert_type": "BURN_RATE_VARIANCE",
 "line_id": "OCIO-PCI-02-FY2026",
 "office_code": "OCIO",
 "action": "Assigned",
 "assignee": "budget.analyst@dci.example.gov",
 "note": "Confirm obligation plan for the uncommitted balance before the option-exercise window closes.",
 "acted_by": "rahul.chopra@databricks.com",
 "acted_at": "2026-11-02T18:07:08.526561+00:00"
}
```

## Alert history (both moves)

`GET /api/alerts/0dff95d8fd2266f732ee5e8b8cbc6e7aae95ac0adc3e1dd75e3b2a9aabd6df09/history` → **HTTP 200** in 48 ms

Response:
```json
[
 {
  "action_id": 8,
  "alert_id": "0dff95d8fd2266f732ee5e8b8cbc6e7aae95ac0adc3e1dd75e3b2a9aabd6df09",
  "alert_type": "BURN_RATE_VARIANCE",
  "line_id": "OCIO-PCI-02-FY2026",
  "office_code": "OCIO",
  "action": "Assigned",
  "assignee": "budget.analyst@dci.example.gov",
  "note": "Confirm obligation plan for the uncommitted balance before the option-exercise window closes.",
  "acted_by": "rahul.chopra@databricks.com",
  "acted_at": "2026-11-02T18:07:08.526561+00:00"
 },
 {
  "action_id": 7,
  "alert_id": "0dff95d8fd2266f732ee5e8b8cbc6e7aae95ac0adc3e1dd75e3b2a9aabd6df09",
  "alert_type": "BURN_RATE_VARIANCE",
  "line_id": "OCIO-PCI-02-FY2026",
  "office_code": "OCIO",
  "action": "Acknowledged",
  "assignee": null,
  "note": null,
  "acted_by": "rahul.chopra@databricks.com",
  "acted_at": "2026-11-02T18:07:08.475828+00:00"
 }
]
```

## Procurement-cycle visibility: pipeline by stage, PALT, open PRs with forecast award

`GET /api/procurement` → **HTTP 200** in 132 ms

Response:
```json
{
 "open": [
  {
   "pr_id": "PR-26-OTS-0200",
   "line_id": "OTS-GA-01-FY2026",
   "ppa_name": "Highway Safety Improvement Grants",
   "office_code": "OTS",
   "title": "Highway Safety Improvement Grants - competitive awards cohort 1",
   "acquisition_type": "Grant Award",
   "contract_vehicle": "Notice of Funding Opportunity",
   "estimated_amount": 5579292.96,
   "status": "Under Evaluation",
   "days_in_status": 6,
   "age_days": 85,
   "forecast_award_date": "2026-10-07",
   "expiration_date": "2026-09-30",
   "at_risk_of_missing_expiration": true,
   "started_at": "2026-05-07T16:06:15+00:00",
   "median_palt_days": 153
  },
  {
   "pr_id": "PR-26-OWD-0003",
   "line_id": "OWD-GA-01-FY2026",
   "ppa_name": "Infrastructure Workforce Grants",
   "office_code": "OWD",
   "title": "Infrastructure Workforce Grants - cooperative agreement 1",
   "acquisition_type": "Grant Award",
   "contract_vehicle": "Notice of Funding Opportunity",
   "estimated_amount": 3496004.45,
   "status": "Under Evaluation",
   "days_in_status": 8,
   "age_days": 82,
   "forecast_award_date": "2026-10-10",
   "expiration_date": "2026-09-30",
   "at_risk_of_missing_expiration": true,
   "started_at": "2026-05-10T14:31:50+00:00",
   "median_palt_days": 153
  },
  {
   "pr_id": "PR-26-OTS-0198",
   "line_id": "OTS-GA-01-FY2026",
   "ppa_name": "Highway Safety Improvement Grants",
   "office_code": "OTS",
   "title": "Highway Safety Improvement Grants - formula allocation region 7",
   "acquisition_type": "Grant Award",
   "contract_vehicle": "Notice of Funding Opportunity",
   "estimated_amount": 3439835.6,
   "status": "In Solicitation",
   "days_in_status": 10,
   "age_days": 33,
   "forecast_award_date": "2026-11-28",
   "expiration_date": "2026-09-30",
   "at_risk_of_missing_expiration": true,
   "started_at": "2026-06-28T15:15:39+00:00",
   "median_palt_days": 153
  },
  {
   "pr_id": "PR-26-OWD-0013",
   "line_id": "OWD-GA-01-FY2026",
   "ppa_name": "Infrastructure Workforce Grants",
   "office_code": "OWD",
   "title": "Infrastructure Workforce Grants - formula allocation region 6",
   "acquisition_type": "Grant Award",
   "contract_vehicle": "Notice of Funding Opportunity",
   "estimated_amount": 2894243.44,
   "status": "Under Evaluation",
   "days_in_status": 4,
   "age_days": 80,
   "forecast_award_date": "2026-10-12",
   "expiration_date": "2026-09-30",
   "at_risk_of_missing_expiration": true,
   "started_at": "2026-05-12T07:11:00+00:00",
   "median_palt_days": 153
  },
  {
   "pr_id": "PR-26-OWS-0030",
   "line_id": "OWS-OS-01-FY2026",
   "ppa_name": "Drinking Water Program Operations",
   "office_code": "OWS",
   "title": "Network hardware refresh",
   "acquisition_type": "New Award",
   "contract_vehicle": "Open Market - Full and Open Competition",
   "estimated_amount": 937386.24,
   "status": "In Solicitation",
   "days_in_status": 67,
   "age_days": 86,
   "forecast_award_date": "2026-10-08",
   "expiration_date": "2026-09-30",
   "at_risk_of_missing_expiration": true,
   "started_at": "2026-05-06T14:03:00+00:00",
   "median_palt_days": 155
  },
  {
   "pr_id": "PR-26-OMA-0189",
   "line_id": "OMA-OS-04-FY2026",
   "ppa_name": "Financial Management Services",
   "office_code": "OMA",
   "title": "Enterprise software license renewal",
   "acquisition_type": "New Award",
   "contract_vehicle": "Open Market - Full and Open Competition",
   "estimated_amount": 925799.28,
   "status": "Under Evaluation",
   "days_in_status": 12,
   "age_days": 70,
   "forecast_award_date": "2026-10-24",
   "expiration_date": "2026-09-30",
   "at_risk_of_missing_expiration": true,
   "started_at": "2026-05-22T11:16:03+00:00",
   "median_palt_days": 155
  },
  "... 294 more items"
 ],
 "by_stage": [
  {
   "status": "Funds Certified",
   "prs": 60,
   "value": 46358175.04
  },
  {
   "status": "Under Evaluation",
   "prs": 113,
   "value": 250770030.87
  },
  {
   "status": "In Solicitation",
   "prs": 120,
   "value": 101757058.85
  },
  {
   "status": "Draft",
   "prs": 16,
   "value": 16630263.31
  },
  {
   "status": "Submitted",
   "prs": 19,
   "value": 19131531.51
  }
 ],
 "palt": [
  {
   "acquisition_type": "Option Exercise",
   "awards": 492,
   "median_palt_days": 21.0,
   "p80_palt_days": 29.0
  },
  {
   "acquisition_type": "Modification",
   "awards": 52,
   "median_palt_days": 26.0,
   "p80_palt_days": 32.0
  },
  {
   "acquisition_type": "New Award (Simplified)",
   "awards": 347,
   "median_palt_days": 51.0,
   "p80_palt_days": 118.0
  },
  {
   "acquisition_type": "Task Order",
   "awards": 1716,
   "median_palt_days": 59.0,
   "p80_palt_days": 82.0
  },
  {
   "acquisition_type": "Grant Award",
   "awards": 239,
   "median_palt_days": 153.0,
   "p80_palt_days": 186.0
  },
  {
   "acquisition_type": "New Award",
   "awards": 827,
   "median_palt_days": 155.0,
   "p80_palt_days": 189.0
  }
 ]
}
```

## Packages submitted to acquisition and AI drafts

`GET /api/packages` → **HTTP 200** in 77 ms

Response:
```json
{
 "submitted": [
  {
   "package_id": "REQ-OTS-PCI-01-FY2024-01",
   "line_id": "OTS-PCI-01-FY2024",
   "office_code": "OTS",
   "title": "Bridge Inspection Systems \u2013 Year-End Option Exercise (OTS-PCI-01)",
   "acquisition_type": "Option Exercise",
   "contract_number": "DCI25C000558",
   "amount": 1039509.21,
   "requirement_summary": "The Bridge Inspection Systems program (OTS-PCI-01) requires continued professional and technical services under Object Class 25.1 to sustain active bridge inspection data collection, analysis, and reporting activities through the current period of availability ending 30 September 2026. Exercising this option now ensures uninterrupted delivery of inspection system support services that constitute a...",
   "justification": "Option exercises carry a median PALT of 21 days and a P80 PALT of 29 days, well within the 47 days remaining before the 16 September 2026 must-award date, providing sufficient schedule margin even under adverse conditions. Contract DCI25C000558 with Horizon Consulting Corp. is an active, in-scope vehicle with a period of performance extending through 28 February 2027, meaning the option can be exe...",
   "required_documents": [
    "Procurement Request (PR) / Funding Document signed by Budget Officer",
    "Contracting Officer's Option Exercise Determination and Findings (D&F)",
    "Bona Fide Need Determination memorandum citing fund citation 999-2024/2026-0400",
    "Independent Government Cost Estimate (IGCE) validating $1,039,509.21 option value",
    "Contractor Performance Assessment (CPARS) review for DCI25C000558",
    "Legal / Policy Review checklist",
    "... 2 more items"
   ],
   "milestones": [
    "2026-07-31: Program Office initiates PR package and drafts Bona Fide Need memo",
    "2026-08-05: IGCE completed and signed by Program Office",
    "2026-08-07: PR package (PR, IGCE, Bona Fide Need memo) submitted to Contracting",
    "2026-08-12: Contracting Officer reviews package; requests any corrections",
    "2026-08-18: D&F and Option Exercise determination drafted and routed for legal review",
    "2026-08-22: Legal / Policy review complete; D&F approved",
    "... 4 more items"
   ],
   "status": "Submitted to Acquisition",
   "source": "Year-end plan - batch AI draft",
   "model_endpoint": "databricks-claude-sonnet-5-5",
   "created_by": "rahul.chopra@databricks.com",
   "created_at": "2026-11-02T18:07:08.023644+00:00",
   "updated_at": "2026-11-02T18:07:08.023644+00:00"
  },
  {
   "package_id": "REQ-OCIO-PCI-01-FY2024-01",
   "line_id": "OCIO-PCI-01-FY2024",
   "office_code": "OCIO",
   "title": "FY2026 Financial System Modernization \u2013 Year-End IT Professional Services Modification (DCI26F001274)",
   "acquisition_type": "Modification",
   "contract_number": "DCI26F001274",
   "amount": 1903840.14,
   "requirement_summary": "The OCIO Financial System Modernization program (OCIO-PCI-01) requires continued IT professional services support during the current period of availability (FY2024\u20132026, expiring 30 September 2026) to sustain active modernization workstreams including system integration testing, data migration validation, and configuration management activities. These services represent a bona fide need of the cur...",
   "justification": "Contract DCI26F001274 with Ironwood Solutions Corp. is an active service contract with a period of performance extending through 27 March 2027, providing a ready vehicle to absorb additional scope via modification well within the 47-day award window; the median modification PALT of 26 days (P80: 32 days) provides sufficient schedule margin against the 16 September 2026 must-award date. The existin...",
   "required_documents": [
    "Independent Government Cost Estimate (IGCE)",
    "Statement of Work (SOW) / Performance Work Statement (PWS) \u2013 updated scope narrative",
    "Contracting Officer's Representative (COR) Designation Letter",
    "Bona Fide Need Determination memorandum signed by Program Manager",
    "Funds Availability Certification (FAC) / Fiscal Law Review",
    "Acquisition Plan or Simplified Acquisition Plan update",
    "... 4 more items"
   ],
   "milestones": [
    "2026-08-01: Program office initiates requirement; PM signs Bona Fide Need Determination memo",
    "2026-08-05: IGCE completed and certified by COR",
    "2026-08-07: Updated SOW/PWS drafted and reviewed by program office",
    "2026-08-11: Acquisition package (IGCE, SOW, FAC, Acquisition Plan) submitted to Contracting Officer",
    "2026-08-13: Contracting Officer conducts completeness review; returns comments to program office",
    "2026-08-15: Program office resolves comments; final package resubmitted to Contracting Officer",
    "... 7 more items"
   ],
   "status": "Submitted to Acquisition",
   "source": "Year-end plan - batch AI draft",
   "model_endpoint": "databricks-claude-sonnet-5-5",
   "created_by": "rahul.chopra@databricks.com",
   "created_at": "2026-11-02T18:04:22.386972+00:00",
   "updated_at": "2026-11-02T18:04:22.386972+00:00"
  },
  {
   "package_id": "REQ-OWD-GA-01-FY2026-02",
   "line_id": "OWD-GA-01-FY2026",
   "office_code": "OWD",
   "title": "Option Exercise on Contract DCI26C000954 (Cobalt Technologies Partners) to Obligate Expiring FY2026 Funds, Fund 999-2026-0600 (OWD-GA-01)",
   "acquisition_type": "Option Exercise",
   "contract_number": "DCI26C000954",
   "amount": 4200000.0,
   "requirement_summary": "Exercise an option on active contract DCI26C000954 (Cobalt Technologies Partners, object class 25.1) for services the program office confirms are needed in the current period of availability, which ends 2026-09-30. The amount is $4,200,000.00, below the contract's obligated_to_date of $4,207,034.66. That figure is the only available proxy for priced option value, so the Contracting Officer must co...",
   "justification": "Projected lapse on fund 999-2026-0600 is $9,271,284.71, and the original recommended package was $7,417,000.00. No single
```

## Quarterly budget-performance review: quarters, AI narratives, sign-offs

`GET /api/quarterly` → **HTTP 200** in 68 ms

Response:
```json
{
 "quarters": [
  {
   "office_code": "OCIO",
   "fiscal_quarter": 1,
   "planned_obligations": 24980783.67,
   "actual_obligations": 29127727.78,
   "actual_expenditures": 70663887.54
  },
  {
   "office_code": "OCIO",
   "fiscal_quarter": 2,
   "planned_obligations": 52592019.26,
   "actual_obligations": 48758660.68,
   "actual_expenditures": 56473462.68
  },
  {
   "office_code": "OCIO",
   "fiscal_quarter": 3,
   "planned_obligations": 73678893.84,
   "actual_obligations": 63374787.4,
   "actual_expenditures": 62428930.08
  },
  {
   "office_code": "OCIO",
   "fiscal_quarter": 4,
   "planned_obligations": 91954322.76,
   "actual_obligations": 26796201.18,
   "actual_expenditures": 23597108.41
  },
  {
   "office_code": "OGM",
   "fiscal_quarter": 1,
   "planned_obligations": 23408647.86,
   "actual_obligations": 10813611.83,
   "actual_expenditures": 67218826.5
  },
  {
   "office_code": "OGM",
   "fiscal_quarter": 2,
   "planned_obligations": 48757661.89,
   "actual_obligations": 74744521.84,
   "actual_expenditures": 46716613.0
  },
  "... 18 more items"
 ],
 "reviews": [
  {
   "office_code": "OCIO",
   "performance_summary": "Through the first three completed quarters, the Office of the Chief Information Officer obligated $141.3M against a planned $151.3M, achieving 93.4% of the cumulative spend plan. Q1 ran 16.6% over plan at $29.1M obligated vs. $25.0M planned, while Q2 and Q3 came in under plan at 92.7% ($48.8M vs. $52.6M) and 86.0% ($63.4M vs. $73.7M) attainment, respectively. Q4 to date reflects only $26.8M obliga...",
   "key_risks": [
    "CRITICAL \u2013 Potential Antideficiency Act (ADA) Violation: Financial System Modernization obligations of $33.9M have exceeded the apportioned amount of $32.5M by $1.4M. Footnote B indicates the balance is withheld pending congressional spend-plan notification; immediate remediation and legal review are required.",
    "HIGH \u2013 Lapse Risk on Financial System Modernization: $20.1M (19.6% of budget) remains neither obligated nor committed with only 61 days until funds expire on 2026-09-30, creating significant risk of a year-end lapse on this line alone.",
    "HIGH \u2013 Cloud Migration Burn Rate Shortfall: Cloud Migration has obligated only $14.5M against a $27.2M baseline plan (53% attainment), indicating a $12.7M execution gap that threatens program delivery timelines and may result in unobligated balances.",
    "MODERATE \u2013 Data and Analytics Platform Over-Obligation: Obligations of $7.2M are running at 128% of the $5.6M baseline plan, signaling a potential budget sufficiency issue that could require reprogramming if the trend continues."
   ],
   "decisions_requested": [
    "IMMEDIATE ACTION REQUIRED \u2013 Authorize the program office to engage the Office of General Counsel and OMB to assess and remediate the potential Antideficiency Act violation on Financial System Modernization, where obligations of $33.9M have exceeded the apportioned level of $32.5M by $1.4M.",
    "Approve an accelerated obligation plan for Financial System Modernization ($20.1M at risk of lapsing) and Cloud Migration ($12.7M execution gap), including authority to execute any required contract modifications or new awards within the next 30 days to prevent year-end lapse of the projected $13.4M.",
    "Direct the program office to submit a formal reprogramming or reapportionment request to address the Data and Analytics Platform over-obligation (128% of plan) and to rebalance funding across the two High-risk and three Moderate-risk budget lines before end of Q4."
   ],
   "grounding_passed": false
  },
  {
   "office_code": "OGM",
   "performance_summary": "The Office of Grid Modernization closed Q1\u2013Q3 at $137.5M obligated against a $149.7M plan (91.8% attainment), masking significant quarter-to-quarter volatility: Q1 came in at only 46.2% of plan ($10.8M vs. $23.4M), Q2 surged to 153.3% ($74.7M vs. $48.8M), and Q3 fell back to 67.0% ($51.9M vs. $77.5M). Q4 is currently tracking at 33.0% of its $116.1M plan with $38.4M obligated to date, leaving a $1...",
   "key_risks": [
    "HIGH \u2013 Commitments Exceed Available Funds (State Energy Resilience Grants): $45.3M in certified open procurement requests exceeds the $41.0M unobligated balance by approximately $4.3M; a funds-control breach is imminent if additional requests are certified or awarded before a corrective review is completed.",
    "MEDIUM \u2013 Lapse Risk (Substation Hardening): $4.4M (4.4% of budget) remains neither obligated nor committed with only 61 days until fund expiration on 2026-09-30, creating a high probability of lapse if procurement actions are not accelerated immediately.",
    "MEDIUM \u2013 Award Timing Risk (PR-25-OGM-0191 'Modeling and Simulation Research'): The $910,778 new award is still under evaluation with a forecast award date of 2026-10-01, one day after the 2026-09-30 fund expiration; the award will lapse unless the procurement is expedited or funds are re-programmed.",
    "MEDIUM \u2013 Burn Rate Variances Across Multiple Lines: Substation Hardening is at 82% of plan ($33.9M vs. $41.2M planned) and Advanced Transmission Research is at 79% of plan ($10.0M vs. $12.6M planned), indicating systemic execution delays that compound Q4 lapse risk; conversely, Grid Resilience Program Operations is at 115% of plan ($35.9M vs. $31.2M planned), suggesting potential over-obligation r..."
   ],
   "decisions_requested": [
    "DECISION REQUIRED \u2013 Funds Control Hold (State Energy Resilience Grants): Authorize an immediate suspension of new procurement certifications and awards against the State Energy Resilience Grants line until a funds-control review reconciles the $4.3M excess commitment ($45.3M certified vs. $40.1M unobligated) and either additional budget authority is identified or open requests are de-scoped.",
    "DECISION REQUIRED \u2013 Expedited Procurement Authority (PR-25-OGM-0191 & Substation Hardening): Approve expedited acquisition review for the 
```

## Write-back: CFO sign-off for OMA

`POST /api/quarterly/OMA/signoff` → **HTTP 200** in 51 ms

Request body:
```json
{
 "fiscal_year": 2026,
 "fiscal_quarter": 3,
 "decision": "Approved with conditions",
 "comment": "Approve Q3; submit Q4 obligation recovery plan for lines behind the approved spend plan."
}
```
Response:
```json
{
 "signoff_id": 6,
 "office_code": "OMA",
 "fiscal_year": 2026,
 "fiscal_quarter": 3,
 "decision": "Approved with conditions",
 "comment": "Approve Q3; submit Q4 obligation recovery plan for lines behind the approved spend plan.",
 "signed_by": "rahul.chopra@databricks.com",
 "signed_at": "2026-11-02T18:07:08.901257+00:00"
}
```

## Ask Genie through the app (on behalf of the signed-in user)

`POST /api/genie` → **HTTP 200** in 16246 ms

Request body:
```json
{
 "question": "What is the projected lapse by office?"
}
```
Response:
```json
{
 "conversation_id": "01f1d6e8385d1d2db0a6b132d0c02e24",
 "status": "COMPLETED",
 "text": "Projected lapse is highest in **OTS** at **$19.4M**, followed by **OCIO** at **$13.4M** and **OWD** at **$12.4M**. Examples include:\n- **OTS** \u2014 **$19.4M** projected lapse across **5** forecasted lines, with **5** high-risk lines\n- **OCIO** \u2014 **$13.4M** across **5** lines, with **2** high-risk lines\n- **OWD** \u2014 **$12.4M** across **4** lines, with **1** high-risk line\n- **OGM** \u2014 **$9.7M** across *...",
 "sql": "SELECT\n  `office_code`,\n  COUNT(*) AS `lines_forecast`,\n  try_divide(SUM(`projected_lapse_amount`),1000000) AS `projected_lapse_m`,\n  COUNT_IF(`risk_tier` IN ('Critical', 'High')) AS `high_risk_lines`\nFROM `rachopra_catalog`.`fe_bar`.`gold_lapse_risk_forecast`\nWHERE `risk_tier` IS NOT NULL\n  AND `office_code` IS NOT NULL\n  AND `risk_tier` <> 'Outside forecast window'\nGROUP BY `office_code`\nORDER B...",
 "description": "You want to see the projected lapse amounts broken down by office. The results show each office's code, the number of budget lines with a forecast, the total projected lapse amount in millions of dollars, and the count of budget lines classified as high risk (Critical or High risk tier).",
 "columns": [
  "office_code",
  "lines_forecast",
  "projected_lapse_m",
  "high_risk_lines"
 ],
 "rows": [
  [
   "OTS",
   "5",
   "19.38626837",
   "5"
  ],
  [
   "OCIO",
   "5",
   "13.38579726",
   "2"
  ],
  [
   "OWD",
   "4",
   "12.362037120000002",
   "1"
  ],
  [
   "OGM",
   "5",
   "9.690055529999999",
   "1"
  ],
  [
   "OWS",
   "5",
   "6.9514387300000005",
   "2"
  ],
  [
   "OMA",
   "5",
   "4.0913353599999995",
   "0"
  ]
 ],
 "identity": "signed-in user"
}
```

## Live activity feed after the write-backs

`GET /api/activity?limit=12` → **HTTP 200** in 44 ms

Response:
```json
[
 {
  "kind": "signoff",
  "at": "2026-11-02T18:07:08.901257+00:00",
  "actor": "rahul.chopra@databricks.com",
  "office_code": "OMA",
  "line_id": null,
  "verb": "approved with conditions",
  "subject": "FY2026 Q3 review",
  "target": null,
  "detail": "Approve Q3; submit Q4 obligation recovery plan for lines behind the approved spend plan.",
  "amount": null
 },
 {
  "kind": "alert",
  "at": "2026-11-02T18:07:08.526561+00:00",
  "actor": "rahul.chopra@databricks.com",
  "office_code": "OCIO",
  "line_id": "OCIO-PCI-02-FY2026",
  "verb": "assigned",
  "subject": "BURN_RATE_VARIANCE",
  "target": "budget.analyst@dci.example.gov",
  "detail": "Confirm obligation plan for the uncommitted balance before the option-exercise window closes.",
  "amount": null
 },
 {
  "kind": "alert",
  "at": "2026-11-02T18:07:08.475828+00:00",
  "actor": "rahul.chopra@databricks.com",
  "office_code": "OCIO",
  "line_id": "OCIO-PCI-02-FY2026",
  "verb": "acknowledged",
  "subject": "BURN_RATE_VARIANCE",
  "target": null,
  "detail": null,
  "amount": null
 },
 {
  "kind": "reprogramming",
  "at": "2026-11-02T18:07:08.183120+00:00",
  "actor": "rahul.chopra@databricks.com",
  "office_code": "OWS",
  "line_id": "OWS-GA-01-FY2026",
  "verb": "requested reprogramming",
  "subject": "RPG-0002",
  "target": "OGM-GA-01-FY2026",
  "detail": "Year-end reprogramming within 999-2026-0600: Tribal and Rural Water Grants is projected to lapse; State Energy Resilience Grants: commitments exceed available funds by $4,343,489.",
  "amount": 433000.0
 },
 {
  "kind": "note",
  "at": "2026-11-02T18:07:08.081312+00:00",
  "actor": "rahul.chopra@databricks.com",
  "office_code": "OTS",
  "line_id": "OTS-PCI-01-FY2024",
  "verb": "added a note on",
  "subject": "OTS-PCI-01-FY2024",
  "target": null,
  "detail": "Option exercise submitted from the year-end plan; program office to confirm the bona fide need memo by 7 Aug.",
  "amount": null
 },
 {
  "kind": "package",
  "at": "2026-11-02T18:07:08.023644+00:00",
  "actor": "rahul.chopra@databricks.com",
  "office_code": "OTS",
  "line_id": "OTS-PCI-01-FY2024",
  "verb": "submitted package",
  "subject": "REQ-OTS-PCI-01-FY2024-01",
  "target": "Option Exercise",
  "detail": "Bridge Inspection Systems \u2013 Year-End Option Exercise (OTS-PCI-01)",
  "amount": 1039509.21
 },
 "... 6 more items"
]
```

