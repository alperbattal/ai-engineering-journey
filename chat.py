import anthropic

client = anthropic.Anthropic()
history = []

print("Chat with Claude. (type 'exit' to quit)")

while True:
    question = input("\nYou: ")
    if question.lower() == "exit":
        break

    history.append({"role": "user", "content": question})

    message = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1000,
        system="You're a friendly mentor who explains AI concepts using Salesforce anologies. Keep answers under 4 sentences.",
        messages=history
    )

    reply=""
    for block in message.content:
        if block.type == "text":
            reply += block.text

    print("\nClaude:", reply)
    history.append({"role": "assistant", "content": reply})

    print("Stop reason:", message.stop_reason)