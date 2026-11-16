import re
from pathlib import Path
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-5-5"
STOP = {"a", "an", "the", "is", "are", "what", "how", "do", "i", "me", "to",
        "of", "in", "for", "my", "on", "can", "much", "does", "it", "and",
        "or", "at", "be", "when", "who", "with"}

def load_chunks(path):
    text = Path(path).read_text(encoding="utf-8")
    return [c.strip() for c in text.split("\n\n") if c.strip()]

def words(text):
    return set(re.findall(r"[a-z0-9$,]+", text.lower()))

def retrieve(question, chunks, k=3):
    q_words = words(question) - STOP
    scored = []
    for i, chunk in enumerate(chunks):
        score = len(q_words & words(chunk))
        scored.append((score, i))
    scored.sort(reverse=True)
    return [i for score, i in scored[:k] if score > 0]

def answer(question, chunks):
    ids = retrieve(question, chunks)
    sources = "\n\n".join(f"[{i}] {chunks[i]}" for i in ids)
    prompt = f"""Answer the question using only the sources below.
Put the source number in brackets, like [2], after each fact you use.
If the sources don't contain the answer, say you don't know.

Sources:
{sources}

Question: {question}"""
    message = client.messages.create(
        model=MODEL, max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    return ids, "".join(b.text for b in message.content if b.type == "text")

chunks = load_chunks("handbook.txt")
print(f"Loaded {len(chunks)} chunks. Ask a question (or type 'quit').")

while True:
    question = input("\nYou: ")
    if question.lower() == "quit":
        break
    ids, text = answer(question, chunks)
    print(f"(retrieved chunks: {ids})")
    print(text)