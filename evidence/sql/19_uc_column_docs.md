# Unity Catalog column documentation on gold_budget_execution

Executed 2026-11-02 18:12 UTC

```sql
SELECT column_name, data_type, comment FROM rachopra_catalog.information_schema.columns
WHERE table_schema = 'fe_bar' AND table_name = 'gold_budget_execution' AND comment IS NOT NULL ORDER BY ordinal_position
```

**Result:**

| column_name | data_type | comment |
|---|---|---|
| line_id | STRING | Budget line key: PPA code + budget fiscal year (e.g. OTS-GA-01-FY2026) |
| budget_fiscal_year | INT | Budget fiscal year (BFY) the funds were appropriated for |
| ppa_code | STRING | Program, Project or Activity (PPA) code |
| tas | STRING | Treasury Account Symbol funding the line (agency-BFY[/EPOA]-main account) |
| fund_type | STRING | annual or multi-year funds |
| expiration_date | DATE | Last day the funds may be newly obligated (end of the period of availability) |
| days_to_expiration | INT | Days from the reporting date until the funds expire |
| fund_status | STRING | Current (still available for new obligations) or Expired |
| total_budget | DECIMAL | Enacted budget authority for the line ($) |
| apportioned_to_date | DECIMAL | OMB-apportioned amount available through the current quarter ($) |
| planned_obligations_to_date | DECIMAL | Obligations the approved baseline spend plan expected by the reporting date ($) |
| committed_not_obligated | DECIMAL | Funds certified on open procurement requests, not yet obligated ($) |
| obligated_to_date | DECIMAL | Net obligations recorded through the reporting date, after deobligations ($) |
| invoiced_to_date | DECIMAL | Invoices and grant drawdowns received against the line, excluding rejected ($) |
| expended_to_date | DECIMAL | Payments disbursed against the line through the reporting date ($) |
| reforecast_obligations_remaining | DECIMAL | Obligations still planned after the reporting date in the office's latest re-forecast ($) |
| spend_plan_age_days | INT | Days since the office last revised its spend plan |
| unobligated_balance | DECIMAL | Remaining balance: total budget minus obligations ($) |
| uncommitted_balance | DECIMAL | Total budget minus obligations minus open commitments ($) |
| obligation_rate | DECIMAL | Obligated to date / total budget |
| expenditure_rate | DECIMAL | Expended to date / total budget |
| burn_rate_vs_plan | DECIMAL | Obligated to date / planned obligations to date (1.0 = on plan) |
| execution_status | STRING | On Plan, Behind Plan (<85% of plan), Ahead of Plan (>115%), No Plan, Expired |
