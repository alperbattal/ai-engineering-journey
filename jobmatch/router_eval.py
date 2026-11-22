# Read CSV files
import csv

# Borrow the router from match.py (works now that the chat loop
# only runs when match.py is started directly)
from match import classify

# Load the test questions: each row becomes {"question": ..., "expected": ...}
with open("router_tests.csv", newline="", encoding="utf-8-sig") as f:
    tests = list(csv.DictReader(f))

correct = 0   # how many the router got right

for t in tests:
    got = classify(t["question"])        # ask the router: "lookup" or "compare"
    ok = got == t["expected"]            # True if it matches the right answer
    correct += ok                        # True counts as 1, False as 0

    mark = "OK  " if ok else "MISS"
    # :<7 pads the word to 7 characters, so the columns line up neatly
    print(f"{mark} expected {t['expected']:<7} got {got:<7} {t['question']}")

print(f"\nRouter accuracy: {correct}/{len(tests)}")