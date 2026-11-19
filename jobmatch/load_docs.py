from pathlib import Path
from chunking import chunk_words

def load_documents(folder, size=40):
    pieces = []
    for path in Path(folder).glob("*.txt"):
        text = " ".join(path.read_text(encoding="utf-8").split())
        for chunk in chunk_words(text, size, size // 4):
            pieces.append({"source": path.name, "text": chunk})
    return pieces

if __name__ == "__main__":
    pieces = load_documents("docs")
    print(f"{len(pieces)} pieces")
    for p in pieces:
        print(f"[{p['source']}] {p['text'][:60]}")