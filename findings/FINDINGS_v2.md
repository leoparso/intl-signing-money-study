# International study, part 2: who becomes a big leaguer (Nov 5, 2026)

The question (Nov 5, 2026): which player types and sizes reach the majors, and what else gives a broad picture of future major leaguers from international signings?

The preregistration (PREREG_v2.md, sha256 a3262f6a…) was sealed before any split by position, size, age or early path. One cohort flaw, in the age test, was found and fixed. It is recorded in PREREG_v2_AMENDMENTS.md. All numbers come from results_v2.json, and the report is report_v2.html (part 1 plus part 2). Unless noted, the data is the 2016–19 classes: 4,186 signees, of whom 143 reached MLB within seven seasons.

## Test results

| Test | Question | Result | Verdict |
|---|---|---|---|
| Q1 | Does position at signing matter once the bonus tier is known? | MLB: p = 0.16. FV 50+: p = 0.10. | Fail |
| Q2 | Do height and weight help once the bonus is known? Four sub-tests (pitchers/hitters × FV 50+/MLB). | Out-of-sample log loss never improves. | Fail, all four |
| Q3 | Is "in full-season ball by pro season 3" a better sorter than bonus tier? | AUC 0.84 vs 0.60. Gap 0.23 (CI 0.19–0.27). | Pass, survives correction |
| Q4 | Does signing at 17+ differ from signing at 16? (Listed players, after tier.) | OR 0.76 (CI 0.43–1.35). | Fail |

## The picture

**Player types**

| Signed as | Share of signees | Share of big leaguers | MLB rate |
|---|---|---|---|
| Shortstop | 13% | 23% | 6.1% |
| Catcher | 10% | 6% | 2.0% |
| Left-handed pitcher | 10% | 6% | 2.0% |
| Right-handed pitcher | 43% | 43% | 3.5% |
| Outfield | 17% | 16% | 3.4% |

- Most of the shortstop edge goes away once you account for bonus tier, because shortstops get the money.
- Catchers become 50+ FV prospects at a higher rate once the bonus is known (OR about 3.6 against right-handed pitchers), but reach MLB at only 2%. That contrast is not proven, but it is worth watching.
- Hitters were 47% of signees and produced 71% of the WAR in the first seven seasons (101 vs 42).
- Only 14 of the 42 signed shortstops who reached MLB (2016–22 classes) played mostly shortstop there. 16 of the 19 catchers stayed at catcher.

**Size at signing**

- Size is known only for players listed within two seasons of signing: 7.4% of signees, but 52% of the eventual big leaguers.
- Big leaguers measured the same as other listed signees:
  - pitchers: median 6'2", 175 lb;
  - hitters: median 6'0", 170 lb.
- Exploratory, small samples: tall hitters (6'3"+) became 50+ FV prospects at 27%, against 7% for hitters 5'10" or shorter. But they reached MLB at 17%, against 30%. The grades reward projection more than outcomes do.

**Age**

- Age at signing does not separate the groups (Q4).
- Big leaguers debuted at a median age of 22.5, mostly between 21 and 24.

**The first three years (the strongest result)**

| Checkpoint | Share of signees | Share of big leaguers |
|---|---|---|
| Still with a club after pro season 2 | 75% | 99% |
| Out of the DSL by pro season 2 | 45% | 97% |
| In full-season ball by pro season 3 | 27% | 92% |

- Cheap signees (under $300K) who were not in full-season ball by year 3: 11 of 3,032 reached MLB (0.4%).
- Cheap signees who were in full-season ball by year 3: 9.9% reached MLB.
- Exceptions: 11 of the 143 were not in full-season ball by year 3 (Maikel Garcia and Yainer Díaz are the best of them), and 3 were released before they debuted.

**Trades**

- 48 of the 143 (34%) were traded before their MLB debut.

## Limits

- Size, age and bats are known only for listed players.
- Position at signing comes from the transaction text, which has oddities. Kirk, for example, is logged as an RHP.
- Levels come from assignment moves. Classes from 2022 on are too young for MLB outcomes.
