"""
TaxHub demo — retrieval layer.

This is the real, runnable half of the RAG pipeline: it chunks the two source
documents by heading, builds a TF-IDF index over the chunks, and retrieves the
top-k most relevant chunks for a given question with a similarity score.

No API key is required for this half — it's pure retrieval, and it's the part
Test 2 is actually stress-testing (does the system surface the CURRENT €100,000
rule, or does it get pulled toward the superseded €50,000/€22,000/€17,500
figures that are also present in the corpus by design).

The generation half (calling Gemini with the retrieved chunks to produce a
cited answer) is in generate_answer.py, and needs a GEMINI_API_KEY set in
the environment where it runs — that's not available in this sandbox, so it's
provided as a ready-to-run script rather than executed here.
"""

import re
import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DOCS_DIR = Path(__file__).parent
SOURCE_FILES = [
    "01_regulatory_kleinunternehmerregelung.md",
    "02_firm_checklist_kleinunternehmer.md",
]


def chunk_markdown(path: Path):
    """Split a markdown file into chunks by ## headings. Each chunk keeps its
    heading as context, which also becomes the citation label shown to the
    user — real chunking, not a fixed-size sliding window, because for these
    documents the headings are the natural retrieval unit."""
    text = path.read_text(encoding="utf-8")
    # Split on level-2 headings, keep the heading with its body
    parts = re.split(r"\n(?=## )", text)
    chunks = []
    for part in parts:
        part = part.strip()
        if not part or part.startswith("# "):  # skip the H1 title block alone
            if "\n## " not in part:
                continue
        heading_match = re.match(r"##\s+(.+)", part)
        heading = heading_match.group(1).strip() if heading_match else path.stem
        chunks.append({
            "source_file": path.name,
            "heading": heading,
            "text": part,
        })
    return chunks


def build_index():
    all_chunks = []
    for fname in SOURCE_FILES:
        all_chunks.extend(chunk_markdown(DOCS_DIR / fname))

    corpus = [c["text"] for c in all_chunks]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(corpus)
    return all_chunks, vectorizer, matrix


def retrieve(question: str, all_chunks, vectorizer, matrix, top_k=4, min_score=0.05):
    q_vec = vectorizer.transform([question])
    scores = cosine_similarity(q_vec, matrix).flatten()
    ranked = sorted(zip(scores, all_chunks), key=lambda x: x[0], reverse=True)
    results = [(score, chunk) for score, chunk in ranked[:top_k] if score >= min_score]
    return results


def run_test(question, all_chunks, vectorizer, matrix, label=""):
    print(f"\n{'='*70}\nQUESTION{(' — ' + label) if label else ''}:\n{question}\n{'-'*70}")
    results = retrieve(question, all_chunks, vectorizer, matrix, top_k=4, min_score=0.0)
    if not results:
        print("NO RESULTS ABOVE THRESHOLD — system should refuse / say it doesn't know.")
        return results
    for score, chunk in results:
        print(f"[score={score:.3f}] {chunk['source_file']} — \"{chunk['heading']}\"")
        preview = chunk["text"].replace("\n", " ")[:160]
        print(f"    {preview}...")
    return results


if __name__ == "__main__":
    all_chunks, vectorizer, matrix = build_index()
    print(f"Indexed {len(all_chunks)} chunks from {len(SOURCE_FILES)} documents.")
    for c in all_chunks:
        print(f"  - {c['source_file']}: {c['heading']}")

    # Test 1 — the main demo case
    run_test(
        "I think I've exceeded the Kleinunternehmerregelung threshold. "
        "What does this mean and what do you need from me?",
        all_chunks, vectorizer, matrix, label="Test 1 (main case)",
    )

    # Test 2 — the old-law trap. This is the one that matters most.
    run_test(
        "A client's current-year turnover just crossed 50,000 euros — "
        "do they lose their Kleinunternehmer status?",
        all_chunks, vectorizer, matrix, label="Test 2 (old-law trap)",
    )

    # Test 3 — out of scope, should retrieve nothing useful
    run_test(
        "How do German inheritance tax allowances work for a client's second home?",
        all_chunks, vectorizer, matrix, label="Test 3 (out-of-scope refusal)",
    )

    # Test 4 — partial information handling
    run_test(
        "One of my clients asked if she needs to start charging VAT. "
        "I don't have her exact revenue numbers in front of me.",
        all_chunks, vectorizer, matrix, label="Test 4 (missing info)",
    )
