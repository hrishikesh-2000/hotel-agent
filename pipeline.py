import os
import asyncio
from typing import List, Dict, Any
from openai import AsyncOpenAI
from search_tool import web_search
from async_fetch import fetch_pages_batch
from schemas import SearchPlan, VillaSearchResponse, VillaOffer

client = AsyncOpenAI(
    api_key=os.environ.get("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
MODEL = "gemini-3.1-flash-lite"

async def build_search_plan(location: str, guests: int, requirements: str, strict_geo: bool) -> SearchPlan:
    geo_rule = (
        f"STRICT GEOGRAPHY ENABLED: Only target micro-localities physically inside {location} "
        f"(e.g., if Mumbai, target Madh Island, Gorai, Manori, Uttan, Powai, Royal Palms) and explicitly put nearby weekend getaways "
        f"(like Alibaug, Lonavala, Karjat, Matheran) into excluded_regions."
        if strict_geo
        else f"FLEXIBLE GEOGRAPHY: Include {location} and popular nearby drive-to weekend hubs within 2 hours."
    )

    prompt = (
        f"You are a Travel Search Architect. Create a multi-source search plan to find villas/hotels in '{location}' "
        f"for {guests} guests with requirements: '{requirements}'.\n"
        f"{geo_rule}\n"
        "Generate 5 distinct search queries targeting major portals (StayVista, SaffronStays, Airbnb, MakeMyTrip, Elivaas) "
        "and specific micro-localities so we get maximum property coverage."
    )

    resp = await client.beta.chat.completions.parse(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format=SearchPlan,
    )
    return resp.choices[0].message.parsed

async def ingest_bronze_pages(queries: List[str], max_urls: int = 12) -> List[Dict[str, Any]]:
    search_tasks = [asyncio.to_thread(web_search, q, 4) for q in queries]
    raw_search_batches = await asyncio.gather(*search_tasks)

    unique_urls = []
    seen = set()
    for batch in raw_search_batches:
        if isinstance(batch, list):
            for item in batch:
                url = item.get("url")
                if url and url not in seen:
                    seen.add(url)
                    unique_urls.append(url)

    target_urls = unique_urls[:max_urls]
    if not target_urls:
        return []

    scraped_pages = await fetch_pages_batch(target_urls, max_chars=7000)
    return [p for p in scraped_pages if p.get("status") == "ok" and len(p.get("text", "")) > 300]

async def extract_silver_entities(
    pages: List[Dict[str, Any]],
    location: str,
    guests: int,
    requirements: str,
    plan: SearchPlan,
    strict_geo: bool,
) -> List[VillaOffer]:
    if not pages:
        return []

    corpus = "\n\n".join(
        f"=== SOURCE [{i+1}] URL: {p['url']} ===\n{p['text']}"
        for i, p in enumerate(pages)
    )

    extraction_prompt = (
        f"Extract EVERY distinct villa, bungalow, or resort property mentioned in the scraped sources below.\n"
        f"- Target Location: {location} (Valid areas: {', '.join(plan.target_micro_localities)})\n"
        f"- Excluded Regions (DO NOT EXTRACT properties located here): {', '.join(plan.excluded_regions) if strict_geo else 'None'}\n"
        f"- Guest Requirement: {guests} adults\n"
        f"- Amenities Requested: {requirements}\n\n"
        "RULES:\n"
        "1. Do NOT stop at 3 properties. Extract ALL valid properties found across all sources (aim for 8 to 20+ if present).\n"
        "2. Set 'city' accurately based on where the property is physically located.\n"
        "3. Extract numeric price in INR into 'price_numeric' if visible (e.g., 45000), else null.\n\n"
        f"SCRAPED CORPUS:\n{corpus}"
    )

    resp = await client.beta.chat.completions.parse(
        model=MODEL,
        messages=[{"role": "user", "content": extraction_prompt}],
        response_format=VillaSearchResponse,
    )
    extracted = resp.choices[0].message.parsed.results

    excluded_lower = {ex.lower().strip() for ex in plan.excluded_regions} if strict_geo else set()
    clean_results = []
    seen_names = set()

    for villa in extracted:
        city_lower = villa.city.lower().strip()
        locality_lower = villa.micro_locality.lower().strip()

        if strict_geo and any(ex in city_lower or ex in locality_lower for ex in excluded_lower):
            continue

        norm_name = villa.name.lower().strip()
        if norm_name not in seen_names:
            seen_names.add(norm_name)
            clean_results.append(villa)

    clean_results.sort(key=lambda x: (-x.match_score, x.price_numeric or 9999999))
    return clean_results

if __name__ == "__main__":
    async def test():
        print("1. Building geo-aware search plan for Mumbai (Strict)...")
        plan = await build_search_plan("Mumbai", 8, "private pool", strict_geo=True)
        print("-> Target Micro-Localities:", plan.target_micro_localities)
        print("-> Excluded Outstation Regions:", plan.excluded_regions)
        print("-> Generated Queries:", plan.search_queries)

    asyncio.run(test())
