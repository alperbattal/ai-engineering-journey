import anthropic

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

tests = [
    {"question": "What is the capital of France?", "expected": "Paris"},
    {"question": "What is the largest planet in our solar system?", "expected": "Jupiter"},
    {"question": "Who wrote 'Pride and Prejudice'?", "expected": "Jane Austen"},
    {"question": "What is the boiling point of water in Celsius?", "expected": "100"},
    {"question": "What is the speed of light in km per second?", "expected": "299,792"},
]

passed = 0
for test in tests:
    answer = ask(test["question"])
    if test["expected"].lower() in answer.lower():
        passed += 1
        print("PASS: ", test["question"])
    else:
        print("FAIL: ", test["question"], "->", answer)

print(f"\nScore: {passed}/{len(tests)} tests passed.")