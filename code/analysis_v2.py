"""analysis_v2.py -- Q1-Q4 and the profile descriptives per PREREG_v2.md. Reads profile_v2.parquet, writes results_v2.json."""
import json, sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm
from sklearn.metrics import roc_auc_score
warnings.filterwarnings("ignore")
OUT = Path(sys.argv[1]); rng = np.random.default_rng(20261105)
P = pd.read_parquet(OUT / "profile_v2.parquet"); U = P[~P.pro].copy()
R = {}
def wilson(k, n, z=1.96):
    if n == 0: return [None, None]
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 4), round(c + h, 4)]
def bh(ps):
    ps = np.asarray(ps, float); n = len(ps); o = np.argsort(ps); q = np.empty(n); prev = 1.0
    for i in range(n - 1, -1, -1): prev = min(prev, ps[o[i]] * n / (i + 1)); q[o[i]] = prev
    return q
def rate(df, y): return dict(n=int(len(df)), hits=int(df[y].sum()), rate=round(float(df[y].mean()), 4) if len(df) else None, ci=wilson(int(df[y].sum()), int(len(df))))
M = U[U.period.between(2016, 2019)].copy(); F = U[U.period.between(2016, 2022)].copy()
M["lb"] = np.log(M.bonus_sign.fillna(5e4).clip(lower=1e4)); F["lb"] = np.log(F.bonus_sign.fillna(5e4).clip(lower=1e4))

# ===== Q1 position at signing
def q1(df, y):
    d = df[df.pos_grp.notna()].reset_index(drop=True)
    base = pd.get_dummies(d[["tier", "period"]].astype(str), drop_first=True).astype(float)
    pos = pd.get_dummies(d.pos_grp, drop_first=False).astype(float).drop(columns="RHP")
    m0 = sm.Logit(d[y].astype(float), sm.add_constant(base)).fit(disp=0)
    m1 = sm.Logit(d[y].astype(float), sm.add_constant(pd.concat([base, pos], axis=1))).fit(disp=0)
    lr = 2 * (m1.llf - m0.llf); df_ = pos.shape[1]; p = float(stats.chi2.sf(lr, df_))
    by = {g: rate(h, y) for g, h in d.groupby("pos_grp")}
    orr = {k: [round(float(np.exp(m1.params[k])), 2), round(float(np.exp(m1.conf_int().loc[k, 0])), 2), round(float(np.exp(m1.conf_int().loc[k, 1])), 2)] for k in pos.columns}
    return dict(n=int(len(d)), lr=round(float(lr), 2), df=df_, p=p, passed=bool(p < 0.05), by_group=by, odds_vs_RHP_after_tier=orr)
R["Q1_mlb7"] = q1(M, "mlb7"); R["Q1_fv50"] = q1(F, "fv50_4")
# share of big leaguers by position vs share of signees
d = M[M.pos_grp.notna()]
R["Q1_share"] = {g: dict(share_signees=round(float((d.pos_grp == g).mean()), 3), share_mlb=round(float(d[d.mlb7].pos_grp.eq(g).mean()), 3),
                         war7=round(float(d[d.pos_grp == g].war7.sum()), 1)) for g in ["RHP", "LHP", "C", "SS", "Other IF", "OF"]}

# ===== Q2 size
def q2(df, y, pitchers):
    d = df[df.height.notna() & df.weight.notna() & df.pos_grp.notna() & (df.is_pitcher == pitchers)].reset_index(drop=True)
    d["y"] = d[y].astype(float)
    l0, l1 = np.zeros(len(d)), np.zeros(len(d))
    for p in d.period.unique():
        tr, te = d[d.period != p], d[d.period == p]
        if tr.y.sum() < 3 or len(te) == 0: continue
        X0 = ["lb"]; X1 = ["lb", "height", "weight"]
        m0 = sm.Logit(tr.y, sm.add_constant(tr[X0])).fit(disp=0); m1 = sm.Logit(tr.y, sm.add_constant(tr[X1])).fit(disp=0)
        p0 = np.clip(m0.predict(sm.add_constant(te[X0], has_constant="add")), 1e-6, 1 - 1e-6); p1 = np.clip(m1.predict(sm.add_constant(te[X1], has_constant="add")), 1e-6, 1 - 1e-6)
        l0[te.index] = -(te.y * np.log(p0) + (1 - te.y) * np.log(1 - p0)); l1[te.index] = -(te.y * np.log(p1) + (1 - te.y) * np.log(1 - p1))
    diff = l0 - l1; bs = np.array([diff[rng.integers(0, len(diff), len(diff))].mean() for _ in range(4000)])
    full = sm.Logit(d.y, sm.add_constant(d[["lb", "height", "weight"]])).fit(disp=0)
    hit = d[d.y == 1]; miss = d[d.y == 0]
    return dict(n=int(len(d)), hits=int(d.y.sum()), improvement=round(float(diff.mean()), 4), ci=[round(float(np.percentile(bs, 2.5)), 4), round(float(np.percentile(bs, 97.5)), 4)],
                p=float((bs <= 0).mean()), passed=bool(np.percentile(bs, 2.5) > 0),
                or_per_inch=round(float(np.exp(full.params["height"])), 3), or_per_10lb=round(float(np.exp(10 * full.params["weight"])), 3),
                median_h_hit=float(hit.height.median()) if len(hit) else None, median_h_miss=float(miss.height.median()),
                median_w_hit=float(hit.weight.median()) if len(hit) else None, median_w_miss=float(miss.weight.median()))
R["Q2"] = {"pitchers_fv50": q2(F, "fv50_4", True), "pitchers_mlb7": q2(M, "mlb7", True), "hitters_fv50": q2(F, "fv50_4", False), "hitters_mlb7": q2(M, "mlb7", False)}
R["size_coverage"] = dict(classes_16_19=float(M.height.notna().mean()), classes_16_22=float(F.height.notna().mean()),
                          mlb7_with_size=float(M[M.mlb7].height.notna().mean()))
# height bands (descriptive, sized subset)
def bands(df, y, pitchers):
    d = df[df.height.notna() & (df.is_pitcher == pitchers)]
    cuts = [0, 71.5, 73.5, 75.5, 90] if pitchers else [0, 70.5, 72.5, 74.5, 90]
    labs = ["6'0\" or less", "6'1\"-6'2\"", "6'3\"-6'4\"", "6'5\"+"] if pitchers else ["5'10\" or less", "5'11\"-6'0\"", "6'1\"-6'2\"", "6'3\"+"]
    b = pd.cut(d.height, cuts, labels=labs)
    return {str(k): rate(g, y) for k, g in d.groupby(b)}
R["height_bands"] = {"pitchers_fv50": bands(F, "fv50_4", True), "hitters_fv50": bands(F, "fv50_4", False), "pitchers_mlb7": bands(M, "mlb7", True), "hitters_mlb7": bands(M, "mlb7", False)}
# size profile: big leaguers vs all sized signees, by pitcher/hitter (2016-19) and sizes of all 2016-19 big leaguers that have one
R["size_profile"] = {}
for nm, pit in (("pitchers", True), ("hitters", False)):
    d = M[M.height.notna() & (M.is_pitcher == pit)]
    R["size_profile"][nm] = dict(all_n=int(len(d)), all_h=float(d.height.median()), all_w=float(d.weight.median()),
                                 mlb_n=int(d.mlb7.sum()), mlb_h=float(d[d.mlb7].height.median()), mlb_w=float(d[d.mlb7].weight.median()),
                                 mlb_h_iqr=[float(d[d.mlb7].height.quantile(.25)), float(d[d.mlb7].height.quantile(.75))],
                                 mlb_w_iqr=[float(d[d.mlb7].weight.quantile(.25)), float(d[d.mlb7].weight.quantile(.75))])
# scatter points: sized 2016-22 signees, FV50 vs not (pitchers / hitters)
pts = F[F.height.notna() & F.pos_grp.notna()][["name", "period", "height", "weight", "is_pitcher", "fv50_4", "mlb_any", "pos_grp"]]
R["size_points"] = pts.astype(object).values.tolist()

# ===== Q3 how early can you tell
d = M.reset_index(drop=True)
d["tord"] = d.tier.map({"A": 2, "B": 1, "C": 0})
def aucs(x):
    return roc_auc_score(x.mlb7, x.fullseason_s3.astype(int)) - roc_auc_score(x.mlb7, x.tord)
groups = [g.index.values for _, g in d.groupby("period")]
bs = []
for _ in range(2000):
    idx = np.concatenate([rng.choice(g, len(g), replace=True) for g in groups]); bs.append(aucs(d.loc[idx]))
bs = np.array(bs)
R["Q3"] = dict(n=int(len(d)), auc_fullseason_s3=round(float(roc_auc_score(d.mlb7, d.fullseason_s3.astype(int))), 3), auc_tier=round(float(roc_auc_score(d.mlb7, d.tord)), 3),
               auc_out_of_dsl_s2=round(float(roc_auc_score(d.mlb7, d.out_of_dsl_s2.astype(int))), 3),
               diff=round(float(aucs(d)), 3), ci=[round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)],
               p=float((bs <= 0).mean()), passed=bool(np.percentile(bs, 2.5) > 0))
# funnel
fun = []
for lab, mask in [("Signed", d.index == d.index), ("Still with a club after pro season 2", ~d.released_s2), ("Out of the DSL by pro season 2", d.out_of_dsl_s2),
                  ("Full-season ball by pro season 3", d.fullseason_s3), ("Reached MLB within 7 seasons", d.mlb7)]:
    g = d[mask]; fun.append(dict(stage=lab, n=int(len(g)), share_of_signees=round(float(len(g) / len(d)), 4), mlb7=int(g.mlb7.sum()),
                                 mlb_rate=round(float(g.mlb7.mean()), 4), share_of_big_leaguers=round(float(g.mlb7.sum() / d.mlb7.sum()), 3)))
R["funnel"] = fun
R["path_rates"] = {f: {"yes": rate(d[d[f]], "mlb7"), "no": rate(d[~d[f]], "mlb7")} for f in ["out_of_dsl_s1", "out_of_dsl_s2", "fullseason_s3", "released_s2", "released_s3"]}
# by tier x path (does early path matter more for cheap signees?)
R["path_by_tier"] = {t: {"full_s3": rate(d[(d.tier == t) & d.fullseason_s3], "mlb7"), "not": rate(d[(d.tier == t) & ~d.fullseason_s3], "mlb7")} for t in "ABC"}
# big leaguers who were late: still in DSL after s2
bl = d[d.mlb7]
R["late_bloomers"] = dict(big_leaguers=int(len(bl)), in_dsl_after_s2=int((~bl.out_of_dsl_s2).sum()), not_full_by_s3=int((~bl.fullseason_s3).sum()),
                          names_not_full_by_s3=bl[~bl.fullseason_s3].sort_values("war_all", ascending=False).head(8)[["name", "period", "sign_org", "war_all"]].round(1).values.tolist(),
                          released_then_mlb=int((bl.first_rel.notna() & (bl.first_rel < bl.first_mlb)).sum()))

# ===== Q4 age at signing
a = M[M.age_band.notna() & M.early_listed].reset_index(drop=True)   # amendment v2-A1: age only where known before outcomes
a["older"] = (a.age_band != "16").astype(float)
X = pd.get_dummies(a[["tier", "period"]].astype(str), drop_first=True).astype(float); X["older"] = a.older
m = sm.Logit(a.mlb7.astype(float), sm.add_constant(X)).fit(disp=0); ci = m.conf_int().loc["older"]
R["Q4"] = dict(n=int(len(a)), or_older=round(float(np.exp(m.params["older"])), 2), ci=[round(float(np.exp(ci[0])), 2), round(float(np.exp(ci[1])), 2)],
               p=float(m.pvalues["older"]), passed=bool(not (np.exp(ci[0]) <= 1 <= np.exp(ci[1]))),
               by_band={str(k): rate(g, "mlb7") for k, g in a.groupby("age_band")}, coverage=float((M.age_band.notna() & M.early_listed).mean()),
               caveat="Cohort is signees on a public list within two seasons of signing (date of birth known before outcomes), so it leans to the top of the market.")

# ===== BH
names = [("Q1_mlb7", R["Q1_mlb7"]["p"]), ("Q1_fv50", R["Q1_fv50"]["p"])] + [(f"Q2_{k}", v["p"]) for k, v in R["Q2"].items()] + [("Q3", R["Q3"]["p"]), ("Q4", R["Q4"]["p"])]
q = bh([p for _, p in names]); R["BH"] = {n: dict(p=round(float(p), 5), q=round(float(qq), 5), survives=bool(qq <= 0.10)) for (n, p), qq in zip(names, q)}

# ===== descriptives
bl = M[M.mlb7]
R["profile"] = dict(
    n_signees=int(len(M)), n_big=int(len(bl)),
    pitcher_share_signees=round(float(M[M.pos_grp.notna()].is_pitcher.mean()), 3), pitcher_share_big=round(float(bl[bl.pos_grp.notna()].is_pitcher.mean()), 3),
    lhp_share_of_pitchers_signees=round(float((M.pos_grp == "LHP").sum() / M.is_pitcher.sum()), 3), lhp_share_of_pitchers_big=round(float((bl.pos_grp == "LHP").sum() / bl.is_pitcher.sum()), 3),
    bats_hitters_big={k: int(v) for k, v in bl[~bl.is_pitcher].bats.value_counts().items()}, bats_hitters_listed={k: int(v) for k, v in M[~M.is_pitcher & M.bats.notna()].bats.value_counts().items()},
    age_band_big={str(k): int(v) for k, v in bl.age_band.value_counts().items()}, age_known_big=round(float(bl.age_sign.notna().mean()), 3),
    early_listed_share_signees=round(float(M.early_listed.mean()), 3), early_listed_share_big=round(float(bl.early_listed.mean()), 3),
    traded_before_debut=int(bl.traded_before_debut.sum()), debut_with_signing_club=None,
    debut_age_median=float(np.nanmedian(bl.debut_age)) if bl.debut_age.notna().any() else None, debut_age_known=int(bl.debut_age.notna().sum()),
    debut_age_dist={str(int(k)): int(v) for k, v in np.floor(bl.debut_age.dropna()).value_counts().sort_index().items()})
# pitcher vs hitter output (MLB 2016-19 and WAR all)
R["side_output"] = {("Pitchers" if k else "Hitters"): dict(signees=int(len(g)), mlb7=int(g.mlb7.sum()), rate=round(float(g.mlb7.mean()), 4), war7=round(float(g.war7.sum()), 1),
                    war_all=round(float(g.war_all.sum()), 1)) for k, g in M[M.pos_grp.notna()].groupby("is_pitcher")}
# position changes among big leaguers (2016-22 classes, house WAR side/pos)
w = pd.read_parquet(Path(sys.argv[2]) / "pack/war.parquet"); w["id"] = w.id.astype(int); w["pt"] = pd.to_numeric(w.pt, errors="coerce").fillna(0)
sd = w.groupby(["id", "side"]).pt.sum().unstack(fill_value=0)
big = F[F.mlb_any & F.pos_grp.notna()].copy()
big["pitched"] = big.mlbam.map(lambda m: sd.loc[m].get("PITCH", 0) > 0 if m in sd.index else np.nan)
big["hit"] = big.mlbam.map(lambda m: sd.loc[m].get("BAT", 0) > 0 if m in sd.index else np.nan)
conv_h2p = big[~big.is_pitcher & (big.pitched == True) & (big.hit == False)]
conv_p2h = big[big.is_pitcher & (big.hit == True) & (big.pitched == False)]
ss = big[big.pos_grp == "SS"]
R["position_changes"] = dict(big_leaguers_16_22=int(len(big)), hitter_to_pitcher=conv_h2p[["name", "pos_sign", "war_all"]].round(1).values.tolist(),
                             pitcher_to_hitter=conv_p2h[["name", "pos_sign", "war_all"]].round(1).values.tolist(),
                             signed_ss=int(len(ss)), signed_ss_mlb_pos={str(k): int(v) for k, v in ss.mlb_pos.value_counts().items()},
                             signed_c=int((big.pos_grp == "C").sum()), signed_c_mlb_pos={str(k): int(v) for k, v in big[big.pos_grp == "C"].mlb_pos.value_counts().items()})
# best producers by position group (2016-22)
R["best_by_pos"] = {g: h.sort_values("war_all", ascending=False).head(4)[["name", "period", "bonus_any", "height", "weight", "war_all"]].round(1).astype(object).where(h.sort_values("war_all", ascending=False).head(4)[["name", "period", "bonus_any", "height", "weight", "war_all"]].notna(), None).values.tolist()
                    for g, h in F[F.pos_grp.notna()].groupby("pos_grp")}
json.dump(R, open(OUT / "results_v2.json", "w"), indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x))
show = {k: R[k] for k in ["Q1_mlb7", "Q1_fv50", "Q1_share", "Q2", "size_coverage", "height_bands", "size_profile", "Q3", "funnel", "path_by_tier", "late_bloomers", "Q4", "BH", "profile", "side_output", "position_changes"]}
print(json.dumps(show, indent=1, default=str))
