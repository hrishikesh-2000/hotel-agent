from hotel_agent.schemas import VillaOffer, compute_match_score


def test_villa_offer_supports_unknown_pool_and_evidence():
    villa = VillaOffer(
        name="Karjat Lake Villa",
        micro_locality="Karjat",
        city="Karjat",
        capacity=8,
        price_display="₹22,000",
        price_numeric=22000,
        private_pool="unknown",
        amenities=["wifi", "kitchen"],
        source_domain="StayVista",
        booking_url="https://example.com/karjat-lake-villa",
        source_url="https://example.com/karjat-lake-villa",
        evidence=["Price shown on listing page", "Guest capacity listed on page"],
        rating=4.5,
        meals="Breakfast included",
        contact="+91 98765 43210",
    )

    assert villa.private_pool == "unknown"
    assert villa.evidence
    assert villa.source_url.endswith("example.com/karjat-lake-villa")
    assert 0 <= villa.match_score <= 100


def test_compute_match_score_rewards_pool_capacity_budget_and_location():
    villa = VillaOffer(
        name="Pool Villa",
        micro_locality="Karjat",
        city="Karjat",
        capacity=10,
        price_display="₹20,000",
        price_numeric=20000,
        private_pool="yes",
        amenities=["pool", "wifi"],
        source_domain="StayVista",
        booking_url="https://example.com/pool-villa",
        source_url="https://example.com/pool-villa",
        evidence=["Confirmed private pool"],
    )

    score = compute_match_score(villa, target_location="Karjat", guests=8, budget_cap=25000)
    assert score >= 70
    assert score <= 100
