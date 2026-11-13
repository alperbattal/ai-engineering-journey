import csv
from datetime import datetime
import anthropic

client = anthropic.Anthropic()
SYSTEM_PROMPT = open("agent_prompt.txt", encoding="utf-8").read()

def ask(question):
    message = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": question}],
    )
    return "".join(b.text for b in message.content if b.type == "text")

def load_tests(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def save_results(results):
    filename = f"results_{datetime.now():%Y-%m-%d_%H%M}.csv"
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["question", "expected", "answer", "result"])
        writer.writeheader()
        writer.writerows(results)
    return filename

tests = load_tests("agent_tests.csv")
results = []
passed = 0

for test in tests:
    answer = ask(test["question"])
    expected = test["expected"].strip().strip('"')
    if expected.lower() in answer.lower():
        result = "PASS"
        passed += 1
    else:
        result = "FAIL"
    print(f"{result}: {test['question']}")
    results.append({"question": test["question"], "expected": expected,
                    "answer": answer, "result": result})

filename = save_results(results)
print(f"\nScore: {passed}/{len(tests)}")
print(f"Report saved to {filename}")