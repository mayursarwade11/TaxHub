# TaxHub MVP — Retrieval Test Cases

Run all four before recording the Loom. Each one checks something specific about whether the system is actually grounded rather than pattern-matching to general LLM knowledge of German tax law (which is very likely to reflect the *pre-2025* rules, since those were far more widely written about online).

---

## Test 1 — The primary demo case (must work perfectly, live)

**Question:**
> "I think I've exceeded the Kleinunternehmerregelung threshold. What does this mean and what do you need from me?"

**Expected behavior:**
- Retrieves both source documents (regulatory summary + firm checklist).
- Recognizes the question is ambiguous between the two thresholds and either asks a clarifying question or explicitly addresses both scenarios, per the firm checklist's Step 1.
- Cites §19 UStG (current-year and prior-year figures: €100,000 / €25,000) with the correct 2025-reform mechanic — immediate cutoff on the triggering transaction, not year-end.
- Cites the firm checklist for the internal next steps (Step 2–4).
- Produces a draft client email that requests the specific figures needed (Step 2) rather than guessing an answer.

**This is the one to rehearse and use in the Loom.**

## Test 2 — The old-law trap (validates grounding, not memory)

**Question:**
> "A client's current-year turnover just crossed €50,000 — do they lose their Kleinunternehmer status?"

**Why this matters:** €50,000 was the *old* current-year forecast limit (pre-2025). A model answering from general training data, rather than the ingested document, may incorrectly treat €50,000 as meaningful or apply the old forecast-based logic. The correct grounded answer is that €50,000 is irrelevant on its own — the current limit is €100,000, and the client's status is unaffected by this fact alone.

**Expected behavior:** The answer must reflect the *current* €100,000 figure from the ingested document, not any figure from general model knowledge, and should ideally flag that €50,000 was a previous, now-superseded threshold if the retrieved document is shown to support that framing.

## Test 3 — Out-of-scope refusal (validates the grounding boundary)

**Question:**
> "Can you also tell me how German inheritance tax (Erbschaftsteuer) allowances work for a client's second home?"

**Expected behavior:** The system has no ingested source on Erbschaftsteuer. It should decline to answer from general knowledge and say plainly that this isn't in the current knowledge base, rather than generating a plausible-sounding but ungrounded answer. This is the single most important thing to show live if asked "what happens when it doesn't know something" — see the one-pager's ChatGPT-hallucination objection response.

## Test 4 — Partial-information handling (validates the draft-output quality)

**Question:**
> "One of my clients asked if she needs to start charging VAT. I don't have her exact revenue numbers in front of me."

**Expected behavior:** Per firm checklist Step 2, the system should not guess an answer — it should produce a draft response to the *client* that requests the specific missing figures (current-year Ist-Umsatz, prior-year turnover), rather than a generic answer or a fabricated conclusion. This is the clearest demonstration that the tool assists the workflow rather than replacing judgment.

---

## Before recording

- Run all four once end-to-end and read the actual retrieved source snippets shown in the UI — don't just check that the final answer sounds right.
- If Test 2 fails (the model leans on general knowledge instead of the document), that's a retrieval-configuration problem to fix before anything else — it's the exact failure mode the one-pager promises won't happen.
- Have Test 3 ready as the "what if I ask something else" moment if CITO or a reviewer wants to probe live.
