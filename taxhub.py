"""
TaxHub — interactive CLI entrypoint.

Type a staff question, receive:
  1. Retrieved source chunks with scores (the evidence)
  2. The grounded, cited answer from Gemini
  3. A draft client-facing response, if the answer calls for one

Requires GEMINI_API_KEY in the environment or a .env file.
Run: python3 taxhub.py
"""

import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types
from retrieval import build_index, retrieve
from generate_answer import format_context, SYSTEM_PROMPT

load_dotenv()

DIVIDER = "─" * 70


def print_retrieved_chunks(results):
    if not results:
        print("  (no chunks retrieved above threshold)")
        return
    for score, chunk in results:
        print(f"  [{score:.3f}]  {chunk['source_file']}  —  \"{chunk['heading']}\"")
        preview = chunk["text"].replace("\n", " ")[:200]
        print(f"           {preview}...")


def answer_question(question: str, client, all_chunks, vectorizer, matrix):
    results = retrieve(question, all_chunks, vectorizer, matrix, top_k=4, min_score=0.0)
    context = format_context(results)

    user_message = f"""RETRIEVED SOURCES:

{context}

---

STAFF QUESTION:
{question}

Answer using only the sources above. If they don't sufficiently cover the question, say so.
If the answer calls for a draft response to send to the client, include it in a clearly
labelled section at the end: "--- DRAFT CLIENT RESPONSE ---"."""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=5000,
        ),
    )
    return response.text, results


def run():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set.")
        print("Copy .env.example to .env and add your key, or export it in your shell.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    print("Building retrieval index...")
    all_chunks, vectorizer, matrix = build_index()
    print(f"Ready. Indexed {len(all_chunks)} chunks.\n")
    print('Type your staff question and press Enter. Type "exit" or Ctrl-C to quit.')

    while True:
        print(f"\n{DIVIDER}")
        try:
            question = input("Question: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            print("Exiting.")
            break

        print(f"\n{DIVIDER}")
        print("RETRIEVED EVIDENCE (what is actually passed to the model):")
        try:
            answer, results = answer_question(question, client, all_chunks, vectorizer, matrix)
        except Exception as exc:
            print(f"\nGeneration failed: {exc}")
            print("No answer produced. Check your GEMINI_API_KEY and account status.")
            continue
        print_retrieved_chunks(results)

        print(f"\n{DIVIDER}")
        print("ANSWER:\n")
        print(answer)


if __name__ == "__main__":
    run()
