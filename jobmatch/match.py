# Borrow tools from your RAG project:
#   embed      -> turns text into numbers that capture meaning (Voyage)
#   cosine     -> scores how similar two of those number lists are (0 to 1)
#   load_index -> embeds a list of texts once and saves them to embeddings.json
#   client, MODEL -> the Claude connection and model name
from rag_semantic import embed, cosine, load_index, client, MODEL

# Borrow the loader you wrote last night (chunks every file, keeps its file name)
from load_docs import load_documents

# Read all 5 files in the docs folder -> a list of 13 dicts like
# {"source": "resume_daniel_okafor.txt", "text": "Daniel Okafor - AI..."}
pieces = load_documents("docs")

# Pull out just the text of each piece, and embed them all.
# vectors[0] is the meaning of pieces[0], vectors[1] of pieces[1], and so on.
vectors = load_index([p["text"] for p in pieces])


def search(question, k=5):
    # Turn the question into numbers too, so it can be compared with the pieces
    q = embed([question], "query")[0]

    # Score every piece against the question, then sort best first.
    # Each item is (score, i), where i is the piece's position in the list.
    scored = sorted(((cosine(q, v), i) for i, v in enumerate(vectors)), reverse=True)

    # Keep only the top k (5) pieces
    return scored[:k]
def search_fair(question, per_file=2):
    # Turn the question into numbers, same as before
    q = embed([question], "query")[0]

    # Group every piece's score by the file it came from.
    # by_file will end up looking like:
    # {
    #   "resume_maya_torres.txt":   [(0.38, 7), (0.31, 8), (0.29, 9)],
    #   "resume_daniel_okafor.txt": [(0.49, 4), (0.41, 5), (0.33, 6)],
    #   ...
    # }
    # Each value is a LIST of (score, piece number) for that one file.
    by_file = {}
    for i, v in enumerate(vectors):
        source = pieces[i]["source"]   # which file this piece came from
        score = cosine(q, v)           # how related it is to the question

        # First time we see this file? Start an empty list for it.
        if source not in by_file:
            by_file[source] = []

        # Add this piece's score to its file's list
        by_file[source].append((score, i))

    # Now take the best pieces from EACH file, so no file is left out
    top = []
    for source, scored in by_file.items():   # .items() gives each file name and its list
        scored.sort(reverse=True)             # best pieces of this file first
        top.extend(scored[:per_file])         # keep this file's top 2

    # Sort the combined list best-first, so the printout looks like before
    top.sort(reverse=True)
    return top

def classify(question):
    # Ask Claude what KIND of question this is, before searching anything
    prompt = f"""Classify this question about resumes and job postings.
Reply with exactly one word:
lookup  - the answer is in one or two places (a specific fact, skill or requirement)
compare - needs information from every candidate or job: comparing, ranking,
          choosing, or listing or summarizing all of them
Question: {question}"""

    # A short request: we only need one word back.
    # (Thinking can still use part of this budget, so it isn't tiny.)
    message = client.messages.create(
        model=MODEL, max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )

    # Keep only the text blocks, remove spaces and make it lowercase
    word = "".join(b.text for b in message.content if b.type == "text").strip().lower()

    # If Claude clearly says "lookup", use plain search.
    # For anything else, use fair search: it's the safer choice,
    # because it never leaves a document out. It just costs a bit more.
    return "lookup" if word.startswith("lookup") else "compare"

def ask(question):
    # Step 0, the router: decide what kind of question this is
    kind = classify(question)

    # Pick the search strategy AND the answer length to match
    if kind == "compare":
        top = search_fair(question)   # best pieces from every file
        budget = 2000                 # comparisons need room
    else:
        top = search(question)        # top 5 most related pieces
        budget = 1000                 # lookups are short

    print(f"(question type: {kind})")

    # Build the documents block, same as before
    sources = "\n\n".join(
        f"[{pieces[i]['source']}] {pieces[i]['text']}" for score, i in top
    )

    prompt = f"""Answer the question using only the documents below.
After each fact, cite the file it came from in brackets, like [resume_maya_torres.txt].
If the documents don't contain the answer, say so.
Don't mention that documents are cut off or incomplete.

Documents:
{sources}

Question: {question}"""

    message = client.messages.create(
        model=MODEL, max_tokens=budget,   # the budget chosen above
        messages=[{"role": "user", "content": prompt}],
    )
    print(f"(stop reason: {message.stop_reason}, output tokens: {message.usage.output_tokens})")
    return top, "".join(b.text for b in message.content if b.type == "text")


# The chat loop: keep asking until you type quit
if __name__ == "__main__":
    while True:
        question = input("\nQuestion: ")
        if question.lower() == "quit":
            break
        top, reply = ask(question)
        print("(found: " + ", ".join(f"{pieces[i]['source']} {score:.2f}" for score, i in top) + ")")
        print(reply)
