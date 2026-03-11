"""
generate_data.py
────────────────
Generates a realistic synthetic Cape Town Airbnb dataset.
Useful for demos, testing, and when real data is unavailable.

In production, replace this with a real scraper or the
Inside Airbnb data download from: https://insideairbnb.com/get-the-data/

Outputs (saved to data/):
    listings.csv  — 2,385 property listings
    hosts.csv     — 800 host profiles
    calendar.csv  — 182,500 daily availability rows (500 listings x 365 days)
    reviews.csv   — 46,000+ guest reviews

Usage:
    python pipeline/generate_data.py
"""

import os
import random
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ── Config ────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(BASE_DIR, "data")
SEED     = 42

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

random.seed(SEED)
np.random.seed(SEED)

# ── Reference data ────────────────────────────────────────────────────────────

NEIGHBOURHOODS = {
    "Cape Town City Centre": {"avg_price": 2200, "listings": 280},
    "Sea Point":             {"avg_price": 2500, "listings": 220},
    "Green Point":           {"avg_price": 2400, "listings": 180},
    "Camps Bay":             {"avg_price": 4800, "listings": 160},
    "Clifton":               {"avg_price": 6200, "listings": 80},
    "Waterfront":            {"avg_price": 3800, "listings": 120},
    "Gardens":               {"avg_price": 1900, "listings": 150},
    "De Waterkant":          {"avg_price": 2800, "listings": 130},
    "Woodstock":             {"avg_price": 1500, "listings": 110},
    "Observatory":           {"avg_price": 1200, "listings": 95},
    "Hout Bay":              {"avg_price": 2600, "listings": 140},
    "Constantia":            {"avg_price": 3500, "listings": 90},
    "Simon's Town":          {"avg_price": 2100, "listings": 85},
    "Muizenberg":            {"avg_price": 1600, "listings": 100},
    "Stellenbosch":          {"avg_price": 1800, "listings": 120},
    "Bloubergstrand":        {"avg_price": 2000, "listings": 95},
    "Kalk Bay":              {"avg_price": 1900, "listings": 75},
    "Parow":                 {"avg_price": 900,  "listings": 60},
    "Bellville":             {"avg_price": 850,  "listings": 55},
    "Mitchell's Plain":      {"avg_price": 700,  "listings": 40},
}

ROOM_TYPES     = ["Entire home/apt"] * 3 + ["Private room"] * 2 + ["Shared room"]
PROPERTY_TYPES = ["Apartment", "Apartment", "House", "House", "Villa",
                  "Studio", "Guesthouse", "Cottage", "Loft", "Townhouse"]

# Seasonal price multipliers — SA summer (Dec-Feb) is peak
MONTH_MULT = {1:1.35, 2:1.40, 3:1.10, 4:1.00, 5:0.85, 6:0.80,
              7:0.82, 8:0.85, 9:0.90, 10:1.00, 11:1.15, 12:1.50}

REVIEW_COMMENTS = [
    "Lovely place, highly recommend!", "Great host and location.",
    "Clean and comfortable.", "Amazing views, will return!",
    "Perfect for a family stay.", "Good value for money.",
    "Central location, easy access.", "Stunning property.",
    "Host was very responsive.", "Would definitely book again.",
    "Not as described, disappointed.", "Average stay, nothing special.",
    "Noisy neighbourhood at night.", "Small but functional.",
    "Incredible sunsets from the balcony!", "Perfect Cape Town base.",
    "Spotless and well equipped.", "Fantastic neighbourhood to explore.",
    "Warm welcome from the host.", "Exactly as pictured.",
]

# ── Generators ────────────────────────────────────────────────────────────────

def generate_hosts(n: int = 800) -> pd.DataFrame:
    host_ids = list(range(1001, 1001 + n))
    df = pd.DataFrame({
        "host_id":                host_ids,
        "host_name":              [f"Host_{i}" for i in host_ids],
        "host_since":             pd.to_datetime([
            datetime(2010, 1, 1) + timedelta(days=random.randint(0, 4500))
            for _ in host_ids
        ]).strftime("%Y-%m-%d"),
        "host_is_superhost":      [random.choice(["t", "t", "f"]) for _ in host_ids],
        "host_listings_count":    np.random.choice([1,1,1,2,2,3,4,5,8,10,15], n),
        "host_response_rate":     [f"{random.randint(70, 100)}%" for _ in host_ids],
        "host_identity_verified": [random.choice(["t", "t", "f"]) for _ in host_ids],
    })
    return df


def generate_listings(host_ids: list) -> pd.DataFrame:
    rows = []
    listing_id = 1

    for neighbourhood, meta in NEIGHBOURHOODS.items():
        for _ in range(meta["listings"]):
            room_type    = random.choice(ROOM_TYPES)
            bedrooms     = random.choice([1, 1, 2, 2, 3, 3, 4, 5])
            avg_p        = meta["avg_price"]
            price_mult   = 0.45 if room_type == "Private room" else \
                           0.20 if room_type == "Shared room"  else 1.0
            price        = max(300, int(np.random.normal(avg_p * price_mult, avg_p * 0.25)))
            is_superhost = random.random() < 0.36
            n_reviews    = random.randint(0, 350)

            rows.append({
                "listing_id":          listing_id,
                "host_id":             random.choice(host_ids),
                "neighbourhood":       neighbourhood,
                "room_type":           room_type,
                "property_type":       random.choice(PROPERTY_TYPES),
                "bedrooms":            bedrooms,
                "bathrooms":           max(1, bedrooms - random.randint(0, 1)),
                "accommodates":        bedrooms * 2,
                "price_zar":           price,
                "minimum_nights":      random.choice([1,1,2,2,3,5,7,30]),
                "maximum_nights":      random.choice([30,60,90,365,1125]),
                "availability_365":    random.randint(0, 365),
                "number_of_reviews":   n_reviews,
                "review_score_rating": round(random.uniform(4.7, 5.0), 2)
                                       if is_superhost
                                       else (round(random.uniform(3.5, 5.0), 2) if n_reviews > 0 else None),
                "reviews_per_month":   round(n_reviews / max(1, random.randint(6, 36)), 2),
                "instant_bookable":    random.choice(["t", "f"]),
                "last_review":         (datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365))
                                       ).strftime("%Y-%m-%d") if n_reviews > 0 else None,
            })
            listing_id += 1

    return pd.DataFrame(rows)


def generate_calendar(listing_ids: list, sample: int = 500) -> pd.DataFrame:
    sample_ids = random.sample(listing_ids, min(sample, len(listing_ids)))
    base_date  = datetime(2024, 1, 1)
    rows = []

    for lid in sample_ids:
        base_price = random.randint(800, 5000)
        for day_offset in range(365):
            d = base_date + timedelta(days=day_offset)
            adj_price = int(base_price * MONTH_MULT[d.month] * random.uniform(0.9, 1.1))
            rows.append({
                "listing_id": lid,
                "date":       d.strftime("%Y-%m-%d"),
                "month":      d.month,
                "available":  "t" if random.random() < 0.55 else "f",
                "price_zar":  adj_price,
            })

    return pd.DataFrame(rows)


def generate_reviews(listings_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    rev_id = 1
    base   = datetime(2022, 1, 1)

    for _, row in listings_df[listings_df["number_of_reviews"] > 0].iterrows():
        n = min(int(row["number_of_reviews"]), 20)
        for _ in range(n):
            rows.append({
                "review_id":   rev_id,
                "listing_id":  row["listing_id"],
                "reviewer_id": random.randint(5000, 99999),
                "date":        (base + timedelta(days=random.randint(0, 800))).strftime("%Y-%m-%d"),
                "comments":    random.choice(REVIEW_COMMENTS),
            })
            rev_id += 1

    return pd.DataFrame(rows)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("══════════════════════════════════════════════")
    log.info("  Airbnb Cape Town — Data Generator")
    log.info(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("══════════════════════════════════════════════")

    os.makedirs(DATA_DIR, exist_ok=True)

    log.info("Generating hosts ...")
    hosts = generate_hosts(800)
    hosts.to_csv(os.path.join(DATA_DIR, "hosts.csv"), index=False)
    log.info(f"  hosts.csv → {len(hosts):,} rows")

    log.info("Generating listings ...")
    listings = generate_listings(hosts["host_id"].tolist())
    listings.to_csv(os.path.join(DATA_DIR, "listings.csv"), index=False)
    log.info(f"  listings.csv → {len(listings):,} rows")

    log.info("Generating calendar ...")
    calendar = generate_calendar(listings["listing_id"].tolist())
    calendar.to_csv(os.path.join(DATA_DIR, "calendar.csv"), index=False)
    log.info(f"  calendar.csv → {len(calendar):,} rows")

    log.info("Generating reviews ...")
    reviews = generate_reviews(listings)
    reviews.to_csv(os.path.join(DATA_DIR, "reviews.csv"), index=False)
    log.info(f"  reviews.csv → {len(reviews):,} rows")

    log.info("\n  All datasets saved to data/")
    log.info("  Next: run `python pipeline/load_data.py` to build the database")


if __name__ == "__main__":
    main()
