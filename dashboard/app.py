"""
app.py — Cape Town Airbnb Analytics Dashboard
══════════════════════════════════════════════
A multi-page Streamlit dashboard exploring the Cape Town
short-term rental market through SQL-driven analytics.

Pages
─────
  1. 🏙  Market Overview      — KPIs, room types, price distribution
  2. 🗺  Neighbourhoods       — Pricing, value scores, quadrant map
  3. 👤  Host Intelligence    — Superhosts, tenure, revenue estimates
  4. 📅  Pricing & Seasons    — Seasonal trends, peak premiums
  5. 💬  Reviews & Occupancy  — Activity trends, occupancy by area

Usage
─────
  streamlit run dashboard/app.py
"""

import os
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from typing import Any, Dict

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Cape Town Airbnb Analytics",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "airbnb_capetown.db")

# ══════════════════════════════════════════════════════════════════════════════
# THEME & CSS — Editorial / Property Magazine aesthetic
# Warm cream background, terracotta accents, ocean blue highlights
# Display font: Playfair Display | Body: DM Sans
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;900&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #faf8f5;
    color: #1a1814;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #1a1814;
    border-right: none;
}
section[data-testid="stSidebar"] * { color: #e8e0d4 !important; }
section[data-testid="stSidebar"] .stRadio label {
    font-size: 0.85rem;
    letter-spacing: 0.04em;
    padding: 5px 0;
    color: #9b8f82 !important;
    transition: color 0.2s;
}
section[data-testid="stSidebar"] .stRadio label:hover { color: #e8936a !important; }

/* ── Page header ── */
.page-eyebrow {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #e8936a;
    margin-bottom: 0.4rem;
}
.page-title {
    font-family: 'Playfair Display', serif;
    font-weight: 900;
    font-size: 2.8rem;
    line-height: 1.05;
    color: #faf8f5;
    margin-bottom: 0.3rem;
}
.page-subtitle {
    font-size: 0.95rem;
    color: #7a6e65;
    font-weight: 300;
    margin-bottom: 2rem;
    max-width: 640px;
    line-height: 1.6;
}

/* ── KPI cards ── */
.kpi-row { display: flex; gap: 1rem; margin-bottom: 2rem; }
.kpi-card {
    flex: 1;
    background: #ffffff;
    border: 1px solid #ede8e2;
    border-radius: 12px;
    padding: 1.3rem 1.5rem;
    position: relative;
    overflow: hidden;
}
.kpi-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #e8936a, #2a9d8f);
}
.kpi-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #9b8f82;
    margin-bottom: 0.5rem;
}
.kpi-value {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    font-weight: 700;
    color: #1a1814;
    line-height: 1;
}
.kpi-sub {
    font-size: 0.75rem;
    color: #9b8f82;
    margin-top: 0.3rem;
}

/* ── Section label ── */
.section-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #9b8f82;
    margin-bottom: 0.6rem;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid #ede8e2;
}

/* ── Insight strip ── */
.insight {
    background: #fff8f4;
    border-left: 3px solid #e8936a;
    border-radius: 0 8px 8px 0;
    padding: 0.9rem 1.2rem;
    margin-bottom: 0.7rem;
    font-size: 0.87rem;
    color: #4a4039;
    line-height: 1.6;
}
.insight strong { color: #1a1814; }

/* ── Divider ── */
hr { border-color: #ede8e2 !important; margin: 1.5rem 0 !important; }

/* ── Streamlit overrides ── */
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
[data-testid="stMetricValue"] {
    font-family: 'Playfair Display', serif !important;
    font-size: 1.8rem !important;
    color: #1a1814 !important;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PLOTLY THEME
# ══════════════════════════════════════════════════════════════════════════════

COLORS = {
    "terracotta": "#e8936a",
    "ocean":      "#2a9d8f",
    "navy":       "#264653",
    "sand":       "#e9c46a",
    "rose":       "#e76f51",
    "sage":       "#a8c5a0",
    "cream":      "#faf8f5",
    "ink":        "#1a1814",
}

COLOR_SEQ = [
    "#e8936a", "#2a9d8f", "#264653", "#e9c46a",
    "#e76f51", "#a8c5a0", "#c9b29a", "#5d7a8a",
]

CHART_BASE: Dict[str, Any] = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#7a6e65", size=12),
    xaxis=dict(gridcolor="#ede8e2", zerolinecolor="#ede8e2",
               tickfont=dict(color="#9b8f82"), linecolor="#ede8e2"),
    yaxis=dict(gridcolor="#ede8e2", zerolinecolor="#ede8e2",
               tickfont=dict(color="#9b8f82"), linecolor="#ede8e2"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#7a6e65")),
    margin=dict(l=20, r=20, t=36, b=20),
)

# ══════════════════════════════════════════════════════════════════════════════
# DATA LAYER — all queries run through here
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn


@st.cache_data(ttl=600)
def q(sql: str) -> pd.DataFrame:
    return pd.read_sql_query(sql, get_conn())


# ── Pre-load key datasets ──────────────────────────────────────────────────

@st.cache_data(ttl=600)
def load_all():
    listings  = q("SELECT * FROM listings")
    hosts     = q("SELECT * FROM hosts")
    calendar  = q("SELECT * FROM calendar")
    reviews   = q("SELECT * FROM reviews")
    return listings, hosts, calendar, reviews

listings, hosts, calendar, reviews = load_all()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(
        "<p style='font-family:Playfair Display,serif;font-size:1.3rem;"
        "font-weight:700;color:#faf8f5;margin:0 0 0.1rem 0;'>"
        "Cape Town</p>"
        "<p style='font-size:0.7rem;letter-spacing:0.2em;text-transform:uppercase;"
        "color:#5a4f47;margin:0 0 2rem 0;'>Airbnb Analytics</p>",
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigate",
        [
            "🏙  Market Overview",
            "🗺  Neighbourhoods",
            "👤  Host Intelligence",
            "📅  Pricing & Seasons",
            "💬  Reviews & Occupancy",
        ],
        label_visibility="collapsed",
    )

    st.markdown("<hr style='border-color:#2e2820;margin:1.5rem 0;'>", unsafe_allow_html=True)

    # Quick stats
    total_listings = len(listings)
    total_hosts    = listings["host_id"].nunique()
    avg_price      = int(listings["price_zar"].mean())
    st.markdown(
        f"<p style='font-size:0.7rem;color:#5a4f47;line-height:2;'>"
        f"<span style='color:#9b8f82;'>Listings</span> &nbsp; "
        f"<span style='color:#e8936a;font-weight:600;'>{total_listings:,}</span><br>"
        f"<span style='color:#9b8f82;'>Hosts</span> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; "
        f"<span style='color:#e8936a;font-weight:600;'>{total_hosts:,}</span><br>"
        f"<span style='color:#9b8f82;'>Avg price</span> &nbsp; "
        f"<span style='color:#e8936a;font-weight:600;'>R{avg_price:,}</span>"
        f"</p>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def kpi(label, value, sub=""):
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{sub_html}</div>'
    )

def section(title):
    st.markdown(f'<div class="section-label">{title}</div>', unsafe_allow_html=True)

def insight(text):
    st.markdown(f'<div class="insight">{text}</div>', unsafe_allow_html=True)

def header(eyebrow, title, subtitle):
    st.markdown(
        f'<div class="page-eyebrow">{eyebrow}</div>'
        f'<div class="page-title">{title}</div>'
        f'<div class="page-subtitle">{subtitle}</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — MARKET OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

if "Market Overview" in page:

    header(
        "Cape Town · 2024",
        "The Short-Term\nRental Market",
        "A data-driven portrait of Cape Town's Airbnb ecosystem — "
        "pricing, supply, room types, and the shape of the market.",
    )

    # ── KPIs ──
    avg_price    = int(listings["price_zar"].mean())
    avg_rating   = round(listings["review_score_rating"].dropna().mean(), 2)
    avg_avail    = int(listings["availability_365"].mean())
    total_rev    = int(listings["number_of_reviews"].sum())
    superhost_n  = int((hosts["host_is_superhost"] == "t").sum())
    superhost_pct = round(superhost_n / len(hosts) * 100, 1)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(kpi("Total Listings",  f"{len(listings):,}", f"{listings['neighbourhood'].nunique()} areas"), unsafe_allow_html=True)
    c2.markdown(kpi("Avg Nightly Price", f"R{avg_price:,}", "across all room types"), unsafe_allow_html=True)
    c3.markdown(kpi("Avg Review Score",  f"{avg_rating}", "out of 5.0"), unsafe_allow_html=True)
    c4.markdown(kpi("Total Reviews",  f"{total_rev:,}", "guest reviews"), unsafe_allow_html=True)
    c5.markdown(kpi("Superhosts",  f"{superhost_pct}%", f"{superhost_n} of {len(hosts)} hosts"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row: Room types + Property types ──
    col1, col2 = st.columns([1, 1])

    with col1:
        section("Supply by Room Type")
        rt = listings["room_type"].value_counts().reset_index()
        rt.columns = ["room_type", "count"]
        fig = go.Figure(go.Pie(
            labels=rt["room_type"], values=rt["count"],
            hole=0.62,
            marker=dict(colors=COLOR_SEQ[:3], line=dict(color="#faf8f5", width=3)),
            textinfo="label+percent",
            textfont=dict(family="DM Sans", color="#4a4039", size=12),
            hovertemplate="<b>%{label}</b><br>%{value:,} listings (%{percent})<extra></extra>",
        ))
        fig.add_annotation(
            text=f"<b>{len(listings):,}</b><br><span style='font-size:11px'>listings</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=18, color="#1a1814", family="Playfair Display"),
        )
        fig.update_layout(CHART_BASE, height=320, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section("Top Property Types")
        pt = listings["property_type"].value_counts().head(8).reset_index()
        pt.columns = ["type", "count"]
        fig2 = go.Figure(go.Bar(
            x=pt["count"], y=pt["type"],
            orientation="h",
            marker=dict(
                color=pt["count"],
                colorscale=[[0,"#f5ede6"],[1,"#e8936a"]],
                line=dict(width=0),
            ),
            text=pt["count"].apply(lambda x: f"{x:,}"),
            textposition="outside",
            textfont=dict(color="#9b8f82", size=11),
            hovertemplate="<b>%{y}</b>: %{x:,} listings<extra></extra>",
        ))
        fig2.update_layout(CHART_BASE, height=320, showlegend=False,
                           coloraxis_showscale=False,
                           xaxis_title="", yaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)

    # ── Price distribution ──
    section("Nightly Price Distribution (ZAR)")
    price_clip = listings[listings["price_zar"] <= 10000]
    fig3 = go.Figure(go.Histogram(
        x=price_clip["price_zar"], nbinsx=50,
        marker=dict(color="#e8936a", opacity=0.85, line=dict(color="#faf8f5", width=0.5)),
        hovertemplate="R%{x:,} — %{y} listings<extra></extra>",
    ))
    fig3.add_vline(
        x=listings["price_zar"].mean(),
        line_dash="dash", line_color="#2a9d8f", line_width=2,
        annotation_text=f"Avg R{int(listings['price_zar'].mean()):,}",
        annotation_font=dict(color="#2a9d8f", size=11),
    )
    fig3.update_layout(CHART_BASE, height=240,
                       xaxis_title="Nightly Price (R)", yaxis_title="Listings")
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    section("Market Insights")
    i1, i2, i3 = st.columns(3)
    with i1:
        insight("<strong>Entire homes dominate.</strong> Over 60% of listings are entire homes or apartments, "
                "reflecting Cape Town's strong leisure tourism demand for private, self-catering stays.")
    with i2:
        insight("<strong>Apartments lead supply.</strong> The most common property type is the apartment, "
                "followed by houses — aligning with Cape Town's dense Atlantic Seaboard and City Bowl precincts.")
    with i3:
        insight("<strong>Most listings are mid-range.</strong> The bulk of supply sits between R800–R3,000 per night, "
                "with a long tail of premium villas and penthouses skewing the average upward.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — NEIGHBOURHOODS
# ══════════════════════════════════════════════════════════════════════════════

elif "Neighbourhoods" in page:

    header(
        "Geographic Analysis",
        "Where to Stay,\nWhere to Invest",
        "Comparing Cape Town's 20 Airbnb neighbourhoods across price, "
        "rating, occupancy, and value — from Clifton to Mitchell's Plain.",
    )

    # ── Neighbourhood summary ──
    nbhd = q("""
        SELECT
            neighbourhood,
            COUNT(*)                                                   AS listings,
            ROUND(AVG(price_zar), 0)                                   AS avg_price,
            ROUND(AVG(review_score_rating), 2)                         AS avg_rating,
            ROUND(AVG((365 - availability_365) / 365.0) * 100, 1)     AS occupancy_pct,
            ROUND(AVG(price_zar) * AVG(365 - availability_365), 0)    AS est_annual_revenue,
            ROUND(AVG(review_score_rating) / (AVG(price_zar)/1000.0), 3) AS value_score
        FROM listings
        WHERE review_score_rating IS NOT NULL
        GROUP BY neighbourhood
        ORDER BY avg_price DESC
    """)

    # ── KPIs ──
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi("Most Expensive", nbhd.iloc[0]["neighbourhood"], f"R{int(nbhd.iloc[0]['avg_price']):,} avg/night"), unsafe_allow_html=True)
    c2.markdown(kpi("Most Affordable", nbhd.iloc[-1]["neighbourhood"], f"R{int(nbhd.iloc[-1]['avg_price']):,} avg/night"), unsafe_allow_html=True)
    best_val = nbhd.loc[nbhd["value_score"].idxmax()]
    c3.markdown(kpi("Best Value", best_val["neighbourhood"], f"Score {best_val['value_score']:.2f}"), unsafe_allow_html=True)
    best_occ = nbhd.loc[nbhd["occupancy_pct"].idxmax()]
    c4.markdown(kpi("Highest Occupancy", best_occ["neighbourhood"], f"{best_occ['occupancy_pct']}%"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Average price by neighbourhood ──
    section("Average Nightly Price by Neighbourhood (ZAR)")
    fig = go.Figure(go.Bar(
        x=nbhd["avg_price"], y=nbhd["neighbourhood"],
        orientation="h",
        marker=dict(
            color=nbhd["avg_price"],
            colorscale=[[0,"#f5ede6"],[0.5,"#e8936a"],[1,"#264653"]],
            line=dict(width=0),
        ),
        text=nbhd["avg_price"].apply(lambda x: f"R{int(x):,}"),
        textposition="outside",
        textfont=dict(color="#9b8f82", size=10),
        hovertemplate="<b>%{y}</b><br>R%{x:,.0f}/night<extra></extra>",
    ))
    fig.update_layout(CHART_BASE, height=520,
                      coloraxis_showscale=False,
                      yaxis=dict(**CHART_BASE["yaxis"], autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

    # ── Bubble: Price vs Rating vs Occupancy ──
    col1, col2 = st.columns(2)

    with col1:
        section("Price vs Rating (bubble = listings)")
        fig2 = px.scatter(
            nbhd, x="avg_price", y="avg_rating",
            size="listings", color="occupancy_pct",
            hover_name="neighbourhood",
            color_continuous_scale=[[0,"#f5ede6"],[1,"#2a9d8f"]],
            labels={"avg_price":"Avg Price (R)","avg_rating":"Avg Rating",
                    "occupancy_pct":"Occupancy %"},
            size_max=40,
        )
        fig2.update_traces(
            hovertemplate="<b>%{hovertext}</b><br>R%{x:,.0f}/night<br>Rating: %{y}<extra></extra>"
        )
        fig2.update_layout(CHART_BASE, height=340,
                           coloraxis_colorbar=dict(title="Occ %",
                                                   tickfont=dict(color="#9b8f82")))
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        section("Estimated Annual Revenue by Neighbourhood")
        rev_df = nbhd.sort_values("est_annual_revenue", ascending=True).tail(12)
        fig3 = go.Figure(go.Bar(
            x=rev_df["est_annual_revenue"], y=rev_df["neighbourhood"],
            orientation="h",
            marker=dict(color="#2a9d8f", opacity=0.85, line=dict(width=0)),
            text=rev_df["est_annual_revenue"].apply(lambda x: f"R{x/1000:.0f}k"),
            textposition="outside",
            textfont=dict(color="#9b8f82", size=10),
            hovertemplate="<b>%{y}</b><br>Est. R%{x:,.0f}/yr<extra></extra>",
        ))
        fig3.update_layout(CHART_BASE, height=340)
        st.plotly_chart(fig3, use_container_width=True)

    # ── Quadrant table ──
    st.markdown("<hr>", unsafe_allow_html=True)
    section("Neighbourhood Market Quadrants")

    med_price  = nbhd["avg_price"].mean()
    med_rating = nbhd["avg_rating"].mean()

    def classify(row):
        if row["avg_price"] >= med_price and row["avg_rating"] >= med_rating:
            return "⭐ Star"
        elif row["avg_price"] >= med_price and row["avg_rating"] < med_rating:
            return "💰 Overpriced"
        elif row["avg_price"] < med_price and row["avg_rating"] >= med_rating:
            return "💎 Hidden Gem"
        else:
            return "⚠️ Struggling"

    nbhd["quadrant"] = nbhd.apply(classify, axis=1)
    quad_display = nbhd[["neighbourhood","avg_price","avg_rating","occupancy_pct","quadrant"]].copy()
    quad_display.columns = ["Neighbourhood","Avg Price (R)","Avg Rating","Occupancy %","Quadrant"]
    quad_display["Avg Price (R)"] = quad_display["Avg Price (R)"].apply(lambda x: f"R{int(x):,}")
    st.dataframe(quad_display.reset_index(drop=True), use_container_width=True, height=380)

    insight("<strong>Hidden Gems:</strong> Observatory and Woodstock offer strong guest ratings at prices "
            "well below the city average — making them the best-value areas for budget-conscious travellers "
            "and high-yield investment for hosts entering the market.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — HOST INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════

elif "Host Intelligence" in page:

    header(
        "Host Analysis",
        "Who Runs the\nCape Town Market?",
        "From individual hosts with a spare room to multi-property operators — "
        "unpacking host behaviour, superhost performance, and revenue concentration.",
    )

    # ── Superhost vs regular ──
    superhost_stats = q("""
        SELECT
            h.host_is_superhost                                        AS superhost,
            COUNT(DISTINCT h.host_id)                                  AS hosts,
            COUNT(l.listing_id)                                        AS listings,
            ROUND(AVG(l.price_zar), 0)                                 AS avg_price,
            ROUND(AVG(l.review_score_rating), 2)                       AS avg_rating,
            ROUND(AVG(l.number_of_reviews), 1)                         AS avg_reviews,
            ROUND(AVG((365 - l.availability_365)/365.0)*100, 1)        AS est_occupancy_pct
        FROM hosts h
        JOIN listings l ON h.host_id = l.host_id
        GROUP BY h.host_is_superhost
    """)

    s_row = superhost_stats[superhost_stats["superhost"] == "t"].iloc[0]
    r_row = superhost_stats[superhost_stats["superhost"] == "f"].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    price_diff = round((s_row["avg_price"] - r_row["avg_price"]) / r_row["avg_price"] * 100, 1)
    rating_diff = round(s_row["avg_rating"] - r_row["avg_rating"], 2)
    c1.markdown(kpi("Superhost Avg Price", f"R{int(s_row['avg_price']):,}", f"+{price_diff}% vs regular"), unsafe_allow_html=True)
    c2.markdown(kpi("Superhost Avg Rating", str(s_row["avg_rating"]), f"+{rating_diff} vs regular"), unsafe_allow_html=True)
    c3.markdown(kpi("Superhost Avg Reviews", str(s_row["avg_reviews"]), "per listing"), unsafe_allow_html=True)
    c4.markdown(kpi("Superhost Occupancy", f"{s_row['est_occupancy_pct']}%", f"vs {r_row['est_occupancy_pct']}% regular"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        section("Superhost vs Regular — Key Metrics")
        categories = ["Avg Price (÷100)", "Avg Rating (×10)", "Avg Reviews (÷10)", "Occupancy %"]
        s_vals = [s_row["avg_price"]/100, s_row["avg_rating"]*10,
                  s_row["avg_reviews"]/10, s_row["est_occupancy_pct"]]
        r_vals = [r_row["avg_price"]/100, r_row["avg_rating"]*10,
                  r_row["avg_reviews"]/10, r_row["est_occupancy_pct"]]

        fig = go.Figure()
        fig.add_trace(go.Bar(name="Superhost", x=categories, y=s_vals,
                             marker_color=COLORS["terracotta"], marker_line_width=0))
        fig.add_trace(go.Bar(name="Regular Host", x=categories, y=r_vals,
                             marker_color=COLORS["ocean"], marker_opacity=0.6,
                             marker_line_width=0))
        fig.update_layout(CHART_BASE, height=320, barmode="group",
                          legend=dict(orientation="h", y=1.08))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section("Host Listings Distribution")
        merged = listings.merge(hosts[["host_id","host_listings_count","host_is_superhost"]],
                                on="host_id", how="left")
        host_count = merged.groupby("host_id")["listing_id"].count().reset_index()
        host_count.columns = ["host_id","actual_listings"]
        bucket = host_count["actual_listings"].apply(
            lambda x: "1 listing" if x == 1
            else "2 listings" if x == 2
            else "3–5 listings" if x <= 5
            else "6+ listings"
        ).value_counts().reset_index()
        bucket.columns = ["type","hosts"]
        order = ["1 listing","2 listings","3–5 listings","6+ listings"]
        bucket["type"] = pd.Categorical(bucket["type"], categories=order, ordered=True)
        bucket = bucket.sort_values("type")

        fig2 = go.Figure(go.Pie(
            labels=bucket["type"], values=bucket["hosts"],
            hole=0.58,
            marker=dict(colors=COLOR_SEQ, line=dict(color="#faf8f5", width=3)),
            textinfo="label+percent",
            textfont=dict(family="DM Sans", size=11, color="#4a4039"),
            hovertemplate="<b>%{label}</b>: %{value} hosts<extra></extra>",
        ))
        fig2.update_layout(CHART_BASE, height=320, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Host tenure ──
    section("Performance by Host Tenure")
    tenure = q("""
        SELECT
            CASE
                WHEN CAST(strftime('%Y','now') AS INT) - CAST(substr(host_since,1,4) AS INT) >= 7
                    THEN '7+ yrs · Veteran'
                WHEN CAST(strftime('%Y','now') AS INT) - CAST(substr(host_since,1,4) AS INT) >= 4
                    THEN '4–6 yrs · Experienced'
                WHEN CAST(strftime('%Y','now') AS INT) - CAST(substr(host_since,1,4) AS INT) >= 2
                    THEN '2–3 yrs · Intermediate'
                ELSE '< 2 yrs · New'
            END AS tenure,
            COUNT(DISTINCT h.host_id)               AS hosts,
            ROUND(AVG(l.review_score_rating), 2)    AS avg_rating,
            ROUND(AVG(l.price_zar), 0)              AS avg_price,
            ROUND(AVG(l.number_of_reviews), 1)      AS avg_reviews
        FROM hosts h
        JOIN listings l ON h.host_id = l.host_id
        WHERE l.review_score_rating IS NOT NULL
        GROUP BY tenure
        ORDER BY avg_rating DESC
    """)

    col3, col4 = st.columns(2)
    with col3:
        fig3 = go.Figure(go.Bar(
            x=tenure["tenure"], y=tenure["avg_rating"],
            marker=dict(color=COLORS["terracotta"], opacity=0.85, line=dict(width=0)),
            text=tenure["avg_rating"], textposition="outside",
            textfont=dict(color="#9b8f82", size=11),
            hovertemplate="<b>%{x}</b><br>Rating: %{y}<extra></extra>",
        ))
        fig3.update_layout(CHART_BASE, height=280,
                           yaxis=dict(**CHART_BASE["yaxis"], range=[4.0, 5.0]),
                           title=dict(text="Avg Rating by Tenure",
                                      font=dict(size=12, color="#9b8f82")))
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        fig4 = go.Figure(go.Bar(
            x=tenure["tenure"], y=tenure["avg_price"],
            marker=dict(color=COLORS["ocean"], opacity=0.85, line=dict(width=0)),
            text=tenure["avg_price"].apply(lambda x: f"R{int(x):,}"),
            textposition="outside",
            textfont=dict(color="#9b8f82", size=11),
            hovertemplate="<b>%{x}</b><br>R%{y:,.0f}/night<extra></extra>",
        ))
        fig4.update_layout(CHART_BASE, height=280,
                           title=dict(text="Avg Price by Tenure",
                                      font=dict(size=12, color="#9b8f82")))
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    section("Host Intelligence Insights")
    ia, ib, ic = st.columns(3)
    with ia:
        insight(f"<strong>Superhosts charge more and earn it.</strong> Superhost listings average "
                f"R{int(s_row['avg_price']):,}/night vs R{int(r_row['avg_price']):,} for regular hosts "
                f"— yet still achieve higher ratings and more reviews.")
    with ib:
        insight("<strong>Most hosts are individuals.</strong> The majority of hosts manage just one listing, "
                "suggesting the Cape Town market is still primarily driven by personal property rather than "
                "commercial operators.")
    with ic:
        insight("<strong>Experience pays off.</strong> Veteran hosts (7+ years) achieve the highest average "
                "review scores, suggesting that accumulated experience, guest communication, and property "
                "refinement compound over time.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — PRICING & SEASONS
# ══════════════════════════════════════════════════════════════════════════════

elif "Pricing & Seasons" in page:

    header(
        "Pricing Intelligence",
        "When Prices Rise\nand Fall",
        "Cape Town's coastal summer drives dramatic seasonal swings. "
        "Understanding when and why prices shift is key for hosts and guests alike.",
    )

    # ── Seasonal trend from calendar ──
    seasonal = q("""
        SELECT
            month,
            CASE month
                WHEN 1  THEN 'Jan' WHEN 2  THEN 'Feb' WHEN 3  THEN 'Mar'
                WHEN 4  THEN 'Apr' WHEN 5  THEN 'May' WHEN 6  THEN 'Jun'
                WHEN 7  THEN 'Jul' WHEN 8  THEN 'Aug' WHEN 9  THEN 'Sep'
                WHEN 10 THEN 'Oct' WHEN 11 THEN 'Nov' WHEN 12 THEN 'Dec'
            END AS month_name,
            ROUND(AVG(price_zar), 0)                                        AS avg_price,
            ROUND(AVG(CASE WHEN available='t' THEN 1.0 ELSE 0.0 END)*100,1) AS availability_pct
        FROM calendar
        GROUP BY month ORDER BY month
    """)

    # KPIs
    peak_month = seasonal.loc[seasonal["avg_price"].idxmax()]
    low_month  = seasonal.loc[seasonal["avg_price"].idxmin()]
    premium    = round((peak_month["avg_price"] - low_month["avg_price"]) / low_month["avg_price"] * 100, 1)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi("Peak Month", peak_month["month_name"], f"R{int(peak_month['avg_price'].item()):,} avg/night"), unsafe_allow_html=True)
    c2.markdown(kpi("Low Season", low_month["month_name"], f"R{int(low_month['avg_price'].item()):,} avg/night"), unsafe_allow_html=True)
    c3.markdown(kpi("Peak Premium", f"+{premium}%", "above low season"), unsafe_allow_html=True)
    c4.markdown(kpi("Peak Availability", f"{peak_month['availability_pct']}%", f"vs {low_month['availability_pct']}% low season"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Seasonal price + availability chart ──
    section("Monthly Avg Price & Availability (2024)")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=seasonal["month_name"], y=seasonal["avg_price"],
        name="Avg Nightly Price (R)",
        marker=dict(
            color=seasonal["avg_price"],
            colorscale=[[0,"#f5ede6"],[0.5,"#e8936a"],[1,"#264653"]],
            line=dict(width=0),
        ),
        hovertemplate="<b>%{x}</b><br>R%{y:,}/night<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=seasonal["month_name"], y=seasonal["availability_pct"],
        name="Availability %",
        mode="lines+markers",
        yaxis="y2",
        line=dict(color=COLORS["ocean"], width=2.5, dash="dot"),
        marker=dict(size=7, color=COLORS["ocean"]),
        hovertemplate="<b>%{x}</b><br>Availability: %{y}%<extra></extra>",
    ))
    fig.update_layout(
        CHART_BASE, height=320,
        coloraxis_showscale=False,
        yaxis=dict(**CHART_BASE["yaxis"], title="Avg Price (R)"),
        yaxis2=dict(overlaying="y", side="right", title="Availability %",
                    tickfont=dict(color=COLORS["ocean"]),
                    gridcolor="rgba(0,0,0,0)", range=[40, 70]),
        legend=dict(orientation="h", y=1.08),
        barmode="group",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Price buckets + bedrooms ──
    col1, col2 = st.columns(2)

    with col1:
        section("Price Band Distribution")
        price_bands = q("""
            SELECT
                CASE
                    WHEN price_zar < 500   THEN 'Under R500'
                    WHEN price_zar < 1000  THEN 'R500–R999'
                    WHEN price_zar < 2000  THEN 'R1,000–R1,999'
                    WHEN price_zar < 3000  THEN 'R2,000–R2,999'
                    WHEN price_zar < 5000  THEN 'R3,000–R4,999'
                    ELSE                        'R5,000+'
                END AS band,
                COUNT(*) AS listings,
                ROUND(AVG(review_score_rating),2) AS avg_rating
            FROM listings
            GROUP BY band
            ORDER BY MIN(price_zar)
        """)
        fig2 = go.Figure(go.Bar(
            x=price_bands["band"], y=price_bands["listings"],
            marker=dict(color=COLORS["terracotta"], opacity=0.85, line=dict(width=0)),
            text=price_bands["listings"], textposition="outside",
            textfont=dict(color="#9b8f82", size=11),
            hovertemplate="<b>%{x}</b><br>%{y} listings<extra></extra>",
        ))
        fig2.update_layout(CHART_BASE, height=300)
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        section("Price Scaling by Bedroom Count")
        bedrooms_df = q("""
            SELECT bedrooms,
                   COUNT(*) AS listings,
                   ROUND(AVG(price_zar),0) AS avg_price,
                   ROUND(MIN(price_zar),0) AS min_price,
                   ROUND(MAX(price_zar),0) AS max_price
            FROM listings WHERE bedrooms BETWEEN 1 AND 6
            GROUP BY bedrooms ORDER BY bedrooms
        """)
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=bedrooms_df["bedrooms"], y=bedrooms_df["avg_price"],
            mode="lines+markers",
            line=dict(color=COLORS["ocean"], width=2.5),
            marker=dict(size=9, color=COLORS["ocean"]),
            fill="tozeroy", fillcolor="rgba(42,157,143,0.08)",
            name="Avg Price",
            hovertemplate="<b>%{x} bedrooms</b><br>R%{y:,} avg<extra></extra>",
        ))
        fig3.update_layout(CHART_BASE, height=300,
                           xaxis=dict(**CHART_BASE["xaxis"],
                                      title="Bedrooms",
                                      tickvals=list(range(1,7))),
                           yaxis=dict(**CHART_BASE["yaxis"], title="Avg Price (R)"))
        st.plotly_chart(fig3, use_container_width=True)

    # ── Instant bookable ──
    st.markdown("<hr>", unsafe_allow_html=True)
    section("Does Instant Booking Change Performance?")
    instant = q("""
        SELECT instant_bookable,
               COUNT(*) AS listings,
               ROUND(AVG(price_zar),0) AS avg_price,
               ROUND(AVG(review_score_rating),2) AS avg_rating,
               ROUND(AVG(number_of_reviews),1) AS avg_reviews,
               ROUND(AVG((365-availability_365)/365.0)*100,1) AS est_occupancy_pct
        FROM listings GROUP BY instant_bookable
    """)
    t_row = instant[instant["instant_bookable"]=="t"].iloc[0]
    f_row = instant[instant["instant_bookable"]=="f"].iloc[0]

    ic1, ic2, ic3, ic4 = st.columns(4)
    ic1.metric("Instant Book Occupancy", f"{t_row['est_occupancy_pct']}%",
               f"+{round(t_row['est_occupancy_pct']-f_row['est_occupancy_pct'],1)}% vs non-instant")
    ic2.metric("Instant Book Avg Price",  f"R{int(t_row['avg_price']):,}")
    ic3.metric("Instant Book Avg Rating", str(t_row["avg_rating"]))
    ic4.metric("Instant Book Avg Reviews",str(t_row["avg_reviews"]))

    insight("<strong>Instant bookable listings outperform on occupancy.</strong> Guests increasingly prefer "
            "the friction-free booking experience — listings with instant booking enabled show higher estimated "
            "occupancy rates, suggesting hosts should consider enabling this feature to maximise bookings.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — REVIEWS & OCCUPANCY
# ══════════════════════════════════════════════════════════════════════════════

elif "Reviews & Occupancy" in page:

    header(
        "Guest Activity",
        "Reviews, Demand\n& Occupancy Patterns",
        "Review volume as a proxy for booking activity — tracking momentum, "
        "identifying high-demand areas, and spotting listings that have gone quiet.",
    )

    # ── KPIs ──
    total_reviews  = len(reviews)
    reviewed_pct   = round(
        len(listings[listings["number_of_reviews"] > 0]) / len(listings) * 100, 1
    )
    avg_occ = round(
        ((365 - listings["availability_365"]) / 365).mean() * 100, 1
    )
    avg_reviews_pm = round(listings["reviews_per_month"].dropna().mean(), 2)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi("Total Reviews", f"{total_reviews:,}", "across all listings"), unsafe_allow_html=True)
    c2.markdown(kpi("Listings Reviewed", f"{reviewed_pct}%", "have at least one review"), unsafe_allow_html=True)
    c3.markdown(kpi("Avg Occupancy", f"{avg_occ}%", "estimated market-wide"), unsafe_allow_html=True)
    c4.markdown(kpi("Avg Reviews/Month", str(avg_reviews_pm), "per active listing"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Review trend ──
    section("Review Activity Over Time (Monthly)")
    rev_trend = q("""
        SELECT substr(date,1,7) AS ym, COUNT(*) AS reviews
        FROM reviews GROUP BY ym ORDER BY ym
    """)
    rev_trend["rolling_3m"] = rev_trend["reviews"].rolling(3, min_periods=1).mean().round(1)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=rev_trend["ym"], y=rev_trend["reviews"],
        name="Monthly Reviews",
        marker=dict(color=COLORS["terracotta"], opacity=0.5, line=dict(width=0)),
        hovertemplate="<b>%{x}</b>: %{y} reviews<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=rev_trend["ym"], y=rev_trend["rolling_3m"],
        name="3-Month Rolling Avg",
        mode="lines",
        line=dict(color=COLORS["navy"], width=2.5),
        hovertemplate="<b>%{x}</b> rolling avg: %{y}<extra></extra>",
    ))
    fig.update_layout(CHART_BASE, height=280,
                      legend=dict(orientation="h", y=1.08))
    st.plotly_chart(fig, use_container_width=True)

    # ── Occupancy + reviews by neighbourhood ──
    col1, col2 = st.columns(2)

    with col1:
        section("Estimated Occupancy by Neighbourhood")
        occ_nbhd = q("""
            SELECT neighbourhood,
                   ROUND(AVG((365-availability_365)/365.0)*100, 1) AS occupancy_pct,
                   COUNT(*) AS listings
            FROM listings
            GROUP BY neighbourhood
            ORDER BY occupancy_pct DESC
        """)
        fig2 = go.Figure(go.Bar(
            x=occ_nbhd["occupancy_pct"],
            y=occ_nbhd["neighbourhood"],
            orientation="h",
            marker=dict(
                color=occ_nbhd["occupancy_pct"],
                colorscale=[[0,"#f5ede6"],[1,"#2a9d8f"]],
                line=dict(width=0),
            ),
            text=occ_nbhd["occupancy_pct"].apply(lambda x: f"{x}%"),
            textposition="outside",
            textfont=dict(color="#9b8f82", size=10),
            hovertemplate="<b>%{y}</b><br>%{x}% occupied<extra></extra>",
        ))
        fig2.update_layout(CHART_BASE, height=520,
                           coloraxis_showscale=False,
                           xaxis=dict(**CHART_BASE["xaxis"], title="Occupancy %"),
                           yaxis=dict(**CHART_BASE["yaxis"], autorange="reversed"))
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        section("Review Volume by Neighbourhood")
        rev_nbhd = q("""
            SELECT l.neighbourhood,
                   COUNT(r.review_id) AS total_reviews,
                   ROUND(COUNT(r.review_id)*1.0/COUNT(DISTINCT r.listing_id),1) AS reviews_per_listing
            FROM listings l
            LEFT JOIN reviews r ON l.listing_id = r.listing_id
            GROUP BY l.neighbourhood
            ORDER BY total_reviews DESC
        """)
        fig3 = go.Figure(go.Bar(
            x=rev_nbhd["total_reviews"],
            y=rev_nbhd["neighbourhood"],
            orientation="h",
            marker=dict(
                color=rev_nbhd["total_reviews"],
                colorscale=[[0,"#f5ede6"],[1,"#264653"]],
                line=dict(width=0),
            ),
            text=rev_nbhd["total_reviews"].apply(lambda x: f"{x:,}"),
            textposition="outside",
            textfont=dict(color="#9b8f82", size=10),
            hovertemplate="<b>%{y}</b><br>%{x:,} reviews<extra></extra>",
        ))
        fig3.update_layout(CHART_BASE, height=520,
                           coloraxis_showscale=False,
                           xaxis=dict(**CHART_BASE["xaxis"], title="Total Reviews"),
                           yaxis=dict(**CHART_BASE["yaxis"], autorange="reversed"))
        st.plotly_chart(fig3, use_container_width=True)

    # ── Rating bands ──
    st.markdown("<hr>", unsafe_allow_html=True)
    section("Review Score vs Occupancy — Does Rating Drive Demand?")
    rating_bands = q("""
        SELECT
            CASE
                WHEN review_score_rating >= 4.9 THEN '4.9–5.0 Exceptional'
                WHEN review_score_rating >= 4.7 THEN '4.7–4.8 Excellent'
                WHEN review_score_rating >= 4.5 THEN '4.5–4.6 Very Good'
                WHEN review_score_rating >= 4.0 THEN '4.0–4.4 Good'
                ELSE 'Below 4.0'
            END AS rating_band,
            COUNT(*) AS listings,
            ROUND(AVG(price_zar),0) AS avg_price,
            ROUND(AVG((365-availability_365)/365.0)*100,1) AS est_occupancy_pct
        FROM listings WHERE review_score_rating IS NOT NULL
        GROUP BY rating_band
        ORDER BY MIN(review_score_rating) DESC
    """)

    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        x=rating_bands["rating_band"], y=rating_bands["est_occupancy_pct"],
        name="Occupancy %",
        marker=dict(color=COLORS["terracotta"], opacity=0.85, line=dict(width=0)),
        text=rating_bands["est_occupancy_pct"].apply(lambda x: f"{x}%"),
        textposition="outside", textfont=dict(color="#9b8f82", size=11),
        hovertemplate="<b>%{x}</b><br>Occupancy: %{y}%<extra></extra>",
    ))
    fig4.add_trace(go.Scatter(
        x=rating_bands["rating_band"], y=rating_bands["avg_price"],
        name="Avg Price (R)", mode="lines+markers", yaxis="y2",
        line=dict(color=COLORS["ocean"], width=2.5),
        marker=dict(size=8, color=COLORS["ocean"]),
        hovertemplate="<b>%{x}</b><br>R%{y:,}<extra></extra>",
    ))
    fig4.update_layout(
        CHART_BASE, height=300,
        yaxis=dict(**CHART_BASE["yaxis"], title="Occupancy %"),
        yaxis2=dict(overlaying="y", side="right", title="Avg Price (R)",
                    tickfont=dict(color=COLORS["ocean"]),
                    gridcolor="rgba(0,0,0,0)"),
        legend=dict(orientation="h", y=1.08),
    )
    st.plotly_chart(fig4, use_container_width=True)

    section("Key Takeaways")
    ta, tb, tc = st.columns(3)
    with ta:
        insight("<strong>Ratings correlate with occupancy.</strong> Listings rated 4.9–5.0 show the highest "
                "estimated occupancy rates — confirming that guest experience directly drives repeat demand "
                "and platform visibility.")
    with tb:
        insight("<strong>City Bowl drives review volume.</strong> Cape Town City Centre and Sea Point generate "
                "the most review activity, reflecting their central location and high tourist footfall year-round.")
    with tc:
        insight("<strong>The market is growing.</strong> Review activity shows a steady upward trend over the "
                "tracked period — a positive signal for new hosts considering entering the Cape Town market.")