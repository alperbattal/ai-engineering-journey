import csv
from pathlib import Path
from rag_semantic import load_chunks, load_index, answer, client, MODEL
import sys

HANDBOOK = Path("handbook.txt").read_text(encoding="utf-8")

def judge(question, expected, reply):
    prompt = f"""You are a strict grader checking an assistant that answers from a handbook.

The full handbook (the only truth):
{HANDBOOK}

Question: {question}
Key fact the answer must contain: {expected}
Assistant's answer: {reply}

Grade PASS only if the answer contains the key fact AND invents nothing that
is not in the handbook. Otherwise grade FAIL.
Reply with PASS or FAIL on the first line, then one short sentence why."""
    message = client.messages.create(
        model=MODEL, max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in message.content if b.type == "text").strip()
    return ("PASS" if text.upper().startswith("PASS") else "FAIL"), text

chunks = load_chunks("handbook.txt")
vectors = load_index(chunks)

test_file = sys.argv[1] if len(sys.argv) > 1 else "rag_tests.csv"
with open(test_file, newline="", encoding="utf-8-sig") as f:
    tests = list(csv.DictReader(f))

retrieval_ok_count = 0
judge_pass_count = 0

for t in tests:
    top, reply = answer(t["question"], chunks, vectors)
    found = [i for score, i in top]
    if t["chunk"] == "none":
        retrieval_ok = not found
    else:
        needed = [int(c) for c in t["chunk"].split(";")]
        retrieval_ok = all(c in found for c in needed)
    verdict, reason = judge(t["question"], t["expected"], reply)

    retrieval_ok_count += retrieval_ok
    judge_pass_count += verdict == "PASS"
    status = "OK  " if retrieval_ok else "MISS"
    print(f"retrieval {status} | judge {verdict}: {t['question']}  (found {found})")
    if verdict == "FAIL":
        print("   why:", reason)