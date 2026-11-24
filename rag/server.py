# json: turns Python dicts into JSON text, the standard format APIs send back
import json

# Python's built-in web server tools (no installs needed)
from http.server import BaseHTTPRequestHandler, HTTPServer

# Tools to read the web address, like /ask?q=Can+I+bring+my+dog
from urllib.parse import urlparse, parse_qs

# Your own RAG functions
from rag_semantic import load_chunks, load_index, answer

# Load the handbook and its embeddings ONCE, when the server starts,
# not on every question
chunks = load_chunks("handbook.txt")
vectors = load_index(chunks)


class Handler(BaseHTTPRequestHandler):
    # do_GET runs every time a browser visits one of this server's addresses
    def do_GET(self):
        url = urlparse(self.path)                 # split the address into parts

        if url.path != "/ask":                    # only /ask is a real address
            self.send_json(404, {"error": "Use /ask?q=your question"})
            return

        # Read the question from ?q=...  (parse_qs gives a list, so take [0])
        question = parse_qs(url.query).get("q", [""])[0]
        if not question:
            self.send_json(400, {"error": "Add a question, like /ask?q=How much is on-call pay"})
            return

        top, text = answer(question, chunks, vectors)   # your librarian + writer

        # Build the response: the answer, plus which sections were used
        self.send_json(200, {
            "question": question,
            "answer": text,
            "sources": [{"section": i, "score": round(score, 2)} for score, i in top],
        })

    def send_json(self, status, data):
        body = json.dumps(data, indent=2).encode("utf-8")  # dict -> JSON text -> bytes
        self.send_response(status)                         # 200 = OK, 400 = bad request, 404 = not found
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)                             # send it back to the browser


print("Server running. Try: http://localhost:8000/ask?q=Can I bring my dog?")
print("Press Ctrl + C to stop.")
HTTPServer(("localhost", 8000), Handler).serve_forever()   # listen until stopped