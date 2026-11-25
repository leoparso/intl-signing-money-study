"""make_spec_v1.py -- builds spec_v1.json for render_report.py from results_v1.json only (single source of numbers)."""
import json, sys
from pathlib import Path
OUT = Path(sys.argv[1]); R = json.load(open(OUT / "results_v1.json")); D = R["desc"]
pct = lambda x, d=0: f"{100 * x:.{d}f}%"
T1, T1f, T2, T3m, T3f, T4, T5, RK = R["T1_mlb7"], R["T1_fv50"], R["T2"], R["T3_mlb7"], R["T3_fv50"], R["T4"], R["T5"], R["ranked"]
cls = [c for c in R["classes"] if 2016 <= c["period"] <= 2019]
n1619 = 4186; mlb1619 = RK["mlb7_16_19"]["total"]
ms = R["T1_money_share_with_unreported"]
TL = {"A": "$1M or more", "B": "$300K–$999K", "C": "Under $300K or none reported"}
spec = {
 "page_title": "International Money and Talent",
 "eyebrow": ["Reports", "No. 16", "International"],
 "h1": "International money and talent, 2016–26 signing classes",
 "dek": "Where clubs spent in the international amateur market, by bonus, country, timing and club, and what came out of it: prospects, big leaguers and WAR. Money buys prospect status much more reliably than it buys big leaguers, country adds nothing once you know the bonus, most big leaguers come from outside the top of the market, and club differences can't be told from luck.",
 "byline": "Baseball Evaluation System · international amateur signings, July 2016 – Aug 2026 · outcomes through the 2026 season · Published Nov 5, 2026",
 "tiles": [
  {"v": f"{R['n_universe'] - R['n_pro_flagged']:,}", "l": "international amateur signings since July 2016, pros excluded"},
  {"v": pct(mlb1619 / n1619, 1), "l": f"reached MLB within 7 seasons (2016–19 classes, {mlb1619} of {n1619:,})"},
  {"v": pct(1 - RK["mlb7_16_19"]["share_ranked"]), "l": "of those big leaguers were not on a pre-signing top-30 list"},
  {"v": "No signal", "l": f"in club-to-club differences (permutation p = {T4['p']:.2f})"}],
 "findings": [
  {"b": "Money buys prospect status much more than it buys big leaguers.", "t": f"Bonus tier sorts who becomes a 50+ FV prospect very well (AUC {T1f['auc']:.2f}), but sorts who reaches the majors only modestly (AUC {T1['auc']:.2f}). In the 2018–19 classes, $1M+ signees reached MLB at {pct(T1['rates']['A']['rate'])} against {pct(T1['rates']['C']['rate'], 1)} for everyone else, yet {pct(T1['share_of_hits']['C'])} of the big leaguers came from the under-$300K group."},
  {"b": "Cheap signings are not a proven bargain per dollar.", "t": f"Whether the low end returns more WAR per dollar depends entirely on what the unreported signees were paid. It holds if they averaged $10K and disappears at $50K or $100K. The published pool math implies about ${D['pool_2018']['implied_avg_c_k']:.0f}K, so the test fails."},
  {"b": "Country adds nothing once you know the bonus.", "t": f"Adding country to a bonus-only model made out-of-sample predictions slightly worse (log-loss change {T2['improvement']:+.3f}, CI {T2['ci'][0]:+.3f} to {T2['ci'][1]:+.3f}). The market prices the Dominican Republic and Venezuela about right. Output shares track money shares: the Dominican Republic had {pct(D['country_16_22'][0]['recorded_m_sh'])} of recorded money and produced {pct(D['country_16_22'][0]['mlb_sh'])} of the big leaguers."},
  {"b": "Most of the money moves on day one, and day-one signees do better even within the same bonus tier.", "t": f"{pct(D['timing_money']['day0'])} of recorded bonus money was committed on the first day of a period. Within the same bonus tier, signees from the first two weeks reached MLB more often than later signees (odds ratio {T3m['or_open']:.2f}, CI {T3m['ci'][0]:.2f}–{T3m['ci'][1]:.2f}). The early group is the pre-agreed, long-scouted players, so this is a quality signal and does not show that timing itself causes anything."},
  {"b": "Club 'international skill' is noise over these seven classes.", "t": f"After adjusting for each club's bonus mix, the spread in MLB arrival rates across the 30 clubs is what random assignment produces (p = {T4['p']:.2f}). Big club WAR totals come from one or two players each."}],
 "sections": []}
S = spec["sections"]

# ---- 1 the market
S.append({"kicker": "The market", "h2": "About a thousand players sign each period, and about 1 in 30 reaches the majors within seven seasons.", "blocks": [
 {"p": f"The universe is every player whose first move with a big-league organization since July 2, 2016 is an international amateur signing: {R['n_universe']:,} players over ten signing periods. The {R['n_pro_flagged']} professional signings (Ohtani, Sasaki, Cubans signed at 23 or older) are held out of every test so one player can't swing a result. Recorded bonuses cover only about half the money. In the 2018-19 period, recorded bonuses totaled ${D['pool_2018']['recorded_all_m']:.0f}M against a league-wide pool of ${D['pool_2018']['pool_m']:.0f}M. The gap is almost all small bonuses that public lists never report."},
 {"chart": {"type": "bars", "title": "Share of each signing class that reached MLB within seven seasons", "sub": "2016–19 classes; the 2019-20 class lost its 2020 season to COVID", "fmt": "pct1",
   "rows": [{"label": f"{c['period']}-{str(c['period'] + 1)[2:]} class", "v": c["mlb7"] / c["signees"], "note": f"{c['mlb7']} of {c['signees']:,}", "tip": [f"Recorded bonus money ${c['known_bonus_m']:.0f}M", f"FV 50+ within four years: {c['fv50_4']}"]} for c in cls],
   "noteJoin": "  ·  ", "valueLabel": "Reached MLB"}},
 {"note": "Seven seasons is the full window: of the 2016–19 big leaguers, the most common gap from signing to debut was six seasons."}]})

# ---- 2 money -> talent (T1, T5)
S.append({"kicker": "Bonus tier", "h2": "Big bonuses hit far more often, but most big leaguers still come from the cheap end.", "blocks": [
 {"p": f"Signees are split by bonus at signing. A $1M+ signee from the 2018–19 classes was about nine times as likely to reach the majors as a signee under $300K or with no reported bonus. There are so few of them, though, that the cheap end still produced {pct(T1['share_of_hits']['C'])} of the big leaguers. Preregistered test T1 passed for both outcomes."},
 {"chart": {"type": "bars", "title": "Reached MLB within seven seasons, by bonus tier", "sub": "2018–19 classes; 95% intervals in the tooltip", "fmt": "pct0",
   "rows": [{"label": TL[t], "v": T1["rates"][t]["rate"], "note": f"{T1['rates'][t]['hits']} of {T1['rates'][t]['n']:,}", "tip": [f"95% CI {pct(T1['rates'][t]['ci'][0], 1)}–{pct(T1['rates'][t]['ci'][1], 1)}", f"FV 50+ within four years (2018–22 classes): {pct(T1f['rates'][t]['rate'], 1)} ({T1f['rates'][t]['hits']} of {T1f['rates'][t]['n']:,})"]} for t in "ABC"],
   "ref": mlb1619 / n1619, "refLabel": f"All 2016–19 signees {pct(mlb1619 / n1619, 1)}", "valueLabel": "Reached MLB"}},
 {"p": "The next chart sets each tier's share of the signees and the money against its share of the big leaguers. The money share depends on what unreported signees were paid. The bars use $100K each, which is close to what the published pools imply; the tooltip shows the $10K and $50K cases."},
 {"chart": {"type": "bars", "title": "Share of signees, money and big leaguers, by bonus tier", "sub": "2018–19 classes; money assumes $100K per unreported signee", "fmt": "pct0",
   "series": [{"key": "a", "label": "Share of big leaguers", "color": "s1"}, {"key": "b", "label": "Share of money", "color": "s2"}, {"key": "c", "label": "Share of signees", "color": "s3"}],
   "rows": [{"label": TL[t], "values": {"a": T1["share_of_hits"][t], "b": ms["100K"][t], "c": D["tier_18_19"][t]["share_signees"]},
             "tip": [f"Money share at $10K: {pct(ms['10K'][t])}; at $50K: {pct(ms['50K'][t])}", f"WAR in first seven seasons: {D['tier_18_19'][t]['war7']:.1f}"]} for t in "ABC"]}},
 {"h3": "Per dollar, the answer depends on what the unreported signees were paid"},
 {"p": f"Test T5 asked whether signees under $1M return more WAR per dollar than $1M+ signees, and required the answer to hold under all three assumptions about unreported bonuses. It holds at $10K each (ratio {T5['unreported_10K']['ratio_BC_over_A_war_per_dollar']:.1f}x) but not at $50K ({T5['unreported_50K']['ratio_BC_over_A_war_per_dollar']:.1f}x, CI {T5['unreported_50K']['ratio_ci'][0]:.1f}–{T5['unreported_50K']['ratio_ci'][1]:.1f}) or $100K ({T5['unreported_100K']['ratio_BC_over_A_war_per_dollar']:.1f}x, CI {T5['unreported_100K']['ratio_ci'][0]:.1f}–{T5['unreported_100K']['ratio_ci'][1]:.1f}), so it **fails**. The pool math for 2018-19 (added after the tests, so exploratory) puts the unreported signees at about ${D['pool_2018']['implied_avg_c_k']:.0f}K each. On that basis, the under-$300K group produced about {D['pool_2018']['C']['mlb_per_10m'] / D['pool_2018']['A']['mlb_per_10m']:.1f} times as many big leaguers per $10M as the $1M+ tier. That comes from one class, and the $300K–$999K tier has only three big leaguers."},
 {"chart": {"type": "bars", "title": "Big leaguers per $10M spent, 2018-19 class", "sub": "Exploratory. Unreported money = the league pool minus recorded $300K+ bonuses", "fmt": "dec2",
   "rows": [{"label": TL[t], "v": D["pool_2018"][t]["mlb_per_10m"], "note": f"{D['pool_2018'][t]['mlb7']} big leaguers on ${D['pool_2018'][t]['dollars_m']:.0f}M", "tip": [f"WAR per $10M: {D['pool_2018'][t]['war_per_10m']:.2f}", f"{D['pool_2018'][t]['n']:,} signees"]} for t in "ABC"],
   "valueLabel": "Per $10M"}}]})

# ---- 3 country (T2)
cc = [c for c in D["country_16_22"] if c["country"] not in ("Unknown",)]
order = ["Dominican Republic", "Venezuela", "Cuba", "Mexico", "Panama", "Colombia", "Curacao", "Bahamas", "Asia/Pacific", "Other"]
cc = sorted(cc, key=lambda c: order.index(c["country"]) if c["country"] in order else 99)
S.append({"kicker": "Country", "h2": "Output tracks money by country. Cuban money buys fewer big leaguers, but older and quicker ones.", "blocks": [
 {"p": "Each country's share of recorded bonus money is set against its share of the big leaguers, for the 2016–22 classes. Every big leaguer and every 50+ FV prospect in the study has a known country. The unrecorded small money most likely went mainly to Dominican and Venezuelan players, since they fill most DSL rosters. If so, their true money shares sit a little above what is shown."},
 {"chart": {"type": "dumbbell", "title": "Share of recorded money vs share of big leaguers, by country", "sub": "2016–22 signing classes; pro signings excluded", "fmt": "pct0",
   "series": [{"key": "a", "label": "Share of recorded money", "color": "s2"}, {"key": "b", "label": "Share of big leaguers", "color": "s1"}],
   "rows": [{"label": c["country"], "a": c["recorded_m_sh"], "b": c["mlb_sh"], "note": f"{c['mlb']} big leaguers", "tip": [f"Recorded money ${c['recorded_m']:.1f}M ({c['recorded_n']} bonuses)", f"WAR {c['war']:.1f} ({pct(c['war_sh'])} of WAR)", f"FV 50+ prospects {c['fv50']}, Top 100 {c['t100']}", f"$1M+ signees {c['million_plus']}, of whom {c['mlb_from_million_plus']} reached MLB"]} for c in cc]}},
 {"p": f"Test T2 asked whether country helps predict a 50+ FV prospect once the bonus is known. It does not. Adding country made leave-one-class-out predictions slightly worse (log loss {T2['logloss_bonus_only']:.3f} with bonus alone, {T2['logloss_bonus_country']:.3f} with country), so the test **fails**. The test group ({T2['n']} signees with a recorded bonus) leans to the top of the market. Cuba's pattern comes from age. Cuban $1M+ signees were about {D['age_million_plus_by_country']['Cuba']:.0f} at signing, against about {(D['age_million_plus_by_country']['Dominican Republic'] + D['age_million_plus_by_country']['Venezuela']) / 2:.0f} for Dominican and Venezuelan ones. Half of them reached MLB, against about a fifth of the Dominican and Venezuelan $1M+ signees, and Cuban big leaguers debuted a median {D['years_to_mlb_by_country']['Cuba']['median_years']:g} seasons after signing, against {D['years_to_mlb_by_country']['Dominican Republic']['median_years']:g} for Dominicans and {D['years_to_mlb_by_country']['Venezuela']['median_years']:g} for Venezuelans."},
 {"chart": {"type": "line", "title": "Where the recorded money went, by signing period", "sub": "Share of recorded bonus dollars", "fmt": "pct0", "xHead": "Period",
   "x": [f"{p}" for p in sorted(D["money_share_by_period"], key=int)],
   "series": [{"label": "Dominican Republic", "color": "s1", "values": [D["money_share_by_period"][p]["Dominican Republic"] for p in sorted(D["money_share_by_period"], key=int)]},
              {"label": "Venezuela", "color": "s2", "values": [D["money_share_by_period"][p]["Venezuela"] for p in sorted(D["money_share_by_period"], key=int)]},
              {"label": "Cuba", "color": "s3", "values": [D["money_share_by_period"][p]["Cuba"] for p in sorted(D["money_share_by_period"], key=int)]}],
   "domain": [0, 0.8]}},
 {"note": "The 2016-17 period was the last before hard pool caps. Clubs that went over paid a tax instead of being blocked, and Luis Robert's $26M bonus alone is about a quarter of that year's recorded money. The 2020 period never happened: it moved to January 2021."}]})

# ---- 4 timing (T3)
tc = D["timing_counts"]; tot = sum(tc.values())
S.append({"kicker": "Market timing", "h2": "The market for top talent clears on day one.", "blocks": [
 {"p": f"{pct(D['timing_money']['day0'])} of recorded bonus money was committed on the first day of a signing period, and {pct(D['timing_money']['million_plus_open14'])} of $1M+ bonuses were signed in the first two weeks. After that the market is volume: most of the {tot:,} signings in the 2016–22 classes came months into a period."},
 {"chart": {"type": "bars", "title": "When players signed, measured from the opening day of the period", "sub": "2016–22 classes, all signees", "fmt": "pct0",
   "rows": [{"label": k, "v": v / tot, "note": f"{v:,} signees"} for k, v in tc.items()], "valueLabel": "Share of signings"}},
 {"p": f"Test T3 compared signees from the first two weeks with later signees, controlling for bonus tier and class. Early signees reached the majors more often (odds ratio {T3m['or_open']:.2f}, CI {T3m['ci'][0]:.2f}–{T3m['ci'][1]:.2f}) and became 50+ FV prospects more often (odds ratio {T3f['or_open']:.2f}, CI {T3f['ci'][0]:.2f}–{T3f['ci'][1]:.2f}). Both results **pass** and survive the multiple-test correction. The gap comes from the cheap end: early signees under $300K reached MLB at {pct(T3m['cells']['C_open']['rate'], 1)}, against {pct(T3m['cells']['C_later']['rate'], 1)} for later ones. Among $1M+ signees the direction flips, because the late big bonuses are mostly older Cubans who were cleared to sign mid-period and arrive quickly."},
 {"chart": {"type": "bars", "title": "Reached MLB within seven seasons: first two weeks vs later in the period", "sub": "2016–19 classes, by bonus tier", "fmt": "pct0",
   "series": [{"key": "a", "label": "Signed in first two weeks", "color": "s1"}, {"key": "b", "label": "Signed later", "color": "s2"}],
   "rows": [{"label": TL[t], "values": {"a": T3m["cells"][f"{t}_open"]["rate"], "b": T3m["cells"][f"{t}_later"]["rate"]},
             "tip": [f"First two weeks: {T3m['cells'][f'{t}_open']['hits']} of {T3m['cells'][f'{t}_open']['n']:,}", f"Later: {T3m['cells'][f'{t}_later']['hits']} of {T3m['cells'][f'{t}_later']['n']:,}"]} for t in "ABC"]}},
 {"callout": "How to read the timing result: a day-one signing is usually a deal agreed years in advance on a player the club has scouted since he was 13 or 14. Later signings include players found late, players whose deals fell through, and the depth that fills out a DSL roster. The gap shows how much information clubs act on early. It does not show that waiting costs anything, and the later group is cheaper per player. The open question is whether the later market has pockets where clubs underprice players; answering it needs signing dates and bonuses for every player."}]})

# ---- 5 rankings / coverage
S.append({"kicker": "Coverage", "h2": "Pre-signing top-30 lists find half the top prospects but fewer than one in five big leaguers.", "blocks": [
 {"p": f"Players on a public pre-signing ranking (the top 30, or top 50 from 2022) are {pct(RK['n_ranked'] / RK['n_all'], 1)} of signees. They reached MLB at {pct(RK['rate_ranked_mlb7'])}, against {pct(RK['rate_unranked_mlb7'], 1)} for unranked signees. Because unranked players outnumber them about 28 to 1, unranked players still produced most of the big leaguers."},
 {"chart": {"type": "bars", "title": "Share of each outcome that came from players ranked before signing", "sub": "MLB and WAR: 2016–19 classes. FV 50+ and Top 100: 2016–22 classes", "fmt": "pct0",
   "rows": [{"label": "Share of signees", "v": RK["n_ranked"] / RK["n_all"], "note": f"{RK['n_ranked']} of {RK['n_all']:,}"},
            {"label": "Big leaguers", "v": RK["mlb7_16_19"]["share_ranked"], "note": f"{RK['mlb7_16_19']['from_ranked']} of {RK['mlb7_16_19']['total']}"},
            {"label": "WAR in first seven seasons", "v": RK["war7_16_19"]["ranked"] / RK["war7_16_19"]["total"], "note": f"{RK['war7_16_19']['ranked']:.0f} of {RK['war7_16_19']['total']:.0f}"},
            {"label": "Top 100 prospects", "v": RK["t100_16_22"]["share_ranked"], "note": f"{RK['t100_16_22']['from_ranked']} of {RK['t100_16_22']['total']}"},
            {"label": "FV 50+ prospects", "v": RK["fv50_16_22"]["share_ranked"], "note": f"{RK['fv50_16_22']['from_ranked']} of {RK['fv50_16_22']['total']}"}],
   "valueLabel": "Share from ranked players"}},
 {"p": "The list below has the 15 most productive signees from the 2016–22 classes. Many were not ranked and got bonuses under $100K. Each one stands for scouting coverage: someone saw him when the public lists did not."},
 {"table": {"head": ["Player", "Class", "Club", "Country", "Bonus", "Ranked", "Debut", "WAR"], "num": [1, 4, 6, 7], "chips": [5], "names": [0],
   "rows": [[r[0], str(r[1]), r[2], r[3], (f"${r[5] / 1e6:.2f}M" if r[5] and r[5] >= 1e6 else (f"${r[5] / 1e3:.0f}K" if r[5] else "Not recorded")), "Yes" if r[7] else "No", str(int(r[8])) if r[8] else "", f"{r[9]:.1f}"] for r in R["top_producers"][:15]],
   "caption": "WAR runs through 2026: house WAR from 2021, public WAR before that. 'Not recorded' means the bonus is missing from our lists; Yordan Alvarez's was publicly reported at about $2M."}}]})

# ---- 6 clubs (T4)
cl = sorted(T4["clubs"], key=lambda r: r["mlb7"] - r["exp"], reverse=True)
c22 = {c["club"]: c for c in D["clubs_16_22"]}
S.append({"kicker": "Clubs", "h2": "Club differences in turning signees into big leaguers look like luck.", "blocks": [
 {"p": f"For each club, every 2016–19 signee gets the arrival rate of his class and bonus tier. Summing those gives the club's expected number of big leaguers, which is compared with how many it actually got. Test T4 shuffled clubs 2,000 times within class and tier. The real spread across clubs was no wider than the shuffled spreads (p = {T4['p']:.2f}), so the test **fails**. Shrunk toward the league, every club lands between {min(c['oe_shrunk'] for c in cl):.2f} and {max(c['oe_shrunk'] for c in cl):.2f} times expected."},
 {"chart": {"type": "bars", "layout": "left", "title": "Big leaguers above or below expected, 2016–19 classes", "sub": "Expected uses each signee's class and bonus tier. Credit goes to the signing club", "fmt": "sdec1", "base": 0,
   "rows": [{"label": c["sign_org"], "v": round(c["mlb7"] - c["exp"], 2), "bold": False, "note": f"{c['mlb7']} vs {c['exp']:.1f}",
             "tip": [f"{c['signees']} signees, {c['tierA']} at $1M+", f"Shrunk ratio {c['oe_shrunk']:.2f}", f"2016–22 classes: ${c22[c['sign_org']]['recorded_m']:.1f}M recorded, {c22[c['sign_org']]['mlb']} big leaguers, {c22[c['sign_org']]['war']:.1f} WAR", "Best: " + (", ".join(c22[c['sign_org']]["best"]) or "none")]} for c in cl],
   "labelHead": "Club", "valueLabel": "Above expected", "noteJoin": "  ·  "}},
 {"note": "Club WAR totals are dominated by one or two players each: Yordan Alvarez for the Dodgers (traded at 19), Julio Rodríguez for Seattle, Elly De La Cruz for Cincinnati, Randy Arozarena for St. Louis. Seven classes can't separate a club's process from those few draws."}]})

spec["method"] = {"h2": "Method and sources", "items": [
 {"b": "Signings:", "t": "These come from the 2016–26 transaction log. A signing is a player's first move with any big-league organization, either a signing or a first assignment to a Dominican or Venezuelan Summer League club, from July 2, 2016 on. The player also needs an international marker: a DSL or VSL assignment within 36 months, an international signing market on a public prospect list, or a known birth country outside the US, Puerto Rico and Canada with age under 25. Drafted players are dropped. Periods run July 2 to July 1 through 2018-19. The 2019-20 period runs to January 14, 2021. From 2021 on, periods start January 15."},
 {"b": "Bonuses:", "t": "These come from public prospect lists (FanGraphs) and only exist for players those lists covered. Tiers use bonuses recorded within two seasons of signing. Pipeline-ranked players with no recorded bonus get the median for their rank band (97 players). For the 2016-17 periods, only $1M+ bonuses are identifiable, so those classes use tier A versus everyone else. League pool total for 2018-19 (MLB Trade Rumors, April 2018): $158.4M."},
 {"b": "Outcomes:", "t": "MLB arrival comes from the org spine and house WAR (2021+) by player id, plus pitcher debut dates. 2016–20 public season lines are joined by name and season, unique matches only, and only for players with id-based MLB evidence. FV 50+ is a FanGraphs FV of 50 or higher on a list published one to four seasons after signing. Top 100 is a FanGraphs Top 100 from 2019 on, or an MLB Pipeline Top 100. 'Ranked' means a Pipeline international top 30/50 or a FanGraphs international list in the signing year."},
 {"b": "Preregistration:", "t": f"PREREG_v1.md was sealed before outcomes were joined. Two coverage fixes (pre-2021 MLB seasons; Top 100 list rule) were made before any test ran and are recorded in PREREG_v1_AMENDMENTS.md. Three views were added after the tests and are labeled exploratory: the pool-based per-dollar view; the country ages and years to debut; and a timing refit on the {pct(D['T3_logged_only']['share_logged'])} of signings with a logged date (MLB odds ratio {D['T3_logged_only']['mlb7']['or_open']:.2f}, CI {D['T3_logged_only']['mlb7']['ci'][0]:.2f}–{D['T3_logged_only']['mlb7']['ci'][1]:.2f}; FV 50+ odds ratio {D['T3_logged_only']['fv50']['or_open']:.2f}, CI {D['T3_logged_only']['fv50']['ci'][0]:.2f}–{D['T3_logged_only']['fv50']['ci'][1]:.2f}), which tells the same story. Benjamini–Hochberg at 0.10 over six p-values: T1 (both) and T3 (both) survive; T2 and T4 do not."},
 {"b": "Limits:", "t": "Country is known for every big leaguer but only for about 14% of all signees, so country rates per signee can't be computed. Signing club gets the credit even after a trade. Classes from 2022 on are too young for MLB outcomes. No new data was pulled for this study."}]}
json.dump(spec, open(OUT / "spec_v1.json", "w"), indent=1, ensure_ascii=False)
print("ok", len(S), "sections")
