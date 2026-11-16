
import ollama

print("AI Store Agent Started!")
print("اكتب exit للخروج")
print("-------------------------")

while True:
    user_input = input("\nYou: ")

    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    response = ollama.chat(
        model="qwen3:4b",
        messages=[
            {
                "role": "user",
                "content": user_input
            }
        ]
    )

    print("\nAI:", response["message"]["content"])

