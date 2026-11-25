# International study, part 2: who becomes a big leaguer. Preregistration v2

**Written:** 2026-11-05, before any split of outcomes by position, size, age, handedness or early path was computed.

**Request (Lenny, 11/05):** "player types and sizes that reach … Any other things you can think of to give us a broad picture of future major leaguers from international signings."

**Data and definitions carried over from part 1:**
- Same universe and outcomes as part 1 (players_v1.parquet), with pro signings excluded.
- MLB7 means reached MLB within 7 seasons; it covers classes 2016–19.
- FV50_4 means FV 50+ within 4 list seasons; it covers classes 2016–22.
- Tiers: A is $1M+; B is $300K–$999K; C is under $300K or not reported.

**What has already been seen:** part 1 outcomes by tier, country, signing timing and club.

## New fields (built in profile_v2.py)

**Position at signing**
- Taken from the signing transaction text, or the first assignment text when the signing isn't logged.
- Groups: C; SS; other infield (2B, 3B, 1B, IF); OF; RHP; LHP; P (unspecified, pooled with RHP).

**Size near signing**
- Height and weight from the earliest public list row published within two seasons of signing (FanGraphs Height/Weight, else Pipeline height/weight).
- Zeros are treated as missing.
- Known only for players who were listed, so every size result is reported with its coverage.

**Age at signing and birth month**
- Taken from the date of birth, where known (listed players and MLB pitchers).

**Bats and throws**
- From the lists, where known.
- Pitcher throwing hand is known for everyone from the signing text.

**Early path, by pro season** (seasons after signing, skipping 2020)
- Levels:
  - Each move to a team is mapped to its level through team_parent (season, team).
  - "Full-season" means Low-A or higher (sport id 14, 13, 12, 11, or 1).
  - "US" means any non-DSL/VSL team.
  - The 2021+ org-spine levels add to this.
- Flags:
  - out_of_dsl_s1, out_of_dsl_s2: played or was assigned outside the DSL/VSL by the end of pro season 1 or 2.
  - fullseason_s3: at a full-season level by the end of pro season 3.
  - released_s3: released by the end of pro season 3.

**Trades and position changes**
- Traded before MLB debut: a trade transaction before his first MLB season.
- Position change: for big leaguers, signed as a pitcher but played MLB as a hitter, or the reverse (house WAR side); and signed as SS but MLB innings mostly elsewhere (house WAR pos).

## Tests (pass bars written now)

**Q1. Position at signing**
- Question: does the MLB7 rate differ by position group once bonus tier and class are known?
- Model: logistic regression of MLB7 on tier and period dummies, plus position-group dummies.
- Pass bar: likelihood-ratio p < 0.05.
- Also reported: MLB7 and FV50_4 rates by group, with Wilson intervals.

**Q2. Size**
- Cohort: signees with a size near signing.
- Outcomes: FV50_4 (classes 2016–22) and MLB7 (classes 2016–19), run separately for pitchers and hitters.
- Models: log bonus (tier imputed as in part 1, with unreported bonuses set to $50K) against log bonus + height + weight.
- Scoring: leave-one-class-out log loss.
- Pass bar: the paired bootstrap 95% CI of the improvement excludes 0.
- Four sub-tests. Caveat: this cohort is listed players only.

**Q3. How early can you tell?**
- Outcome: MLB7, classes 2016–19.
- Measure: AUC of fullseason_s3, set against the AUC of bonus tier.
- Pass bar: fullseason_s3 AUC exceeds tier AUC, with a paired bootstrap CI that excludes 0.
- Also reported: MLB7 rates for every path flag (s1, s2, s3, released).

**Q4. Age at signing**
- Cohort: signees with a known date of birth.
- Question: is signing at 17+ different from signing at 16, controlling for tier and class? Model: logistic regression on MLB7.
- Pass bar: the odds-ratio CI excludes 1.
- Caveat: age is known mostly for listed players.

**Multiple testing:** Benjamini–Hochberg at 0.10 across Q1, Q2 (four sub-tests), Q3 and Q4.

## Descriptive only (no pass bars)

**Profile of the 2016–19 big leaguers set against all signees in those classes:**
- position;
- pitcher vs hitter;
- throwing hand;
- height and weight;
- age at signing;
- birth month;
- bonus;
- days into period.

**Funnel:**
- signed;
- still in org after pro season 2;
- out of the DSL by pro season 2;
- full-season by pro season 3;
- MLB.

**Other:**
- Trades before debut.
- Position changes.
- Debut age.
- Share of big leaguers and WAR from pitchers vs hitters.
