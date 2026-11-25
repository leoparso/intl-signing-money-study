# International spending vs talent output: preregistration v1

Written 2026-11-05, before any outcome (MLB arrival, WAR, prospect grade after signing) was joined to the signing universe. Lenny asked for this on 11/04: "Can we run a test on $ spent by MLB clubs in international (by country) and talent output since?" The outcomes he chose are prospect value and MLB arrival.

All data is local, and no new data was pulled. The sources are:

- the 2016–26 transaction log;
- FanGraphs prospect boards from 2017–26 (bonus, country, FV);
- MLB Pipeline lists from 2012–26 (international top 30/50, Top 100, club lists);
- the org spine (MLB level by season);
- house WAR for 2021–26;
- public WAR for 2019–20 seasons, joined on name and season, unique matches only.

## Universe (built in build_v1.py, already run)

The universe is every player whose first transaction with an MLB-affiliated club, from July 2, 2016 onward, is a signing, or whose first such transaction is an assignment to a DSL or VSL club. To count as international, the player also needs one of the following:

- a DSL or VSL assignment within 36 months;
- a FanGraphs signing market of J2 or Intl15;
- a known birth country outside the USA, Puerto Rico and Canada, with age under 25 at signing.

Drafted players are excluded, as are players signed at 25 or older.

The result is 9,984 players across signing periods 2016-17 through 2026. Periods run July 2 to July 1 through 2018-19. The 2019-20 period runs to January 14, 2021 because of COVID. From 2021, periods run January 15 to January 14.

Pro signings are flagged (19 players: signed at 23 or older, or Japan, Korea or Taiwan at 19 or older; Ohtani and Sasaki are in this group). Each test is reported with and without them.

## Money (what we know and don't)

- **Bonus** is the FanGraphs Sign_Bonus. "Early" means it was recorded on a list published by period + 2. Big bonuses are close to complete from the 2018 period on. Small bonuses are mostly missing, because FanGraphs records a bonus only for players it lists.
- **Tier at signing:**
  - A = $1M+;
  - B = $300K–$999K;
  - C = under $300K, or no reported bonus.
- **Imputed bonuses for ranked players:** a player ranked by Pipeline before signing who has no recorded bonus gets the median early bonus of ranked players in the same period and rank band (1–10, 11–20, 21–50). Those rows are flagged as imputed.
- **Known limitation:** the money totals cover most of the big money and little of the small money. Every "per $" figure is shown with a sensitivity in which each unreported signee is assigned $10K, $50K or $100K.

## Outcomes, with equal windows so classes compare fairly

- **MLB7:** reached MLB (org spine level MLB, or a house WAR row) by season period + 7. Periods 2016–2019.
- **WAR7:** MLB WAR in seasons period + 1 through period + 7. Periods 2016–2019. This uses house WAR for 2021+ and public WAR for 2019–20.
- **FV50_4:** FanGraphs FV 50 or higher on any prospect list published from period + 1 through period + 4. Periods 2016–2022.
- **T100:** on a FanGraphs Top 100 (Ovr_Rank ≤ 100) or the Pipeline Top 100, from period + 1 on. Reported, not tested.
- **Censoring:** the 2023–26 classes are too young for these outcomes. They are shown only for money totals.

## Tests (each has its pass bar written now)

**T1. Does money buy talent?**
- Data: periods 2018–2019 for MLB7, and periods 2018–2022 for FV50_4. These are the periods with early bonus records.
- Measure: tier order (A > B > C) as the predictor, scored by AUC.
- Pass bar: the 95% bootstrap CI of the AUC, resampling players within period, excludes 0.5.
- Also reported:
  - the hit rates by tier;
  - the share of all MLB7 players who came from each tier, against that tier's share of the known money.

**T2. Does country add anything once you know the bonus?**
- Data: signees with an early or imputed bonus and a known country, periods 2018–2022, outcome FV50_4.
- Models: logistic regression on log bonus, against log bonus plus country (Dominican Republic as the base, then Venezuela, then all others pooled).
- Validation: leave-one-period-out log loss.
- Pass bar: the paired bootstrap 95% CI of the log-loss improvement excludes 0. This cohort is selected (known bonus), and that caveat is printed with the result.

**T3. Market timing.**
- Comparison: signing within the first 14 days of a period (the opening window) against later in the period.
- Data: all signees.
- Model: a logistic regression of the outcome on opening window plus tier dummies plus period dummies.
- Outcomes: FV50_4 (periods 2016–2022) and MLB7 (periods 2016–2019).
- Pass bar: the 95% CI of the odds ratio for the opening window excludes 1. This test is two-sided; no direction is assumed.

**T4. Do clubs differ in turning signees into big leaguers?**
- Outcome: MLB7, periods 2016–2019, all signees.
- Club effect: observed minus expected, where expected comes from each signee's tier × period base rate.
- Test statistic: the between-club variance of (O − E) / √E.
- Permutation: 2,000 shuffles of club labels within period × tier.
- Pass bar: p < 0.05. If it passes, clubs are shown with shrinkage (empirical Bayes). If it fails, club rankings are labeled noise.

**T5. Value per dollar by tier (descriptive, with a check).**
- Measure: WAR7 per $1M and MLB7 players per $1M for tier A against tiers B and C.
- Data: periods 2016–2019.
- Uncertainty: bootstrap CIs.
- Check: the conclusion "lower tiers return more per dollar" stands only if it holds under all three unreported-bonus assumptions ($10K, $50K, $100K).

## Descriptive (no pass bars)

- Money and output by country:
  - known bonus dollars;
  - signees with known bonus;
  - MLB7 players, WAR7, FV50_4 and T100;
  - share of money against share of output.
- Money and output by club.
- Pipeline-ranked against unranked signees: the share of MLB7 and FV50_4 coming from outside the pre-signing top 30/50.
- Years from signing to MLB.

## Multiple testing

Benjamini–Hochberg at 0.10 across T1–T4 (six p-values: T1 has two outcomes, T3 has two outcomes).
