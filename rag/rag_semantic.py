import json                          # convert between Python dicts and JSON text
import math                          # square roots for cosine similarity
import os                            # read API keys from environment variables
import time                          # wait between retries
import urllib.request                # Python's built-in way to call web APIs
from urllib.error import HTTPError   # the error raised when an API says no
from pathlib import Path             # read and write files

MODEL = "claude-sonnet-5-5"          # Claude model for answers
EMBED_MODEL = "voyage-4-lite"        # Voyage model for embeddings
CACHE = Path("embeddings.json")      # where the handbook's embeddings are saved
MIN_SCORE = 0.35                     # weaker matches than this are ignored


def post_json(url, payload, headers):
    # Send a JSON request to an API and return its JSON reply.
    # Used for BOTH Voyage and Claude, so the retry logic lives in one place.
    body = json.dumps(payload).encode("utf-8")      # dict -> JSON text -> bytes
    all_headers = dict(headers)                     # copy the headers we were given
    all_headers["Content-Type"] = "application/json"  # tell the API we're sending JSON
    request = urllib.request.Request(url, data=body, headers=all_headers)

    for attempt in range(5):
        try:
            with urllib.request.urlopen(request) as response:
                return json.load(response)          # success: JSON reply -> dict
        except HTTPError as error:
            # 429 = rate limited, 529 = Claude temporarily overloaded: worth retrying.
            # Anything else (like a wrong key) won't fix itself, so raise it now.
            if error.code not in (429, 529) or attempt == 4:
                raise
            wait = 20 * (attempt + 1)               # wait longer each time (backoff)
            print(f"   (busy or rate limited, waiting {wait} seconds...)")
            time.sleep(wait)


def ask_claude(prompt, max_tokens=1000):
    # Call Claude directly: the same request the anthropic package used to send for us
    data = post_json(
        "https://api.anthropic.com/v1/messages",            # Claude's web address
        {
            "model": MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
        {
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],   # your key, from the environment
            "anthropic-version": "2023-06-01",              # which version of the API format we speak
        },
    )
    # The reply's "content" is a list of blocks (now plain dicts, not objects).
    # Keep only the text blocks, skipping any thinking blocks.
    return "".join(block["text"] for block in data["content"] if block["type"] == "text")


def load_chunks(path):
    text = Path(path).read_text(encoding="utf-8")
    return [c.strip() for c in text.split("\n\n") if c.strip()]   # one chunk per paragraph


def embed(texts, input_type):
    # Same Voyage call as before, now using the shared post_json helper
    data = post_json(
        "https://api.voyageai.com/v1/embeddings",
        {"input": texts, "model": EMBED_MODEL, "input_type": input_type},
        {"Authorization": f"Bearer {os.environ['VOYAGE_API_KEY']}"},
    )
    items = sorted(data["data"], key=lambda d: d["index"])   # keep the original order
    return [item["embedding"] for item in items]


def cosine(a, b):
    # How similar two embeddings are: close to 1 = similar meaning
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def load_index(chunks):
    # Reuse saved embeddings if the chunks haven't changed; otherwise embed and save
    if CACHE.exists():
        saved = json.loads(CACHE.read_text(encoding="utf-8"))
        if saved["chunks"] == chunks:
            return saved["vectors"]
    print("Embedding the handbook (first run only)...")
    vectors = embed(chunks, "document")
    CACHE.write_text(json.dumps({"chunks": chunks, "vectors": vectors}), encoding="utf-8")
    return vectors


def retrieve(question, vectors, k=3):
    # The librarian: score every chunk, keep the top k that pass the minimum score
    q = embed([question], "query")[0]
    scored = sorted(((cosine(q, v), i) for i, v in enumerate(vectors)), reverse=True)
    return [(score, i) for score, i in scored[:k] if score >= MIN_SCORE]


def answer(question, chunks, vectors):
    # The writer: answer only from the retrieved chunks, with citations
    top = retrieve(question, vectors)
    if not top:
        return top, "I don't know. The handbook doesn't cover that."

    sources = "\n\n".join(f"[{i}] {chunks[i]}" for score, i in top)
    prompt = f"""Answer the question using only the sources below.
Put the source number in brackets, like [2], after each fact you use.
If the sources don't contain the answer, say the handbook doesn't cover it. Don't describe what the sources do cover.
Don't mention that sources are cut off or incomplete.

Sources:
{sources}

Question: {question}"""
    return top, ask_claude(prompt)


if __name__ == "__main__":
    chunks = load_chunks("handbook.txt")
    vectors = load_index(chunks)
    print(f"Loaded {len(chunks)} chunks. Ask a question (or type 'quit').")

    while True:
        question = input("\nYou: ")
        if question.lower() == "quit":
            break
        top, text = answer(question, chunks, vectors)
        print("(retrieved: " + ", ".join(f"[{i}] {score:.2f}" for score, i in top) + ")")
        print(text)