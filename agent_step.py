import os
import json
from openai import OpenAI
from search_tool import web_search

client = OpenAI(
    api_key=os.environ["GEMINI_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
MODEL = "gemini-3.1-flash-lite"

# 1. Describe the tool to the model
tools = [{
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web. Returns titles, URLs and short snippets.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"],
        },
    },
}]

messages = [{
    "role": "user",
    "content": "Find 3 candidate private-pool villas near Karjat that can host 8 adults. Search first.",
}]

# 2. Ask the model; it may answer, or ask us to run a tool
response = client.chat.completions.create(
    model=MODEL, max_tokens=1500, messages=messages, tools=tools
)
msg = response.choices[0].message
print("Tool calls requested:", msg.tool_calls)

# 3. If it asked for a tool, run it and send the result back
if msg.tool_calls:
    messages.append(msg)
    for call in msg.tool_calls:
        args = json.loads(call.function.arguments)
        print("Searching for:", args["query"])
        result = web_search(args["query"])
        messages.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": json.dumps(result),
        })
    final = client.chat.completions.create(
        model=MODEL, max_tokens=1500, messages=messages, tools=tools
    )
    print(final.choices[0].message.content)