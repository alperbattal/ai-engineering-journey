import csv
import sys
from datetime import datetime
from pathlib import Path
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-5-5"

agent = sys.argv[1] if len(sys.argv) > 1 else "brightbike"
folder = Path("agents") / agent
RULES = (folder / "prompt.txt").read_text(encoding="utf-8")
FACTS = (folder / "facts.txt").read_text(encoding="utf-8")
SYSTEM_PROMPT = RULES + "\n\nBusiness information:\n" + FACTS

def get_text(message):
    return "".join(b.text for b in message.content if b.type == "text")

def ask(question):
    message = client.messages.create(
        model=MODEL, max_tokens=1000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": question}],
    )
    return get_text(message)

def judge(question, expected, answer):
    prompt = f"""You are a strict grader checking a customer support agent.

The only true facts about the business:
{FACTS}

Customer question: {question}
Key fact the answer must contain: {expected}
Agent's answer: {answer}

Grade PASS only if the answer contains the key fact AND invents nothing
(no made-up prices, hours, products or policies). Otherwise grade FAIL.
Reply with PASS or FAIL on the first line, then one short sentence why."""
    message = client.messages.create(
        model=MODEL, max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = get_text(message).strip()
    verdict = "PASS" if text.upper().startswith("PASS") else "FAIL"
    return verdict, text

def load_tests(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def save_results(results):
    filename = folder / f"results_{datetime.now():%Y-%m-%d_%H%M}.csv"
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    return filename

tests = load_tests(folder / "tests.csv")
results = []
passed = 0

print(f"Testing agent: {agent} ({len(tests)} tests)\n")
for test in tests:
    expected = test["expected"].strip().strip('"')
    answer = ask(test["question"])
    keyword = "PASS" if expected.lower() in answer.lower() else "FAIL"
    verdict, reason = judge(test["question"], expected, answer)
    if verdict == "PASS":
        passed += 1
    print(f"keyword {keyword} | judge {verdict}: {test['question']}")
    results.append({"question": test["question"], "expected": expected,
                    "answer": answer, "keyword": keyword,
                    "judge": verdict, "judge_reason": reason})

filename = save_results(results)
print(f"\nJudge score: {passed}/{len(tests)}")
print(f"Report saved to {filename}")