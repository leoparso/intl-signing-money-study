# Does international bonus money buy talent?

A preregistered study of 9,965 international amateur signings, July 2016 through August 2026, in Python.

Leonard Parsons, November 2026

## The question

Every club spends a hard-capped bonus pool, roughly $5M to $7.5M a year, on 16-year-olds who are years from the majors. I wanted to know what that money actually buys:

1. Does a bigger bonus predict a better outcome?
2. Once the bonus is known, does the player's country add anything?
3. Do players signed in the first two weeks of a period do better at the same bonus?
4. Can clubs be told apart in turning signees into big leaguers?
5. Do cheaper signees return more per dollar?

Part 2 asked what else, beyond the bonus, sorts future big leaguers: position, size, age at signing and early path through the minors.

## How I worked

1. **Built the signing universe before looking at any outcome** (`code/build_v1.py`). Every first signing with an MLB club from July 2, 2016 on, drafted players and pro signings excluded.
2. **Wrote the test plan with a pass bar for every test, then sealed it** with a SHA-256 hash before any outcome (MLB arrival, WAR, prospect grade) was joined. The plans are in `prereg/` exactly as sealed. Check them with `shasum -a 256 prereg/PREREG_v1.md prereg/PREREG_v2.md` against the `.sha256` files.
3. **Logged every change made after sealing**, with when and why, in the amendments files. Two coverage fixes in part 1 were made before any test ran. In part 2, a cohort flaw in the age test was found after the first run, fixed, and the discarded result is still reported.
4. **Ran the tests and corrected for multiple testing** (Benjamini–Hochberg at 0.10), then wrote the findings (`findings/`).
5. **Part 2 repeated the same steps** with its own sealed plan.

## Results

| Test | Question | Result | Verdict |
|---|---|---|---|
| T1 | Does bonus tier predict outcomes? | MLB within 7 seasons (2018–19 classes): AUC 0.61 (0.55–0.67). FV 50+ (2018–22 classes): AUC 0.83 (0.76–0.89) | Pass, both |
| T2 | Does country add anything once the bonus is known? | Log loss slightly worse (−0.006, CI −0.016 to +0.003) | Fail |
| T3 | Do signees from the opening two weeks do better within the same bonus tier? | MLB: OR 1.65 (1.15–2.36). FV 50+: OR 2.26 (1.18–4.33) | Pass, both |
| T4 | Do clubs differ in turning signees into big leaguers? | Permutation p = 0.36 | Fail |
| T5 | Do cheaper signees return more WAR per dollar under every money assumption? | Holds at $10K per unreported signee, not at $50K or $100K | Fail |
| Q1 | Does position at signing matter once the tier is known? | MLB p = 0.16, FV 50+ p = 0.10 | Fail |
| Q2 | Do height and weight help once the bonus is known? | Out-of-sample log loss never improves (four sub-tests) | Fail |
| Q3 | Is "in full-season ball by pro season 3" a better sorter than bonus tier? | AUC 0.84 vs 0.60, gap 0.23 (0.19–0.27) | Pass |
| Q4 | Does signing at 17+ differ from signing at 16? | OR 0.76 (0.43–1.35) | Fail |

## What it means

- **Money buys prospect status much more reliably than big leaguers.** In the 2018–19 classes, $1M+ signees reached the majors 20% of the time (11 of 56) and signees under $300K 2.2% (40 of 1,856). The cheap group still produced 74% of the big leaguers, because it is 95% of all signees.
- **Public lists miss most of the eventual big leaguers.** 82% of the big leaguers from the 2016–19 classes were never on a public ranking before they signed.
- **Early signees do better at the same bonus.** These are the players clubs followed longest, so this is an information signal. It is not evidence that waiting costs anything.
- **Country adds nothing once the bonus is known.** The Dominican Republic and Venezuela produce big leaguers in line with their share of the money. Cuban money buys fewer big leaguers, but older and quicker ones.
- **Seven classes are not enough to tell club skill from luck.** Most club totals come from one or two players.
- **The early path says far more than the bonus.** By the end of pro season 3, 92% of future big leaguers were already in full-season ball.

## What the data can't see

The answer is incomplete in ways I can name.

- Public lists record only about half of the bonus money (for 2018–19, $70M recorded against a $158.4M league pool). That is why T5 could not prove anything per dollar.
- There is no medical, makeup, academy or physical testing data.
- Outcomes take about six years, so classes from 2022 on are too young to grade.
- The samples are small: 143 big leaguers from 4,186 signees in the 2016–19 classes.
- MLB seasons before 2021 come from a name join (amendment A1), which can miss a player whose career ended before 2021.

A club's own data would close most of these gaps.

## Running it

The input data is not in this repo. It combines public transaction logs and MLB stats with third-party prospect lists that can't be redistributed. The scripts take their input and output folders as arguments, in this order:

```
python code/build_v1.py    <data_dir> <team_parents_dir> <out_dir>   # signing universe
python code/outcomes_v1.py <data_dir> <out_dir> <people_meta_dir>    # outcomes, joined after the seal
python code/analysis_v1.py <out_dir>                                 # T1 to T5, BH correction
python code/describe_v1.py <out_dir>                                 # descriptive tables
python code/make_spec_v1.py <out_dir>                                # report spec
python code/profile_v2.py  <data_dir> <out_dir> <team_parents_dir>   # part 2 player profiles
python code/analysis_v2.py <out_dir> <data_dir>                      # Q1 to Q4
python code/make_spec_v2.py <out_dir>                                # part 2 report spec
```

Requirements are in `requirements.txt`.

## What's here

| Folder | Contents |
|---|---|
| `code/` | The eight scripts above |
| `prereg/` | Both sealed test plans, their hashes and the amendments |
| `findings/` | Findings write-ups and the analysis logs |
| `results/` | Every number in the findings, as JSON |
| `report/` | The rendered report (open `report_v2.html` in a browser) |

This copy leaves out one club-specific table and my personal notes. Nothing in the tests or results changed.

## How it was built

It runs on MLB data, and I build it using coding and AI assistance (Claude). The test plans and logs were written as the work happened and are kept exactly as sealed, so they refer to me as Lenny.

The study is part of a larger evaluation system I built: https://baseballevaluationsystem.vercel.app
