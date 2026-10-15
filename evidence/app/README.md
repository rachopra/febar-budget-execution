# Databricks App API evidence: `febar-budget-execution`

- URL: https://febar-budget-execution-7474648312380302.aws.databricksapps.com
- App status: RUNNING / compute ACTIVE
- Active deployment: `01f1c8a24c6f1c1f8b4e72f3cc4d94fc` (SUCCEEDED)
- Resources: lakebase (postgres), genie (genie_space), llm (serving_endpoint), warehouse (sql_warehouse)
- User API scopes (on-behalf-of-user): dashboards.genie, iam.access-control:read, iam.current-user:read
- Captured 2026-10-15 14:25 UTC

## Health (Lakebase connectivity)

`GET /api/health` → **HTTP 200** in 943 ms

Response:
```json
{
 "status": "ok",
 "today": "2026-10-15"
}
```

## Signed-in user and office scope (from office_access_map)

`GET /api/me` → **HTTP 200** in 34 ms

Response:
```json
{
 "email": "rahul.chopra@databricks.com",
 "role": "Budget Director",
 "offices": null,
 "genie_on_behalf_of_user": true
}
```

## Budget execution dashboard KPIs, funding by office and appropriation

`GET /api/overview` → **HTTP 200** in 85 ms

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

## Cumulative obligations vs plan (burn curve)

`GET /api/burn` → **HTTP 200** in 49 ms

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

## Unobligated balances approaching expiration, with ML forecast and AI headline

`GET /api/lines?max_days=120` → **HTTP 200** in 63 ms

Response:
```json
[
 {
  "line_id": "OWD-GA-01-FY2026",
  "ppa_code": "OWD-GA-01",
  "ppa_name": "Infrastructure Workforce Grants",
  "office_code": "OWD",
  "tas": "999-2026-0600",
  "fund_type": "annual",
  "budget_fiscal_year": 2026,
  "expiration_date": "2026-09-30",
  "days_to_expiration": 61,
  "total_budget": 65761000.0,
  "planned_obligations_to_date": 37360300.0,
  "obligated_to_date": 27098757.45,
  "committed_not_obligated": 33369061.77,
  "expended_to_date": 2894097.55,
  "unobligated_balance": 38662242.55,
  "uncommitted_balance": 5293180.78,
  "obligation_rate": 0.4121,
  "burn_rate_vs_plan": 0.7253,
  "execution_status": "Behind Plan",
  "predicted_lapse_rate": 0.14098454568336033,
  "projected_lapse_amount": 9271284.71,
  "risk_tier": "Critical",
  "top_risk_drivers": [
   "cancelled PR value 13% vs typical 0% (+4.2 pp)",
   "obligations vs spend plan 80% vs typical 94% (+2.2 pp)",
   "long-PALT pipeline (new awards/grants) 42% vs typical 8% (+2.0 pp)"
  ],
  "briefing_headline": "Critical lapse risk: $9.3M projected to expire in 61 days"
 },
 {
  "line_id": "OCIO-PCI-01-FY2024",
  "ppa_code": "OCIO-PCI-01",
  "ppa_name": "Financial System Modernization",
  "office_code": "OCIO",
  "tas": "999-2024/2026-0400",
  "fund_type": "multi-year",
  "budget_fiscal_year": 2024,
  "expiration_date": "2026-09-30",
  "days_to_expiration": 61,
  "total_budget": 102170000.0,
  "planned_obligations_to_date": 96439415.15,
  "obligated_to_date": 74121632.18,
  "committed_not_obligated": 7986331.52,
  "expended_to_date": 68009489.16,
  "unobligated_balance": 28048367.82,
  "uncommitted_balance": 20062036.3,
  "obligation_rate": 0.7255,
  "burn_rate_vs_plan": 0.7686,
  "execution_status": "Behind Plan",
  "predicted_lapse_rate": 0.07194699615561008,
  "projected_lapse_amount": 7350824.6,
  "risk_tier": "High",
  "top_risk_drivers": [
   "cancelled PR value 16% vs typical 0% (+2.9 pp)",
   "prior-year lapse rate 3% vs typical 1% (+1.4 pp)"
  ],
  "briefing_headline": "High lapse risk: $20.1M uncommitted with 61 days until fund expiration"
 },
 {
  "line_id": "OTS-PCI-01-FY2024",
  "ppa_code": "OTS-PCI-01",
  "ppa_name": "Bridge Inspection Systems",
  "office_code": "OTS",
  "tas": "999-2024/2026-0400",
  "fund_type": "multi-year",
  "budget_fiscal_year": 2024,
  "expiration_date": "2026-09-30",
  "days_to_expiration": 61,
  "total_budget": 54467000.0,
  "planned_obligations_to_date": 51541900.0,
  "obligated_to_date": 47378969.73,
  "committed_not_obligated": 5891338.0,
  "expended_to_date": 37694574.9,
  "unobligated_balance": 7088030.27,
  "uncommitted_balance": 1196692.27,
  "obligation_rate": 0.8699,
  "burn_rate_vs_plan": 0.9192,
  "execution_status": "On Plan",
  "predicted_lapse_rate": 0.11198626172728568,
  "projected_lapse_amount": 6099555.72,
  "risk_tier": "Critical",
  "top_risk_drivers": [
   "cancelled PR value 11% vs typical 0% (+4.2 pp)",
   "prior-year lapse rate 3% vs typical 1% (+2.0 pp)",
   "obligations vs spend plan 92% vs typical 94% (+1.8 pp)"
  ],
  "briefing_headline": "Critical lapse risk: $6.1M projected to expire in 61 days"
 },
 {
  "line_id": "OTS-GA-01-FY2026",
  "ppa_code": "OTS-GA-01",
  "ppa_name": "Highway Safety Improvement Grants",
  "office_code": "OTS",
  "tas": "999-2026-0600",
  "fund_type": "annual",
  "budget_fiscal_year": 2026,
  "expiration_date": "2026-09-30",
  "days_to_expiration": 61,
  "total_budget": 21073000.0,
  "planned_obligations_to_date": 11663300.0,
  "obligated_to_date": 3522003.78,
  "committed_not_obligated": 17449072.24,
  "expended_to_date": 290435.27,
  "unobligated_balance": 17550996.22,
  "uncommitted_balance": 101923.98,
  "obligation_rate": 0.1671,
  "burn_rate_vs_plan": 0.302,
  "execution_status": "Behind Plan",
  "predicted_lapse_rate": 0.2633751058673276,
  "projected_lapse_amount": 5550103.61,
  "risk_tier": "Critical",
  "top_risk_drivers": [
   "prior-year lapse rate 23% vs typical 1% (+8.7 pp)",
   "obligations vs spend plan 30% vs typical 94% (+7.8 pp)",
   "long-PALT pipeline (new awards/grants) 83% vs typical 8% (+0.9 pp)"
  ],
  "briefing_headline": "Critical lapse risk: $5.6M projected to expire with only 16.7% obligated"
 },
 {
  "line_id": "OGM-GA-01-FY2026",
  "ppa_code": "OGM-GA-01",
  "ppa_name": "State Energy Resilience Grants",
  "office_code": "OGM",
  "tas": "999-2026-0600",
  "fund_type": "annual",
  "budget_fiscal_year": 2026,
  "expiration_date": "2026-09-30",
  "days_to_expiration": 61,
  "total_budget": 81663000.0,
  "planned_obligations_to_date": 45623097.14,
  "obligated_to_date": 40667093.87,
  "committed_not_obligated": 45339395.3,
  "expended_to_date": 2932825.79,
  "unobligated_balance": 40995906.13,
  "uncommitted_balance": -4343489.17,
  "obligation_rate": 0.498,
  "burn_rate_vs_plan": 0.8914,
  "execution_status": "On Plan",
  "predicted_lapse_rate": 0.05400887207610972,
  "projected_lapse_amount": 4410526.52,
  "risk_tier": "High",
  "top_risk_drivers": [
   "cancelled PR value 4% vs typical 0% (+1.7 pp)",
   "avg age of open PRs (days) 116 vs typical 56 (+0.4 pp)",
   "open procurement pipeline 56% vs typical 19% (+0.3 pp)"
  ],
  "briefing_headline": "High lapse risk: $4.4M projected to expire with commitments exceeding available funds"
 },
 {
  "line_id": "OCIO-PCI-02-FY2024",
  "ppa_code": "OCIO-PCI-02",
  "ppa_name": "Cloud Migration",
  "office_code": "OCIO",
  "tas": "999-2024/2026-0400",
  "fund_type": "multi-year",
  "budget_fiscal_year": 2024,
  "expiration_date": "2026-09-30",
  "days_to_expiration": 61,
  "total_budget": 66233000.0,
  "planned_obligations_to_date": 62686517.3,
  "obligated_to_date": 60906132.78,
  "committed_not_obligated": 3788981.85,
  "expended_to_date": 51909677.53,
  "unobligated_balance": 5326867.22,
  "uncommitted_balance": 1537885.37,
  "obligation_rate": 0.9196,
  "burn_rate_vs_plan": 0.9716,
  "execution_status": "On Plan",
  "predicted_lapse_rate": 0.05224960516459987,
  "projected_lapse_amount": 3460648.1,
  "risk_tier": "High",
  "top_risk_drivers": [
   "prior-yea
```

## Line detail for OWD-GA-01-FY2026: briefing, open PRs, alerts, package draft

`GET /api/lines/OWD-GA-01-FY2026` → **HTTP 200** in 101 ms

Response:
```json
{
 "line": {
  "line_id": "OWD-GA-01-FY2026",
  "budget_fiscal_year": 2026,
  "ppa_code": "OWD-GA-01",
  "ppa_name": "Infrastructure Workforce Grants",
  "office_code": "OWD",
  "office_name": "Office of Workforce Development",
  "appropriation_code": "GA",
  "appropriation_name": "Grants and Assistance",
  "tas": "999-2026-0600",
  "fund_type": "annual",
  "expiration_date": "2026-09-30",
  "as_of_date": "2026-07-31",
  "days_to_expiration": 61,
  "fund_status": "Current",
  "total_budget": 65761000.0,
  "apportioned_to_date": 65761000.0,
  "apportionment_footnote": null,
  "planned_obligations_total": 64457800.0,
  "planned_obligations_to_date": 37360300.0,
  "planned_expenditures_to_date": 3849600.0,
  "requested_not_certified": 0.0,
  "committed_not_obligated": 33369061.77,
  "obligated_to_date": 27098757.45,
  "deobligated_to_date": 50126.49,
  "obligated_last_30_days": 1522971.26,
  "invoiced_to_date": 3635748.08,
  "expended_to_date": 2894097.55,
  "invoices_pending_payment": 741650.53,
  "open_procurement_requests": 13,
  "spend_plan_revision": 4,
  "spend_plan_revised_on": "2026-07-10",
  "spend_plan_template": "legacy_office_template",
  "spend_plan_age_days": 21,
  "unobligated_balance": 38662242.55,
  "uncommitted_balance": 5293180.78,
  "undelivered_orders": 24204659.9,
  "obligation_rate": 0.4121,
  "expenditure_rate": 0.044,
  "burn_rate_vs_plan": 0.7253,
  "expenditure_burn_vs_plan": 0.7518,
  "obligation_variance_to_plan": -10261542.55,
  "execution_status": "Behind Plan",
  "baseline_plan_revision": 2,
  "reforecast_obligations_remaining": 30463600.0,
  "predicted_lapse_rate": 0.14098454568336033,
  "projected_lapse_amount": 9271284.71,
  "risk_tier": "Critical",
  "top_risk_drivers": [
   "cancelled PR value 13% vs typical 0% (+4.2 pp)",
   "obligations vs spend plan 80% vs typical 94% (+2.2 pp)",
   "long-PALT pipeline (new awards/grants) 42% vs typical 8% (+2.0 pp)"
  ],
  "spend_plan_implied_lapse_rate": 0.12467332579999996,
  "model_version": "2"
 },
 "briefing": {
  "headline": "Critical lapse risk: $9.3M projected to expire in 61 days",
  "summary": "OWD-GA-01 is executing at only 72.5% of plan, with $27.1M obligated against $37.4M planned \u2014 a $10.3M shortfall against Spend Plan Rev 4. The unobligated balance stands at $38.7M (59% of the $65.8M budget) with just 61 days remaining, and the forecast projects a $9.3M lapse (14.1%), exceeding the spend-plan-implied lapse of 12.5% by 1.6 percentage points. The three primary drivers are an elevated ...",
  "recommended_actions": [
   "Grants Officer must expedite evaluation and award PR-26-OWD-0003 (Infrastructure Workforce Grants \u2013 Cooperative Agreement 1, $3.5M) and PR-26-OWD-0013 (Formula Allocation Region 6, $2.9M) \u2014 both currently forecast to award after the September 30 expiration \u2014 by no later than September 26 to allow time for obligation processing before fund expiration.",
   "Budget Officer should immediately develop an obligation plan for the $5.3M uncommitted, unobligated balance (fund 999-2026-0600) within the next 7 days, identifying eligible grant recipients or re-scoping existing awards to absorb funds before the pipeline closes, given only 61 days remain.",
   "OWD Program Manager should convene an emergency spend plan review (Rev 5) within 5 business days to reconcile the 27.5% burn-rate variance, document the elevated 13% cancelled-PR rate versus the 0% typical baseline, and re-baseline the lapse forecast \u2014 ensuring the Budget Director has an updated projection before the next congressional reporting cycle."
  ],
  "grounding_passed": false,
  "model_endpoint": "databricks-claude-sonnet-4-6"
 },
 "open_procurements": [
  {
   "pr_id": "PR-26-OWD-0031",
   "title": "Independent verification and validation (year-end)",
   "acquisition_type": "Task Order",
   "contract_vehicle": "DCI Professional Services IDIQ",
   "estimated_amount": 5637463.97,
   "status": "Funds Certified",
   "days_in_status": 4,
   "forecast_award_date": "2026-09-20",
   "at_risk_of_missing_expiration": false
  },
  {
   "pr_id": "PR-26-OWD-0020",
   "title": "Infrastructure Workforce Grants - competitive awards cohort 8",
   "acquisition_type": "Grant Award",
   "contract_vehicle": "Notice of Funding Opportunity",
   "estimated_amount": 5421626.66,
   "status": "Under Evaluation",
   "days_in_status": 30,
   "forecast_award_date": "2026-08-16",
   "at_risk_of_missing_expiration": false
  },
  {
   "pr_id": "PR-26-OWD-0001",
   "title": "Infrastructure Workforce Grants - formula allocation region 7",
   "acquisition_type": "Grant Award",
   "contract_vehicle": "Notice of Funding Opportunity",
   "estimated_amount": 4709066.58,
   "status": "Under Evaluation",
   "days_in_status": 41,
   "forecast_award_date": "2026-08-01",
   "at_risk_of_missing_expiration": false
  },
  {
   "pr_id": "PR-26-OWD-0003",
   "title": "Infrastructure Workforce Grants - cooperative agreement 1",
   "acquisition_type": "Grant Award",
   "contract_vehicle": "Notice of Funding Opportunity",
   "estimated_amount": 3496004.45,
   "status": "Under Evaluation",
   "days_in_status": 8,
   "forecast_award_date": "2026-10-10",
   "at_risk_of_missing_expiration": true
  },
  {
   "pr_id": "PR-26-OWD-0013",
   "title": "Infrastructure Workforce Grants - formula allocation region 6",
   "acquisition_type": "Grant Award",
   "contract_vehicle": "Notice of Funding Opportunity",
   "estimated_amount": 2894243.44,
   "status": "Under Evaluation",
   "days_in_status": 4,
   "forecast_award_date": "2026-10-12",
   "at_risk_of_missing_expiration": true
  },
  {
   "pr_id": "PR-26-OWD-0010",
   "title": "Infrastructure Workforce Grants - competitive awards cohort 4",
   "acquisition_type": "Grant Award",
   "contract_vehicle": "Notice of Funding Opportunity",
   "estimated_amount": 2856387.29,
   "status": "Under Evaluation",
   "days_in_status": 82,
   "forecast_award_date": "2026-08-01",
   "at_risk_of_missing_expiration": false
  },
  "... 7 mo
```

## Risk alert summary

`GET /api/alerts/summary` → **HTTP 200** in 43 ms

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

## Critical alerts

`GET /api/alerts?severity=Critical` → **HTTP 200** in 48 ms

Response:
```json
[
 {
  "alert_id": "47a557853016f120747c21a70798645b64d920b75d28424c53a0aaf38e122456",
  "alert_type": "APPORTIONMENT_EXCEEDED",
  "severity": "Critical",
  "line_id": "OCIO-PCI-01-FY2026",
  "office_code": "OCIO",
  "ppa_code": "OCIO-PCI-01",
  "entity_id": "OCIO-PCI-01-FY2026",
  "amount_at_risk": 1355925.74,
  "detail": "Financial System Modernization obligations of $33,892,926 exceed the apportioned amount of $32,537,000 by $1,355,926 - potential Antideficiency Act violation. Footnote B: balance withheld pending congressional spend-plan notification",
  "last_action": "Assigned",
  "assignee": "budget.analyst@dci.example.gov",
  "acted_by": "rahul.chopra@databricks.com",
  "acted_at": "2026-10-15T14:10:00.029609+00:00"
 }
]
```

## Write-back: acknowledge a critical alert

`POST /api/alerts/47a557853016f120747c21a70798645b64d920b75d28424c53a0aaf38e122456/actions` → **HTTP 200** in 58 ms

Request body:
```json
{
 "action": "Assigned",
 "assignee": "budget.analyst@dci.example.gov",
 "note": "Prepare apportionment reapportionment request before further obligations."
}
```
Response:
```json
{
 "action_id": 4,
 "alert_id": "47a557853016f120747c21a70798645b64d920b75d28424c53a0aaf38e122456",
 "alert_type": "APPORTIONMENT_EXCEEDED",
 "line_id": "OCIO-PCI-01-FY2026",
 "office_code": "OCIO",
 "action": "Assigned",
 "assignee": "budget.analyst@dci.example.gov",
 "note": "Prepare apportionment reapportionment request before further obligations.",
 "acted_by": "rahul.chopra@databricks.com",
 "acted_at": "2026-10-15T14:25:06.769659+00:00"
}
```

## Procurement-cycle visibility: pipeline by stage, PALT, open PRs

`GET /api/procurement` → **HTTP 200** in 110 ms

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
   "at_risk_of_missing_expiration": true
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
   "at_risk_of_missing_expiration": true
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
   "at_risk_of_missing_expiration": true
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
   "at_risk_of_missing_expiration": true
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
   "at_risk_of_missing_expiration": true
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
   "at_risk_of_missing_expiration": true
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

## On-demand AI procurement package draft for OWD-GA-01-FY2026

`POST /api/packages/OWD-GA-01-FY2026/draft` → **HTTP 200** in 20996 ms

Response:
```json
{
 "line_id": "OWD-GA-01-FY2026",
 "office_code": "OWD",
 "facts": {
  "ppa": "Infrastructure Workforce Grants (OWD-GA-01)",
  "fund": "999-2026-0600",
  "expires_on": "2026-09-30",
  "must_award_by": "2026-09-16",
  "days_until_must_award": 47,
  "projected_lapse_amount": 9271284.71,
  "recommended_package_amount": 7417000.0,
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
    "contract_number": "DCI26C000954",
    "vendor": "Cobalt Technologies Partners",
    "object_class": "25.1",
    "obligated_to_date": 4207034.66
   },
   {
    "contract_number": "DCI26F001410",
    "vendor": "Summit Federal JV",
    "object_class": "25.1",
    "obligated_to_date": 883687.96
   },
   {
    "contract_number": "DCI26F001411",
    "vendor": "Granite Systems Group",
    "object_class": "25.1",
    "obligated_to_date": 866507.1
   }
  ],
  "risk_drivers": [
   "cancelled PR value 13% vs typical 0% (+4.2 pp)",
   "obligations vs spend plan 80% vs typical 94% (+2.2 pp)",
   "long-PALT pipeline (new awards/grants) 42% vs typical 8% (+2.0 pp)"
  ]
 },
 "draft": {
  "title": "Option Exercise on Contract DCI26C000954 (Cobalt Technologies Partners) to Obligate Expiring FY2026 Funds, Fund 999-2026-0600 (OWD-GA-01)",
  "recommended_acquisition_type": "Option Exercise",
  "contract_number": "DCI26C000954",
  "amount": 4200000.0,
  "requirement_summary": "Exercise an option on active contract DCI26C000954 (Cobalt Technologies Partners, object class 25.1) for services the program office confirms are needed in the current period of availability, which ends 2026-09-30. The amount is $4,200,000.00, below the contract's obligated_to_date of $4,207,034.66. That figure is the only available proxy for priced option value, so the Contracting Officer must co...",
  "justification": "Projected lapse on fund 999-2026-0600 is $9,271,284.71, and the original recommended package was $7,417,000.00. No single active contract can absorb that amount. The largest, DCI26C000954, has obligated_to_date of $4,207,034.66, and the other two (DCI26F001410 at $883,687.96 and DCI26F001411 at $866,507.10) are much smaller. The package is therefore reduced to $4,200,000.00 rather than stretching ...",
  "required_documents": [
   "Purchase request / requisition with funds certification for fund 999-2026-0600",
   "Bona fide need statement tying the requirement to the current period of availability (expires 2026-09-30)",
   "Statement of work or requirement description for the option period, confirmed against the contract's option terms",
   "Confirmation of the priced option value on DCI26C000954 (must be at or above $4,200,000.00)",
   "Confirmation that the services are a proper use of the PPA and fund",
   "Contracting Officer's determination and documentation supporting the option exercise, including price reasonableness and current vendor responsibility",
   "... 3 more items"
  ],
  "milestones": [
   "2026-08-03: Program office confirms the bona fide need, defines the option-period requirement, and designates a point of contact for the package",
   "2026-08-07: Contracting Officer confirms the priced option value and the option exercise terms and timing on DCI26C000954; amount is finalized (not above $4,207,034.66)",
   "2026-08-12: Purchase request and funds certification completed and approved by the program office and budget/finance",
   "2026-08-14: Complete package submitted to Contracting (ahead of the latest P80 start date)",
   "2026-08-18: Latest start of the 29-day P80 PALT window for Option Exercise; escalate immediately if Contracting has not started",
   "2026-08-28: Contracting Officer determinations and price reasonableness documentation drafted; vendor notified of the intended exercise",
   "... 5 more items"
  ]
 },
 "validation_issues": [],
 "model_endpoint": "databricks-claude-sonnet-5-5"
}
```

## Write-back: submit the AI-drafted package to acquisition

`POST /api/packages/OWD-GA-01-FY2026` → **HTTP 200** in 68 ms

Request body:
```json
{
 "title": "Option Exercise on Contract DCI26C000954 (Cobalt Technologies Partners) to Obligate Expiring FY2026 Funds, Fund 999-2026-0600 (OWD-GA-01)",
 "acquisition_type": "Option Exercise",
 "contract_number": "DCI26C000954",
 "amount": 4200000.0,
 "requirement_summary": "Exercise an option on active contract DCI26C000954 (Cobalt Technologies Partners, object class 25.1) for services the program office confirms are needed in the current period of availability, which ends 2026-09-30. The amount is $4,200,000.00, below the contract's obligated_to_date of $4,207,034.66. That figure is the only available proxy for priced option value, so the Contracting Officer must confirm it against the actual priced option. The program office must define the specific services, quantities and performance period covered by the option before the package goes forward.",
 "justification": "Projected lapse on fund 999-2026-0600 is $9,271,284.71, and the original recommended package was $7,417,000.00. No single active contract can absorb that amount. The largest, DCI26C000954, has obligated_to_date of $4,207,034.66, and the other two (DCI26F001410 at $883,687.96 and DCI26F001411 at $866,507.10) are much smaller. The package is therefore reduced to $4,200,000.00 rather than stretching an option or modification beyond its priced value. Option Exercise is chosen over Modification because its PALT is shorter (median 21 days, P80 29 days, versus 26 and 32). With 47 days until the must-award date of 2026-09-16, that leaves about 18 days of buffer at P80. This timing matters because the risk drivers are cancelled PR value (13% vs typical 0%), obligations behind spend plan (80% vs typical 94%), and a heavy long-PALT pipeline of new awards and grants (42% vs typical 8%). Using an existing vehicle avoids adding to that pipeline. The award is only appropriate if the requirement is a bona fide need of the current period of availability. Funds must not be used to pre-buy next-year needs. The program office and Contracting Officer must also confirm that the services under DCI26C000954 are a proper use of this fund and PPA (Infrastructure Workforce Grants), since the facts show only object class 25.1. The $3,217,000.00 gap to the original recommendation, and the remaining projected lapse of about $5,071,284.71, cannot be addressed by this package. Smaller separate option or modification packages on the other two contracts could be considered only if each has a documented bona fide need and stays within that contract's obligated_to_date. They are not included here.",
 "required_documents": [
  "Purchase request / requisition with funds certification for fund 999-2026-0600",
  "Bona fide need statement tying the requirement to the current period of availability (expires 2026-09-30)",
  "Statement of work or requirement description for the option period, confirmed against the contract's option terms",
  "Confirmation of the priced option value on DCI26C000954 (must be at or above $4,200,000.00)",
  "Confirmation that the services are a proper use of the PPA and fund",
  "Contracting Officer's determination and documentation supporting the option exercise, including price reasonableness and current vendor responsibility",
  "Unilateral option exercise modification (SF-30 or equivalent) for Contracting Officer signature",
  "Funding/accounting data and obligation record for the award",
  "Written fallback decision: if the option cannot be exercised by 2026-09-16, either reduce the amount or release the funds"
 ],
 "milestones": [
  "2026-08-03: Program office confirms the bona fide need, defines the option-period requirement, and designates a point of contact for the package",
  "2026-08-07: Contracting Officer confirms the priced option value and the option exercise terms and timing on DCI26C000954; amount is finalized (not above $4,207,034.66)",
  "2026-08-12: Purchase request and funds certification completed and approved by the program office and budget/finance",
  "2026-08-14: Complete package submitted to Contracting (ahead of the latest P80 start date)",
  "2026-08-18: Latest start of the 29-day P80 PALT window for Option Exercise; escalate immediately if Contracting has not started",
  "2026-08-28: Contracting Officer determinations and price reasonableness documentation drafted; vendor notified of the intended exercise",
  "2026-09-04: Draft option exercise modification through legal/supervisory review",
  "2026-09-11: Modification finalized and sent for signature; go/no-go on amount, with fallback to a smaller amount or release of funds if blocked",
  "2026-09-16: Option exercise executed and funds obligated (must-award date)",
  "2026-09-23: Confirm obligation is recorded in the financial system, leaving a buffer before expiry",
  "2026-09-30: Fund 999-2026-0600 expires"
 ]
}
```
Response:
```json
{
 "package_id": "REQ-OWD-GA-01-FY2026-02",
 "line_id": "OWD-GA-01-FY2026",
 "office_code": "OWD",
 "title": "Option Exercise on Contract DCI26C000954 (Cobalt Technologies Partners) to Obligate Expiring FY2026 Funds, Fund 999-2026-0600 (OWD-GA-01)",
 "acquisition_type": "Option Exercise",
 "contract_number": "DCI26C000954",
 "amount": 4200000.0,
 "requirement_summary": "Exercise an option on active contract DCI26C000954 (Cobalt Technologies Partners, object class 25.1) for services the program office confirms are needed in the current period of availability, which ends 2026-09-30. The amount is $4,200,000.00, below the contract's obligated_to_date of $4,207,034.66. That figure is the only available proxy for priced option value, so the Contracting Officer must co...",
 "justification": "Projected lapse on fund 999-2026-0600 is $9,271,284.71, and the original recommended package was $7,417,000.00. No single active contract can absorb that amount. The largest, DCI26C000954, has obligated_to_date of $4,207,034.66, and the other two (DCI26F001410 at $883,687.96 and DCI26F001411 at $866,507.10) are much smaller. The package is therefore reduced to $4,200,000.00 rather than stretching ...",
 "required_documents": [
  "Purchase request / requisition with funds certification for fund 999-2026-0600",
  "Bona fide need statement tying the requirement to the current period of availability (expires 2026-09-30)",
  "Statement of work or requirement description for the option period, confirmed against the contract's option terms",
  "Confirmation of the priced option value on DCI26C000954 (must be at or above $4,200,000.00)",
  "Confirmation that the services are a proper use of the PPA and fund",
  "Contracting Officer's determination and documentation supporting the option exercise, including price reasonableness and current vendor responsibility",
  "... 3 more items"
 ],
 "milestones": [
  "2026-08-03: Program office confirms the bona fide need, defines the option-period requirement, and designates a point of contact for the package",
  "2026-08-07: Contracting Officer confirms the priced option value and the option exercise terms and timing on DCI26C000954; amount is finalized (not above $4,207,034.66)",
  "2026-08-12: Purchase request and funds certification completed and approved by the program office and budget/finance",
  "2026-08-14: Complete package submitted to Contracting (ahead of the latest P80 start date)",
  "2026-08-18: Latest start of the 29-day P80 PALT window for Option Exercise; escalate immediately if Contracting has not started",
  "2026-08-28: Contracting Officer determinations and price reasonableness documentation drafted; vendor notified of the intended exercise",
  "... 5 more items"
 ],
 "status": "Submitted to Acquisition",
 "source": "App - on-demand AI draft",
 "model_endpoint": "databricks-claude-sonnet-5-5",
 "created_by": "rahul.chopra@databricks.com",
 "created_at": "2026-10-15T14:25:27.944012+00:00",
 "updated_at": "2026-10-15T14:25:27.944012+00:00"
}
```

## Quarterly budget-performance review: quarters, AI narratives, sign-offs

`GET /api/quarterly` → **HTTP 200** in 70 ms

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

## Write-back: CFO sign-off for OCIO

`POST /api/quarterly/OCIO/signoff` → **HTTP 200** in 50 ms

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
 "signoff_id": 4,
 "office_code": "OCIO",
 "fiscal_year": 2026,
 "fiscal_quarter": 3,
 "decision": "Approved with conditions",
 "comment": "Approve Q3; submit Q4 obligation recovery plan for lines behind the approved spend plan.",
 "signed_by": "rahul.chopra@databricks.com",
 "signed_at": "2026-10-15T14:25:28.066673+00:00"
}
```

## Ask Genie through the app (on behalf of the signed-in user)

`POST /api/genie` → **HTTP 200** in 27102 ms

Request body:
```json
{
 "question": "Which program offices are furthest behind their spend plan?"
}
```
Response:
```json
{
 "conversation_id": "01f1c8a445081bada9cecbf5ffa4b8bb",
 "status": "COMPLETED",
 "text": "Would you prefer to see how offices compare based on expenditures versus plan instead of obligations versus plan?",
 "sql": "SELECT `office`, `office_code`, ROUND(try_divide(MEASURE(`total_budget`),1e6), 1) AS `total_budget_m`, ROUND(try_divide(MEASURE(`planned_obligations_to_date`),1e6), 1) AS `planned_obligations_to_date_m`, ROUND(try_divide(MEASURE(`obligated_to_date`),1e6), 1) AS `obligated_to_date_m`, ROUND(100 * MEASURE(`burn_rate_vs_plan`), 1) AS `burn_rate_vs_plan_pct`\nFROM rachopra_catalog.fe_bar.mv_budget_exec...",
 "description": "You want to see the budget execution status for each program office, including their total budget, planned obligations to date, actual obligations to date, and how their actual spending compares to the planned spending.",
 "columns": [
  "office",
  "office_code",
  "total_budget_m",
  "planned_obligations_to_date_m",
  "obligated_to_date_m",
  "burn_rate_vs_plan_pct"
 ],
 "rows": [
  [
   "Office of Transportation Safety",
   "OTS",
   "304.1",
   "212.1",
   "176.2",
   "83.1"
  ],
  [
   "Office of Workforce Development",
   "OWD",
   "165.6",
   "104.0",
   "95.0",
   "91.4"
  ],
  [
   "Office of Grid Modernization",
   "OGM",
   "492.6",
   "337.7",
   "309.5",
   "91.7"
  ],
  [
   "Office of the Chief Information Officer",
   "OCIO",
   "595.4",
   "418.5",
   "384.9",
   "92.0"
  ],
  [
   "Office of Water Systems",
   "OWS",
   "297.7",
   "203.2",
   "190.8",
   "93.9"
  ],
  [
   "Office of Management and Administration",
   "OMA",
   "291.6",
   "210.4",
   "199.6",
   "94.9"
  ]
 ],
 "identity": "signed-in user"
}
```

