# International money vs talent output: findings v1 (Nov 5, 2026)

The question (Nov 4, 2026): does the money MLB clubs spend on international amateurs, by country, buy talent output? This study uses local data only and makes no new pulls. The preregistration (PREREG_v1.md, sha256 8a7e95f0…) was sealed before any outcome was joined. Two coverage fixes are recorded in PREREG_v1_AMENDMENTS.md; both were made before any test ran. Every number below comes from results_v1.json.

## The universe

The study covers 9,984 international amateur signings from July 2016 to August 2026. That is 9,965 once the 19 pro signings are excluded (Ohtani, Sasaki, and Cubans signed at 23 or older).

Recorded bonuses cover only about half the money. For the 2018-19 period, recorded bonuses total $70M against a league pool of $158.4M. Almost all of the gap is small bonuses that public lists never report. That gap is the main limit on any per-dollar claim.

Of the 2016–19 classes, 3.4% reached MLB within seven seasons (143 of 4,186). The most common gap from signing to debut was six seasons.

## Test results

| Test | Question | Result | Verdict |
|---|---|---|---|
| T1 | Does bonus tier predict outcomes? | MLB within 7 seasons, 2018–19 classes: AUC 0.61 (0.55–0.67). FV 50+, 2018–22 classes: AUC 0.83 (0.76–0.89). | Pass, both |
| T2 | Does country add anything once the bonus is known? | Log loss got slightly worse (−0.006, CI −0.016 to +0.003). | Fail |
| T3 | Do signees from the opening two weeks do better, within the same bonus tier? | MLB: OR 1.65 (1.15–2.36). FV 50+: OR 2.26 (1.18–4.33). Holds on logged signing dates only (OR 1.54 and 2.15). | Pass, both |
| T4 | Do clubs differ in turning signees into big leaguers? | Permutation p = 0.36. Shrunk club ratios run 0.96–1.04. | Fail |
| T5 | Do cheaper signees return more WAR per dollar under every money assumption? | Holds at $10K per unreported signee (7.2x). Not at $50K (2.1x, CI 0.8–11.2) or $100K (1.1x, CI 0.4–4.9). | Fail |

Benjamini–Hochberg at 0.10: both T1 results and both T3 results survive; T2 and T4 do not.

## What it means

**1. Money buys prospect status more reliably than it buys big leaguers.**

In the 2018–19 classes:

- $1M+ signees reached MLB at 20% (11 of 56).
- $300K–$999K signees reached MLB at 7% (3 of 43).
- Signees under $300K or with no reported bonus reached MLB at 2.2% (40 of 1,856).

Even so, 74% of the big leaguers came from that last group, because it is 95% of all signees.

**2. Per dollar, nothing is proven.**

Whether the cheap end is a better value depends on what unreported signees were paid. The 2018-19 pool math implies about $94K each. This view is exploratory, added after the tests: on that basis, the under-$300K group produced about 1.7 times as many big leaguers per $10M as the $1M+ tier, from one class.

**3. Country is priced correctly.**

Output share tracks money share by country (2016–22 classes):

| Country | Share of recorded money | Share of big leaguers |
|---|---|---|
| Dominican Republic | 43% | 49% |
| Venezuela | 25% | 27% |
| Cuba | 26% | 11% |
| Mexico | 1.4% | 4.7% |

Cuba's money buys fewer big leaguers, but each one is older and quicker:

- Cuban $1M+ signees were about 19 at signing, against about 17 elsewhere.
- Half of Cuban $1M+ signees reached MLB, against about a fifth of Dominican and Venezuelan ones.
- Cuban big leaguers debuted a median 5 seasons after signing, against 6–6.5 for Dominicans and Venezuelans.

**4. The top of the market clears on day one.**

- 68% of recorded money was committed on the first day of a period.
- 83% of $1M+ bonuses were signed in the first two weeks.
- Most signings by count came months later.

Within a tier, early signees under $300K reached MLB at 3.9%, against 1.9% for later ones. The early group is the pre-agreed, long-scouted players, so this is an information signal. It is not evidence that waiting costs anything.

**5. Coverage matters more than lists.**

Players ranked before signing (Pipeline top 30/50 or the FanGraphs international list) are 3.5% of signees. Their share of each outcome:

- 18% of big leaguers (2016–19 classes);
- 35% of WAR in the first seven seasons;
- 44% of Top 100 prospects;
- 52% of FV 50+ prospects.

82% of big leaguers came from players nobody ranked publicly. Examples:

- Elly De La Cruz, $65K;
- Alejandro Kirk, $30K;
- Geraldo Perdomo, $70K;
- Junior Caminero, $225K;
- Gabriel Moreno, $25K;
- Brayan Bello, $28K.

**6. Club skill can't be told from luck over seven classes.**

Club WAR totals each come from one or two players: Yordan Alvarez for the Dodgers, Julio Rodríguez for Seattle, Elly De La Cruz for Cincinnati, Arozarena for St. Louis.

## Limits

- Country is known for every big leaguer but for only about 14% of signees overall, so per-signee rates by country can't be computed.
- Credit goes to the signing club, even after a trade.
- Classes from 2022 on are too young for MLB outcomes.
- 2016–17 bonuses are thin in the data, so those classes only separate $1M+ from everyone else. Yordan Alvarez's roughly $2M bonus, for example, is not recorded.
- Pre-2021 MLB seasons come from a name join, and only for players with id-based MLB evidence.

## Files

- Code (intl_code): build_v1.py, outcomes_v1.py, analysis_v1.py, describe_v1.py, make_spec_v1.py
- Data: universe_v1.parquet, players_v1.parquet
- Results: results_v1.json
- Report: spec_v1.json, report_v1.html
- Preregistration: PREREG_v1.md, PREREG_v1.sha256, PREREG_v1_AMENDMENTS.md
