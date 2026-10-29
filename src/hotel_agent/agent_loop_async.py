import os
import json
import asyncio
from openai import AsyncOpenAI
from hotel_agent.tools.search import web_search
from hotel_agent.tools.fetch_async import fetch_pages_batch
from hotel_agent.schemas import VillaSearchResponse

client = AsyncOpenAI(
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
            "description": "Search the web for property listings, links, and summaries.",
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
            "name": "fetch_pages_batch",
            "description": "Fetch multiple URLs simultaneously to extract deep details (pricing, pool, capacity).",
            "parameters": {
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of URLs to scrape in parallel",
                    }
                },
                "required": ["urls"],
            },
        },
    },
]

async def execute_tool_call(call) -> dict:
    """Helper to dispatch tool execution safely."""
    name = call.function.name
    try:
        args = json.loads(call.function.arguments)
        print(f"Executing: {name}({args})")
        if name == "web_search":
            # web_search uses DDGS (synchronous), run in thread pool to prevent blocking loop
            result = await asyncio.to_thread(web_search, **args)
        elif name == "fetch_pages_batch":
            result = await fetch_pages_batch(**args)
        else:
            result = {"error": f"Unknown tool: {name}"}
    except Exception as e:
        result = {"error": f"{type(e).__name__}: {str(e)}"}
        print(f"Tool error on {name}: {result['error']}")

    return {
        "role": "tool",
        "tool_call_id": call.id,
        "content": json.dumps(result),
    }

async def run_agent():
    messages = [
        {
            "role": "user",
            "content": (
                "Find 3 private-pool villas near Karjat that can host 8 adults. "
                "Search first, then use fetch_pages_batch to inspect candidate links concurrently for amenities and pricing."
            ),
        }
    ]

    for step in range(1, MAX_STEPS + 1):
        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
        )
        choice = response.choices[0]
        msg = choice.message
        print(f"\n--- step {step} | finish_reason: {choice.finish_reason} ---")

        # Exit loop when tools are finished, proceed to structured parse
        if not msg.tool_calls:
            print("\nSynthesizing extracted properties into Pydantic schema...\n")
            messages.append({
                "role": "user",
                "content": "Extract all discovered properties into the requested JSON schema format.",
            })
            final_response = await client.beta.chat.completions.parse(
                model=MODEL,
                messages=messages,
                response_format=VillaSearchResponse,
            )
            parsed_data = final_response.choices[0].message.parsed
            print(parsed_data.model_dump_json(indent=2))
            return

        messages.append(msg)

        # Execute all requested tool calls in parallel via asyncio.gather
        tool_results = await asyncio.gather(*(execute_tool_call(call) for call in msg.tool_calls))
        messages.extend(tool_results)

    print("\nStopped: reached MAX_STEPS without completing.")

if __name__ == "__main__":
    asyncio.run(run_agent())