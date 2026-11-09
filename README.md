# Group consolidation with real data: Koenig & Bauer FY2025

I wanted to understand group consolidation the way it happens in SAP S/4HANA Group Reporting, but without access to a real SAP system. So I took a real listed group, Koenig & Bauer from Würzburg, and rebuilt the main consolidation steps from its public 2025 annual report.

The question behind the project: **how do the accounts of 40 separate companies turn into one set of group figures?**

I chose this topic because group reporting is where finance, systems and business analysis meet, and I wanted to see how it works with real numbers instead of a textbook example.

---

## What I found

- The group has **40 consolidation units** (parent plus 39 subsidiaries) in **13 currencies**. Only one unit, in Turkey, has a minority shareholder (10%), and its currency is hyperinflationary.
- Adding up all companies' own equity gives **€752.4m**. After removing the parent's investments in its subsidiaries (€415.9m) and adding goodwill (€39.8m), I can explain **€376.3m** of the published group equity of **€343.1m**. The remaining **–€33.2m** comes from items that public data does not show, mainly investments held by subsidiaries in other subsidiaries.
- The parent alone lost €53.5m in 2025, the group only €13.5m. Part of the difference is intercompany income that disappears in consolidation (dividends, profit transfers, loss absorption).
- The US subsidiary grew **33% in US dollars** but only **18% in euros**, because the dollar lost about 13% against the euro. The translation difference of –€4.4m goes to equity, not to profit.

---

## Project files

| File | What it covers |
|---|---|
| `01_consolidation_units_FY2025.xlsx` | Group structure: all consolidation units with ownership, currency, direct/indirect holding, equity 2024 and 2025, and scope changes |
| `02_consolidation_bridge_FY2025.xlsx` | Equity bridge from single-entity figures to group equity, intercompany items in the parent's accounts, NCI plausibility check |
| `03_currency_translation_FY2025.xlsx` | Currency translation of the US and Swiss subsidiaries with ECB rates (closing vs average rate, translation difference) |
| `04_group_close_process_and_SAP_mapping.md` | Monthly group close as a process model, mapping to SAP S/4HANA Group Reporting, fit-gap notes |
| `python/` | The same calculations in Python, with live ECB exchange rates and automated tests |

In the Excel files, blue cells are figures taken from a source, black cells are formulas, and yellow cells are the key results. Every sheet lists its sources.

### Python version

The `python/` folder recalculates the main results from the source data, so they can be reproduced without Excel:

- `ecb_rates.py` downloads the official ECB closing and average exchange rates and saves them to `data/ecb_rates.csv`. The ECB server is sometimes slow, so the download retries automatically.
- `consolidation.py` recalculates the equity bridge, the NCI check, the currency translation and the parent-to-group result.
- `test_consolidation.py` checks that the Python results match the Excel model (6 tests).

To run it:

```
cd python
pip install -r requirements.txt
python ecb_rates.py
python consolidation.py
python -m pytest test_consolidation.py
```

<!-- Add your screenshot of the "6 passed" output here, e.g. ![Test results](python/test_results.png) -->



---

## How I approached it

1. **Group structure.** Built the consolidation unit list from the shareholdings table in the notes and compared it with 2024 to find scope changes (four new units in 2025).
2. **Consolidation bridge.** Started from the parent's HGB balance sheet, added all subsidiaries' equity and removed the parent's investments. Documented what cannot be explained with public data instead of forcing the numbers to match.
3. **Currency translation.** Converted reported euro figures back into local currency with ECB rates and translated them again the way IAS 21 requires.
4. **Process and system view.** Described the monthly close and mapped each step to SAP Group Reporting functions.

---

## What I learned

<!-- Draft - rewrite in my own words before applying. -->

- Consolidation is more than adding up companies. Each company is a consolidation unit with its own currency, ownership and accounting rules.
- The parent's investment in a subsidiary and the subsidiary's equity are the same money counted twice, so the investment has to be removed. What the parent paid above the company's value stays in the group as goodwill.
- If the parent owns less than 100%, part of the equity belongs to minority shareholders. In this group only the Turkish company has one (10%), and its currency is hyperinflationary, which makes it the most complex unit.
- Money moving inside the group (loans, sales, dividends, German profit transfers) is not real income or debt for the group, so it is removed on both sides.
- The P&L is translated at the average rate because profit is earned over the whole year. The balance sheet uses the closing rate because it shows one day. The difference goes into equity, not into profit.
- A weak currency can hide good performance: the US company grew 33% in dollars but only 18% in euros.
- Public data cannot explain everything. My bridge ends with a remainder of -€33.2m, mainly because some subsidiaries own other subsidiaries. It is better to explain a difference honestly than to force it to zero.
- Group closing is a monthly process (collect, check, translate, match intercompany, eliminate, consolidate, report), and each step has a matching function in SAP S/4HANA Group Reporting.
- In the Python part I learned that external data sources like the ECB sometimes fail, so the code should retry instead of crashing, and that tests can prove the code gives the same results as the Excel model.

---

## Limits of this project

- Public reports show subsidiaries' equity, but not their full balance sheets, results or intercompany balances with each other. The bridge therefore works at equity level and ends with a documented remainder.
- Subsidiary equity in the shareholdings list is based on local accounting rules, not IFRS.
- The company does not publish the exchange rates it used. I used ECB reference rates instead.
- Koenig & Bauer runs its consolidation in OneStream, not SAP Group Reporting. The SAP mapping is a design exercise, not a description of their system.
- The SAP terms are based on SAP's public learning material. <!-- Add: "I checked them against the SAP Learning journeys on [date]." once you have done this. -->

---

## Sources

- Koenig & Bauer Annual Report 2025 and Summary Annual Report 2025: https://annualreport.koenig-bauer.com
- Koenig & Bauer Annual Report 2024 (comparative figures)
- European Central Bank reference exchange rates: https://data.ecb.europa.eu
- SAP Learning, SAP S/4HANA Finance for Group Reporting: https://learning.sap.com

The annual reports are not included in this repository. Please download them from the company's website.
