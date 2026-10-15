-- Gold: the governed budget-execution model leadership, Genie, ML and the app all read.
-- ${as_of_date} is the reporting date (pipeline configuration), so every metric is
-- point-in-time and reproducible.

-- ---------------------------------------------------------------------------------------
-- Budget execution by line (PPA x budget fiscal year): the dashboard's core table.
-- ---------------------------------------------------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW gold_budget_execution
COMMENT 'Budget execution by budget line (PPA x budget fiscal year) as of the reporting date: total budget, apportionment, baseline spend plan and latest re-forecast, commitments, obligations, expenditures, balances and rates. One row per line.'
AS
WITH params AS (SELECT DATE '${as_of_date}' AS as_of),
plan AS (  -- approved baseline operating plan: what execution is measured against
  SELECT sp.budget_fiscal_year, sp.ppa_code,
         SUM(sp.planned_obligations) AS planned_obligations_total,
         SUM(CASE WHEN sp.plan_month <= p.as_of THEN sp.planned_obligations ELSE 0 END) AS planned_obligations_to_date,
         SUM(CASE WHEN sp.plan_month <= p.as_of THEN sp.planned_expenditures ELSE 0 END) AS planned_expenditures_to_date,
         MAX(sp.revision_no) AS baseline_plan_revision
  FROM silver_spend_plan_baseline sp CROSS JOIN params p
  GROUP BY sp.budget_fiscal_year, sp.ppa_code
),
reforecast AS (  -- latest revision submitted by the office
  SELECT sp.budget_fiscal_year, sp.ppa_code,
         SUM(CASE WHEN sp.plan_month > p.as_of THEN sp.planned_obligations ELSE 0 END) AS reforecast_obligations_remaining,
         MAX(sp.revision_no) AS spend_plan_revision,
         MAX(sp.revision_date) AS spend_plan_revised_on,
         MAX(sp.source_template) AS spend_plan_template
  FROM silver_spend_plan_current sp CROSS JOIN params p
  GROUP BY sp.budget_fiscal_year, sp.ppa_code
),
obl AS (
  SELECT o.budget_fiscal_year, o.ppa_code,
         SUM(o.obligated_amount) AS obligated_to_date,
         SUM(CASE WHEN o.obligated_amount < 0 THEN -o.obligated_amount ELSE 0 END) AS deobligated_to_date,
         SUM(CASE WHEN o.obligation_date > date_sub(p.as_of, 30) THEN o.obligated_amount ELSE 0 END) AS obligated_last_30_days,
         COUNT(DISTINCT o.contract_number) AS obligating_documents
  FROM silver_obligations o CROSS JOIN params p
  WHERE o.obligation_date <= p.as_of
  GROUP BY o.budget_fiscal_year, o.ppa_code
),
doc_line AS (
  SELECT DISTINCT obligation_document, budget_fiscal_year, ppa_code FROM silver_obligations
),
spend AS (
  SELECT d.budget_fiscal_year, d.ppa_code,
         SUM(CASE WHEN i.status <> 'Rejected' THEN i.invoice_amount ELSE 0 END) AS invoiced_to_date,
         SUM(CASE WHEN i.status = 'Paid' AND i.paid_date <= p.as_of THEN i.paid_amount ELSE 0 END) AS expended_to_date,
         SUM(CASE WHEN i.status IN ('Received', 'Approved') THEN i.invoice_amount ELSE 0 END) AS invoices_pending_payment
  FROM silver_invoices i
  JOIN doc_line d ON i.obligation_document = d.obligation_document
  CROSS JOIN params p
  WHERE i.received_date <= p.as_of
  GROUP BY d.budget_fiscal_year, d.ppa_code
),
prs AS (
  SELECT budget_fiscal_year, ppa_code,
         SUM(CASE WHEN status IN ('Funds Certified', 'In Solicitation', 'Under Evaluation') THEN estimated_amount ELSE 0 END) AS committed_not_obligated,
         SUM(CASE WHEN status IN ('Draft', 'Submitted') THEN estimated_amount ELSE 0 END) AS requested_not_certified,
         COUNT_IF(status NOT IN ('Awarded', 'Cancelled')) AS open_procurement_requests
  FROM silver_procurement_requests
  GROUP BY budget_fiscal_year, ppa_code
),
base AS (
  SELECT
    l.line_id, l.budget_fiscal_year, l.ppa_code, l.ppa_name, l.office_code, l.office_name,
    l.appropriation_code, l.appropriation_name, l.tas, l.fund_type, l.expiration_date,
    p.as_of AS as_of_date,
    datediff(l.expiration_date, p.as_of) AS days_to_expiration,
    CASE WHEN p.as_of <= l.expiration_date THEN 'Current' ELSE 'Expired' END AS fund_status,
    l.enacted_amount AS total_budget,
    CASE
      WHEN p.as_of < make_date(l.budget_fiscal_year, 1, 1) THEN l.apportioned_q1
      WHEN p.as_of < make_date(l.budget_fiscal_year, 4, 1) THEN l.apportioned_q2
      WHEN p.as_of < make_date(l.budget_fiscal_year, 7, 1) THEN l.apportioned_q3
      ELSE l.apportioned_q4
    END AS apportioned_to_date,
    l.apportionment_footnote,
    COALESCE(pl.planned_obligations_total, 0) AS planned_obligations_total,
    COALESCE(pl.planned_obligations_to_date, 0) AS planned_obligations_to_date,
    COALESCE(pl.planned_expenditures_to_date, 0) AS planned_expenditures_to_date,
    COALESCE(pr.requested_not_certified, 0) AS requested_not_certified,
    COALESCE(pr.committed_not_obligated, 0) AS committed_not_obligated,
    COALESCE(o.obligated_to_date, 0) AS obligated_to_date,
    COALESCE(o.deobligated_to_date, 0) AS deobligated_to_date,
    COALESCE(o.obligated_last_30_days, 0) AS obligated_last_30_days,
    COALESCE(s.invoiced_to_date, 0) AS invoiced_to_date,
    COALESCE(s.expended_to_date, 0) AS expended_to_date,
    COALESCE(s.invoices_pending_payment, 0) AS invoices_pending_payment,
    COALESCE(pr.open_procurement_requests, 0) AS open_procurement_requests,
    pl.baseline_plan_revision, rf.spend_plan_revision, rf.spend_plan_revised_on, rf.spend_plan_template,
    COALESCE(rf.reforecast_obligations_remaining, 0) AS reforecast_obligations_remaining,
    datediff(p.as_of, rf.spend_plan_revised_on) AS spend_plan_age_days
  FROM silver_budget_lines l
  CROSS JOIN params p
  LEFT JOIN plan pl ON l.budget_fiscal_year = pl.budget_fiscal_year AND l.ppa_code = pl.ppa_code
  LEFT JOIN reforecast rf ON l.budget_fiscal_year = rf.budget_fiscal_year AND l.ppa_code = rf.ppa_code
  LEFT JOIN obl o ON l.budget_fiscal_year = o.budget_fiscal_year AND l.ppa_code = o.ppa_code
  LEFT JOIN spend s ON l.budget_fiscal_year = s.budget_fiscal_year AND l.ppa_code = s.ppa_code
  LEFT JOIN prs pr ON l.budget_fiscal_year = pr.budget_fiscal_year AND l.ppa_code = pr.ppa_code
)
SELECT
  *,
  total_budget - obligated_to_date AS unobligated_balance,
  total_budget - obligated_to_date - committed_not_obligated AS uncommitted_balance,
  obligated_to_date - expended_to_date AS undelivered_orders,
  CAST(try_divide(obligated_to_date, total_budget) AS DECIMAL(9, 4)) AS obligation_rate,
  CAST(try_divide(expended_to_date, total_budget) AS DECIMAL(9, 4)) AS expenditure_rate,
  CAST(try_divide(obligated_to_date, planned_obligations_to_date) AS DECIMAL(9, 4)) AS burn_rate_vs_plan,
  CAST(try_divide(expended_to_date, planned_expenditures_to_date) AS DECIMAL(9, 4)) AS expenditure_burn_vs_plan,
  obligated_to_date - planned_obligations_to_date AS obligation_variance_to_plan,
  CASE
    WHEN fund_status = 'Expired' THEN 'Expired'
    WHEN planned_obligations_to_date = 0 THEN 'No Plan'
    WHEN obligated_to_date / planned_obligations_to_date < 0.85 THEN 'Behind Plan'
    WHEN obligated_to_date / planned_obligations_to_date > 1.15 THEN 'Ahead of Plan'
    ELSE 'On Plan'
  END AS execution_status
FROM base;


-- ---------------------------------------------------------------------------------------
-- Monthly planned vs actual obligations and expenditures (burn curves).
-- ---------------------------------------------------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW gold_monthly_execution
COMMENT 'Monthly and cumulative planned (baseline operating plan) vs actual obligations and expenditures by budget line, through the reporting date. Use for burn-rate charts.'
AS
WITH params AS (SELECT DATE '${as_of_date}' AS as_of),
plan AS (
  SELECT budget_fiscal_year, ppa_code, plan_month AS month,
         SUM(planned_obligations) AS planned_obligations,
         SUM(planned_expenditures) AS planned_expenditures
  FROM silver_spend_plan_baseline
  GROUP BY ALL
),
act AS (
  SELECT o.budget_fiscal_year, o.ppa_code, CAST(date_trunc('MONTH', o.obligation_date) AS DATE) AS month,
         SUM(o.obligated_amount) AS actual_obligations
  FROM silver_obligations o CROSS JOIN params p
  WHERE o.obligation_date <= p.as_of
  GROUP BY ALL
),
paid AS (
  SELECT d.budget_fiscal_year, d.ppa_code, CAST(date_trunc('MONTH', i.paid_date) AS DATE) AS month,
         SUM(i.paid_amount) AS actual_expenditures
  FROM silver_invoices i
  JOIN (SELECT DISTINCT obligation_document, budget_fiscal_year, ppa_code FROM silver_obligations) d
    ON i.obligation_document = d.obligation_document
  CROSS JOIN params p
  WHERE i.status = 'Paid' AND i.paid_date <= p.as_of
  GROUP BY ALL
),
spine AS (
  SELECT budget_fiscal_year, ppa_code, month FROM plan
  UNION SELECT budget_fiscal_year, ppa_code, month FROM act
  UNION SELECT budget_fiscal_year, ppa_code, month FROM paid
),
monthly AS (
  SELECT s.budget_fiscal_year, s.ppa_code, s.month,
         year(s.month) + CASE WHEN month(s.month) >= 10 THEN 1 ELSE 0 END AS activity_fiscal_year,
         CAST(((month(s.month) + 2) % 12) DIV 3 + 1 AS INT) AS fiscal_quarter,
         COALESCE(pl.planned_obligations, 0) AS planned_obligations,
         COALESCE(a.actual_obligations, 0) AS actual_obligations,
         COALESCE(pl.planned_expenditures, 0) AS planned_expenditures,
         COALESCE(pd.actual_expenditures, 0) AS actual_expenditures
  FROM spine s
  LEFT JOIN plan pl USING (budget_fiscal_year, ppa_code, month)
  LEFT JOIN act a USING (budget_fiscal_year, ppa_code, month)
  LEFT JOIN paid pd USING (budget_fiscal_year, ppa_code, month)
)
SELECT
  l.line_id, m.budget_fiscal_year, m.ppa_code, l.ppa_name, l.office_code, l.appropriation_code,
  m.month, m.activity_fiscal_year, m.fiscal_quarter, m.month <= p.as_of AS is_actualized,
  m.planned_obligations, m.actual_obligations, m.planned_expenditures, m.actual_expenditures,
  SUM(m.planned_obligations) OVER w AS cumulative_planned_obligations,
  SUM(m.actual_obligations) OVER w AS cumulative_actual_obligations,
  SUM(m.planned_expenditures) OVER w AS cumulative_planned_expenditures,
  SUM(m.actual_expenditures) OVER w AS cumulative_actual_expenditures,
  l.enacted_amount AS total_budget
FROM monthly m
JOIN silver_budget_lines l USING (budget_fiscal_year, ppa_code)
CROSS JOIN params p
WINDOW w AS (PARTITION BY m.budget_fiscal_year, m.ppa_code ORDER BY m.month
             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW);


-- ---------------------------------------------------------------------------------------
-- Procurement-cycle visibility and forecasting.
-- ---------------------------------------------------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW gold_procurement_pipeline
COMMENT 'Procurement-cycle visibility: every procurement request with milestone dates, days in current status, PALT, and for open requests a forecast award date (historical median PALT for the acquisition type) compared with fund expiration.'
AS
WITH params AS (SELECT DATE '${as_of_date}' AS as_of),
milestones AS (
  SELECT pr_id,
         MIN(CASE WHEN status = 'Draft' THEN event_ts END) AS drafted_at,
         MIN(CASE WHEN status = 'Submitted' THEN event_ts END) AS submitted_at,
         MIN(CASE WHEN status = 'Funds Certified' THEN event_ts END) AS funds_certified_at,
         MIN(CASE WHEN status = 'In Solicitation' THEN event_ts END) AS solicitation_at,
         MIN(CASE WHEN status = 'Under Evaluation' THEN event_ts END) AS evaluation_at,
         MIN(CASE WHEN status = 'Awarded' THEN event_ts END) AS awarded_at,
         MIN(CASE WHEN status = 'Cancelled' THEN event_ts END) AS cancelled_at
  FROM silver_pr_events
  WHERE event_type IN ('PR_STATUS_CHANGE', 'AWARD')
  GROUP BY pr_id
),
palt AS (
  SELECT r.acquisition_type,
         CAST(percentile_approx(datediff(m.awarded_at, m.submitted_at), 0.5) AS INT) AS median_palt_days,
         CAST(percentile_approx(datediff(m.awarded_at, m.submitted_at), 0.8) AS INT) AS p80_palt_days,
         COUNT(*) AS historical_awards
  FROM silver_procurement_requests r JOIN milestones m USING (pr_id)
  WHERE r.status = 'Awarded' AND m.submitted_at IS NOT NULL
  GROUP BY r.acquisition_type
),
joined AS (
  SELECT r.pr_id, l.line_id, r.budget_fiscal_year, r.ppa_code, l.ppa_name, r.office_code, l.tas,
         l.expiration_date, r.title, r.description, r.object_class, r.acquisition_type,
         r.contract_vehicle, r.priority, r.estimated_amount, r.status, r.status_reason,
         r.event_ts AS status_since, r.requested_by, r.contracting_officer, r.need_by_date,
         r.year_end_action, r.contract_number, r.obligated_amount AS award_amount, r.vendor_name,
         m.drafted_at, m.submitted_at, m.funds_certified_at, m.solicitation_at, m.evaluation_at,
         m.awarded_at, m.cancelled_at,
         pa.median_palt_days, pa.p80_palt_days,
         r.status NOT IN ('Awarded', 'Cancelled') AS is_open,
         p.as_of
  FROM silver_procurement_requests r
  JOIN silver_budget_lines l USING (budget_fiscal_year, ppa_code)
  LEFT JOIN milestones m USING (pr_id)
  LEFT JOIN palt pa USING (acquisition_type)
  CROSS JOIN params p
)
SELECT
  * EXCEPT (as_of),
  datediff(as_of, to_date(status_since)) AS days_in_status,
  datediff(awarded_at, submitted_at) AS palt_days,
  CASE WHEN is_open THEN datediff(as_of, to_date(COALESCE(submitted_at, drafted_at))) END AS age_days,
  CASE WHEN is_open THEN greatest(
         date_add(to_date(COALESCE(submitted_at, date_add(drafted_at, 7))), median_palt_days),
         date_add(as_of, 1)) END AS forecast_award_date,
  is_open AND greatest(
         date_add(to_date(COALESCE(submitted_at, date_add(drafted_at, 7))), median_palt_days),
         date_add(as_of, 1)) > expiration_date AS at_risk_of_missing_expiration
FROM joined;


CREATE OR REFRESH MATERIALIZED VIEW gold_procurement_cycle_times
COMMENT 'Procurement administrative lead time by stage: median and p80 days spent in each status by office and acquisition type, from the SCD2 status history.'
AS
SELECT office_code, acquisition_type, status AS stage,
       COUNT(*) AS completed_stage_transitions,
       CAST(percentile_approx(datediff(__END_AT, __START_AT), 0.5) AS INT) AS median_days_in_stage,
       CAST(percentile_approx(datediff(__END_AT, __START_AT), 0.8) AS INT) AS p80_days_in_stage,
       ROUND(AVG(datediff(__END_AT, __START_AT)), 1) AS avg_days_in_stage
FROM silver_pr_status_history
WHERE __END_AT IS NOT NULL AND status NOT IN ('Awarded', 'Cancelled')
GROUP BY ALL;


-- ---------------------------------------------------------------------------------------
-- Financial risk and variance alerts.
-- ---------------------------------------------------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW gold_financial_risk_alerts
COMMENT 'Financial risk and variance alerts as of the reporting date: lapse risk, apportionment (Antideficiency Act) exposure, commitments exceeding available funds, burn-rate variance, stale spend plans, procurements that will miss fund expiration, stalled procurements, over-billing, duplicate and unmatched invoices, and Prompt Payment Act exposure.'
AS
WITH params AS (SELECT DATE '${as_of_date}' AS as_of),
cur AS (SELECT * FROM gold_budget_execution WHERE fund_status = 'Current'),
doc_line AS (
  SELECT obligation_document, MAX(line_id) AS line_id, MAX(o.office_code) AS office_code,
         MAX(o.ppa_code) AS ppa_code, MAX(o.budget_fiscal_year) AS budget_fiscal_year,
         SUM(o.obligated_amount) AS obligated_amount
  FROM silver_obligations o
  JOIN silver_budget_lines l USING (budget_fiscal_year, ppa_code)
  GROUP BY obligation_document
),
alerts AS (
  SELECT 'LAPSE_RISK' AS alert_type,
         CASE WHEN days_to_expiration <= 60 AND uncommitted_balance / total_budget > 0.10 THEN 'Critical'
              WHEN uncommitted_balance / total_budget > 0.07 THEN 'High' ELSE 'Medium' END AS severity,
         line_id, office_code, ppa_code, budget_fiscal_year, line_id AS entity_id,
         uncommitted_balance AS amount_at_risk,
         format_string('%s (%s) has $%,.0f (%.1f%% of budget) neither obligated nor committed, with %d days until the funds expire on %s.',
                       ppa_name, tas, CAST(uncommitted_balance AS DOUBLE), 100 * CAST(uncommitted_balance / total_budget AS DOUBLE),
                       days_to_expiration, CAST(expiration_date AS STRING)) AS detail
  FROM cur
  WHERE days_to_expiration <= 120 AND uncommitted_balance / total_budget > 0.03

  UNION ALL
  SELECT 'APPORTIONMENT_EXCEEDED', 'Critical', line_id, office_code, ppa_code, budget_fiscal_year, line_id,
         obligated_to_date - apportioned_to_date,
         format_string('%s obligations of $%,.0f exceed the apportioned amount of $%,.0f by $%,.0f - potential Antideficiency Act violation. %s',
                       ppa_name, CAST(obligated_to_date AS DOUBLE), CAST(apportioned_to_date AS DOUBLE),
                       CAST(obligated_to_date - apportioned_to_date AS DOUBLE), COALESCE(apportionment_footnote, ''))
  FROM cur
  WHERE obligated_to_date > apportioned_to_date

  UNION ALL
  SELECT 'COMMITMENTS_EXCEED_AVAILABLE', 'High', line_id, office_code, ppa_code, budget_fiscal_year, line_id,
         committed_not_obligated - unobligated_balance,
         format_string('%s has $%,.0f certified on open procurement requests but only $%,.0f unobligated; funds-control review needed before more requests are certified or awarded.',
                       ppa_name, CAST(committed_not_obligated AS DOUBLE), CAST(unobligated_balance AS DOUBLE))
  FROM cur
  WHERE committed_not_obligated > unobligated_balance

  UNION ALL
  SELECT 'BURN_RATE_VARIANCE',
         CASE WHEN abs(burn_rate_vs_plan - 1) > 0.30 THEN 'High' ELSE 'Medium' END,
         line_id, office_code, ppa_code, budget_fiscal_year, line_id,
         abs(obligation_variance_to_plan),
         format_string('%s obligations are %.0f%% of the approved spend plan to date ($%,.0f obligated vs $%,.0f planned in baseline rev %d).',
                       ppa_name, 100 * CAST(burn_rate_vs_plan AS DOUBLE), CAST(obligated_to_date AS DOUBLE),
                       CAST(planned_obligations_to_date AS DOUBLE), baseline_plan_revision)
  FROM cur
  WHERE planned_obligations_to_date > 0 AND abs(burn_rate_vs_plan - 1) > 0.15

  UNION ALL
  SELECT 'STALE_SPEND_PLAN', 'Medium', line_id, office_code, ppa_code, budget_fiscal_year, line_id,
         unobligated_balance,
         format_string('%s spend plan was last revised %d days ago (rev %d on %s); balances may be mis-forecast.',
                       ppa_name, spend_plan_age_days, spend_plan_revision, CAST(spend_plan_revised_on AS STRING))
  FROM cur
  WHERE spend_plan_age_days > 120

  UNION ALL
  SELECT 'PROCUREMENT_WILL_MISS_EXPIRATION',
         CASE WHEN estimated_amount >= 1000000 THEN 'High' ELSE 'Medium' END,
         line_id, office_code, ppa_code, budget_fiscal_year, pr_id, estimated_amount,
         format_string('%s "%s" ($%,.0f, %s) is %s; forecast award %s is after the funds expire on %s.',
                       pr_id, title, CAST(estimated_amount AS DOUBLE), acquisition_type, status,
                       CAST(forecast_award_date AS STRING), CAST(expiration_date AS STRING))
  FROM gold_procurement_pipeline
  WHERE at_risk_of_missing_expiration

  UNION ALL
  SELECT 'STALLED_PROCUREMENT', 'Medium', line_id, office_code, ppa_code, budget_fiscal_year, pr_id,
         estimated_amount,
         format_string('%s "%s" has been in %s for %d days (median PALT for %s is %d days).',
                       pr_id, title, status, days_in_status, acquisition_type, median_palt_days)
  FROM gold_procurement_pipeline
  WHERE is_open AND days_in_status > greatest(60, median_palt_days) AND NOT at_risk_of_missing_expiration

  UNION ALL
  SELECT 'INVOICE_EXCEEDS_OBLIGATION', 'High', d.line_id, d.office_code, d.ppa_code, d.budget_fiscal_year,
         i.obligation_document, SUM(i.invoice_amount) - MAX(d.obligated_amount),
         format_string('Invoices against %s total $%,.0f, exceeding the $%,.0f obligated.',
                       i.obligation_document, CAST(SUM(i.invoice_amount) AS DOUBLE), CAST(MAX(d.obligated_amount) AS DOUBLE))
  FROM silver_invoices i JOIN doc_line d USING (obligation_document)
  WHERE i.status <> 'Rejected'
  GROUP BY d.line_id, d.office_code, d.ppa_code, d.budget_fiscal_year, i.obligation_document
  HAVING SUM(i.invoice_amount) > MAX(d.obligated_amount) * 1.001

  UNION ALL
  SELECT 'POTENTIAL_DUPLICATE_INVOICE', 'High', MAX(d.line_id), MAX(d.office_code), MAX(d.ppa_code),
         MAX(d.budget_fiscal_year), MAX(i.invoice_id), MAX(i.invoice_amount),
         format_string('Vendor invoice %s from %s ($%,.0f) was received %d times (%s).',
                       i.vendor_invoice_number, MAX(i.vendor_name), CAST(MAX(i.invoice_amount) AS DOUBLE),
                       COUNT(*), array_join(sort_array(collect_list(i.invoice_id)), ', '))
  FROM silver_invoices i LEFT JOIN doc_line d USING (obligation_document)
  WHERE i.status <> 'Rejected'
  GROUP BY i.vendor_uei, i.vendor_invoice_number, i.invoice_amount
  HAVING COUNT(*) > 1

  UNION ALL
  SELECT 'UNMATCHED_INVOICE', 'Medium', NULL, 'UNASSIGNED', NULL, NULL, i.invoice_id, i.invoice_amount,
         format_string('Invoice %s from %s ($%,.0f) references %s, which matches no recorded obligation.',
                       i.invoice_id, i.vendor_name, CAST(i.invoice_amount AS DOUBLE), i.contract_number)
  FROM silver_invoices i LEFT ANTI JOIN doc_line d USING (obligation_document)

  UNION ALL
  SELECT 'PROMPT_PAY_RISK',
         CASE WHEN i.prompt_pay_due_date < p.as_of THEN 'High' ELSE 'Medium' END,
         d.line_id, d.office_code, d.ppa_code, d.budget_fiscal_year, i.invoice_id, i.invoice_amount,
         format_string('Invoice %s ($%,.0f, %s) is %s and %s on %s; Prompt Payment Act interest accrues after the due date.',
                       i.invoice_id, CAST(i.invoice_amount AS DOUBLE), i.vendor_name, i.status,
                       CASE WHEN i.prompt_pay_due_date < p.as_of THEN 'was due' ELSE 'is due' END,
                       CAST(i.prompt_pay_due_date AS STRING))
  FROM silver_invoices i JOIN doc_line d USING (obligation_document) CROSS JOIN params p
  WHERE i.status IN ('Received', 'Approved') AND i.prompt_pay_due_date <= date_add(p.as_of, 7)
)
SELECT sha2(concat_ws('|', a.alert_type, a.entity_id), 256) AS alert_id, a.*, p.as_of AS detected_as_of
FROM alerts a CROSS JOIN params p;


-- ---------------------------------------------------------------------------------------
-- Funding by office and quarterly budget-performance review.
-- ---------------------------------------------------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW gold_office_execution_summary
COMMENT 'Funding and execution rolled up by program office and budget fiscal year (current and expired lines).'
AS
SELECT office_code, office_name, budget_fiscal_year, fund_status,
       COUNT(*) AS budget_lines,
       SUM(total_budget) AS total_budget,
       SUM(planned_obligations_to_date) AS planned_obligations_to_date,
       SUM(committed_not_obligated) AS committed_not_obligated,
       SUM(obligated_to_date) AS obligated_to_date,
       SUM(expended_to_date) AS expended_to_date,
       SUM(unobligated_balance) AS unobligated_balance,
       CAST(try_divide(SUM(obligated_to_date), SUM(total_budget)) AS DECIMAL(9, 4)) AS obligation_rate,
       CAST(try_divide(SUM(obligated_to_date), SUM(planned_obligations_to_date)) AS DECIMAL(9, 4)) AS burn_rate_vs_plan,
       COUNT_IF(execution_status = 'Behind Plan') AS lines_behind_plan,
       MIN(CASE WHEN fund_status = 'Current' THEN days_to_expiration END) AS nearest_expiration_days
FROM gold_budget_execution
GROUP BY ALL;


CREATE OR REFRESH MATERIALIZED VIEW gold_quarterly_review
COMMENT 'Quarterly budget-performance review for the current fiscal year: planned vs actual obligations and expenditures by office, PPA and fiscal quarter, with cumulative variance.'
AS
WITH params AS (SELECT DATE '${as_of_date}' AS as_of),
q AS (
  SELECT m.office_code, m.line_id, m.ppa_code, m.ppa_name, m.budget_fiscal_year,
         m.activity_fiscal_year, m.fiscal_quarter,
         SUM(m.planned_obligations) AS planned_obligations,
         SUM(m.actual_obligations) AS actual_obligations,
         SUM(m.planned_expenditures) AS planned_expenditures,
         SUM(m.actual_expenditures) AS actual_expenditures
  FROM gold_monthly_execution m CROSS JOIN params p
  WHERE m.activity_fiscal_year = year(p.as_of) + CASE WHEN month(p.as_of) >= 10 THEN 1 ELSE 0 END
  GROUP BY ALL
)
SELECT *,
       actual_obligations - planned_obligations AS obligation_variance,
       CAST(try_divide(actual_obligations, planned_obligations) AS DECIMAL(9, 4)) AS obligation_attainment,
       SUM(actual_obligations - planned_obligations) OVER (
         PARTITION BY line_id ORDER BY fiscal_quarter ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS cumulative_obligation_variance
FROM q;
