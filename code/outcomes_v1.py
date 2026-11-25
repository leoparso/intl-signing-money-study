"""outcomes_v1.py -- joins outcomes to universe_v1.parquet per PREREG_v1.md (sealed 8a7e95f0...). Writes players_v1.parquet."""
import json, re, sys, unicodedata
from pathlib import Path
import numpy as np, pandas as pd

W = Path(sys.argv[1]); OUT = Path(sys.argv[2])
u = pd.read_parquet(OUT / "universe_v1.parquet")
R = {}
def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(jr|sr|ii|iii|iv)\b\.?", "", s)
    return re.sub(r"[^a-z]", "", s)

# ---- MLB seasons: org spine level MLB, plus house WAR rows
sp = pd.read_parquet(W / "pack/player_org_spine.parquet", columns=["mlbam_id", "season", "levels", "level_top"])
sp = sp[sp.levels.astype(str).str.contains("MLB") | (sp.level_top == "MLB")]
mlb_seasons = sp.groupby("mlbam_id").season.apply(lambda s: sorted(set(int(x) for x in s)))
war = pd.read_parquet(W / "pack/war.parquet")
war["id"] = war.id.astype(int)
ws = war.groupby(["id", "season"]).war_a.sum()
war_seasons = war.groupby("id").season.apply(lambda s: sorted(set(int(x) for x in s)))
def seasons(m):
    a = mlb_seasons.get(m, []); b = war_seasons.get(m, [])
    return sorted(set(a) | set(b))
u["mlb_seasons"] = u.mlbam.map(seasons)          # id-based, 2021+ only (spine levels and house WAR start 2021)
pm = pd.read_csv(sys.argv[3] + "/people_meta_v1.csv")  # pitchers: id-based MLB debut date
pdeb = pd.to_datetime(pm.set_index("mlbam_id").mlb_debut, errors="coerce").dt.year

# ---- 2016-20 seasons (amendment A1): public lines joined on name + season, unique rows only, and only for players with
# id-based MLB evidence (2021+ seasons or a pitcher debut date), so a same-named veteran cannot create an arrival.
fb = pd.read_parquet(W / "pack/FGBatting2010_2026.parquet", columns=["Season", "Name", "WAR"]); fb["side"] = "B"
fp = pd.read_parquet(W / "pack/FGPitching2010_2026.parquet", columns=["Season", "Name", "WAR"]); fp["side"] = "P"
f = pd.concat([fb, fp]); f = f[f.Season.between(2016, 2020)].copy(); f["nname"] = f.Name.map(norm)
dup_rows = f.groupby(["nname", "Season", "side"]).size()
amb = set(k[:2] for k, v in dup_rows.items() if v > 1)
fsum = f.groupby(["nname", "Season"]).WAR.sum()
uname_counts = u.nname.value_counts()
pub, amb_hits, early_seasons = {}, 0, {}
for r in u.itertuples():
    has_id = bool(r.mlb_seasons) or pd.notna(pdeb.get(r.mlbam))
    if not has_id: continue
    for s in range(max(2016, r.period + 1), 2021):
        if (r.nname, s) in fsum.index:
            if (r.nname, s) in amb or uname_counts[r.nname] > 1: amb_hits += 1; continue
            pub[(r.mlbam, s)] = float(fsum[(r.nname, s)]); early_seasons.setdefault(r.mlbam, []).append(s)
def first(r):
    c = list(r.mlb_seasons) + early_seasons.get(r.mlbam, [])
    d = pdeb.get(r.mlbam)
    if pd.notna(d) and d >= r.period: c.append(int(d))
    return min(c) if c else np.nan
u["first_mlb"] = [first(r) for r in u.itertuples()]
R["public_war_2016_20_matches"] = len(pub); R["public_war_ambiguous_skipped"] = amb_hits
def war_window(m, p, lo_off=1, hi_off=7):
    tot = 0.0
    for s in range(p + lo_off, p + hi_off + 1):
        if s >= 2021: tot += float(ws.get((m, s), 0.0))
        else: tot += pub.get((m, s), 0.0)
    return tot
u["war7"] = [war_window(m, p) for m, p in zip(u.mlbam, u.period)]
u["war_all"] = [war_window(m, p, 0, 2026 - p) for m, p in zip(u.mlbam, u.period)]
u["mlb7"] = u.first_mlb.notna() & (u.first_mlb <= u.period + 7)
u["mlb_any"] = u.first_mlb.notna()

# ---- FanGraphs prospect lists (post-signing): peak FV, FV50 within 4 list seasons, Top 100
fg = pd.read_parquet(W / "pack/fg_board.parquet").reset_index(drop=True)
mp = pd.read_parquet(W / "pack/fg_board_map.parquet").reset_index(drop=True)
fg["mlbam"] = mp.mlbam.values; fg = fg[fg.mlbam.notna()].copy(); fg["mlbam"] = fg.mlbam.astype(int)
fg["ls"] = fg.list_slug.str[:4].astype(int)
pros = fg[fg.list_slug.str.contains("prospect-list")][["mlbam", "ls", "FV_Current", "Ovr_Rank"]]
pros = pros.merge(u[["mlbam", "period"]], on="mlbam")
pros = pros[pros.ls >= pros.period + 1]
w4 = pros[pros.ls <= pros.period + 4]
u["peak_fv4"] = u.mlbam.map(w4.groupby("mlbam").FV_Current.max())
u["peak_fv"] = u.mlbam.map(pros.groupby("mlbam").FV_Current.max())
u["fv50_4"] = u.peak_fv4 >= 50
u["fv50_any"] = u.peak_fv >= 50
# Ovr_Rank is an overall rank only on lists where about 100-140 rows carry one (2019+); 2017-18 lists fill it for every row
ovr_ok = fg[fg.list_slug.str.contains("prospect-list")].groupby("list_slug").Ovr_Rank.apply(lambda s: s.notna().sum() <= 160)
ok_lists = set(ovr_ok[ovr_ok].index)
pros2 = fg[fg.list_slug.isin(ok_lists)][["mlbam", "ls", "Ovr_Rank"]].merge(u[["mlbam", "period"]], on="mlbam")
pros2 = pros2[pros2.ls >= pros2.period + 1]
t100_fg = set(pros2[pros2.Ovr_Rank.notna() & (pros2.Ovr_Rank <= 100)].mlbam)
R["fg_top100_lists_used"] = sorted(ok_lists)
pl = pd.read_parquet(W / "pack/pipeline.parquet", columns=["list", "year", "rank", "mlbam"])
pl = pl[pl.mlbam.notna()].copy(); pl["mlbam"] = pl.mlbam.astype(int)
t1 = pl[pl.list == "top100"].merge(u[["mlbam", "period"]], on="mlbam"); t1 = t1[t1.year >= t1.period + 1]
u["t100"] = u.mlbam.isin(t100_fg) | u.mlbam.isin(set(t1.mlbam))
u["fg_listed_ever"] = u.mlbam.isin(set(pros.mlbam))

# ---- tiers at signing (prereg): early bonus, imputed for Pipeline-ranked players without one
def band(r): return np.nan if pd.isna(r) else ("1-10" if r <= 10 else ("11-20" if r <= 20 else "21-50"))
u["rank_band"] = u.pipe_intl_rank.map(band)
ref = u[u.pipe_intl_rank.notna() & u.bonus_early.notna()].groupby(["period", "rank_band"]).bonus_early.median()
ref_all = u[u.pipe_intl_rank.notna() & u.bonus_any.notna()].groupby("rank_band").bonus_any.median()   # fallback for 2016-17 (no early records)
def sign_bonus(r):
    if pd.notna(r.bonus_early): return r.bonus_early, "early"
    if pd.notna(r.pipe_intl_rank):
        v = ref.get((r.period, r.rank_band))
        if v is None or pd.isna(v): v = ref_all.get(r.rank_band)
        return float(v), "imputed_rank"
    return np.nan, "unreported"
sb = [sign_bonus(r) for r in u.itertuples()]
u["bonus_sign"] = [a for a, b in sb]; u["bonus_src"] = [b for a, b in sb]
u["tier"] = np.where(u.bonus_sign >= 1e6, "A", np.where(u.bonus_sign >= 3e5, "B", "C"))
# for 2016-17 periods there are no early records: tiers there use any-time bonus for $1M+ only (big bonuses are recorded regardless of outcome)
old = u.period <= 2017
u.loc[old & u.bonus_any.notna() & (u.bonus_any >= 1e6), "tier"] = "A"
u.loc[old & u.bonus_any.notna() & (u.bonus_any >= 1e6), "bonus_src"] = "any_1m_plus"
u.loc[old & u.bonus_any.notna() & (u.bonus_any >= 1e6), "bonus_sign"] = u.bonus_any
R["tier_counts"] = {str(k): int(v) for k, v in u.groupby(["period", "tier"]).size().items()}
R["bonus_src"] = {str(k): int(v) for k, v in u.bonus_src.value_counts().items()}

# country group
def cg(c):
    if not isinstance(c, str): return "Unknown"
    if c in ("Dominican Republic", "Venezuela", "Cuba", "Colombia", "Panama", "Mexico", "Curacao", "Curaçao", "Bahamas", "Aruba", "Nicaragua",
             "Japan", "South Korea", "Taiwan", "Brazil", "Australia", "Germany", "Netherlands", "Honduras", "Haiti", "Peru", "Italy", "Spain",
             "South Africa", "Czech Republic", "China", "Jamaica", "Lithuania", "Philippines", "Guatemala", "Ecuador", "Uganda", "Hong Kong"):
        return "Curacao" if c in ("Curacao", "Curaçao") else c
    return c
u["country"] = u.country.map(cg)
u = u.drop(columns=["mlb_seasons"])
u.to_parquet(OUT / "players_v1.parquet", index=False)
R["n"] = int(len(u))
for p in sorted(u.period.unique()):
    g = u[u.period == p]
    R.setdefault("by_period", {})[int(p)] = dict(n=int(len(g)), mlb7=int(g.mlb7.sum()), mlb_any=int(g.mlb_any.sum()), fv50_4=int(g.fv50_4.sum()),
                                                  t100=int(g.t100.sum()), war7=round(float(g.war7.sum()), 1))
json.dump(R, open(OUT / "outcomes_receipt_v1.json", "w"), indent=1)
print(json.dumps({k: v for k, v in R.items() if k != "tier_counts"}, indent=1))
