#!/usr/bin/env python3
"""
08_korea_deep_analysis.py
=========================
Deep analysis of the Korean accrual anomaly, reproducing the results in
Section 4.1 of the manuscript ("The accrual anomaly reverses in Korea").

Inputs (relative to ../data):
    kr_accounting_panel.csv   firm-year NI, OCF, assets, revenue, COGS, TACC, GPOA
    kr_monthly_prices.csv     wide monthly KRX prices (columns = 6-digit codes)
    kr_factors.csv            emerging-market factors (MktRF, SMB, HML)

Outputs (written to ../results/tables):
    kr_tacc_hedge_alphas.csv      baseline P5-P1 hedge (CAPM, FF3)
    kr_tacc_quintile_returns.csv  quintile mean monthly returns
    kr_size_heterogeneity.csv     hedge by firm-size subsample (Table 3)
    kr_fama_macbeth.csv           FM coefficients, univariate + multivariate
    kr_fm_extended.csv            FM with momentum / reversal / volatility controls
    kr_weighting_robustness.csv   equal- vs value-weighted hedge
    kr_year_by_year.csv           hedge by sort year

Run:
    pip install pandas numpy statsmodels
    python 08_korea_deep_analysis.py
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
import warnings
warnings.filterwarnings("ignore")

DATA = "../data"
OUT = "../results/tables"
os.makedirs(OUT, exist_ok=True)

# --------------------------------------------------------------------------
# Load
# --------------------------------------------------------------------------
acc = pd.read_csv(f"{DATA}/kr_accounting_panel.csv", dtype={"stock_code": str})
acc["stock_code"] = acc["stock_code"].str.replace(r"\.0$", "", regex=True).str.zfill(6)
px = pd.read_csv(f"{DATA}/kr_monthly_prices.csv", index_col=0, parse_dates=True)
px.columns = [str(c).zfill(6) for c in px.columns]
px.index = px.index.to_period("M").to_timestamp()
fac = pd.read_csv(f"{DATA}/kr_factors.csv", index_col=0, parse_dates=True)
fac.index = fac.index.to_period("M").to_timestamp()

rets = px.pct_change(fill_method=None).iloc[1:].clip(-0.9, 4.0)
rets.index = rets.index.to_period("M").to_timestamp()
price_codes = set(rets.columns)


def winz(s, p=0.01):
    return s.clip(s.quantile(p), s.quantile(1 - p))


acc["tacc_w"] = winz(acc["tacc"])
acc["gpoa_w"] = winz(acc["gpoa"])
acc["lnat"] = np.log(acc["at"].clip(lower=1))


def alphas(series, models={"CAPM": ["MktRF"], "FF3": ["MktRF", "SMB", "HML"]}):
    d = pd.DataFrame({"y": series}).join(fac, how="inner").dropna()
    out = {}
    for name, cols in models.items():
        m = sm.OLS(d["y"], sm.add_constant(d[cols])).fit(
            cov_type="HAC", cov_kwds={"maxlags": 3})
        out[name] = (round(m.params["const"] * 100, 3), round(m.tvalues["const"], 2))
    return out, len(d)


# --------------------------------------------------------------------------
# 1. Baseline quintile sort (P5 = low accrual)
# --------------------------------------------------------------------------
def build_quintiles(mask=lambda s: s, vw=False):
    recs = []
    for fy in sorted(acc["fyear"].dropna().unique()):
        sub = acc[acc["fyear"] == fy].dropna(subset=["tacc_w", "at"])
        sub = sub[sub["stock_code"].isin(price_codes)]
        sub = mask(sub)
        if len(sub) < 50:
            continue
        sub = sub.copy()
        sub["q"] = 5 - pd.qcut(sub["tacc_w"], 5, labels=False, duplicates="drop")
        hold = pd.date_range(f"{int(fy)+1}-07-01", f"{int(fy)+2}-06-30", freq="MS")
        for q in range(1, 6):
            qs = sub[sub["q"] == q]
            tks = [t for t in qs["stock_code"] if t in price_codes]
            if not tks:
                continue
            if vw:
                w = qs.set_index("stock_code")["at"].reindex(tks)
                w = w / w.sum()
                pr = (rets.reindex(hold)[tks] * w).sum(axis=1, min_count=1)
            else:
                pr = rets.reindex(hold)[tks].mean(axis=1)
            for dt, v in pr.items():
                if pd.notna(v):
                    recs.append((dt, q, v))
    wide = pd.DataFrame(recs, columns=["date", "q", "ret"]).pivot_table(
        index="date", columns="q", values="ret")
    wide.columns = [f"P{c}" for c in wide.columns]
    wide["P5_P1"] = wide["P5"] - wide["P1"]
    return wide


wide = build_quintiles()
qret = (wide[[f"P{i}" for i in range(1, 6)]].mean() * 100).round(3)
qret.index = ["P1_high_accrual", "P2", "P3", "P4", "P5_low_accrual"]
qret.rename("mean_monthly_return_pct").to_csv(f"{OUT}/kr_tacc_quintile_returns.csv")

a, n = alphas(wide["P5_P1"])
pd.DataFrame([{"model": k, "alpha_pct": v[0], "t": v[1]} for k, v in a.items()]).to_csv(
    f"{OUT}/kr_tacc_hedge_alphas.csv", index=False)
print("Baseline hedge:", a, "| months:", n)

# --------------------------------------------------------------------------
# 2. Size heterogeneity (Table 3)
# --------------------------------------------------------------------------
def hedge_for(mask):
    w = build_quintiles(mask=mask)
    if "P5_P1" not in w:
        return None, 0
    return alphas(w["P5_P1"])


rows = []
for lab, mask in [
    ("All", lambda s: s),
    ("Small (bottom 50%)", lambda s: s[s["at"] <= s["at"].median()]),
    ("Large (top 50%)", lambda s: s[s["at"] > s["at"].median()]),
    ("Micro (bottom 30%)", lambda s: s[s["at"] <= s["at"].quantile(0.3)]),
    ("Big (top 30%)", lambda s: s[s["at"] >= s["at"].quantile(0.7)]),
]:
    a, n = hedge_for(mask)
    rows.append({"subsample": lab, "CAPM_alpha": a["CAPM"][0], "CAPM_t": a["CAPM"][1],
                 "FF3_alpha": a["FF3"][0], "FF3_t": a["FF3"][1], "months": n})
pd.DataFrame(rows).to_csv(f"{OUT}/kr_size_heterogeneity.csv", index=False)
print("Size heterogeneity written.")

# --------------------------------------------------------------------------
# 3. Fama-MacBeth cross-sectional regressions (Table 2 / extended)
# --------------------------------------------------------------------------
mom = (1 + rets).rolling(11).apply(np.prod, raw=True).shift(2) - 1
strev = rets.shift(1)
vol = rets.rolling(12).std().shift(1)


def zc(s):
    return (s - s.mean()) / s.std()


recs = []
for fy in sorted(acc["fyear"].dropna().unique()):
    sub = acc[acc["fyear"] == fy].dropna(subset=["tacc_w"]).copy()
    sub = sub[sub["stock_code"].isin(price_codes)]
    char = sub.set_index("stock_code")[["tacc_w", "lnat", "gpoa_w"]]
    hold = pd.date_range(f"{int(fy)+1}-07-01", f"{int(fy)+2}-06-30", freq="MS")
    for dt in hold:
        if dt not in rets.index:
            continue
        for t, row in char.iterrows():
            if t not in price_codes:
                continue
            y = rets.at[dt, t]
            if pd.isna(y):
                continue
            recs.append((dt, t, y, row["tacc_w"], row["lnat"], row["gpoa_w"],
                         mom.at[dt, t] if t in mom.columns else np.nan,
                         strev.at[dt, t] if t in strev.columns else np.nan,
                         vol.at[dt, t] if t in vol.columns else np.nan))
mc = pd.DataFrame(recs, columns=["date", "tk", "ret", "tacc", "lnat", "gpoa",
                                 "mom", "strev", "vol"])


def fm(cols, standardize_controls=True):
    coefs = []
    for dt, g in mc.groupby("date"):
        g = g.dropna(subset=cols + ["ret"])
        if len(g) < 30:
            continue
        gg = g.copy()
        if standardize_controls:
            for c in cols:
                if c != "tacc":
                    gg[c] = zc(gg[c])
        coefs.append(sm.OLS(gg["ret"], sm.add_constant(gg[cols])).fit().params)
    cf = pd.DataFrame(coefs).reset_index(drop=True)
    out = {}
    for c in ["const"] + cols:
        m = sm.OLS(cf[c].values, np.ones(len(cf))).fit(
            cov_type="HAC", cov_kwds={"maxlags": 3})
        out[c] = (round(m.params[0] * 100, 4), round(m.tvalues[0], 2))
    return out, len(cf)


# Table 2: univariate + multivariate
u, n1 = fm(["tacc"])
m3, n2 = fm(["tacc", "lnat", "gpoa"])
pd.DataFrame([
    {"spec": "Univariate", "var": "TACC", "coef_pct": u["tacc"][0], "t": u["tacc"][1], "months": n1},
    {"spec": "Multivariate", "var": "TACC", "coef_pct": m3["tacc"][0], "t": m3["tacc"][1], "months": n2},
    {"spec": "Multivariate", "var": "Size(lnAT)", "coef_pct": m3["lnat"][0], "t": m3["lnat"][1], "months": n2},
    {"spec": "Multivariate", "var": "GP/A", "coef_pct": m3["gpoa"][0], "t": m3["gpoa"][1], "months": n2},
]).to_csv(f"{OUT}/kr_fama_macbeth.csv", index=False)

# Extended: cumulative price-based controls
rows = []
for name, cols in [
    ("(1) TACC only", ["tacc"]),
    ("(2) +size,GP/A", ["tacc", "lnat", "gpoa"]),
    ("(3) +momentum", ["tacc", "lnat", "gpoa", "mom"]),
    ("(4) +ST reversal", ["tacc", "lnat", "gpoa", "mom", "strev"]),
    ("(5) +volatility", ["tacc", "lnat", "gpoa", "mom", "strev", "vol"]),
]:
    o, n = fm(cols)
    rows.append({"spec": name, "TACC_coef_pct": o["tacc"][0], "TACC_t": o["tacc"][1], "months": n})
pd.DataFrame(rows).to_csv(f"{OUT}/kr_fm_extended.csv", index=False)
print("Fama-MacBeth written. Univariate TACC:", u["tacc"], "Multivariate:", m3["tacc"])

# --------------------------------------------------------------------------
# 4. Weighting robustness + year-by-year
# --------------------------------------------------------------------------
rows = []
for lab, vw in [("Equal-weighted", False), ("Value-weighted (assets)", True)]:
    w = build_quintiles(vw=vw)
    a, n = alphas(w["P5_P1"])
    rows.append({"weighting": lab, "CAPM_alpha": a["CAPM"][0], "CAPM_t": a["CAPM"][1],
                 "FF3_alpha": a["FF3"][0], "FF3_t": a["FF3"][1], "months": n})
pd.DataFrame(rows).to_csv(f"{OUT}/kr_weighting_robustness.csv", index=False)

rows = []
for fy in sorted(acc["fyear"].dropna().unique()):
    sub = acc[acc["fyear"] == fy].dropna(subset=["tacc_w"])
    sub = sub[sub["stock_code"].isin(price_codes)].copy()
    if len(sub) < 50:
        continue
    sub["q"] = 5 - pd.qcut(sub["tacc_w"], 5, labels=False, duplicates="drop")
    hold = pd.date_range(f"{int(fy)+1}-07-01", f"{int(fy)+2}-06-30", freq="MS")
    p5 = rets.reindex(hold)[[t for t in sub[sub["q"] == 5]["stock_code"] if t in price_codes]].mean(axis=1)
    p1 = rets.reindex(hold)[[t for t in sub[sub["q"] == 1]["stock_code"] if t in price_codes]].mean(axis=1)
    h = (p5 - p1).dropna()
    rows.append({"sort_year": int(fy), "hedge_pct_mo": round(h.mean() * 100, 3),
                 "n_firms": len(sub), "months": len(h)})
pd.DataFrame(rows).to_csv(f"{OUT}/kr_year_by_year.csv", index=False)
print("Robustness + year-by-year written. Done.")
