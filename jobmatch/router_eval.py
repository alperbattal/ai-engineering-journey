# Read CSV files
import csv

# Borrow the router from match.py
from match import classify

RUNS = 3   # ask the router each question this many times

# Load the test questions: each row is {"question": ..., "expected": ...}
with open("router_tests.csv", newline="", encoding="utf-8-sig") as f:
    tests = list(csv.DictReader(f))

total = 0            # every single router decision (11 questions x 3 runs)
correct = 0          # decisions that matched the expected route
harmful = 0          # expected compare, got lookup: a candidate could be skipped
safe = 0             # expected lookup, got compare: just costs a bit more
flaky_questions = 0  # questions where the 3 runs didn't all agree

for t in tests:
    answers = []                         # this question's 3 answers
    for run in range(RUNS):
        got = classify(t["question"])    # ask the router once
        answers.append(got)
        total += 1

        if got == t["expected"]:
            correct += 1                 # right route
        elif t["expected"] == "compare":
            harmful += 1                 # should compare, but got lookup
        else:
            safe += 1                    # should look up, but got compare

    # set() keeps only the unique values: {"lookup"} if all 3 agreed,
    # {"lookup", "compare"} if they didn't. More than 1 unique value = flaky.
    flaky = len(set(answers)) > 1
    flaky_questions += flaky

    note = "   <-- flaky" if flaky else ""
    print(f"expected {t['expected']:<7} got {', '.join(answers):<25} {t['question']}{note}")

print(f"\nCorrect:          {correct}/{total}")
print(f"Harmful misses:   {harmful}   (compare sent to lookup)")
print(f"Safe misses:      {safe}   (lookup sent to compare)")
print(f"Flaky questions:  {flaky_questions}/{len(tests)}")