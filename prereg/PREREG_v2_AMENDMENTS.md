# Amendments to PREREG_v2 (sealed a3262f6a…)

## v2-A1. Q4 age cohort. This change was made after Q4 was first run.

**The flaw.** Date of birth comes from several sources, and one of them (MLB pitcher records) exists only for players who reached MLB. As first run, birth dates were known for 100% of big leaguers but only 12% of everyone else. The Q4 cohort was therefore selected on the outcome.

**The fix.** Q4 now uses only signees who were on a public list within two seasons of signing (early_listed). That is the same kind of cohort as the size test. The first run was also null (OR 0.99) and is discarded because the cohort was biased.

Birth-month comparisons were dropped from the descriptives for the same reason.

## v2-A2. Position at signing comes from the transaction text as written

The transaction log has some oddities. For example, Alejandro Kirk is logged as an RHP at signing, although he signed as a catcher. These were left as logged, because changing them by hand would mean correcting only the players we know about.
