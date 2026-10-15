# Highest-exposure alert of each type

Executed 2026-10-15 14:26 UTC

```sql
SELECT alert_type, severity, entity_id, ROUND(amount_at_risk / 1e6, 2) AS amount_at_risk_m, detail
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY alert_type ORDER BY amount_at_risk DESC) AS rn
      FROM rachopra_catalog.fe_bar.gold_financial_risk_alerts) WHERE rn = 1 ORDER BY amount_at_risk_m DESC
```

**Result:**

| alert_type | severity | entity_id | amount_at_risk_m | detail |
|---|---|---|---|---|
| STALE_SPEND_PLAN | Medium | OTS-PCI-01-FY2026 | 48.79 | Bridge Inspection Systems spend plan was last revised 161 days ago (rev 2 on 2026-02-20); balances may be mis-forecast. |
| BURN_RATE_VARIANCE | Medium | OCIO-PCI-01-FY2024 | 22.32 | Financial System Modernization obligations are 77% of the approved spend plan to date ($74,121,632 obligated vs $96,439,415 planned in baseline rev 2). |
| LAPSE_RISK | High | OCIO-PCI-01-FY2024 | 20.06 | Financial System Modernization (999-2024/2026-0400) has $20,062,036 (19.6% of budget) neither obligated nor committed, with 61 days until the funds expire on 2026-09-30. |
| PROCUREMENT_WILL_MISS_EXPIRATION | High | PR-26-OTS-0200 | 5.58 | PR-26-OTS-0200 "Highway Safety Improvement Grants - competitive awards cohort 1" ($5,579,293, Grant Award) is Under Evaluation; forecast award 2026-10-07 is after the funds expire on 2026-09-30. |
| COMMITMENTS_EXCEED_AVAILABLE | High | OGM-GA-01-FY2026 | 4.34 | State Energy Resilience Grants has $45,339,395 certified on open procurement requests but only $40,995,906 unobligated; funds-control review needed before more requests are certified or awarded. |
| INVOICE_EXCEEDS_OBLIGATION | High | DCI24F001882-000 | 1.41 | Invoices against DCI24F001882-000 total $2,816,268, exceeding the $1,408,134 obligated. |
| POTENTIAL_DUPLICATE_INVOICE | High | INV-00019734 | 1.41 | Vendor invoice RED-00203 from Redline Federal Group ($1,408,134) was received 2 times (INV-00019453, INV-00019734). |
| PROMPT_PAY_RISK | High | INV-00019734 | 1.41 | Invoice INV-00019734 ($1,408,134, Redline Federal Group) is Received and was due on 2024-09-03; Prompt Payment Act interest accrues after the due date. |
| APPORTIONMENT_EXCEEDED | Critical | OCIO-PCI-01-FY2026 | 1.36 | Financial System Modernization obligations of $33,892,926 exceed the apportioned amount of $32,537,000 by $1,355,926 - potential Antideficiency Act violation. Footnote B: balance withheld pending congressional spend-plan notification |
| UNMATCHED_INVOICE | Medium | INV-00006201 | 0.27 | Invoice INV-00006201 from Vantage Federal Group ($266,122) references DCI24F0005XX, which matches no recorded obligation. |
