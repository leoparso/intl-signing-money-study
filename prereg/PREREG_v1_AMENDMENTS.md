# Amendments to PREREG_v1 (sealed hash 8a7e95f0…)

Both amendments were made while checking the outcome join for coverage, before any test in T1–T5 was run. The only outcome numbers seen at that point were each class's totals (counts of MLB arrivals, FV50, Top 100, WAR7), not any split by tier, country, timing or club.

## A1. MLB seasons before 2021

**Problem.** The org spine leaves the level blank for 2016–20, and house WAR starts in 2021. Because of that, a debut in 2019 or 2020 was being dated to the player's first 2021+ season, and 2016–20 WAR was missing.

**Fix.** For players who have id-based MLB evidence (a 2021+ MLB season, or a pitcher debut date in people_meta), add their 2016–20 public season lines. The join is on normalized name and season. A match counts only when both of these hold:

- the name is unique among the signees;
- the name, season and side row is unique in the public table.

In practice:

- WAR7 now uses public WAR for 2016–20 seasons (the prereg said 2019–20).
- First MLB season is the earliest of those sources.

**Known gap.** A player whose whole MLB career ended before 2021 and who has no pitcher debut record is still missed. Such players are rare in these classes, which were signed in 2016 or later, mostly at age 16.

## A2. FanGraphs Top 100

On the 2017 and 2018 FanGraphs lists, Ovr_Rank is filled for every row (674–989 rows, with a maximum of about 100), so it is not an overall rank there.

The FanGraphs Top 100 therefore uses only lists where 160 rows or fewer carry Ovr_Rank (2019 onward). Pipeline Top 100 covers every year. The problem showed up when the Top 100 count for the 2016 class (94) exceeded its FV50 count (15).
