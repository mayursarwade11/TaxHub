"""
TaxHub — Flask web application.

Serves the browser UI and the /ask endpoint, which runs the full
retrieval → generation pipeline and returns grounded, cited answers.

Retrieval (TF-IDF over the two knowledge documents) runs at startup
and requires no API key.  Generation (Gemini via the Google AI API)
requires GEMINI_API_KEY to be set in the environment.

Three failure states are handled explicitly — see the /ask handler.
"""

import logging
import os

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from generate_answer import SYSTEM_PROMPT, format_context
from retrieval import build_index, retrieve

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
log = logging.getLogger(__name__)

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Startup — build the TF-IDF retrieval index.  No API call is made here.
# ---------------------------------------------------------------------------
log.info("Building retrieval index...")
_chunks, _vectorizer, _matrix = build_index()
log.info("Retrieval index ready: %d chunks indexed.", len(_chunks))

# ---------------------------------------------------------------------------
# API key — read once at startup.  Never logged.  Never sent to the browser.
# ---------------------------------------------------------------------------
_API_KEY = os.environ.get("GEMINI_API_KEY")
_gemini = genai.Client(api_key=_API_KEY) if _API_KEY else None

if _API_KEY:
    log.info("GEMINI_API_KEY is configured.  Generation is available.")
else:
    log.warning(
        "GEMINI_API_KEY is not set.  "
        "Retrieval is operational; generation will return 503."
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    """Health check — does NOT call the Gemini API."""
    return jsonify({
        "status": "ok",
        "chunks_indexed": len(_chunks),
        "api_key_configured": bool(_API_KEY),
    })


@app.route("/ask", methods=["POST"])
def ask():
    """
    POST body (JSON): { "question": "..." }

    Always runs retrieval and returns the retrieved chunks.
    Generation only runs when GEMINI_API_KEY is set.

    Three explicit failure states:
      no_key           — key absent in environment (503)
      invalid_key      — Gemini status UNAUTHENTICATED (401)
      access_denied    — Gemini status PERMISSION_DENIED (403)
      rate_limit       — Gemini status RESOURCE_EXHAUSTED (429)
      api_error        — Gemini ServerError or unrecognised ClientError (502/400)
      connection_error — network failure reaching Gemini (503)
      unexpected       — uncaught exception (500)

    The actual API key is never referenced in any response body.
    """
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error_type": "bad_request", "error": "No question provided."}), 400

    # --- Retrieval: always runs, no API key required. ---
    results = retrieve(question, _chunks, _vectorizer, _matrix, top_k=4, min_score=0.0)
    chunks_out = [
        {
            "source_file": chunk["source_file"],
            "heading": chunk["heading"],
            "score": round(score, 3),
            "preview": " ".join(chunk["text"].split())[:320],
        }
        for score, chunk in results
    ]

    # --- State 1: No API key. ---
    # Retrieval ran and chunks are returned so the evidence panel
    # shows real results.  Generation did not occur — this is stated
    # explicitly, not hidden behind a fallback.
    if not _API_KEY:
        return jsonify({
            "error_type": "no_key",
            "error": (
                "No Gemini API key is configured on this server. "
                "Retrieval ran and source evidence is shown below, "
                "but generation requires GEMINI_API_KEY to be set "
                "in the deployment environment."
            ),
            "chunks": chunks_out,
        }), 503

    context = format_context(results)
    user_message = (
        "RETRIEVED SOURCES:\n\n"
        f"{context}\n\n"
        "---\n\n"
        f"STAFF QUESTION:\n{question}\n\n"
        "Answer using only the sources above. "
        "If they do not sufficiently cover the question, say so plainly.\n"
        "If the answer calls for a draft response to send to the client, "
        "include it in a clearly labelled section at the end: "
        '"--- DRAFT CLIENT RESPONSE ---".'
    )

    try:
        response = _gemini.models.generate_content(
            model="gemini-3.6-flash",
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=5000,
            ),
        )
        full_text = response.text

    # --- State 2: Gemini client-side error (4xx). ---
    # exc.status is the canonical Google API status string.
    # exc.code is the HTTP status integer, used as a secondary guard.
    except genai_errors.ClientError as exc:
        gstatus = getattr(exc, "status", "") or ""
        gcode = getattr(exc, "code", 0) or 0
        log.warning("Gemini client error (status=%r, code=%s): %s", gstatus, gcode, exc)
        if gstatus == "RESOURCE_EXHAUSTED" or gcode == 429:
            return jsonify({
                "error_type": "rate_limit",
                "error": (
                    "The Gemini API quota or rate limit was exceeded. "
                    "Wait a moment and submit the question again."
                ),
                "chunks": chunks_out,
            }), 429
        elif gstatus == "UNAUTHENTICATED" or gcode == 401:
            return jsonify({
                "error_type": "invalid_key",
                "error": (
                    "The configured Gemini API key was rejected (UNAUTHENTICATED). "
                    "Verify the key is correct and active in the deployment environment."
                ),
                "chunks": chunks_out,
            }), 401
        elif gstatus == "PERMISSION_DENIED" or gcode == 403:
            return jsonify({
                "error_type": "access_denied",
                "error": (
                    "The Gemini API denied the request (PERMISSION_DENIED). "
                    "Check your Google AI Studio account and billing status."
                ),
                "chunks": chunks_out,
            }), 403
        else:
            return jsonify({
                "error_type": "api_error",
                "error": (
                    f"The Gemini API returned a client error "
                    f"(status={gstatus!r}, code={gcode}). "
                    "Generation could not be completed."
                ),
                "chunks": chunks_out,
            }), 400

    # --- State 3: Gemini server-side error (5xx). ---
    except genai_errors.ServerError as exc:
        log.warning("Gemini server error: %s", exc)
        return jsonify({
            "error_type": "api_error",
            "error": (
                "The Gemini API returned a server error. "
                "Generation could not be completed. Try again shortly."
            ),
            "chunks": chunks_out,
        }), 502

    # --- State 4: Network / connection failure. ---
    # ClientError and ServerError are only raised after the API is reached.
    # Failures before that (DNS, TCP, TLS) surface as OSError subclasses.
    except OSError as exc:
        log.warning("Network error reaching Gemini API: %s", exc)
        return jsonify({
            "error_type": "connection_error",
            "error": (
                "Could not reach the Gemini API. "
                "Check server network connectivity and try again."
            ),
            "chunks": chunks_out,
        }), 503

    except Exception:
        log.exception("Unexpected error during generation.")
        return jsonify({
            "error_type": "unexpected",
            "error": "An unexpected error occurred during generation. Check server logs.",
            "chunks": chunks_out,
        }), 500

    # --- Success: split answer body from optional draft. ---
    marker = "--- DRAFT CLIENT RESPONSE ---"
    answer_text = full_text
    draft_text = None
    if marker in full_text:
        parts = full_text.split(marker, 1)
        answer_text = parts[0].strip()
        draft_text = parts[1].strip()

    return jsonify({
        "chunks": chunks_out,
        "answer": answer_text,
        "draft": draft_text,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
