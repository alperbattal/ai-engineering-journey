import csv
import sys
from datetime import datetime
from pathlib import Path
import anthropic
import html
import webbrowser

client = anthropic.Anthropic()
MODEL = "claude-sonnet-5-5"
RUNS = 3
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

STYLE = """
body { font-family: Segoe UI, Arial, sans-serif; margin: 32px; color: #1f2933; background: #fafaf7; }
h1 { margin-bottom: 4px; }
.sub { color: #616e7c; margin-top: 0; }
.cards { display: flex; gap: 16px; margin: 24px 0; }
.card { background: white; border: 1px solid #e4e7eb; border-radius: 12px; padding: 16px 20px; min-width: 140px; }
.card b { display: block; font-size: 28px; }
.bar { height: 14px; background: #f8d7da; border-radius: 7px; overflow: hidden; margin: 8px 0 24px; }
.bar div { height: 100%; background: #2f9e6e; }
table { border-collapse: collapse; width: 100%; background: white; }
th, td { border: 1px solid #e4e7eb; padding: 8px 10px; text-align: left; vertical-align: top; white-space: pre-wrap; }
th { background: #f0f2f5; }
td.pass { color: #1b7a50; font-weight: bold; }
td.fail { color: #b42318; font-weight: bold; }
tr.disagree { background: #fff6db; }
"""

def save_html_report(results, passed, csv_file):
    total = len(results)
    pct = round(passed / total * 100)
    disagree = sum(1 for r in results if r["keyword"] != r["judge"])

    rows = ""
    for r in results:
        row_class = "disagree" if r["keyword"] != r["judge"] else ""
        rows += f"""<tr class="{row_class}">
<td>{html.escape(r['question'])} (run {r['run']})</td>
<td>{html.escape(r['expected'])}</td>
<td>{html.escape(r['answer'])}</td>
<td class="{r['keyword'].lower()}">{r['keyword']}</td>
<td class="{r['judge'].lower()}">{r['judge']}</td>
<td>{html.escape(r['judge_reason'])}</td>
</tr>"""

    page = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Health Check: {agent}</title>
<style>{STYLE}</style></head><body>
<h1>Agent Health Check: {agent}</h1>
<p class="sub">Run {datetime.now():%B %d, %Y at %I:%M %p}</p>
<div class="cards">
  <div class="card">Judge score<b>{passed}/{total}</b></div>
  <div class="card">Pass rate<b>{pct}%</b></div>
  <div class="card">Graders disagree<b>{disagree}</b></div>
</div>
<div class="bar"><div style="width:{pct}%"></div></div>
<p class="sub">Highlighted rows: the keyword check and the judge disagree. Review these by hand.</p>
<table>
<tr><th>Question</th><th>Expected</th><th>Answer</th><th>Keyword</th><th>Judge</th><th>Judge reason</th></tr>
{rows}
</table></body></html>"""

    report = Path(str(csv_file).replace(".csv", ".html"))
    report.write_text(page, encoding="utf-8")
    webbrowser.open(report.resolve().as_uri())
    return report
tests = load_tests(folder / "tests.csv")
results = []
passed = 0

print(f"Testing agent: {agent} ({len(tests)} tests)\n")
for test in tests:
    expected = test["expected"].strip().strip('"')
    test_passes = 0
    for run in range(1, RUNS + 1):
        answer = ask(test["question"])
        keyword = "PASS" if expected.lower() in answer.lower() else "FAIL"
        verdict, reason = judge(test["question"], expected, answer)
        if verdict == "PASS":
            passed += 1
            test_passes += 1
        results.append({"run": run, "question": test["question"], "expected": expected,
                        "answer": answer, "keyword": keyword,
                        "judge": verdict, "judge_reason": reason})
    flaky = "   <-- flaky" if 0 < test_passes < RUNS else ""
    print(f"{test_passes}/{RUNS} judge passes: {test['question']}{flaky}")

filename = save_results(results)
print(f"\nJudge score: {passed}/{len(results)}")
print(f"Report saved to {filename}")

report = save_html_report(results, passed, filename)
print(f"Visual report: {report}")