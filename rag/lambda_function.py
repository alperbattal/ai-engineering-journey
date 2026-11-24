import json   # turn dicts into JSON text
import os     # read settings (API keys, token) from environment variables

# Lambda runs your code from a folder of its own choosing. Move into the
# folder this file is in, so handbook.txt and embeddings.json are found.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Your own RAG functions (no installed packages needed anymore)
from rag_semantic import load_chunks, load_index, answer

# Load the handbook and its saved embeddings once, when Lambda starts up
chunks = load_chunks("handbook.txt")
vectors = load_index(chunks)


def respond(status, data):
    # The shape Lambda expects back: a status code, headers, and the body as text
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(data),
    }


def lambda_handler(event, context):
    # AWS calls this function for every request.
    # "event" holds the request; the ?q=... and ?token=... parts are in here.
    params = event.get("queryStringParameters") or {}   # empty dict if there are none

    # The password check. If ACCESS_TOKEN isn't set, refuse EVERYONE.
    # This is called "failing closed": a missing setting never means "open to all."
    expected = os.environ.get("ACCESS_TOKEN")
    if not expected or params.get("token") != expected:
        return respond(401, {"error": "Missing or wrong token"})   # 401 = not allowed

    question = params.get("q", "")
    if not question:
        return respond(400, {"error": "Add a question with ?q=..."})

    top, text = answer(question, chunks, vectors)   # your librarian + writer
    return respond(200, {
        "question": question,
        "answer": text,
        "sources": [{"section": i, "score": round(score, 2)} for score, i in top],
    })