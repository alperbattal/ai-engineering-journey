from pathlib import Path

text = Path("handbook.txt").read_text(encoding="utf-8")
text = " ".join(text.split()) 

def chunk_words(text, size, overlap):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break   
        start += size - overlap
    return chunks

chunks = chunk_words(text, 40, 10)
print(f"{len(chunks)}chunks")
for i,c in enumerate(chunks):
    print(f"\n[{i}] {c}")