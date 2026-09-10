# The Accrual Anomaly Reverses in Korea

A free-data, cross-market study of the accrual anomaly of Sloan (1996), with
**Korea as the primary emerging-market evidence** and the United States as a
validated developed-market reference. Everything runs on free, public data
through open, executable pipelines — no paid subscription required.

> **Headline result.** In Korea the accrual anomaly does not merely fail to
> appear — it **reverses**. High-accrual firms earn significantly *higher*
> subsequent returns (Fama–MacBeth loading ≈ **+2.3%/month, t ≈ 2.5**), robust to
> size, profitability, momentum, short-term-reversal, and volatility controls,
> and **concentrated in small-cap firms**. In the United States the classic Sloan
> sign appears, but validation against survivorship-corrected CRSP shows only the
> *sign* is reliable.

Prepared for the **Pacific-Basin Finance Journal** (replication track).

---

## Why this repository

Empirical anomaly studies are often hard to reproduce because they rely on paid
data (CRSP, Compustat, commercial factor libraries). This project rebuilds an
entire cross-market accrual study from **free public sources**:

- **Korea** — the Financial Supervisory Service's electronic disclosure system
  (OpenDART) for firm-level financials, KRX prices via `finance-datareader`, and
  Kenneth French emerging-market factors.
- **United States** — the SEC EDGAR XBRL/submissions APIs and the Kenneth French
  Data Library, validated against the survivorship-corrected CRSP-based accrual
  portfolios.

Anyone can clone the repo and reproduce every table and figure on zero budget.

---

## Key findings

| Proxy | Korea (primary) | United States (reference) |
|-------|-----------------|---------------------------|
| **Total accruals (G)** | **Reversal** — positive FM loading (+2.3%/mo, *t*≈2.5), small-cap | Sloan sign; insignificant in CRSP benchmark |
| Sin industry (S) | Not tested (definition differs) | Sin premium (free data) |
| Carbon efficiency (E) | — | Not testable (no free emissions data) |

The reversal is:
- **Significant** in Fama–MacBeth cross-sectional regressions (robust to controls);
- **Concentrated in small caps** (CAPM hedge −0.98%/mo, *t*=−2.46 in the smallest
  30%; ≈0 among large firms);
- **Stable** across equal/value weighting and across five of six sort-years.

---

## Repository layout

```
.
├── paper/                     # LaTeX manuscript (Elsevier elsarticle)
│   ├── manuscript.tex
│   ├── references.bib         # 62 verified references
│   ├── elsarticle.cls, elsarticle-harv.bst
│   └── figures/               # grayscale figures + structural diagrams
├── data/                      # Korean (DART/KRX) + US (EDGAR/French) firm-level data
├── notebooks/
│   ├── 01–06 …                # US collection, portfolios, sin, CRSP validation
│   ├── 07_collect_korea_dart_FINAL.ipynb   # Korea DART collection (run in Korea)
│   ├── 08_korea_deep_analysis.py           # reproduces Section 4.1 (the reversal)
│   └── README_korea.md
├── results/
│   ├── tables/                # output CSVs behind the manuscript tables
│   └── figures/               # grayscale PNGs used in the manuscript
├── requirements.txt
└── DATA_DICTIONARY.md
```

---

## Quick start

```bash
git clone https://github.com/<user>/accrual-anomaly-cross-market.git
cd accrual-anomaly-cross-market
pip install -r requirements.txt

# Reproduce the Korean results (Section 4.1) — runs offline on included data
cd notebooks
python 08_korea_deep_analysis.py
```

This writes all `kr_*.csv` to `results/tables/`, reproducing the negative
portfolio hedge, the significant Fama–MacBeth reversal, the small-cap
concentration, and the robustness checks.

### Re-collecting the data (optional)

- **US** — run notebooks `01`–`06` in order (no key needed; SEC EDGAR is public).
- **Korea** — `07_collect_korea_dart_FINAL.ipynb` needs a free
  [OpenDART](https://opendart.fss.or.kr) key and must run from an unblocked
  network (DART blocks many overseas/cloud IPs). The collected `kr_*.csv` are
  already in `data/`, so analysis runs without re-collection.

---

## Building the paper

```bash
cd paper
pdflatex manuscript && bibtex manuscript && pdflatex manuscript && pdflatex manuscript
```
Or upload the `paper/` folder to [Overleaf](https://www.overleaf.com) and compile
with pdfLaTeX.

---

## Method notes

- **Total accruals**: cash-flow-statement definition, TACC = (NI − OCF) / Assets₍ₜ₋₁₎
  (Hribar & Collins, 2002), winsorized 1/99.
- **Portfolios**: annual quintile sorts, held July *t*+1 → June *t*+2; P5 = low
  accrual. CAPM / Fama–French 3-factor (US also Carhart 4-factor), Newey–West
  (3-lag) standard errors.
- **Primary Korean test**: monthly Fama–MacBeth cross-sectional regressions on the
  full cross-section (more powerful than tail quintiles with a 6-year panel).
- **US validation**: free-data accrual portfolios vs the CRSP-based Kenneth French
  accrual portfolios (sign agrees; free-data magnitude is inflated by
  survivorship/micro-cap effects).

---

## Data caveats

- The free US price feed is **not** survivorship-bias-free; we restrict US claims
  to the *sign* and validate against CRSP. This is quantified in the paper.
- The Korean panel is from DART (authoritative, free) with far less survivorship
  concern; it is the study's primary evidence.
- See `DATA_DICTIONARY.md` for column-level definitions.

---

## Citation

If you use this code or data, please cite the paper (details to be added upon
acceptance) and this repository.

## License

Code released under the MIT License. Data are redistributed from public sources
(SEC EDGAR, OpenDART, the Kenneth French Data Library) for reproducibility;
please respect each source's terms.
