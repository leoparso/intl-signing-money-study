"""analysis_v1.py -- tests T1-T5 and descriptives per PREREG_v1.md (+ AMENDMENTS). Reads players_v1.parquet, writes results_v1.json."""
import json, sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm
from sklearn.metrics import roc_auc_score
warnings.filterwarnings("ignore")
OUT = Path(sys.argv[1]); rng = np.random.default_rng(20261105)
P = pd.read_parquet(OUT / "players_v1.parquet")
R = {"n_universe": int(len(P)), "n_pro_flagged": int(P.pro.sum())}
U = P[~P.pro].copy()                     # main analysis excludes pro signings (Ohtani, Sasaki, older Cubans)
def wilson(k, n, z=1.96):
    if n == 0: return [None, None]
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 4), round(c + h, 4)]
def bh(ps):
    ps = np.asarray(ps, float); n = len(ps); o = np.argsort(ps); q = np.empty(n); prev = 1.0
    for i in range(n - 1, -1, -1):
        prev = min(prev, ps[o[i]] * n / (i + 1)); q[o[i]] = prev
    return q
def strat_boot(df, fn, n=2000, by="period"):
    groups = [g.index.values for _, g in df.groupby(by)]; out = []
    for _ in range(n):
        idx = np.concatenate([rng.choice(g, len(g), replace=True) for g in groups])
        try: out.append(fn(df.loc[idx]))
        except Exception: pass
    return np.array(out)
TORD = {"A": 2, "B": 1, "C": 0}
U["tord"] = U.tier.map(TORD)

# ===================== class overview
ov = []
for p, g in P.groupby("period"):
    ov.append(dict(period=int(p), signees=int(len(g)), known_bonus_n=int(g.bonus_any.notna().sum()), known_bonus_m=round(float(g.bonus_any.sum()) / 1e6, 1),
                   mlb7=int(g.mlb7.sum()), mlb_any=int(g.mlb_any.sum()), fv50_4=int(g.fv50_4.sum()), t100=int(g.t100.sum()), war_all=round(float(g.war_all.sum()), 1)))
R["classes"] = ov

# ===================== T1 money -> talent (tier order AUC)
def t1(df, y):
    a = roc_auc_score(df[y], df.tord)
    bs = strat_boot(df, lambda d: roc_auc_score(d[y], d.tord))
    k1 = df[df[y]].tord; k0 = df[~df[y]].tord
    p = stats.mannwhitneyu(k1, k0, alternative="greater").pvalue
    rates = {t: dict(n=int((df.tier == t).sum()), hits=int(df[df.tier == t][y].sum()), rate=round(float(df[df.tier == t][y].mean()), 4),
                     ci=wilson(int(df[df.tier == t][y].sum()), int((df.tier == t).sum()))) for t in "ABC"}
    share = {t: round(float(df[df.tier == t][y].sum() / max(df[y].sum(), 1)), 3) for t in "ABC"}
    return dict(auc=round(a, 3), ci=[round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)], p=float(p),
                n=int(len(df)), hits=int(df[y].sum()), rates=rates, share_of_hits=share, passed=bool(np.percentile(bs, 2.5) > 0.5))
d18 = U[U.period.isin([2018, 2019])]; d18f = U[U.period.isin([2018, 2019, 2021, 2022])]
R["T1_mlb7"] = t1(d18.reset_index(drop=True), "mlb7")
R["T1_fv50"] = t1(d18f.reset_index(drop=True), "fv50_4")
# money share by tier (known + imputed), same periods
def money_share(df):
    m = df.groupby("tier").bonus_sign.sum(); tot = m.sum()
    return {t: round(float(m.get(t, 0) / tot), 3) for t in "ABC"}
R["T1_money_share_known"] = money_share(d18)
for v in (10e3, 50e3, 100e3):
    dd = d18.copy(); dd.loc[dd.bonus_src == "unreported", "bonus_sign"] = v
    R.setdefault("T1_money_share_with_unreported", {})[f"{int(v/1e3)}K"] = money_share(dd)

# ===================== T2 country beyond bonus
c2 = U[U.period.isin([2018, 2019, 2021, 2022]) & U.bonus_src.isin(["early", "imputed_rank"]) & U.country.notna() & (U.country != "Unknown")].copy()
c2["lb"] = np.log(c2.bonus_sign); c2["VEN"] = (c2.country == "Venezuela").astype(float)
c2["OTH"] = (~c2.country.isin(["Dominican Republic", "Venezuela"])).astype(float); c2["y"] = c2.fv50_4.astype(float)
loss0, loss1 = np.zeros(len(c2)), np.zeros(len(c2)); c2 = c2.reset_index(drop=True)
for p in c2.period.unique():
    tr, te = c2[c2.period != p], c2[c2.period == p]
    m0 = sm.Logit(tr.y, sm.add_constant(tr[["lb"]])).fit(disp=0)
    m1 = sm.Logit(tr.y, sm.add_constant(tr[["lb", "VEN", "OTH"]])).fit(disp=0)
    p0 = np.clip(m0.predict(sm.add_constant(te[["lb"]], has_constant="add")), 1e-6, 1 - 1e-6)
    p1 = np.clip(m1.predict(sm.add_constant(te[["lb", "VEN", "OTH"]], has_constant="add")), 1e-6, 1 - 1e-6)
    loss0[te.index] = -(te.y * np.log(p0) + (1 - te.y) * np.log(1 - p0)); loss1[te.index] = -(te.y * np.log(p1) + (1 - te.y) * np.log(1 - p1))
diff = loss0 - loss1
bs = np.array([diff[rng.integers(0, len(diff), len(diff))].mean() for _ in range(4000)])
full = sm.Logit(c2.y, sm.add_constant(c2[["lb", "VEN", "OTH"]])).fit(disp=0)
R["T2"] = dict(n=int(len(c2)), hits=int(c2.y.sum()), by_country={k: dict(n=int(len(g)), hits=int(g.y.sum()), rate=round(float(g.y.mean()), 3),
               median_bonus_k=round(float(g.bonus_sign.median()) / 1e3)) for k, g in c2.groupby(np.where(c2.country.isin(["Dominican Republic", "Venezuela"]), c2.country, "Other"))},
               logloss_bonus_only=round(float(loss0.mean()), 4), logloss_bonus_country=round(float(loss1.mean()), 4),
               improvement=round(float(diff.mean()), 4), ci=[round(float(np.percentile(bs, 2.5)), 4), round(float(np.percentile(bs, 97.5)), 4)],
               p=float((bs <= 0).mean()), passed=bool(np.percentile(bs, 2.5) > 0),
               full_fit_or={k: round(float(np.exp(v)), 3) for k, v in full.params.items()},
               caveat="Cohort is signees with an early or rank-imputed bonus and a known country, so it leans to the top of the market.")

# ===================== T3 market timing
def t3(df, y):
    X = pd.get_dummies(df[["tier", "period"]].astype(str), drop_first=True).astype(float)
    X["open"] = df.opening_window.astype(float); X = sm.add_constant(X)
    m = sm.Logit(df[y].astype(float), X).fit(disp=0)
    b, se = m.params["open"], m.bse["open"]
    cell = {}
    for t in "ABC":
        g = df[df.tier == t]
        for o in (True, False):
            h = g[g.opening_window == o]
            cell[f"{t}_{'open' if o else 'later'}"] = dict(n=int(len(h)), hits=int(h[y].sum()), rate=round(float(h[y].mean()), 4) if len(h) else None)
    return dict(n=int(len(df)), or_open=round(float(np.exp(b)), 3), ci=[round(float(np.exp(b - 1.96 * se)), 3), round(float(np.exp(b + 1.96 * se)), 3)],
                p=float(m.pvalues["open"]), passed=bool(not (np.exp(b - 1.96 * se) <= 1 <= np.exp(b + 1.96 * se))), cells=cell,
                share_open=round(float(df.opening_window.mean()), 3))
R["T3_fv50"] = t3(U[U.period.between(2016, 2022)].reset_index(drop=True), "fv50_4")
R["T3_mlb7"] = t3(U[U.period.between(2016, 2019)].reset_index(drop=True), "mlb7")
# who signs late: tier mix by window
tw = U[U.period.between(2016, 2022)]
R["T3_tier_mix"] = {("open" if k else "later"): {t: int(v) for t, v in g.tier.value_counts().items()} for k, g in tw.groupby("opening_window")}

# ===================== T4 club differences (MLB7, periods 2016-2019)
c4 = U[U.period.between(2016, 2019)].copy()
c4["cell"] = c4.period.astype(str) + c4.tier
base = c4.groupby("cell").mlb7.mean(); c4["e"] = c4.cell.map(base)
def stat(df):
    g = df.groupby("sign_org").agg(o=("mlb7", "sum"), e=("e", "sum"))
    z = (g.o - g.e) / np.sqrt(g.e); return float(z.var())
obs = stat(c4); perm = []
cells = [g.index.values for _, g in c4.groupby("cell")]
orgs = c4.sign_org.values.copy()
for _ in range(2000):
    o2 = orgs.copy()
    for ix in cells:
        pos = c4.index.get_indexer(ix); o2[pos] = rng.permutation(o2[pos])
    perm.append(stat(c4.assign(sign_org=o2)))
perm = np.array(perm); p4 = float((perm >= obs).mean())
g = c4.groupby("sign_org").agg(signees=("mlb7", "size"), mlb7=("mlb7", "sum"), exp=("e", "sum"), war7=("war7", "sum"),
                               tierA=("tier", lambda s: int((s == "A").sum()))).reset_index()
# empirical-Bayes shrink of O/E ratio (Poisson-gamma): prior strength chosen by method of moments
g["oe"] = g.mlb7 / g.exp
v_between = max(float(np.var(g.oe) - np.mean(1 / g.exp)), 1e-6)
k = 1 / v_between                          # prior 'expected arrivals' weight
g["oe_shrunk"] = (g.mlb7 + k) / (g.exp + k)
R["T4"] = dict(n=int(len(c4)), stat_obs=round(obs, 3), perm_mean=round(float(perm.mean()), 3), p=p4, passed=bool(p4 < 0.05),
               prior_weight=round(k, 2), clubs=g.sort_values("oe_shrunk", ascending=False).round(3).to_dict("records"))

# ===================== T5 value per $ by tier (periods 2016-2019; A vs not-A for 2016-17, A/B/C for 2018-19)
def per_dollar(df, unrep):
    d = df.copy(); d.loc[d.bonus_src == "unreported", "bonus_sign"] = unrep
    d.loc[d.bonus_sign.isna(), "bonus_sign"] = unrep
    d["grp"] = np.where(d.tier == "A", "A", "BC")
    out = {}
    for k_, h in d.groupby("grp"):
        out[k_] = dict(n=int(len(h)), dollars_m=round(float(h.bonus_sign.sum()) / 1e6, 2), mlb7=int(h.mlb7.sum()), war7=round(float(h.war7.sum()), 1),
                       war_per_m=round(float(h.war7.sum() / (h.bonus_sign.sum() / 1e6)), 3), mlb_per_m=round(float(h.mlb7.sum() / (h.bonus_sign.sum() / 1e6)), 3))
    return out, d
t5 = {}; passes = []
d5 = U[U.period.between(2016, 2019)].reset_index(drop=True)
for v in (10e3, 50e3, 100e3):
    o, d = per_dollar(d5, v)
    def ratio(x):
        a = x[x.grp == "A"]; b = x[x.grp == "BC"]
        return (b.war7.sum() / b.bonus_sign.sum()) / max(a.war7.sum() / a.bonus_sign.sum(), 1e-9)
    bs = strat_boot(d, ratio, n=1000)
    o["ratio_BC_over_A_war_per_dollar"] = round(float(ratio(d)), 2)
    o["ratio_ci"] = [round(float(np.percentile(bs, 2.5)), 2), round(float(np.percentile(bs, 97.5)), 2)]
    passes.append(np.percentile(bs, 2.5) > 1); t5[f"unreported_{int(v/1e3)}K"] = o
t5["passed_all_three"] = bool(all(passes)); R["T5"] = t5

# ===================== multiple testing
names = ["T1_mlb7", "T1_fv50", "T2", "T3_fv50", "T3_mlb7", "T4"]
ps = [R[n]["p"] for n in names]; q = bh(ps)
R["BH"] = {n: dict(p=round(float(p), 5), q=round(float(qq), 5), survives_q10=bool(qq <= 0.10)) for n, p, qq in zip(names, ps, q)}

# ===================== descriptives: country
U["fv50_any_ok"] = U.fv50_any & U.period.between(2016, 2022)
cty = U.copy(); cty["country"] = cty.country.fillna("Unknown")
rows = []
for c, h in cty.groupby("country"):
    rows.append(dict(country=c, known_bonus_n=int(h.bonus_any.notna().sum()), known_bonus_m=round(float(h.bonus_any.sum()) / 1e6, 2),
                     mlb_2016_19=int(h[h.period.between(2016, 2019)].mlb_any.sum()), mlb_all=int(h.mlb_any.sum()),
                     war_all=round(float(h.war_all.sum()), 1), fv50_2016_22=int(h.fv50_any_ok.sum()), t100=int(h.t100.sum())))
cdf = pd.DataFrame(rows).sort_values("known_bonus_m", ascending=False)
known = cdf[cdf.country != "Unknown"]
for col in ["known_bonus_m", "mlb_all", "war_all", "fv50_2016_22", "t100"]:
    cdf[col + "_share"] = (cdf[col] / known[col].sum()).round(3)
R["country"] = cdf.to_dict("records")
R["country_coverage"] = dict(mlb_any_with_country=float(U[U.mlb_any].country.notna().mean()), fv50_with_country=float(U[U.fv50_any].country.notna().mean()))
# country x period known money (for trend)
R["country_money_by_period"] = {int(p): {c: round(float(v) / 1e6, 2) for c, v in g.groupby(g.country.fillna("Unknown")).bonus_any.sum().items() if v > 0}
                                for p, g in U.groupby("period")}

# ===================== descriptives: clubs (money 2016-2022 known; output)
cl = []
for o_, h in U.groupby("sign_org"):
    h19 = h[h.period.between(2016, 2019)]; h22 = h[h.period.between(2016, 2022)]
    cl.append(dict(club=o_, signees_16_22=int(len(h22)), known_m_16_22=round(float(h22.bonus_any.sum()) / 1e6, 2), known_m_16_19=round(float(h19.bonus_any.sum()) / 1e6, 2),
                   mlb7_16_19=int(h19.mlb7.sum()), war7_16_19=round(float(h19.war7.sum()), 1), war_all_16_22=round(float(h22.war_all.sum()), 1),
                   fv50_16_22=int(h22.fv50_4.sum()), t100_16_22=int(h22.t100.sum()),
                   top_war=h22.sort_values("war_all", ascending=False).head(3)[["name", "war_all"]].round(1).values.tolist()))
R["clubs"] = sorted(cl, key=lambda r: -r["war_all_16_22"])

# ===================== ranked vs unranked
rk = U[U.period.between(2016, 2022)]
def share(df, y): return dict(total=int(df[y].sum()), from_ranked=int(df[df.ranked_pre][y].sum()), share_ranked=round(float(df[df.ranked_pre][y].sum() / max(df[y].sum(), 1)), 3))
R["ranked"] = dict(n_ranked=int(rk.ranked_pre.sum()), n_all=int(len(rk)),
                   mlb7_16_19=share(U[U.period.between(2016, 2019)], "mlb7"), fv50_16_22=share(rk, "fv50_4"), t100_16_22=share(rk, "t100"),
                   war7_16_19=dict(total=round(float(U[U.period.between(2016, 2019)].war7.sum()), 1),
                                   ranked=round(float(U[U.period.between(2016, 2019) & U.ranked_pre].war7.sum()), 1)),
                   rate_ranked_mlb7=round(float(U[U.period.between(2016, 2019) & U.ranked_pre].mlb7.mean()), 3),
                   rate_unranked_mlb7=round(float(U[U.period.between(2016, 2019) & ~U.ranked_pre].mlb7.mean()), 4))
# top producers list (2016-2022 classes)
tp = U[U.period.between(2016, 2022)].sort_values("war_all", ascending=False).head(25)
R["top_producers"] = tp[["name", "period", "sign_org", "country", "tier", "bonus_any", "bonus_src", "ranked_pre", "first_mlb", "war_all", "peak_fv"]].round(1).astype(object).where(tp.notna(), None).values.tolist()
# years to MLB
ar = U[U.mlb_any & U.period.between(2016, 2019)]
R["years_to_mlb"] = {str(int(k)): int(v) for k, v in (ar.first_mlb - ar.period).value_counts().sort_index().items()}
# pro signings shown separately
pr = P[P.pro]
R["pro_signings"] = pr[["name", "period", "sign_org", "country", "age_sign", "bonus_any", "mlb_any", "war_all"]].round(1).astype(object).where(pr.notna(), None).values.tolist()
json.dump(R, open(OUT / "results_v1.json", "w"), indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x))
print(json.dumps({k: R[k] for k in ["T1_mlb7", "T1_fv50", "T1_money_share_known", "T1_money_share_with_unreported", "T2", "T3_fv50", "T3_mlb7", "T3_tier_mix", "BH", "ranked", "years_to_mlb"]}, indent=1, default=str))
print(json.dumps({k: v for k, v in R["T4"].items() if k != "clubs"}, indent=1)); print(json.dumps(R["T5"], indent=1))
