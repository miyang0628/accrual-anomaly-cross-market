# Korean Data Collection (notebook 07) — Run Locally

Notebook `07_collect_korea_dart.ipynb` builds the Korean firm-level
total-accrual panel from DART (OpenDART), the Korean equivalent of SEC EDGAR.
It mirrors the US pipeline (notebooks 01–03) so the two markets are analyzed
identically.

## Why run locally
DART blocks many overseas / cloud IP ranges (returns HTTP 503 "remote
connection failure"). It must be run from an unblocked network — e.g. inside
Korea — with your own free OpenDART key.

## Steps
1. Get a free key at https://opendart.fss.or.kr (instant, no card).
2. Paste it into the `DART_KEY = "..."` line in the first code cell.
3. Install dependencies:
   ```
   pip install pandas numpy statsmodels finance-datareader
   ```
4. Run the cells in order. Checkpoints (`kr_edgar_raw.csv`) let you resume the
   slow firm×year loop.

## What it produces
- `data/kr_corp_map.csv`            corp_code ↔ stock_code map
- `data/kr_accounting_panel.csv`    TACC and GPOA per firm-year (Eq. 10, Eq. 4)
- `data/kr_monthly_prices.csv`      monthly KRX prices (via FinanceDataReader)
- `data/kr_factors.csv`             Korean/emerging factors (Kenneth French)
- `results/tables/kr_tacc_hedge_alphas.csv`  CAPM/FF3 hedge alphas

## Notes on fidelity
- Account matching uses IFRS XBRL `account_id`s with Korean account-name
  fallbacks; spot-check a few firms against their filings.
- The emerging-market French factors are used as the Korean benchmark; swap in
  a Korea-specific factor file if you have one for closer alignment.
- Add the emerging-market momentum (WML) file the same way to obtain the
  Carhart 4-factor alpha for Korea, matching the US tables.
