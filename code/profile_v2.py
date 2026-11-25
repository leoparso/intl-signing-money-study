"""profile_v2.py -- part 2 fields per PREREG_v2.md (sealed a3262f6a...): position at signing, size near signing, age/birth month,
bats/throws, early path by pro season, trades before debut, MLB side/position. Writes profile_v2.parquet (players_v1 + new fields)."""
import json, re, sys
from pathlib import Path
import numpy as np, pandas as pd
W = Path(sys.argv[1]); OUT = Path(sys.argv[2]); TP = Path(sys.argv[3])
P = pd.read_parquet(OUT / "players_v1.parquet")
R = {}
# ---- position at signing
POS = r"(C|1B|2B|3B|SS|LF|CF|RF|OF|RHP|LHP|P|IF|DH|UT)"
p1 = P.description.str.extract(r"signed free agent\s+" + POS + r"\b")[0]
p2 = P.description.str.extract(r"^" + POS + r"\s")[0]
P["pos_sign"] = p1.fillna(p2)
GRP = {"C": "C", "SS": "SS", "2B": "Other IF", "3B": "Other IF", "1B": "Other IF", "IF": "Other IF", "UT": "Other IF",
       "OF": "OF", "LF": "OF", "CF": "OF", "RF": "OF", "DH": "Other IF", "RHP": "RHP", "P": "RHP", "LHP": "LHP"}
P["pos_grp"] = P.pos_sign.map(GRP)
P["is_pitcher"] = P.pos_grp.isin(["RHP", "LHP"])
R["pos_known"] = float(P.pos_grp.notna().mean())

# ---- lists: size near signing, bats/throws
fg = pd.read_parquet(W / "pack/fg_board.parquet").reset_index(drop=True)
mp = pd.read_parquet(W / "pack/fg_board_map.parquet").reset_index(drop=True)
fg["mlbam"] = mp.mlbam.values; fg = fg[fg.mlbam.notna()].copy(); fg["mlbam"] = fg.mlbam.astype(int)
fg["ls"] = fg.list_slug.str[:4].astype(int)
f = fg.merge(P[["mlbam", "period"]], on="mlbam")
f = f[(f.ls >= f.period) & (f.ls <= f.period + 2) & (f.Height > 0) & (f.Weight > 0)].sort_values("ls")
fs = f.groupby("mlbam").head(1).set_index("mlbam")
pl = pd.read_parquet(W / "pack/pipeline.parquet"); pl = pl[pl.mlbam.notna()].copy(); pl["mlbam"] = pl.mlbam.astype(int)
def inches(s):
    m = re.match(r"(\d)'\s*(\d+)", str(s)); return int(m.group(1)) * 12 + int(m.group(2)) if m else np.nan
pl["h_in"] = pl.height.map(inches)
q = pl.merge(P[["mlbam", "period"]], on="mlbam")
q = q[(q.year >= q.period) & (q.year <= q.period + 2) & q.h_in.notna() & (q.weight > 0)].sort_values("year")
qs = q.groupby("mlbam").head(1).set_index("mlbam")
# early_listed: on any public list published within two seasons of signing (the cohort where size and age are known before outcomes)
fe = fg.merge(P[["mlbam", "period"]], on="mlbam"); fe = fe[(fe.ls >= fe.period) & (fe.ls <= fe.period + 2)]
pe = pl.merge(P[["mlbam", "period"]], on="mlbam"); pe = pe[(pe.year >= pe.period) & (pe.year <= pe.period + 2)]
P["early_listed"] = P.mlbam.isin(set(fe.mlbam)) | P.mlbam.isin(set(pe.mlbam))
P["height"] = P.mlbam.map(fs.Height).fillna(P.mlbam.map(qs.h_in))
P["weight"] = P.mlbam.map(fs.Weight).fillna(P.mlbam.map(qs.weight))
P["size_src"] = np.where(P.mlbam.isin(fs.index), "fg", np.where(P.mlbam.isin(qs.index), "pipeline", None))
bt = fg[fg.Bats.notna()].groupby("mlbam").Bats.agg(lambda s: s.mode().iat[0])
P["bats"] = P.mlbam.map(bt).fillna(P.mlbam.map(pl[pl.bats.notna()].groupby("mlbam").bats.first()))
P["throws_p"] = np.where(P.pos_grp == "LHP", "L", np.where(P.pos_grp == "RHP", "R", None))
P["age_band"] = pd.cut(P.age_sign, [0, 16.5, 17.5, 30], labels=["16", "17", "18+"])
P["birth_month"] = P.dob.dt.month
R["size_known"] = float(P.height.notna().mean()); R["age_known"] = float(P.age_sign.notna().mean())

# ---- early path from transactions + team levels
tp = pd.read_csv(TP / "team_parent_v1.csv")
LVL = {(int(r.season), int(r.team_id)): int(r.sport_id) for r in tp.itertuples()}
LVL_ANY = {}
for (s, t), v in sorted(LVL.items()): LVL_ANY[t] = v
t = pd.read_parquet(W / "txn/txn.parquet"); t = t[t.mlbam_id.notna()].copy(); t["mlbam"] = t.mlbam_id.astype(int)
t = t[t.mlbam.isin(set(P.mlbam))]
t["season"] = t.date.str[:4].astype(int)
t["sport"] = [LVL.get((s, int(x)), LVL_ANY.get(int(x))) if pd.notna(x) else None for s, x in zip(t.season, t.to_team_id)]
t["dsl_to"] = t.to_team.str.match(r"^(DSL|VSL) ", na=False)
def pro_seasons(p):
    first = p + 1 if p <= 2018 else (2021 if p == 2019 else p)
    return [s for s in range(first, 2027) if s != 2020]
P["ps"] = P.period.map(pro_seasons)
def end_of(ps, k): return ps[k - 1] if len(ps) >= k else None
# US / full-season evidence by season: moves to non-DSL affiliated teams, plus 2021+ spine levels
# level evidence: assignments/options to a minor-league team only (signings, trades and claims name the MLB parent, not a level);
# training-site placeholders are not levels. MLB itself comes from first_mlb.
mv = t[t.to_team_id.notna() & t.type_code.isin(["ASG", "OPT"]) & (t.sport != 1)
       & ~t.to_team.str.contains("Alternate|Ext\\.|Spring|Instruct|Training", na=False)]
us = mv[~mv.dsl_to & mv.sport.isin([16, 15, 14, 13, 12, 11])].groupby("mlbam").season.min()
fs_ = mv[mv.sport.isin([14, 13, 12, 11])].groupby("mlbam").season.min()
ms = pd.read_parquet(W / "pack/minors_org_spine.parquet")
ms = ms[ms.mlbam_id.isin(set(P.mlbam))]
ms_full = ms[ms.level.isin(["A", "A+", "AA", "AAA", "MLB"])].groupby("mlbam_id").season.min()
ms_us = ms[~ms.affiliate.astype(str).str.match(r"^(DSL|VSL) ")].groupby("mlbam_id").season.min()
rel = t[t.type_code == "REL"].groupby("mlbam").season.min()
P["first_us"] = pd.concat([P.mlbam.map(us), P.mlbam.map(ms_us), P.first_mlb], axis=1).min(axis=1)
P["first_full"] = pd.concat([P.mlbam.map(fs_), P.mlbam.map(ms_full), P.first_mlb], axis=1).min(axis=1)
P["first_rel"] = P.mlbam.map(rel)
for k in (1, 2):
    e = P.ps.map(lambda s: end_of(s, k))
    P[f"out_of_dsl_s{k}"] = (P.first_us <= e) & e.notna()
e3 = P.ps.map(lambda s: end_of(s, 3))
P["fullseason_s3"] = (P.first_full <= e3) & e3.notna()
P["released_s3"] = (P.first_rel <= e3) & e3.notna()
e2 = P.ps.map(lambda s: end_of(s, 2))
P["released_s2"] = (P.first_rel <= e2) & e2.notna()
P["path_complete_s3"] = e3.notna() & (e3 <= 2026)

# ---- trades before debut; MLB side and position
tr = t[t.type_code == "TR"].groupby("mlbam").season.min()
P["first_trade"] = P.mlbam.map(tr)
P["traded_before_debut"] = P.first_mlb.notna() & P.first_trade.notna() & (P.first_trade <= P.first_mlb)
war = pd.read_parquet(W / "pack/war.parquet"); war["id"] = war.id.astype(int)
war = war[war.id.isin(set(P.mlbam))]
side = war.groupby(["id", "side"]).pt.sum().unstack(fill_value=0) if "pt" in war else None
war["pt"] = pd.to_numeric(war.pt, errors="coerce").fillna(0)
side = war.groupby(["id", "side"]).pt.sum().unstack(fill_value=0)
P["mlb_side"] = P.mlbam.map(lambda m: (None if m not in side.index else ("PITCH" if side.loc[m].get("PITCH", 0) > 0 and side.loc[m].get("PITCH", 0) >= side.loc[m].get("BAT", 0) * 0 and side.loc[m].get("BAT", 0) == 0 else ("BAT" if side.loc[m].get("PITCH", 0) == 0 else "BOTH"))))
bp = war[war.side == "BAT"].groupby(["id", "pos"]).pt.sum().reset_index().sort_values("pt").groupby("id").tail(1).set_index("id").pos
P["mlb_pos"] = P.mlbam.map(bp)
P["debut_age"] = np.where(P.first_mlb.notna() & P.dob.notna(), P.first_mlb - P.dob.dt.year - (P.dob.dt.month > 6) * 1.0 + 0.5, np.nan)
R["path_complete_share_16_19"] = float(P[P.period.between(2016, 2019)].path_complete_s3.mean())
P.drop(columns=["ps"]).to_parquet(OUT / "profile_v2.parquet", index=False)
json.dump(R, open(OUT / "profile_receipt_v2.json", "w"), indent=1)
print(json.dumps(R, indent=1))
print(P.pos_grp.value_counts(dropna=False).to_dict()); print(P.size_src.value_counts(dropna=False).to_dict())
x = P[P.period.between(2016, 2019)]
print("coverage 2016-19: size", round(x.height.notna().mean(), 3), "age", round(x.age_sign.notna().mean(), 3), "bats", round(x.bats.notna().mean(), 3))
print("path flags share (no outcome split):", {c: round(float(x[c].mean()), 3) for c in ["out_of_dsl_s1", "out_of_dsl_s2", "fullseason_s3", "released_s2", "released_s3"]})
print("war side/pos sample", war[["side", "pos", "pt"]].head(3).to_dict("records"))
