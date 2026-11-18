from pathlib import Path

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

if __name__ == "__main__":
    text = Path("handbook.txt").read_text(encoding="utf-8") 
    text = " ".join(text.split())

    chunks = chunk_words(text, 40, 10)
    print(f"{len(chunks)} chunks")
    for i,c in enumerate(chunks):
        print(f"\n[{i}] {c}")

