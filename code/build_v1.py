"""build_v1.py -- international amateur signing universe, signing periods 2016-17 through 2026 (Lenny 11/04).
Local data only (overnight pack + FG board + Pipeline + team parents). No new pulls.

Universe (written before any outcome is joined):
  signing      = a player's first transaction with an MLB-affiliated org in the 2016-26 log is SFA/SGN (signed) by that org,
                 or his first affiliated move is an assignment to a DSL/VSL club (signing not logged). National-team and
                 foreign-league moves before it do not count.
  international = (a) he is assigned to a DSL/VSL club within 36 months of signing (no DSL season in 2020), or (b) FanGraphs lists his signing market
                 as J2/Intl15, or (c) a known birth country outside USA/Puerto Rico/Canada and age < 25 at signing.
  excluded     = drafted players (FG Draft/UDFA/NDFA, Pipeline draft year), born USA/PR/Canada, age 25+ at signing (not pool money).
  period       = MLB signing period: Jul 2 - Jul 1 through 2019-20 (the 2019-20 period runs to Jan 14 2021, COVID), then Jan 15 - Jan 14.
  pro flag     = signed at 23+, or born Japan/South Korea/Taiwan and signed at 19+ (Ohtani/Sasaki type). Shown separately.
Writes universe_v1.parquet (one row per player) with signing facts only. Outcomes are joined in outcomes_v1.py."""
import json, re, sys, unicodedata
from pathlib import Path
import numpy as np, pandas as pd

W = Path(sys.argv[1]); TP = Path(sys.argv[2]); OUT = Path(sys.argv[3]); OUT.mkdir(parents=True, exist_ok=True)
ID2CODE = {108: "LAA", 109: "AZ", 110: "BAL", 111: "BOS", 112: "CHC", 113: "CIN", 114: "CLE", 115: "COL", 116: "DET", 117: "HOU", 118: "KC",
           119: "LAD", 120: "WSH", 121: "NYM", 133: "ATH", 134: "PIT", 135: "SD", 136: "SEA", 137: "SF", 138: "STL", 139: "TB", 140: "TEX",
           141: "TOR", 142: "MIN", 143: "PHI", 144: "ATL", 145: "CWS", 146: "MIA", 147: "NYY", 158: "MIL"}
R = {}

def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(jr|sr|ii|iii|iv)\b\.?", "", s)
    return re.sub(r"[^a-z]", "", s)

# ---- team -> org
tp = pd.read_csv(TP / "team_parent_v1.csv")
PAR = {}
for r in tp.itertuples():
    p = r.parent_org_id if pd.notna(r.parent_org_id) else (r.team_id if r.team_id in ID2CODE else None)
    if p is not None and int(p) in ID2CODE: PAR[(int(r.season), int(r.team_id))] = ID2CODE[int(p)]
PAR_ANY = {}
for (s, t), c in sorted(PAR.items()): PAR_ANY[t] = c          # latest season wins
def org(team_id, season):
    if pd.isna(team_id): return None
    t = int(team_id)
    if t in ID2CODE: return ID2CODE[t]
    return PAR.get((int(season), t)) or PAR_ANY.get(t)

# ---- transactions
t = pd.read_parquet(W / "txn/txn.parquet")
t = t[t.mlbam_id.notna()].copy(); t["mlbam"] = t.mlbam_id.astype(int)
t["season"] = t.date.str[:4].astype(int)
t["to_org"] = [org(a, s) for a, s in zip(t.to_team_id, t.season)]
t["from_org"] = [org(a, s) for a, s in zip(t.from_team_id, t.season)]
t["aff"] = t.to_org.notna() | t.from_org.notna()
t["dsl"] = t.to_team.str.match(r"^(DSL|VSL) ", na=False) | t.from_team.str.match(r"^(DSL|VSL) ", na=False)
t = t.sort_values(["mlbam", "date", "txn_id"])
a = t[t.aff]
first = a.groupby("mlbam").head(1).set_index("mlbam")
R["players_with_affiliated_moves"] = int(len(first))
is_sign = first.type_code.isin(["SFA", "SGN"])
is_dsl_first = first.to_team.str.match(r"^(DSL|VSL) ", na=False)
cand = first[(is_sign | is_dsl_first) & (first.date >= "2016-07-02")].copy()
cand["sign_date"] = pd.to_datetime(cand.date)
cand["sign_org"] = cand.to_org.fillna(cand.from_org)
cand["sign_logged"] = is_sign.reindex(cand.index)
dsl_first = t[t.dsl].groupby("mlbam").date.min()
cand["dsl_date"] = pd.to_datetime(dsl_first.reindex(cand.index))
cand["dsl24"] = cand.dsl_date.notna() & ((cand.dsl_date - cand.sign_date).dt.days <= 1100)
R["candidates_first_affiliated_signing_since_2016_07_02"] = int(len(cand))

# ---- FG board (+ MLBAM map), Pipeline, people meta
fg = pd.read_parquet(W / "pack/fg_board.parquet").reset_index(drop=True)
mp = pd.read_parquet(W / "pack/fg_board_map.parquet").reset_index(drop=True)
assert (fg.list_slug.values == mp.list_slug.values).all()
fg["mlbam"] = mp.mlbam.values; fg["dob_map"] = mp.dob.values
fg["Signed_Mkt"] = fg.Signed_Mkt.astype(str).str.strip()
fg = fg[fg.mlbam.notna()].copy(); fg["mlbam"] = fg.mlbam.astype(int)
fg["list_season"] = fg.list_slug.str[:4].astype(int)
mkt = fg.groupby("mlbam").Signed_Mkt.agg(lambda s: s.mode().iat[0] if len(s.mode()) else None)
ctry_fg = fg[fg.Country.notna()].groupby("mlbam").Country.agg(lambda s: s.mode().iat[0])
dob_fg = fg[fg.dob_map.notna()].groupby("mlbam").dob_map.first()
pl = pd.read_parquet(W / "pack/pipeline.parquet")
pl = pl[pl.mlbam.notna()].copy(); pl["mlbam"] = pl.mlbam.astype(int)
ctry_pl = pl[pl.birthplace.notna()].groupby("mlbam").birthplace.first().str.split(",").str[-1].str.strip()
dob_pl = pl[pl.birth_date.notna()].groupby("mlbam").birth_date.first()
drafted_pl = set(pl[pl.draft_year.notna()].mlbam)
pm = pd.read_csv(TP / "people_meta_v1.csv")
ctry_pm = pm.set_index("mlbam_id").birth_country; dob_pm = pm.set_index("mlbam_id").birth_date
drafted_pm = set(pm[pm.draft_year.notna()].mlbam_id)

u = cand[["name", "sign_date", "sign_org", "sign_logged", "type_code", "description", "dsl24"]].copy()
u["fg_mkt"] = mkt.reindex(u.index)
CMAP = {"DR": "Dominican Republic", "Dominican Rep.": "Dominican Republic", "D.R.": "Dominican Republic", "Venezuela": "Venezuela",
        "USA": "USA", "United States": "USA", "Puerto Rico": "Puerto Rico", "P.R.": "Puerto Rico"}
c = ctry_fg.reindex(u.index)
c = c.fillna(ctry_pl.reindex(u.index)).fillna(ctry_pm.reindex(u.index))
u["country"] = c.map(lambda x: CMAP.get(x, x) if isinstance(x, str) else None)
dob = pd.to_datetime(dob_fg.reindex(u.index), errors="coerce")
dob = dob.fillna(pd.to_datetime(dob_pl.reindex(u.index), errors="coerce")).fillna(pd.to_datetime(dob_pm.reindex(u.index), errors="coerce"))
u["dob"] = dob
u["age_sign"] = (u.sign_date - u.dob).dt.days / 365.25
u["drafted"] = u.fg_mkt.isin(["Draft", "UDFA", "NDFA"]) | u.index.isin(drafted_pl) | u.index.isin(drafted_pm)
dom = u.country.isin(["USA", "Puerto Rico", "Canada"])
intl = u.dsl24 | u.fg_mkt.isin(["J2", "Intl15"]) | (u.country.notna() & ~dom & (u.age_sign < 25))
keep = intl & ~u.drafted & ~dom & ~(u.age_sign >= 25)
R["excluded"] = {"not_international_signal": int((~intl).sum()), "drafted": int((intl & u.drafted).sum()),
                 "born_usa_pr_can": int((intl & ~u.drafted & dom).sum()), "age25plus": int((intl & ~u.drafted & ~dom & (u.age_sign >= 25)).sum())}
u = u[keep].copy()

def period(d):
    if d < pd.Timestamp("2021-01-15"):
        y = d.year if d >= pd.Timestamp(f"{d.year}-07-02") else d.year - 1
        return min(y, 2019)
    y = d.year if d >= pd.Timestamp(f"{d.year}-01-15") else d.year - 1
    return y
u["period"] = u.sign_date.map(period)
def opening(d, p):
    start = pd.Timestamp(f"{p}-07-02") if p <= 2019 else pd.Timestamp(f"{p}-01-15")
    return (d - start).days
u["days_into_period"] = [opening(d, p) for d, p in zip(u.sign_date, u.period)]
u["opening_window"] = u.days_into_period <= 14
u["pro"] = (u.age_sign >= 23) | (u.country.isin(["Japan", "South Korea", "Taiwan"]) & (u.age_sign >= 19))

# ---- bonus: FG Sign_Bonus. 'early' = recorded on an FG list published by period+2 (the first lists after signing),
# so it is known before most of the outcome window; 'any' = recorded on any list (survivor-weighted for small bonuses).
b = fg[fg.Sign_Bonus.notna() & (fg.Sign_Bonus > 0)][["mlbam", "list_season", "Sign_Bonus"]]
b_any = b.groupby("mlbam").Sign_Bonus.max()
u["bonus_any"] = b_any.reindex(u.index)
bb = b.merge(u[["period"]], left_on="mlbam", right_index=True)
b_early = bb[bb.list_season <= bb.period + 2].groupby("mlbam").Sign_Bonus.max()
u["bonus_early"] = b_early.reindex(u.index)

# ---- pre-signing rankings: Pipeline international list (top 30, top 50 from 2022) and FG international-prospects list,
# matched to the list year closest to the signing period (list year = period for Jul 2 periods ranked that summer; Jan 15 lists same year).
pi = pl[pl.list == "international"][["mlbam", "year", "rank"]]
def ranked(df, yr_col, rk_col, tag):
    m = df.merge(u[["period"]], left_on="mlbam", right_index=True)
    m = m[(m[yr_col] - m.period).abs() <= 1].sort_values(rk_col).groupby("mlbam").head(1)
    u[tag] = m.set_index("mlbam")[rk_col].reindex(u.index)
ranked(pi, "year", "rank", "pipe_intl_rank")
fi = fg[fg.list_slug.str.contains("international")][["mlbam", "list_season", "FV_Current"]].copy()
fi["rk"] = 1
ranked(fi.rename(columns={"list_season": "yr"}), "yr", "rk", "_fgi")
u["fg_intl_listed"] = u._fgi.notna(); u = u.drop(columns="_fgi")
u["ranked_pre"] = u.pipe_intl_rank.notna() | u.fg_intl_listed
u["mlbam"] = u.index
u = u.reset_index(drop=True)
u["nname"] = u.name.map(norm)
R["universe"] = int(len(u))
R["by_period"] = {int(k): int(v) for k, v in u.period.value_counts().sort_index().items()}
R["country_known_share"] = float(u.country.notna().mean())
R["bonus_any_known_share"] = float(u.bonus_any.notna().mean())
R["bonus_early_known_share"] = float(u.bonus_early.notna().mean())
R["pro_flagged"] = u[u.pro].name.tolist()
R["dsl24_share"] = float(u.dsl24.mean())
u.to_parquet(OUT / "universe_v1.parquet", index=False)
json.dump(R, open(OUT / "build_receipt_v1.json", "w"), indent=1, default=str)
print(json.dumps({k: v for k, v in R.items() if k != "pro_flagged"}, indent=1, default=str)); print("pro", len(R["pro_flagged"]), R["pro_flagged"][:30])
