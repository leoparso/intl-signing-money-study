"""describe_v1.py -- aligned descriptive tables for the report (no tests). Adds keys to results_v1.json under "desc".
Post-hoc additions (labeled in the report): pool-based estimate of unreported money for the 2018-19 period, using the published
league pool total ($158,389,900, MLBTR 2018-04) -- pool minus recorded tier A/B bonuses, spread over the remaining signees."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
OUT = Path(sys.argv[1]); R = json.load(open(OUT / "results_v1.json"))
P = pd.read_parquet(OUT / "players_v1.parquet"); U = P[~P.pro].copy(); U["country"] = U.country.fillna("Unknown")
D = {}
def grp(c):
    return c if c in ("Dominican Republic", "Venezuela", "Cuba", "Mexico", "Colombia", "Panama", "Curacao", "Bahamas") else ("Asia/Pacific" if c in ("Japan", "South Korea", "Taiwan", "Australia", "China", "Philippines", "Hong Kong") else ("Unknown" if c == "Unknown" else "Other"))
U["cg"] = U.country.map(grp)
w = U[U.period.between(2016, 2022)]
rows = []
for c, h in w.groupby("cg"):
    rows.append(dict(country=c, recorded_n=int(h.bonus_any.notna().sum()), recorded_m=float(h.bonus_any.sum()) / 1e6, mlb=int(h.mlb_any.sum()),
                     mlb_16_19=int(h[h.period <= 2019].mlb_any.sum()), war=float(h.war_all.sum()), fv50=int(h.fv50_any.sum()), t100=int(h.t100.sum()),
                     million_plus=int((h.bonus_any >= 1e6).sum()), mlb_from_million_plus=int(h[h.bonus_any >= 1e6].mlb_any.sum())))
c = pd.DataFrame(rows); k = c[c.country != "Unknown"]
for col in ["recorded_m", "mlb", "war", "fv50", "t100"]: c[col + "_sh"] = c[col] / k[col].sum()
D["country_16_22"] = c.sort_values("recorded_m", ascending=False).round(4).to_dict("records")
# recorded money share by period for the three big markets
tr = {}
for p, h in U.groupby("period"):
    tot = h.bonus_any.sum(); tr[int(p)] = {g: round(float(h[h.cg == g].bonus_any.sum() / tot), 3) for g in ["Dominican Republic", "Venezuela", "Cuba"]}
    tr[int(p)]["Other"] = round(1 - sum(tr[int(p)].values()), 3); tr[int(p)]["recorded_m"] = round(float(tot) / 1e6, 1)
D["money_share_by_period"] = tr
# 2018-19 period: pool-based estimate
POOL_2018 = 158_389_900
h = U[U.period == 2018]
ab = h[h.tier.isin(["A", "B"])].bonus_sign.sum(); cn = int((h.tier == "C").sum())
c_known = h[(h.tier == "C") & h.bonus_sign.notna()].bonus_sign.sum()
avg = (POOL_2018 - ab) / cn
D["pool_2018"] = dict(pool_m=POOL_2018 / 1e6, recorded_ab_m=round(float(ab) / 1e6, 1), recorded_all_m=round(float(h.bonus_any.sum()) / 1e6, 1),
                      c_signees=cn, implied_avg_c_k=round(float(avg) / 1e3, 1),
                      note="Pool minus recorded tier A/B money, spread over tier C. Upper-ish bound: clubs can trade pool space and $10K-or-less signings sit outside the pool.")
for t in "ABC":
    g = h[h.tier == t]; dollars = g.bonus_sign.sum() if t != "C" else POOL_2018 - ab
    D["pool_2018"][t] = dict(n=int(len(g)), dollars_m=round(float(dollars) / 1e6, 1), mlb7=int(g.mlb7.sum()), war7=round(float(g.war7.sum()), 1),
                             mlb_per_10m=round(float(g.mlb7.sum() / (dollars / 1e7)), 2), war_per_10m=round(float(g.war7.sum() / (dollars / 1e7)), 2))
# tier view across 2018-19 with realistic money
h2 = U[U.period.isin([2018, 2019])]
D["tier_18_19"] = {t: dict(n=int((h2.tier == t).sum()), share_signees=round(float((h2.tier == t).mean()), 3), mlb7=int(h2[h2.tier == t].mlb7.sum()),
                           war7=round(float(h2[h2.tier == t].war7.sum()), 1), fv50=int(h2[h2.tier == t].fv50_4.sum())) for t in "ABC"}
# timing: money committed in opening window
k2 = U[U.period.between(2016, 2022) & U.bonus_any.notna()]
D["timing_money"] = dict(open14=round(float(k2[k2.opening_window].bonus_any.sum() / k2.bonus_any.sum()), 3),
                         day0=round(float(k2[k2.days_into_period <= 0].bonus_any.sum() / k2.bonus_any.sum()), 3),
                         million_plus_open14=round(float(k2[(k2.bonus_any >= 1e6)].opening_window.mean()), 3))
x = U[U.period.between(2016, 2022)]
D["timing_counts"] = {lab: int(v) for lab, v in pd.cut(x.days_into_period, [-1, 0, 14, 60, 180, 400, 800], labels=["Day 1", "Days 2-15", "Weeks 3-8", "Months 3-6", "Months 7-13", "Later"]).value_counts().sort_index().items()}
# club table
cl = []
for o_, g in U[U.period.between(2016, 2022)].groupby("sign_org"):
    g19 = g[g.period <= 2019]
    cl.append(dict(club=o_, signees=int(len(g)), recorded_m=round(float(g.bonus_any.sum()) / 1e6, 1), million_plus=int((g.bonus_any >= 1e6).sum()),
                   mlb=int(g.mlb_any.sum()), war=round(float(g.war_all.sum()), 1), fv50=int(g.fv50_any.sum()), t100=int(g.t100.sum()),
                   mlb7_16_19=int(g19.mlb7.sum()),
                   best=[f"{r.name} {r.war_all:.1f}" for r in g.sort_values("war_all", ascending=False).head(2).itertuples() if r.war_all > 0]))
D["clubs_16_22"] = sorted(cl, key=lambda r: -r["war"])
# exploratory: years from signing to debut by country group (big leaguers, 2016-19 classes) and age at signing for $1M+ signees
a = U[U.mlb_any & U.period.between(2016, 2019)].copy(); a["yrs"] = a.first_mlb - a.period
D["years_to_mlb_by_country"] = {g: dict(n=int(len(h)), median_years=float(h.yrs.median())) for g, h in a.groupby(a.country.where(a.country.isin(["Dominican Republic", "Venezuela", "Cuba"]), "Other"))}
m = U[U.period.between(2016, 2022) & (U.bonus_any >= 1e6)]
D["age_million_plus_by_country"] = {g: round(float(h.age_sign.median()), 1) for g, h in m.groupby(m.country.where(m.country.isin(["Dominican Republic", "Venezuela", "Cuba"]), "Other"))}
# exploratory: T3 refit on logged signings only (signing date known exactly)
import statsmodels.api as sm
def t3(df, y):
    X = pd.get_dummies(df[["tier", "period"]].astype(str), drop_first=True).astype(float); X["open"] = df.opening_window.astype(float); X = sm.add_constant(X)
    mm = sm.Logit(df[y].astype(float), X).fit(disp=0); b, se = mm.params["open"], mm.bse["open"]
    return dict(n=int(len(df)), or_open=round(float(np.exp(b)), 2), ci=[round(float(np.exp(b - 1.96 * se)), 2), round(float(np.exp(b + 1.96 * se)), 2)], p=round(float(mm.pvalues["open"]), 4))
L = U[U.sign_logged]
D["T3_logged_only"] = dict(share_logged=round(float(U.sign_logged.mean()), 3), mlb7=t3(L[L.period.between(2016, 2019)].reset_index(drop=True), "mlb7"),
                           fv50=t3(L[L.period.between(2016, 2022)].reset_index(drop=True), "fv50_4"))
R["desc"] = D
json.dump(R, open(OUT / "results_v1.json", "w"), indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x))
print(json.dumps(D, indent=1, default=str)[:9000])
