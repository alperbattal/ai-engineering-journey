import csv
from pathlib import Path
from rag_semantic import load_chunks, load_index, answer, ask_claude
import sys
from chunking import chunk_words
import os                 # read settings from environment variables
import json               # turn the cloud's JSON reply into a dict
import urllib.request     # call the cloud web address
import urllib.parse       # build a safe web address from the question and token

HANDBOOK = Path("handbook.txt").read_text(encoding="utf-8")

def judge(question, expected, reply):
    prompt = f"""You are a strict grader checking an assistant that answers from a handbook.

The full handbook (the only truth):
{HANDBOOK}

Question: {question}
Key fact the answer must contain: {expected}
Assistant's answer: {reply}

Ignore source numbers in brackets like [3]; they refer to search results, not the handbook.
Grade PASS only if the answer contains the key fact AND invents nothing that
is not in the handbook. Otherwise grade FAIL.
Reply with PASS or FAIL on the first line, then one short sentence why."""
    text = ask_claude(prompt).strip()       # one line now, thanks to the helper
    return ("PASS" if text.upper().startswith("PASS") else "FAIL"), text


CLOUD_URL = os.environ.get("HANDBOOK_URL")       # your Function URL, if set
CLOUD_TOKEN = os.environ.get("HANDBOOK_TOKEN")   # your access token, if set

def answer_cloud(question):
    # urlencode turns spaces, "?" and other characters into a web-safe format,
    # e.g. "Can I bring my dog?" -> "Can+I+bring+my+dog%3F"
    query = urllib.parse.urlencode({"q": question, "token": CLOUD_TOKEN})

    # Call your Lambda. timeout=150 gives it longer than its own 2-minute limit.
    with urllib.request.urlopen(f"{CLOUD_URL}?{query}", timeout=150) as response:
        data = json.load(response)                # JSON reply -> dict

    # Rebuild the same (score, section) list that answer() returns locally,
    # so the rest of the eval doesn't need to change
    top = [(s["score"], s["section"]) for s in data["sources"]]
    return top, data["answer"]

size = int(sys.argv[2]) if len(sys.argv) > 2 else None

if size:
    text = Path("handbook.txt").read_text(encoding="utf-8")
    text = " ".join(text.split())
    chunks = chunk_words(text, size, size // 4)
else:
    chunks = load_chunks("handbook.txt")

print(f"Using {len(chunks)} chunks")

vectors = load_index(chunks)

test_file = sys.argv[1] if len(sys.argv) > 1 else "rag_tests.csv"
with open(test_file, newline="", encoding="utf-8-sig") as f:
    tests = list(csv.DictReader(f))

retrieval_ok_count = 0
retrieval_total = 0
judge_pass_count = 0

for t in tests:
    if CLOUD_URL:
        top, reply = answer_cloud(t["question"])              # ask the AWS version
    else:
        top, reply = answer(t["question"], chunks, vectors)   # ask the laptop version
    found = [i for score, i in top]
    verdict, reason = judge(t["question"], t["expected"], reply)
    judge_pass_count += verdict == "PASS"

    if t["chunk"] == "none":
        status = "N/A "
    else:
        fact = t["expected"].lower()
        retrieval_ok = any(fact in chunks[i].lower() for i in found)
        retrieval_total += 1
        retrieval_ok_count += retrieval_ok
        status = "OK  " if retrieval_ok else "MISS"

    print(f"retrieval {status} | judge {verdict}: {t['question']}  (found {found})")
    if verdict == "FAIL":
        print("   why:", reason)

print(f"\nRetrieval: {retrieval_ok_count}/{retrieval_total}  (questions the handbook answers)")
print(f"Answers:   {judge_pass_count}/{len(tests)}  (all questions)")