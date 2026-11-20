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

def ask(question):
    # Step 1, the librarian: find the 5 most related pieces
    top = search_fair(question)
        
    # Build the "Documents" text for Claude: one block per found piece,
    # labeled with its FILE NAME so Claude can cite it. For example:
    #   [resume_daniel_okafor.txt] Daniel Okafor - AI Solutions Engineer...
    # The blocks are joined with a blank line ("\n\n") between them.
    sources = "\n\n".join(
        f"[{pieces[i]['source']}] {pieces[i]['text']}" for score, i in top
    )

    # Step 2, the writer: the instructions for Claude, with the documents inserted
    prompt = f"""Answer the question using only the documents below.
After each fact, cite the file it came from in brackets, like [resume_maya_torres.txt].
If the documents don't contain the answer, say so.

Documents:
{sources}

Question: {question}"""

    # Send the prompt to Claude
    message = client.messages.create(
        model=MODEL, max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )

    # Return two things: what was found (for printing) and Claude's answer.
    # The join keeps only the text blocks, skipping any thinking blocks.
    return top, "".join(b.text for b in message.content if b.type == "text")


# The chat loop: keep asking until you type quit
while True:
    question = input("\nQuestion: ")
    if question.lower() == "quit":
        break

    top, reply = ask(question)

    # Show which files the librarian picked and their scores, e.g.
    # (found: resume_daniel_okafor.txt 0.52, job_ai_engineer.txt 0.48, ...)
    print("(found: " + ", ".join(f"{pieces[i]['source']} {score:.2f}" for score, i in top) + ")")

    # Show Claude's answer
    print(reply)