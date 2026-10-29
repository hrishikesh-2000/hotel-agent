import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["GEMINI_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

response = client.chat.completions.create(
    model="gemini-3.1-flash-lite",
    max_tokens=300,
    messages=[
        {"role": "user", "content": "In two sentences, what makes a good villa for a group of 8 adults?"}
    ],
)

print(response.choices[0].message.content)