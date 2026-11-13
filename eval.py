import anthropic
import csv

client = anthropic.Anthropic()

def ask(question):
    message = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": question}
        ]
    )
    return "".join(b.text for b in message.content if b.type == "text")

def load_tests(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

tests = load_tests("tests.csv")

passed = 0
for test in tests:
    answer = ask(test["question"])
    if test["expected"].lower() in answer.lower():
        passed += 1
        print("PASS: ", test["question"])
    else:
        print("FAIL:", test["question"], "| expected:", repr(test["expected"]), "| got:", answer)

print(f"\nScore: {passed}/{len(tests)} tests passed.")

