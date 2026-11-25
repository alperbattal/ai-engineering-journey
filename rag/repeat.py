import json
import os
import urllib.parse
import urllib.request
from rag_semantic import load_chunks, load_index, answer

URL = os.environ.get("HANDBOOK_URL")       # set = test the cloud, not set = test locally
TOKEN = os.environ.get("HANDBOOK_TOKEN")
print("Testing:", "CLOUD" if URL else "LOCAL")
chunks = load_chunks("handbook.txt")
vectors = load_index(chunks)

def ask(question):
    if URL:
        query = urllib.parse.urlencode({"q": question, "token": TOKEN})
        with urllib.request.urlopen(f"{URL}?{query}", timeout=150) as response:
            return json.load(response)["answer"]
    top, text = answer(question, chunks, vectors)   # local version, with the new prompt
    return text

QUESTION = "Am I allowed to take the truck home on weekends?"
RUNS = 5

not_covered = 0   # how many times the writer said the handbook doesn't cover it

for run in range(1, RUNS + 1):
    answer_text = ask(QUESTION)                     # cloud or local, decided inside ask()
    lower = answer_text.lower()

    # Check both spellings: "doesn't cover" and "does not cover"
    said_not_covered = "doesn't cover" in lower or "does not cover" in lower
    not_covered += said_not_covered

    label = "NOT COVERED" if said_not_covered else "ANSWERED   "
    print(f"Run {run}: {label} -> {answer_text}")

print(f"\nSaid 'not covered' in {not_covered} of {RUNS} runs")