# Grounding check pass rate for all AI outputs

Executed 2026-11-02 18:12 UTC

```sql
SELECT 'execution briefings' AS output, COUNT(*) AS generated, COUNT_IF(grounding_passed) AS grounded,
       ROUND(100 * COUNT_IF(grounding_passed) / COUNT(*), 1) AS pass_pct FROM rachopra_catalog.fe_bar.gold_execution_briefings
UNION ALL
SELECT 'quarterly review narratives', COUNT(*), COUNT_IF(grounding_passed), ROUND(100 * COUNT_IF(grounding_passed) / COUNT(*), 1)
FROM rachopra_catalog.fe_bar.gold_quarterly_review_briefings
UNION ALL
SELECT 'procurement package drafts', COUNT(*), COUNT_IF(size(validation_issues) = 0),
       ROUND(100 * COUNT_IF(size(validation_issues) = 0) / COUNT(*), 1) FROM rachopra_catalog.fe_bar.gold_procurement_package_drafts
```

**Result:**

| output | generated | grounded | pass_pct |
|---|---|---|---|
| execution briefings | 29 | 27 | 93.1 |
| quarterly review narratives | 6 | 2 | 33.3 |
| procurement package drafts | 26 | 26 | 100.0 |
