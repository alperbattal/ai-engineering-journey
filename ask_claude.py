import anthropic

client = anthropic.Anthropic()

question = input("Ask Claude: ")

message = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=1000,
    messages=[
        {"role": "user", "content": question}
    ]
)

for block in message.content:
    if block.type == "text":
        print(block.text)

print("Stop reason:", message.stop_reason)