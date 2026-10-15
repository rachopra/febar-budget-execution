"""Point-in-time features for lapse-risk forecasting.

Given (line_id, checkpoint_date) pairs, reconstruct what the budget office could have known
about each budget line on that date - obligations, the spend plan revision in force, the open
procurement pipeline - using only records timestamped on or before the checkpoint. The label
(share of budget authority left unobligated when the funds expire) is attached separately so
scoring uses exactly the same feature code as training.
"""

NUMERIC_FEATURES = [
    "days_to_expiration",
    "log_total_budget",
    "obligation_rate",
    "plan_attainment",
    "planned_remaining_share",
    "open_pipeline_share",
    "certified_pipeline_share",
    "long_palt_pipeline_share",
    "pipeline_coverage",
    "open_pr_avg_age_days",
    "cancelled_share",
    "obligated_last_60d_share",
    "spend_plan_age_days",
    "prior_year_lapse_rate",
]
CATEGORICAL_FEATURES = ["office_code", "appropriation_code", "fund_type"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
LABEL = "lapse_rate"


def feature_sql(fq: str, as_of: str, checkpoints_view: str = "checkpoints") -> str:
    """SQL producing one feature row per (line_id, checkpoint_date) in ``checkpoints_view``.

    The label is populated only for lines whose funds expired on or before ``as_of``.
    """
    return f"""
WITH lc AS (
  SELECT l.*, c.checkpoint_date
  FROM {fq}.silver_budget_lines l
  JOIN {checkpoints_view} c USING (line_id)
),
obl AS (
  SELECT lc.line_id, lc.checkpoint_date,
         SUM(CASE WHEN o.obligation_date <= lc.checkpoint_date THEN o.obligated_amount ELSE 0 END) AS obligated,
         SUM(CASE WHEN o.obligation_date <= lc.checkpoint_date
                   AND o.obligation_date > date_sub(lc.checkpoint_date, 60) THEN o.obligated_amount ELSE 0 END) AS obligated_60d
  FROM lc LEFT JOIN {fq}.silver_obligations o
    ON o.budget_fiscal_year = lc.budget_fiscal_year AND o.ppa_code = lc.ppa_code
  GROUP BY lc.line_id, lc.checkpoint_date
),
pr AS (
  SELECT pr_id, budget_fiscal_year, ppa_code,
         MAX(acquisition_type) AS acquisition_type,
         MAX(estimated_amount) AS estimated_amount,
         to_date(MIN(CASE WHEN status = 'Submitted' THEN event_ts END)) AS submitted_on,
         to_date(MIN(CASE WHEN status = 'Funds Certified' THEN event_ts END)) AS certified_on,
         to_date(MIN(CASE WHEN status = 'Awarded' THEN event_ts END)) AS awarded_on,
         to_date(MIN(CASE WHEN status = 'Cancelled' THEN event_ts END)) AS cancelled_on
  FROM {fq}.silver_pr_events
  WHERE event_type IN ('PR_STATUS_CHANGE', 'AWARD')
  GROUP BY pr_id, budget_fiscal_year, ppa_code
),
pipe AS (
  SELECT lc.line_id, lc.checkpoint_date,
         SUM(CASE WHEN is_open THEN pr.estimated_amount ELSE 0 END) AS open_pipeline,
         SUM(CASE WHEN is_open AND pr.certified_on <= lc.checkpoint_date THEN pr.estimated_amount ELSE 0 END) AS certified_pipeline,
         SUM(CASE WHEN is_open AND pr.acquisition_type IN ('New Award', 'Grant Award') THEN pr.estimated_amount ELSE 0 END) AS long_palt_pipeline,
         AVG(CASE WHEN is_open THEN datediff(lc.checkpoint_date, pr.submitted_on) END) AS open_pr_avg_age_days,
         SUM(CASE WHEN pr.cancelled_on <= lc.checkpoint_date THEN pr.estimated_amount ELSE 0 END) AS cancelled_value
  FROM lc
  LEFT JOIN (
    SELECT p.*, lc2.line_id AS _line_id, lc2.checkpoint_date AS _cp,
           p.submitted_on <= lc2.checkpoint_date
             AND (p.awarded_on IS NULL OR p.awarded_on > lc2.checkpoint_date)
             AND (p.cancelled_on IS NULL OR p.cancelled_on > lc2.checkpoint_date) AS is_open
    FROM pr p JOIN lc lc2 ON p.budget_fiscal_year = lc2.budget_fiscal_year AND p.ppa_code = lc2.ppa_code
  ) pr ON pr._line_id = lc.line_id AND pr._cp = lc.checkpoint_date
  GROUP BY lc.line_id, lc.checkpoint_date
),
rev AS (
  SELECT lc.line_id, lc.checkpoint_date, MAX(sp.revision_no) AS revision_no, MAX(sp.revision_date) AS revision_date
  FROM lc JOIN {fq}.silver_spend_plan sp
    ON sp.budget_fiscal_year = lc.budget_fiscal_year AND sp.ppa_code = lc.ppa_code
   AND sp.revision_date <= lc.checkpoint_date
  GROUP BY lc.line_id, lc.checkpoint_date
),
plan AS (
  SELECT r.line_id, r.checkpoint_date, r.revision_date,
         SUM(sp.planned_obligations) AS planned_total,
         SUM(CASE WHEN sp.plan_month <= r.checkpoint_date THEN sp.planned_obligations ELSE 0 END) AS planned_to_date
  FROM rev r
  JOIN lc ON lc.line_id = r.line_id AND lc.checkpoint_date = r.checkpoint_date
  JOIN {fq}.silver_spend_plan sp
    ON sp.budget_fiscal_year = lc.budget_fiscal_year AND sp.ppa_code = lc.ppa_code
   AND sp.revision_no = r.revision_no
  GROUP BY r.line_id, r.checkpoint_date, r.revision_date
),
final AS (
  SELECT l.budget_fiscal_year, l.ppa_code, l.expiration_date,
         1 - SUM(o.obligated_amount) / MAX(l.enacted_amount) AS final_lapse_rate
  FROM {fq}.silver_budget_lines l
  JOIN {fq}.silver_obligations o
    ON o.budget_fiscal_year = l.budget_fiscal_year AND o.ppa_code = l.ppa_code
   AND o.obligation_date <= l.expiration_date
  GROUP BY l.budget_fiscal_year, l.ppa_code, l.expiration_date
),
prior AS (
  SELECT lc.line_id, lc.checkpoint_date, MAX(f.final_lapse_rate) AS prior_year_lapse_rate
  FROM lc JOIN final f
    ON f.ppa_code = lc.ppa_code AND f.budget_fiscal_year = lc.budget_fiscal_year - 1
   AND f.expiration_date < lc.checkpoint_date
  GROUP BY lc.line_id, lc.checkpoint_date
)
SELECT
  lc.line_id, lc.checkpoint_date, lc.budget_fiscal_year, lc.ppa_code, lc.ppa_name,
  lc.office_code, lc.appropriation_code, lc.fund_type, lc.tas, lc.expiration_date,
  CAST(lc.enacted_amount AS DOUBLE) AS total_budget,
  datediff(lc.expiration_date, lc.checkpoint_date) AS days_to_expiration,
  ln(CAST(lc.enacted_amount AS DOUBLE)) AS log_total_budget,
  CAST(COALESCE(o.obligated, 0) / lc.enacted_amount AS DOUBLE) AS obligation_rate,
  CAST(COALESCE(try_divide(o.obligated, NULLIF(pl.planned_to_date, 0)), 1) AS DOUBLE) AS plan_attainment,
  CAST(COALESCE((pl.planned_total - pl.planned_to_date) / lc.enacted_amount, 0) AS DOUBLE) AS planned_remaining_share,
  CAST(COALESCE(p.open_pipeline, 0) / lc.enacted_amount AS DOUBLE) AS open_pipeline_share,
  CAST(COALESCE(p.certified_pipeline, 0) / lc.enacted_amount AS DOUBLE) AS certified_pipeline_share,
  CAST(COALESCE(p.long_palt_pipeline, 0) / lc.enacted_amount AS DOUBLE) AS long_palt_pipeline_share,
  CAST((COALESCE(o.obligated, 0) + COALESCE(p.open_pipeline, 0)) / lc.enacted_amount AS DOUBLE) AS pipeline_coverage,
  CAST(COALESCE(p.open_pr_avg_age_days, 0) AS DOUBLE) AS open_pr_avg_age_days,
  CAST(COALESCE(p.cancelled_value, 0) / lc.enacted_amount AS DOUBLE) AS cancelled_share,
  CAST(COALESCE(o.obligated_60d, 0) / lc.enacted_amount AS DOUBLE) AS obligated_last_60d_share,
  CAST(COALESCE(datediff(lc.checkpoint_date, pl.revision_date), 365) AS DOUBLE) AS spend_plan_age_days,
  CAST(COALESCE(pri.prior_year_lapse_rate, -1) AS DOUBLE) AS prior_year_lapse_rate,
  CAST(COALESCE(o.obligated, 0) AS DOUBLE) AS obligated_at_checkpoint,
  CAST(COALESCE(p.open_pipeline, 0) AS DOUBLE) AS open_pipeline_at_checkpoint,
  CAST(f.final_lapse_rate AS DOUBLE) AS {LABEL}
FROM lc
LEFT JOIN obl o USING (line_id, checkpoint_date)
LEFT JOIN pipe p USING (line_id, checkpoint_date)
LEFT JOIN plan pl USING (line_id, checkpoint_date)
LEFT JOIN prior pri USING (line_id, checkpoint_date)
LEFT JOIN final f ON f.budget_fiscal_year = lc.budget_fiscal_year AND f.ppa_code = lc.ppa_code
                 AND f.expiration_date <= DATE '{as_of}'
"""
