from typing import List, Optional
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
    has_private_pool: bool = Field(description="True if private pool is confirmed")
    amenities: List[str] = Field(default_factory=list, description="Up to 6 verified amenities")
    source_domain: str = Field(description="Platform name (e.g., 'StayVista', 'Airbnb', 'SaffronStays', 'MakeMyTrip')")
    booking_url: str = Field(description="Direct URL where the property was found")
    match_score: int = Field(description="Score from 0 to 100 based on how strictly it matches location, guest count, and amenities")
    summary: str = Field(description="1-sentence factual summary")

class VillaSearchResponse(BaseModel):
    results: List[VillaOffer] = Field(description="Exhaustive list of all valid properties found across scraped pages")
