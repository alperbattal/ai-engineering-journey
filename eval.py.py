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

tests =  [
    {"question": "What is the capital of France?", "expected": "The capital of France is Paris."},
    {"question": "What is the largest planet in our solar system?", "expected": "The largest planet in our solar system is Jupiter."},
    {"question": "Who wrote 'Pride and Prejudice'?", "expected": "'Pride and Prejudice' was written by Jane Austen."},
    {"question": "What is the boiling point of water?", "expected": "The boiling point of water is 100 degrees Celsius (212 degrees Fahrenheit) at standard atmospheric pressure."},
    {"question": "What is the speed of light?", "expected": "The speed of light in a vacuum is approximately 299,792 kilometers per second (186,282 miles per second)."}
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