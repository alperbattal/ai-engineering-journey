from rag_semantic import load_chunks, load_index, embed, cosine

chunks = load_chunks("handbook.txt")
vectors = load_index(chunks)

question = input("Question: ")
q = embed([question], "query")[0]

for i, v in enumerate(vectors):
    score = cosine(q, v)
    print(f"[{i}] {score:.2f}  {chunks[i][:50]}")