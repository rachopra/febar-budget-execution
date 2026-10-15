# Top projected lapses with model-explained drivers

Executed 2026-10-15 14:26 UTC

```sql
SELECT line_id, ppa_name, days_to_expiration, ROUND(100 * obligation_rate, 1) AS obligated_pct,
       ROUND(100 * predicted_lapse_rate, 1) AS predicted_lapse_pct, ROUND(projected_lapse_amount / 1e6, 2) AS projected_lapse_m,
       risk_tier, array_join(top_risk_drivers, '; ') AS drivers
FROM rachopra_catalog.fe_bar.gold_lapse_risk_forecast WHERE predicted_lapse_rate IS NOT NULL
ORDER BY projected_lapse_amount DESC LIMIT 12
```

**Result:**

| line_id | ppa_name | days_to_expiration | obligated_pct | predicted_lapse_pct | projected_lapse_m | risk_tier | drivers |
|---|---|---|---|---|---|---|---|
| OWD-GA-01-FY2026 | Infrastructure Workforce Grants | 61 | 41.2 | 14.1 | 9.27 | Critical | cancelled PR value 13% vs typical 0% (+4.2 pp); obligations vs spend plan 80% vs typical 94% (+2.2 pp); long-PALT pipeline (new awards/grants) 42% vs typical 8% (+2.0 pp) |
| OCIO-PCI-01-FY2024 | Financial System Modernization | 61 | 72.5 | 7.2 | 7.35 | High | cancelled PR value 16% vs typical 0% (+2.9 pp); prior-year lapse rate 3% vs typical 1% (+1.4 pp) |
| OTS-PCI-01-FY2024 | Bridge Inspection Systems | 61 | 87.0 | 11.2 | 6.1 | Critical | cancelled PR value 11% vs typical 0% (+4.2 pp); prior-year lapse rate 3% vs typical 1% (+2.0 pp); obligations vs spend plan 92% vs typical 94% (+1.8 pp) |
| OTS-GA-01-FY2026 | Highway Safety Improvement Grants | 61 | 16.7 | 26.3 | 5.55 | Critical | prior-year lapse rate 23% vs typical 1% (+8.7 pp); obligations vs spend plan 30% vs typical 94% (+7.8 pp); long-PALT pipeline (new awards/grants) 83% vs typical 8% (+0.9 pp) |
| OGM-GA-01-FY2026 | State Energy Resilience Grants | 61 | 49.8 | 5.4 | 4.41 | High | cancelled PR value 4% vs typical 0% (+1.7 pp); avg age of open PRs (days) 116 vs typical 56 (+0.4 pp); open procurement pipeline 56% vs typical 19% (+0.3 pp) |
| OCIO-PCI-02-FY2024 | Cloud Migration | 61 | 92.0 | 5.2 | 3.46 | High | prior-year lapse rate 2% vs typical 1% (+0.7 pp); cancelled PR value 1% vs typical 0% (+0.6 pp) |
| OTS-OS-01-FY2026 | Safety Inspection Operations | 61 | 76.6 | 8.8 | 3.37 | High | prior-year lapse rate 20% vs typical 1% (+4.3 pp); cancelled PR value 5% vs typical 0% (+0.9 pp) |
| OGM-PCI-01-FY2024 | Substation Hardening | 61 | 88.1 | 2.9 | 2.91 | Moderate | cancelled PR value 6% vs typical 0% (+1.0 pp) |
| OTS-OS-02-FY2026 | Incident Investigation | 61 | 68.5 | 10.6 | 2.52 | Critical | prior-year lapse rate 26% vs typical 1% (+3.2 pp); obligations vs spend plan 92% vs typical 94% (+1.7 pp); cancelled PR value 9% vs typical 0% (+0.9 pp) |
| OWS-GA-01-FY2026 | Tribal and Rural Water Grants | 61 | 39.0 | 4.5 | 2.15 | Moderate | cancelled PR value 5% vs typical 0% (+1.0 pp); prior-year lapse rate 9% vs typical 1% (+0.5 pp) |
| OWS-PCI-01-FY2024 | Water Infrastructure Modernization | 61 | 97.3 | 3.6 | 1.99 | Moderate | prior-year lapse rate 3% vs typical 1% (+2.2 pp) |
| OTS-RD-01-FY2025 | Automated Vehicle Safety Research | 61 | 77.2 | 8.8 | 1.85 | High | obligations vs spend plan 84% vs typical 94% (+4.2 pp); prior-year lapse rate 3% vs typical 1% (+3.7 pp) |
