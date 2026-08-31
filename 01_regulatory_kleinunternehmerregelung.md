# §19 / §19a UStG — Kleinunternehmerregelung (current rules, valid 2025–2026)

**Document type:** Curated regulatory summary for TaxHub demo ingestion.
**Basis:** Consolidated UStG text following the Jahressteuergesetz 2024 (Wachstumschancengesetz), in force since 1 January 2025.
**Primary source:** § 19 UStG, gesetze-im-internet.de/ustg/__19.html (official statute text — not reproduced verbatim here; this is a factual paraphrase for retrieval purposes).
**Secondary confirming sources:** IHK Region Stuttgart, "Kleinunternehmerregelung, Umsatzgrenzen, § 19 UStG" (ihk.de); NWB Rechnungswesen, "Neuregelungen für Kleinunternehmer ab 2025" (nwb.de).
**Last verified:** August 2026.

---

## 1. Who qualifies as a Kleinunternehmer

An entrepreneur qualifies for the Kleinunternehmerregelung under § 19 UStG only if **both** of the following hold at the same time:

1. **Prior-year threshold:** Total turnover (Gesamtumsatz, based on amounts actually received — not profit) in the preceding calendar year did not exceed **€25,000** (gross).
2. **Current-year threshold:** Total turnover in the current calendar year does not exceed **€100,000** (gross).

Both conditions are mandatory ("und," not "oder"). This is a change from the pre-2025 rules, which used €22,000 (prior year) and a €50,000 *forecast* for the current year.

## 1a. Official statute wording (current, post-2025 reform)

The current §19 Abs. 1 UStG (in force since 1 January 2025), per dejure.org's consolidated statute text: turnover is tax-exempt ("ist steuerfrei") where prior-year Gesamtumsatz did not exceed €25,000 and current-year Gesamtumsatz does not exceed €100,000. This replaced the pre-2025 wording, under which the tax was merely "not collected" (nicht erhoben) rather than the turnover being exempt outright.

**Sources:** dejure.org/gesetze/UStG/19.html (statute mirror); official text at gesetze-im-internet.de/ustg/__19.html.

## 1b. Historical threshold values — important for grounding, do not confuse with current figures

Multiple threshold pairs have applied at different times and **all three are still findable online**, which makes this a natural test of whether an answer is actually grounded in current law or in stale training data / an outdated cached page:

| Period | Prior-year limit | Current-year limit | Basis |
|---|---|---|---|
| Older / superseded (pre-2020, per UStAE 2017 text) | €17,500 | €50,000 | UStAE administrative guidance, 2017 wording |
| 2020–2024 | €22,000 | €50,000 (forecast-based) | Pre-reform §19 UStG |
| **Current, since 1 Jan 2025** | **€25,000** | **€100,000 (hard cap)** | Post-Jahressteuergesetz 2024 §19 UStG |

Any answer citing €17,500, €22,000, or €50,000 as a *current* figure is wrong and is drawing on outdated material — this table exists specifically so the retrieval system has the superseded values available to reason about explicitly, not just the current ones in isolation.

## 2. What counts toward the turnover figure

Turnover is measured on amounts received, not profit. It excludes:
- Imports from non-EU countries and intra-Community acquisitions.
- Certain tax-exempt transactions under §4 Nr. 8i, 9b, 11–28 UStG (e.g. rental income in some cases).
- Certain tax-exempt ancillary transactions under §4 Nr. 8a–h, 9a, 10 UStG (e.g. transactions falling under the Grunderwerbsteuergesetz).
- One-off sales of fixed assets, and non-business income such as employment salary.

## 3. What happens when a threshold is crossed — this is the part that changed most in 2025

**Crossing the current-year €100,000 limit:** Kleinunternehmer status ends **immediately**, starting with the specific transaction that causes the limit to be exceeded — not retroactively to the start of the year, and not carried through to year-end. Example (NWB, 2025): an entrepreneur with €80,000 turnover so far this year takes on a new order for €40,000. The moment that payment is received, the €100,000 line is crossed, and *that transaction itself* is already subject to standard VAT — the Kleinunternehmer exemption does not apply to it.

This is a meaningful change from the pre-2025 rule, under which the current-year figure was only a forecast and Kleinunternehmer status typically ran through to the end of the calendar year even if actual turnover ran higher than expected. Older online material describing the "runs to year-end" behavior is describing the pre-2025 rule and should not be treated as current.

**Crossing the prior-year €25,000 limit:** Status is lost starting **1 January of the following year**, regardless of how much turnover the current year produces. Example (kleinunternehmer.de): an entrepreneur with €29,300 turnover in 2025 is automatically subject to standard taxation from 1 January 2026, even if 2026 turnover would otherwise stay low.

## 4. Tax treatment since 2025

Since the 2025 reform, Kleinunternehmer turnover is **genuinely VAT-exempt** (echt umsatzsteuerfrei) rather than merely "not collected" as under the pre-2025 wording of §19 UStG. The practical consequence: no VAT is shown on invoices, but there is also no input VAT deduction (Vorsteuerabzug) on business purchases.

## 5. Cross-border: the new EU-wide scheme

§19a UStG, new since 2025, introduces a special notification procedure allowing a business established in Germany to apply the small-business exemption in **other EU member states** as well, not only domestically. This is new territory and firm-specific guidance on it should be treated cautiously in any client-facing draft.

## 6. Voluntary opt-out

An entrepreneur may voluntarily opt out of the Kleinunternehmerregelung and elect standard taxation (Regelbesteuerung) — commonly worthwhile when input VAT recovery on major purchases outweighs the simplicity of the exemption. This election is **binding for 5 calendar years** (§19 Abs. 2 UStG) and cannot be reversed early.

## 7. Invoice requirement

Invoices issued under the Kleinunternehmerregelung must not show VAT, and must reference the exemption, e.g.: "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet."

---

*This document is a curated summary for demo/retrieval purposes. It is not a substitute for consulting the current statutory text or a qualified Steuerberater, and TaxHub's own answers should always cite back to this document or the primary statute — never present unsourced conclusions.*
