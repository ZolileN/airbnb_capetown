# Cape Town Airbnb Analytics

A SQL-first data analytics portfolio project exploring the Cape Town short-term rental market using SQLite, Python, and Streamlit.

---

## Project Overview

This project uses a realistic Cape Town Airbnb dataset to answer key business questions about the short-term rental market:

- Which neighbourhoods command the highest prices and occupancy?
- Do superhosts earn significantly more than regular hosts?
- How does pricing shift across seasons?
- What makes a listing a hidden gem vs overpriced?
- Which areas are best value for guests?

The centrepiece is a library of **25 production-quality SQL queries** covering market analysis, host behaviour, pricing strategy, occupancy patterns, and advanced window functions.

---

## Project Structure

```
airbnb_capetown/
│
├── data/
│   ├── listings.csv          # 2,385 Cape Town property listings
│   ├── hosts.csv             # 800 host profiles
│   ├── calendar.csv          # 182,500 daily availability rows
│   ├── reviews.csv           # 46,000+ guest reviews
│   └── airbnb_capetown.db    # SQLite database (auto-generated)
│
├── queries/
│   └── analysis.sql          # 25 SQL queries across 7 analytical sections
│
├── pipeline/
│   ├── generate_data.py      # Generates the synthetic dataset
│   └── load_data.py          # Loads CSVs into SQLite with indexes
│
├── dashboard/
│   └── app.py                # Streamlit interactive dashboard
│
├── notebooks/                # Jupyter notebooks for exploration
│
├── docs/                     # Supporting documentation
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Database Schema

```
listings                       hosts
─────────────────────────      ─────────────────────────
listing_id        PK           host_id           PK
host_id           FK ────────► host_name
neighbourhood                  host_since
room_type                      host_is_superhost
property_type                  host_listings_count
bedrooms                       host_response_rate
bathrooms                      host_identity_verified
accommodates
price_zar                      calendar
minimum_nights                 ─────────────────────────
availability_365               listing_id        FK
number_of_reviews              date
review_score_rating            month
instant_bookable               available
last_review                    price_zar

reviews
─────────────────────────
review_id         PK
listing_id        FK
reviewer_id
date
comments
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/airbnb_capetown.git
cd airbnb_capetown
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Generate the dataset

```bash
python pipeline/generate_data.py
```

### 4. Load into SQLite

```bash
python pipeline/load_data.py
```

### 5. Run the SQL queries

```bash
sqlite3 data/airbnb_capetown.db
.read queries/analysis.sql
```

### 6. Launch the dashboard

```bash
streamlit run dashboard/app.py
```

---

## SQL Query Index

| # | Query | Technique |
|---|---|---|
| Q1 | Market snapshot KPIs | Aggregation |
| Q2 | Listings by room type | GROUP BY + window |
| Q3 | Property type breakdown | GROUP BY |
| Q4 | Neighbourhood performance | Multi-metric aggregation |
| Q5 | Most expensive vs affordable areas | UNION + window ROW_NUMBER |
| Q6 | Best value neighbourhoods | Composite scoring |
| Q7 | Price per bedroom by area | Normalised comparison |
| Q8 | Superhost vs regular host | JOIN + GROUP BY |
| Q9 | Multi-listing commercial hosts | HAVING filter |
| Q10 | Host tenure analysis | CASE + date arithmetic |
| Q11 | Top hosts by estimated revenue | Revenue estimation |
| Q12 | Price distribution buckets | CASE bucketing |
| Q13 | Price vs bedroom count | Scaling analysis |
| Q14 | Seasonal pricing from calendar | Monthly aggregation |
| Q15 | Peak season price premium | CTE + CROSS JOIN |
| Q16 | Occupancy rate by neighbourhood | Derived metric |
| Q17 | Instant bookable performance | Comparative GROUP BY |
| Q18 | Minimum nights impact | CASE + occupancy |
| Q19 | Review volume by neighbourhood | LEFT JOIN |
| Q20 | Review trends over time | Time series |
| Q21 | Stale listing detection | Multi-condition filter |
| Q22 | Revenue ranking | RANK() window function |
| Q23 | Rolling 3-month review trend | CTE + rolling AVG |
| Q24 | Neighbourhood quadrant matrix | Multi-CTE + CASE |
| Q25 | Rating vs price premium | Band analysis |

---

## Key Insights

- **Clifton and Camps Bay** command the highest prices, averaging R6,200 and R4,800 per night respectively.
- **Superhosts** achieve ~15% higher review scores and ~20% more reviews than regular hosts.
- **December pricing** runs up to 50% above the cheapest month (June), reflecting Cape Town's summer tourism peak.
- **Observatory and Woodstock** emerge as hidden gem neighbourhoods — high ratings at significantly lower prices.
- **Instant bookable listings** show higher estimated occupancy rates, suggesting guests favour flexibility.

---

## Tech Stack

| Tool | Purpose |
|---|---|
| SQLite | Analytical database |
| Python + pandas | Data generation and pipeline |
| Streamlit + Plotly | Interactive dashboard |
| SQL (25 queries) | Core analytics layer |

---

## Data Source

Dataset is synthetically generated to mirror real Cape Town Airbnb market dynamics. For real data, download from [Inside Airbnb](https://insideairbnb.com/get-the-data/) and run `pipeline/load_data.py`.

---

## Author

Zolile Nonzapa — Data Analytics Portfolio Project
