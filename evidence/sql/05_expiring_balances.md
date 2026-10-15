# Unobligated balances approaching deadlines (expire within 90 days)

Executed 2026-10-15 14:26 UTC

```sql
SELECT b.line_id, b.ppa_name, b.tas, b.days_to_expiration, ROUND(b.total_budget / 1e6, 2) AS budget_m,
       ROUND(100 * b.obligation_rate, 1) AS obligated_pct, ROUND(b.uncommitted_balance / 1e6, 2) AS uncommitted_m,
       ROUND(100 * b.burn_rate_vs_plan, 0) AS vs_plan_pct, f.risk_tier, ROUND(f.projected_lapse_amount / 1e6, 2) AS projected_lapse_m
FROM rachopra_catalog.fe_bar.gold_budget_execution b LEFT JOIN rachopra_catalog.fe_bar.gold_lapse_risk_forecast f USING (line_id)
WHERE b.fund_status = 'Current' AND b.days_to_expiration <= 90
ORDER BY f.projected_lapse_amount DESC NULLS LAST
```

**Result:**

| line_id | ppa_name | tas | days_to_expiration | budget_m | obligated_pct | uncommitted_m | vs_plan_pct | risk_tier | projected_lapse_m |
|---|---|---|---|---|---|---|---|---|---|
| OWD-GA-01-FY2026 | Infrastructure Workforce Grants | 999-2026-0600 | 61 | 65.76 | 41.2 | 5.29 | 73 | Critical | 9.27 |
| OCIO-PCI-01-FY2024 | Financial System Modernization | 999-2024/2026-0400 | 61 | 102.17 | 72.6 | 20.06 | 77 | High | 7.35 |
| OTS-PCI-01-FY2024 | Bridge Inspection Systems | 999-2024/2026-0400 | 61 | 54.47 | 87.0 | 1.2 | 92 | Critical | 6.1 |
| OTS-GA-01-FY2026 | Highway Safety Improvement Grants | 999-2026-0600 | 61 | 21.07 | 16.7 | 0.1 | 30 | Critical | 5.55 |
| OGM-GA-01-FY2026 | State Energy Resilience Grants | 999-2026-0600 | 61 | 81.66 | 49.8 | -4.34 | 89 | High | 4.41 |
| OCIO-PCI-02-FY2024 | Cloud Migration | 999-2024/2026-0400 | 61 | 66.23 | 92.0 | 1.54 | 97 | High | 3.46 |
| OTS-OS-01-FY2026 | Safety Inspection Operations | 999-2026-0100 | 61 | 38.35 | 76.7 | 2.45 | 102 | High | 3.37 |
| OGM-PCI-01-FY2024 | Substation Hardening | 999-2024/2026-0400 | 61 | 99.1 | 88.1 | 4.38 | 93 | Moderate | 2.91 |
| OTS-OS-02-FY2026 | Incident Investigation | 999-2026-0100 | 61 | 23.69 | 68.5 | 4.44 | 92 | Critical | 2.52 |
| OWS-GA-01-FY2026 | Tribal and Rural Water Grants | 999-2026-0600 | 61 | 47.87 | 39.0 | 0.43 | 71 | Moderate | 2.15 |
| OWS-PCI-01-FY2024 | Water Infrastructure Modernization | 999-2024/2026-0400 | 61 | 54.52 | 97.3 | 1.19 | 102 | Moderate | 1.99 |
| OTS-RD-01-FY2025 | Automated Vehicle Safety Research | 999-2025/2026-0800 | 61 | 21.07 | 77.2 | 0.63 | 85 | High | 1.85 |
| OWD-GA-02-FY2026 | Apprenticeship Expansion Grants | 999-2026-0600 | 61 | 33.24 | 61.1 | -1.53 | 109 | Moderate | 1.66 |
| OWS-OS-01-FY2026 | Drinking Water Program Operations | 999-2026-0100 | 61 | 22.88 | 46.0 | 1.69 | 62 | High | 1.42 |
| OCIO-OS-01-FY2026 | Enterprise IT Operations | 999-2026-0100 | 61 | 34.44 | 77.6 | 0.14 | 104 | Moderate | 1.35 |
| OWS-OS-02-FY2026 | Laboratory Services | 999-2026-0100 | 61 | 23.48 | 82.8 | -0.92 | 111 | High | 1.23 |
| OMA-OS-02-FY2026 | Human Capital Services | 999-2026-0100 | 61 | 30.62 | 60.8 | 1.31 | 81 | Moderate | 1.05 |
| OMA-OS-01-FY2026 | Facilities and Logistics | 999-2026-0100 | 61 | 29.91 | 53.5 | 0.77 | 71 | Moderate | 1.05 |
| OMA-PCI-01-FY2024 | Headquarters Consolidation | 999-2024/2026-0400 | 61 | 53.56 | 94.6 | 2.89 | 100 | Low | 1.02 |
| OGM-RD-01-FY2025 | Advanced Transmission Research | 999-2025/2026-0800 | 61 | 20.48 | 85.9 | 0.71 | 93 | Moderate | 0.99 |
| OWD-RD-01-FY2025 | Workforce Outcomes Evaluation | 999-2025/2026-0800 | 61 | 26.63 | 96.3 | 0.6 | 105 | Moderate | 0.99 |
| OCIO-OS-02-FY2026 | Cybersecurity Operations | 999-2026-0100 | 61 | 26.46 | 76.7 | 1.06 | 102 | Moderate | 0.98 |
| OMA-OS-04-FY2026 | Financial Management Services | 999-2026-0100 | 61 | 34.78 | 74.9 | 0.13 | 100 | Moderate | 0.89 |
| OGM-OS-01-FY2026 | Grid Resilience Program Operations | 999-2026-0100 | 61 | 41.08 | 87.5 | -0.22 | 115 | Low | 0.7 |
| OGM-OS-02-FY2026 | Outage Analytics and Monitoring | 999-2026-0100 | 61 | 22.77 | 78.6 | 0.15 | 106 | Moderate | 0.68 |
| OWD-OS-01-FY2026 | Training Program Administration | 999-2026-0100 | 61 | 10.28 | 45.1 | 1.77 | 60 | Moderate | 0.44 |
| OCIO-OS-03-FY2026 | Data and Analytics Platform | 999-2026-0100 | 61 | 7.55 | 96.0 | 0.15 | 128 | Moderate | 0.25 |
| OWS-RD-01-FY2025 | Water Quality Sensor Research | 999-2025/2026-0800 | 61 | 13.65 | 95.3 | 0.21 | 104 | Low | 0.16 |
| OMA-OS-03-FY2026 | Acquisition Management | 999-2026-0100 | 61 | 35.96 | 90.4 | 0.35 | 120 | Low | 0.08 |
