"""
Checks that the Python calculation gives the same results as the Excel files.
Run:  python -m pytest test_consolidation.py
"""

import pytest

from consolidation import (
    equity_bridge, indirect_equity, load_data, nci_check, parent_to_group_result,
    translation_examples,
)

units, reported, rates = load_data()


def step(bridge, name):
    return bridge.loc[bridge["step"] == name, "eur_m"].iloc[0]


def test_unit_count():
    assert len(units) == 40
    assert (units["holding"] == "Parent").sum() == 1


def test_equity_bridge_matches_excel():
    bridge = equity_bridge(units, reported)
    assert step(bridge, "= Sum of single-entity equity") == pytest.approx(752.4, abs=0.05)
    assert step(bridge, "= Equity explained by public data") == pytest.approx(376.3, abs=0.05)
    assert step(bridge, "Unexplained remainder") == pytest.approx(-33.2, abs=0.05)


def test_indirect_equity():
    assert indirect_equity(units) == pytest.approx(297.7, abs=0.05)


def test_nci():
    expected, published, _ = nci_check(units, reported)
    assert expected == pytest.approx(0.38, abs=0.005)
    assert published == pytest.approx(0.6)


def test_currency_translation_matches_excel():
    fx = translation_examples(units, rates)
    us = fx["Koenig & Bauer (US) Inc."]
    ch = fx["Koenig & Bauer Banknote Solutions SA"]
    assert us["translation_difference_eur"] == pytest.approx(-4.40, abs=0.01)
    assert ch["translation_difference_eur"] == pytest.approx(0.86, abs=0.01)
    assert us["growth_local_currency"] == pytest.approx(0.334, abs=0.001)
    assert us["growth_in_eur"] == pytest.approx(0.180, abs=0.001)


def test_parent_to_group_result():
    _, internal, parent_clean, group = parent_to_group_result(reported)
    assert internal == pytest.approx(6.3, abs=0.05)
    assert group - parent_clean == pytest.approx(46.3, abs=0.05)
