"""
Downloads official ECB exchange rates and saves them to data/ecb_rates.csv,
the file used by consolidation.py.

Run:  python ecb_rates.py
"""

import time
from pathlib import Path

import pandas as pd

ECB_URL = "https://data-api.ecb.europa.eu/service/data/EXR/"
DATA = Path(__file__).parent / "data"


def fetch_ecb(series, start, end):
    """Download one ECB series. Tries 3 times, because the ECB server is sometimes slow."""
    url = f"{ECB_URL}{series}?startPeriod={start}&endPeriod={end}&format=csvdata"
    for attempt in range(3):
        try:
            return pd.read_csv(url)
        except Exception:
            print(f"ECB not responding, retrying ({attempt + 1}/3)...")
            time.sleep(5)
    raise RuntimeError(f"Could not download {series} from the ECB.")


def get_closing_rate(currency, year):
    """Last published daily rate of the year (31 Dec can be a weekend or holiday)."""
    df = fetch_ecb(f"D.{currency}.EUR.SP00.A", f"{year}-12-24", f"{year}-12-31")
    return df["OBS_VALUE"].iloc[-1]


def get_average_rate(currency, year):
    """Official ECB annual average rate."""
    df = fetch_ecb(f"A.{currency}.EUR.SP00.A", year, year)
    return df["OBS_VALUE"].iloc[-1]


def build_rates_table(currencies, year):
    """Opening rate, closing rate and average rate for each currency."""
    rows = []
    for currency in currencies:
        rows.append({
            "currency": currency,
            f"closing_{year - 1}": get_closing_rate(currency, year - 1),
            f"closing_{year}": get_closing_rate(currency, year),
            f"average_{year}": get_average_rate(currency, year),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    rates = build_rates_table(["USD", "CHF"], 2025)
    print(rates)
    rates.to_csv(DATA / "ecb_rates.csv", index=False)
    print("Saved to data/ecb_rates.csv")