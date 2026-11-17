import json
import math
import os
import urllib.request
from pathlib import Path
import anthropic
import time
from urllib.error import HTTPError

client = anthropic.Anthropic()
MODEL = "claude-sonnet-5-5"
EMBED_MODEL = "voyage-4-lite"
CACHE = Path("embeddings.json")
MIN_SCORE = 0.35
def load_chunks(path):
    text = Path(path).read_text(encoding="utf-8")
    return [c.strip() for c in text.split("\n\n") if c.strip()]

def embed(texts, input_type):
    body = json.dumps({"input": texts, "model": EMBED_MODEL,
                       "input_type": input_type}).encode("utf-8")
    request = urllib.request.Request(
        "https://api.voyageai.com/v1/embeddings", data=body,
        headers={"Authorization": f"Bearer {os.environ['VOYAGE_API_KEY']}",
                 "Content-Type": "application/json"},
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request) as response:
                data = json.load(response)
            break
        except HTTPError as error:
            if error.code != 429 or attempt == 4:
                raise
            wait = 20 * (attempt + 1)
            print(f"   (rate limited, waiting {wait} seconds...)")
            time.sleep(wait)
    items = sorted(data["data"], key=lambda d: d["index"])
    return [item["embedding"] for item in items]

def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))

def load_index(chunks):
    if CACHE.exists():
        saved = json.loads(CACHE.read_text(encoding="utf-8"))
        if saved["chunks"] == chunks:
            return saved["vectors"]
    print("Embedding the handbook (first run only)...")
    vectors = embed(chunks, "document")
    CACHE.write_text(json.dumps({"chunks": chunks, "vectors": vectors}), encoding="utf-8")
    return vectors

def retrieve(question, vectors, k=3):
    q = embed([question], "query")[0]
    scored = sorted(((cosine(q, v), i) for i, v in enumerate(vectors)), reverse=True)
    return [(score, i) for score, i in scored[:k] if score >= MIN_SCORE]

def answer(question, chunks, vectors):
    top = retrieve(question, vectors)
    if not top:
        return top, "I don't know. The handbook doesn't cover that."
    sources = "\n\n".join(f"[{i}] {chunks[i]}" for score, i in top)
    prompt = f"""Answer the question using only the sources below.
Put the source number in brackets, like [2], after each fact you use.
If the sources don't contain the answer, say the handbook doesn't cover it. Don't describe what the sources do cover.

Sources:
{sources}

Question: {question}"""
    message = client.messages.create(
        model=MODEL, max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    return top, "".join(b.text for b in message.content if b.type == "text")

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