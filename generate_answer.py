"""
TaxHub demo — generation layer.

Takes the chunks retrieved by retrieval.py and calls Gemini to produce a
grounded, cited answer. Requires GEMINI_API_KEY in the environment.

Key design choice, based on what the retrieval test run actually showed:
refusal is enforced by the model reading the retrieved chunks and judging
relevance, NOT by a similarity-score cutoff in the retrieval layer. Test 3
(the out-of-scope question) came back with retrieval scores similar to or
higher than genuinely relevant questions, because this is a small, topically
narrow corpus — a hard threshold isn't reliable here. The instructions below
make that judgment call explicit and put it in the right place.

Usage:
    pip install google-genai python-dotenv --break-system-packages
    cp .env.example .env        # then edit .env and paste your real key in — never commit .env
    python3 generate_answer.py
"""

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from retrieval import build_index, retrieve

load_dotenv()  # reads .env if present; does nothing if it isn't — safe either way

SYSTEM_PROMPT = """You are TaxHub, an internal assistant for a German tax advisory practice \
(Steuerberater). You answer staff questions using ONLY the source material provided to you \
below — never your own general knowledge of German tax law, which may be outdated.

Rules, in order of importance:
1. Before answering, check whether the retrieved source chunks actually discuss the topic \
the question is asking about. If the chunks concern a different subject entirely — for \
example, the question is about Erbschaftsteuer or any area outside §19/§19a UStG, but \
every retrieved chunk concerns Kleinunternehmerregelung VAT exemptions — the correct \
response is: "This topic is not covered by the current knowledge base." Do not supplement \
with general knowledge even if you believe you know the answer. If the sources do not \
contain enough information to answer the question confidently, apply the same rule: state \
that this isn't covered by the current knowledge base, and do not attempt an answer from \
general knowledge. The whole point of this tool is that answers are traceable to a source \
the firm has verified, not to your training data.
2. Every substantive claim in your answer must be attributable to one of the provided \
source chunks. Cite the source document and section heading for each claim.
3. Where a rule has multiple conditions that must ALL hold (e.g. "and" not "or"), check \
each one against what's actually retrieved and what the question actually tells you. If \
information relevant to one of those conditions is missing from the question, say so \
explicitly rather than concluding the rule is satisfied based on only the conditions you \
do have data for. A right answer on one condition and silence on another is not a complete \
answer.
4. If the sources contain historical/superseded figures alongside current ones, be explicit \
about which is current and flag the superseded ones if relevant to avoid the reader confusing them.
5. If the question requires information you don't have (e.g. a client's specific revenue \
figures), say what's missing rather than guessing — and note that a draft response should \
ask the client for it.
6. Never present your answer as final professional tax advice. Frame it as source-grounded \
information for staff review before anything goes to a client.
"""


def evaluate_test2(answer_text: str, retrieved_chunks: list) -> dict:
    """
    Structured regression check for Test 2 — three independent criteria, not a
    single pass/fail on the prose. This is a heuristic text check (keyword /
    pattern matching), not a semantic judge — it will catch obvious misses
    reliably but can be fooled by unusual phrasing. Treat it as a fast
    regression signal, not a substitute for actually reading the answer.
    """
    text = answer_text.lower().replace(".", "").replace(",", "")

    # Criterion 1: states the current threshold is 100,000, not 50,000
    mentions_100k = "100000" in text or "100 000" in answer_text or "€100,000" in answer_text
    # Weak signal that it's treating 50k as THE answer rather than rejecting it
    treats_50k_as_current = (
        "50000" in text
        and "100000" not in text
        and "not the current" not in answer_text.lower()
        and "no longer" not in answer_text.lower()
    )
    criterion_1_current_threshold = mentions_100k and not treats_50k_as_current

    # Criterion 2: explicitly flags 50k as obsolete/historical/not current
    historical_flags = ["not the current", "superseded", "no longer", "outdated",
                         "old", "historical", "previous", "pre-2025", "prior to 2025"]
    criterion_2_historical_distinction = any(flag in answer_text.lower() for flag in historical_flags)

    # Criterion 3: does NOT conclude eligibility is confirmed — should instead
    # flag the missing prior-year figure. We check for both a premature
    # confirmation pattern AND a missing-information acknowledgment.
    premature_confirmation = any(p in answer_text.lower() for p in [
        "still eligible", "remains eligible", "status is unaffected",
        "unaffected by this", "no change to their status",
    ]) and "25,000" not in answer_text and "prior-year" not in answer_text.lower() and "prior year" not in answer_text.lower()
    acknowledges_missing_condition = (
        "25,000" in answer_text or "25000" in text
    ) and ("prior" in answer_text.lower() or "previous year" in answer_text.lower())
    criterion_3_missing_condition = acknowledges_missing_condition and not premature_confirmation

    all_pass = criterion_1_current_threshold and criterion_2_historical_distinction and criterion_3_missing_condition

    return {
        "current_threshold_correct": criterion_1_current_threshold,
        "historical_distinction_made": criterion_2_historical_distinction,
        "missing_condition_flagged": criterion_3_missing_condition,
        "overall_pass": all_pass,
        "note": "Heuristic text check — read the actual answer below regardless of this result.",
    }


def format_context(results):
    if not results:
        return "NO RELEVANT SOURCES RETRIEVED."
    blocks = []
    for score, chunk in results:
        blocks.append(
            f"[Source: {chunk['source_file']} — \"{chunk['heading']}\" (retrieval score {score:.2f})]\n"
            f"{chunk['text']}"
        )
    return "\n\n---\n\n".join(blocks)


def answer_question(question: str, client, all_chunks, vectorizer, matrix):
    results = retrieve(question, all_chunks, vectorizer, matrix, top_k=4, min_score=0.0)
    context = format_context(results)

    user_message = f"""RETRIEVED SOURCES:

{context}

---

STAFF QUESTION:
{question}

Answer using only the sources above. If they don't sufficiently cover the question, say so."""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=5000,
        ),
    )
    return response.text, results


if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Set GEMINI_API_KEY in your environment before running this.")
        raise SystemExit(1)

    client = genai.Client(api_key=api_key)
    all_chunks, vectorizer, matrix = build_index()

    test_questions = {
        "Test 1 (main case)": "I think I've exceeded the Kleinunternehmerregelung threshold. "
                               "What does this mean and what do you need from me?",
        "Test 2 (old-law trap)": "A client's current-year turnover just crossed 50,000 euros — "
                                  "do they lose their Kleinunternehmer status?",
        "Test 3 (out-of-scope)": "How do German inheritance tax allowances work for a client's second home?",
        "Test 4 (missing info)": "One of my clients asked if she needs to start charging VAT. "
                                  "I don't have her exact revenue numbers in front of me.",
    }

    for label, question in test_questions.items():
        print(f"\n{'='*70}\n{label}\n{question}\n{'-'*70}")
        answer, results = answer_question(question, client, all_chunks, vectorizer, matrix)

        print("RETRIEVED CHUNKS (this is the evidence actually passed to the model —")
        print("inspect this, not just the answer below, before treating a test as passed):")
        if not results:
            print("  (none above threshold)")
        for score, chunk in results:
            print(f"  [{score:.3f}] {chunk['source_file']} — \"{chunk['heading']}\"")

        print("\nFINAL ANSWER:")
        print(answer)
        print("\n^ A correct final answer with wrong or missing retrieved evidence above")
        print("  is a FAIL, not a pass — it means the model answered from general")
        print("  knowledge rather than the corpus, which is exactly what these tests exist to catch.")

        if label.startswith("Test 2"):
            print("\nSTRUCTURED EVALUATION (Test 2 — three independent criteria):")
            eval_result = evaluate_test2(answer, results)
            for k, v in eval_result.items():
                if k == "note":
                    continue
                mark = "PASS" if v else "FAIL"
                print(f"  [{mark}] {k}")
            print(f"  -> {eval_result['note']}")
            if not eval_result["overall_pass"]:
                print("  -> At least one criterion failed. This is the signal to fix the")
                print("     prompt/retrieval BEFORE touching the UI, per the agreed gate.")
