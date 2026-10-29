from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class SearchPlan(BaseModel):
    target_micro_localities: List[str] = Field(
        description="Specific neighborhoods or pockets within the requested city (e.g., for Mumbai: Madh Island, Gorai, Manori, Yeoor Hills, Powai, Uttan)"
    )
    excluded_regions: List[str] = Field(
        description="Nearby outstation towns that SEO blogs falsely market as the target city (e.g., if strict Mumbai: exclude Alibaug, Lonavala, Karjat, Igatpuri)"
    )
    search_queries: List[str] = Field(
        description="5 to 6 targeted search queries covering different platforms (StayVista, SaffronStays, Airbnb, MakeMyTrip, Booking) and micro-localities"
    )


class VillaOffer(BaseModel):
    name: str = Field(description="Exact name of the villa or property")
    micro_locality: str = Field(description="Specific neighborhood/area (e.g., 'Madh Island, Mumbai' or 'Karjat')")
    city: str = Field(description="Actual city or town name")
    capacity: Optional[int] = Field(default=None, description="Max guest capacity as an integer")
    price_display: str = Field(default="Not listed", description="Formatted price per night (e.g., '₹45,000') or 'Not listed'")
    price_numeric: Optional[int] = Field(default=None, description="Raw numeric price in INR per night for sorting/math, or null if unknown")
    private_pool: Literal["yes", "no", "unknown"] = Field(default="unknown", description="Pool status confirmed by the page, or unknown when not stated")
    amenities: List[str] = Field(default_factory=list, description="Up to 6 verified amenities")
    source_domain: str = Field(description="Platform name (e.g., 'StayVista', 'Airbnb', 'SaffronStays', 'MakeMyTrip')")
    booking_url: str = Field(default="", description="Direct URL where the property was found")
    source_url: str = Field(default="", description="The exact source page that supplied the facts")
    evidence: List[str] = Field(default_factory=list, description="Quoted fact snippets or source notes that support the listing")
    rating: Optional[float] = Field(default=None, description="Average rating when publicly stated on the source page")
    meals: Optional[str] = Field(default=None, description="Meal offering such as 'Breakfast included' or 'No meals listed'")
    contact: Optional[str] = Field(default=None, description="Contact number or booking contact if publicly listed")
    match_score: int = Field(default=0, ge=0, le=100, description="Deterministic score from 0 to 100 based on locality, guests, budget, and pool fit")
    summary: str = Field(default="", description="1-sentence factual summary")


class VillaSearchResponse(BaseModel):
    results: List[VillaOffer] = Field(description="Exhaustive list of all valid properties found across scraped pages")


def compute_match_score(villa: VillaOffer, target_location: str, guests: int, budget_cap: int = 25000) -> int:
    """Compute a deterministic score instead of trusting model-generated rankings."""
    score = 0

    target = target_location.lower().strip()
    city = villa.city.lower().strip()
    micro = villa.micro_locality.lower().strip()

    if target in city or target in micro:
        score += 30
    elif city or micro:
        score += 10

    if villa.capacity is not None:
        if villa.capacity >= guests:
            score += 30
        else:
            shortage = guests - villa.capacity
            score += max(0, 30 - shortage * 10)
    else:
        score += 10

    if villa.price_numeric is not None:
        if villa.price_numeric <= budget_cap:
            score += 20
        else:
            over = villa.price_numeric - budget_cap
            score += max(0, 20 - (over // 5000))
    else:
        score += 5

    if villa.private_pool == "yes":
        score += 15
    elif villa.private_pool == "unknown":
        score += 5

    score += min(5, len(villa.amenities))
    return min(100, max(0, int(round(score))))
