"""
Group consolidation check for Koenig & Bauer, FY2025.

Reads the public data in /data and recalculates the main results of the
Excel workbooks:
  1. Equity bridge (sum of companies -> published group equity)
  2. Non-controlling interest plausibility check
  3. Currency translation for the US and Swiss subsidiaries
  4. Parent result vs group result (intercompany income)

Run:  python consolidation.py
All amounts in EUR millions unless stated otherwise.
"""

from pathlib import Path

import pandas as pd

DATA = Path(__file__).parent / "data"
OUTPUT = Path(__file__).parent / "output"


# ---------------------------------------------------------------- loading

def load_data():
    units = pd.read_csv(DATA / "consolidation_units_FY2025.csv")
    reported = pd.read_csv(DATA / "reported_figures_FY2025.csv").set_index("item")
    rates = pd.read_csv(DATA / "ecb_rates.csv").set_index("currency")
    return units, reported, rates


def figure(reported, item, year=2025):
    """Get one published figure, e.g. figure(reported, 'group_equity')."""
    return float(reported.loc[item, f"value_{year}_eur_m"])


# ---------------------------------------------------------------- 1. equity bridge

def equity_bridge(units, reported):
    parent = units.loc[units["holding"] == "Parent", "equity_2025_eur_m"].sum()
    subsidiaries = units.loc[units["holding"] != "Parent", "equity_2025_eur_m"].sum()
    investments = figure(reported, "parent_financial_assets")
    goodwill = figure(reported, "group_goodwill")
    published = figure(reported, "group_equity")

    explained = parent + subsidiaries - investments + goodwill

    return pd.DataFrame(
        [
            ("Parent equity (HGB)", parent),
            ("+ Equity of subsidiaries", subsidiaries),
            ("= Sum of single-entity equity", parent + subsidiaries),
            ("- Parent's investments in subsidiaries", -investments),
            ("+ Goodwill in the group", goodwill),
            ("= Equity explained by public data", explained),
            ("Published group equity (IFRS)", published),
            ("Unexplained remainder", published - explained),
        ],
        columns=["step", "eur_m"],
    )


def indirect_equity(units):
    """Equity of units held through other subsidiaries - the biggest unknown in the bridge."""
    return units.loc[units["holding"] == "Indirect", "equity_2025_eur_m"].sum()


# ---------------------------------------------------------------- 2. NCI check

def nci_check(units, reported):
    minority_units = units[units["ownership"] < 1]
    expected = (minority_units["equity_2025_eur_m"] * (1 - minority_units["ownership"])).sum()
    published = figure(reported, "group_nci")
    return expected, published, published - expected


# ---------------------------------------------------------------- 3. currency translation

def translate(equity_open_eur, equity_close_eur, rate):
    """
    Current rate method (IAS 21), simplified:
    - change in local-currency equity is treated as the year's result
    - result translated at the average rate
    - balance sheet translated at the closing rate
    - the difference goes to OCI (currency translation reserve)
    Rates are in foreign currency per 1 EUR (ECB convention).
    """
    open_lc = equity_open_eur * rate["closing_2024"]
    close_lc = equity_close_eur * rate["closing_2025"]
    result_lc = close_lc - open_lc

    result_eur = result_lc / rate["average_2025"]
    expected_close_eur = equity_open_eur + result_eur
    translation_difference = equity_close_eur - expected_close_eur

    return {
        "equity_2024_lc": open_lc,
        "equity_2025_lc": close_lc,
        "result_lc": result_lc,
        "result_eur_at_average": result_eur,
        "translation_difference_eur": translation_difference,
        "growth_local_currency": close_lc / open_lc - 1,
        "growth_in_eur": equity_close_eur / equity_open_eur - 1,
    }


def translation_examples(units, rates):
    examples = {
        "Koenig & Bauer (US) Inc.": "USD",
        "Koenig & Bauer Banknote Solutions SA": "CHF",
    }
    results = {}
    for company, currency in examples.items():
        row = units.loc[units["company"] == company].iloc[0]
        results[company] = translate(
            row["equity_2024_eur_m"], row["equity_2025_eur_m"], rates.loc[currency]
        )
    return pd.DataFrame(results)


# ---------------------------------------------------------------- 4. P&L view

def parent_to_group_result(reported):
    parent_result = figure(reported, "parent_net_result")
    internal_income = sum(
        figure(reported, item)
        for item in [
            "parent_dividend_income",
            "parent_profit_transfer_income",
            "parent_loss_absorption",
            "parent_investment_impairments",
        ]
    )
    group_result = figure(reported, "group_net_result")
    parent_without_internal = parent_result - internal_income
    return parent_result, internal_income, parent_without_internal, group_result


# ---------------------------------------------------------------- report

def main():
    units, reported, rates = load_data()
    OUTPUT.mkdir(exist_ok=True)
    pd.set_option("display.float_format", "{:,.1f}".format)

    print("\n1. EQUITY BRIDGE, 31 Dec 2025 (EUR m)")
    bridge = equity_bridge(units, reported)
    print(bridge.to_string(index=False))
    print(f"Equity of indirectly held units: {indirect_equity(units):,.1f}")
    bridge.to_csv(OUTPUT / "equity_bridge.csv", index=False)

    print("\n2. NON-CONTROLLING INTEREST CHECK (EUR m)")
    expected, published, diff = nci_check(units, reported)
    print(f"Expected from equity x minority share: {expected:,.2f}")
    print(f"Published:                             {published:,.2f}")
    print(f"Difference:                            {diff:,.2f}")

    print("\n3. CURRENCY TRANSLATION (local currency in m, EUR m)")
    fx = translation_examples(units, rates)
    print(fx.to_string(float_format="{:,.3f}".format))
    fx.to_csv(OUTPUT / "currency_translation.csv")
    total = fx.loc["translation_difference_eur"].sum()
    group_oci = figure(reported, "group_oci_fx_translation")
    print(f"Sum of both translation differences: {total:,.1f}")
    print(f"Group OCI from translation (all units): {group_oci:,.1f}")

    print("\n4. PARENT RESULT vs GROUP RESULT (EUR m)")
    p, internal, p_clean, g = parent_to_group_result(reported)
    print(f"Parent net result (HGB):                 {p:,.1f}")
    print(f"of which group-internal income:          {internal:,.1f}")
    print(f"Parent result without internal income:   {p_clean:,.1f}")
    print(f"Group net result (IFRS):                 {g:,.1f}")
    print(f"Gap (subsidiaries' results + IFRS adj.): {g - p_clean:,.1f}")
    print(f"\nResult files written to {OUTPUT}/")


if __name__ == "__main__":
    main()
