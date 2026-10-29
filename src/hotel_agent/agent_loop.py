import os
import json
from openai import OpenAI
from hotel_agent.tools.search import web_search
from hotel_agent.tools.fetch import fetch_page
from hotel_agent.schemas import VillaSearchResponse

client = OpenAI(
    api_key=os.environ["GEMINI_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
MODEL = "gemini-3.1-flash-lite"
MAX_STEPS = 6

tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for property links and basic details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_page",
            "description": "Scrape readable text from a URL to extract deep property details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Webpage URL to fetch"}
                },
                "required": ["url"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "web_search": web_search,
    "fetch_page": fetch_page,
}

messages = [
    {
        "role": "user",
        "content": (
            "Find 3 private-pool villas near Karjat that can host 8 adults. "
            "Search and fetch pages to verify private pool, capacity, and details."
        ),
    }
]

for step in range(1, MAX_STEPS + 1):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
    )
    choice = response.choices[0]
    msg = choice.message
    print(f"\n--- step {step} | finish_reason: {choice.finish_reason} ---")

    # When the model stops calling tools, trigger the structured synthesis step
    if not msg.tool_calls:
        print("\nTool gathering finished. Formatting into structured schema...\n")
        messages.append({
            "role": "user",
            "content": "Extract the discovered properties into the requested JSON schema format.",
        })
        final_response = client.beta.chat.completions.parse(
            model=MODEL,
            messages=messages,
            response_format=VillaSearchResponse,
        )
        parsed_data = final_response.choices[0].message.parsed
        print(parsed_data.model_dump_json(indent=2))
        break

    messages.append(msg)
    for call in msg.tool_calls:
        name = call.function.name
        try:
            args = json.loads(call.function.arguments)
            print("Tool:", name, args)
            result = TOOL_FUNCTIONS[name](**args)
        except Exception as e:
            result = {"error": f"{type(e).__name__}: {e}"}
            print("Tool error:", result["error"])

        messages.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": json.dumps(result),
        })
else:
    print("\nStopped: reached MAX_STEPS without completing.")