-- ═══════════════════════════════════════════════════════════════════════════
-- Cape Town Airbnb Analytics — SQL Portfolio
-- Database: airbnb_capetown.db (SQLite)
-- Author:   Zolile Nonzapa
-- ═══════════════════════════════════════════════════════════════════════════
-- Tables:
--   listings  — property details, price, availability, reviews
--   hosts     — host profiles, superhost status, listing count
--   calendar  — daily availability and price per listing (500 listings x 365d)
--   reviews   — guest review text and dates
-- ═══════════════════════════════════════════════════════════════════════════


-- ───────────────────────────────────────────────────────────────────────────
-- SECTION 1: MARKET OVERVIEW
-- ───────────────────────────────────────────────────────────────────────────

-- Q1. High-level market snapshot
-- What does the Cape Town Airbnb market look like at a glance?
SELECT
    COUNT(*)                                        AS total_listings,
    COUNT(DISTINCT host_id)                         AS total_hosts,
    COUNT(DISTINCT neighbourhood)                   AS total_neighbourhoods,
    ROUND(AVG(price_zar), 0)                        AS avg_price_zar,
    ROUND(MIN(price_zar), 0)                        AS min_price_zar,
    ROUND(MAX(price_zar), 0)                        AS max_price_zar,
    ROUND(AVG(number_of_reviews), 1)                AS avg_reviews_per_listing,
    ROUND(AVG(review_score_rating), 2)              AS avg_review_score,
    ROUND(AVG(availability_365), 0)                 AS avg_availability_days
FROM listings;


-- Q2. Listings and average price by room type
-- Which room types dominate the market?
SELECT
    room_type,
    COUNT(*)                                        AS total_listings,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS market_share_pct,
    ROUND(AVG(price_zar), 0)                        AS avg_price_zar,
    ROUND(MIN(price_zar), 0)                        AS min_price_zar,
    ROUND(MAX(price_zar), 0)                        AS max_price_zar
FROM listings
GROUP BY room_type
ORDER BY total_listings DESC;


-- Q3. Property type breakdown
-- What types of properties are listed?
SELECT
    property_type,
    COUNT(*)                                        AS total_listings,
    ROUND(AVG(price_zar), 0)                        AS avg_price_zar,
    ROUND(AVG(review_score_rating), 2)              AS avg_rating
FROM listings
GROUP BY property_type
ORDER BY total_listings DESC
LIMIT 10;


-- ───────────────────────────────────────────────────────────────────────────
-- SECTION 2: NEIGHBOURHOOD ANALYSIS
-- ───────────────────────────────────────────────────────────────────────────

-- Q4. Neighbourhood performance overview
-- Which areas have the most listings, highest prices, and best ratings?
SELECT
    neighbourhood,
    COUNT(*)                                        AS total_listings,
    ROUND(AVG(price_zar), 0)                        AS avg_price_zar,
    ROUND(AVG(review_score_rating), 2)              AS avg_rating,
    ROUND(AVG(availability_365), 0)                 AS avg_availability_days,
    SUM(number_of_reviews)                          AS total_reviews
FROM listings
GROUP BY neighbourhood
ORDER BY avg_price_zar DESC;


-- Q5. Most expensive vs most affordable neighbourhoods
-- Top 5 priciest and bottom 5 most affordable areas
SELECT neighbourhood, avg_price_zar, price_tier
FROM (
    SELECT
        neighbourhood,
        ROUND(AVG(price_zar), 0)                    AS avg_price_zar,
        'Premium'                                   AS price_tier,
        ROW_NUMBER() OVER (ORDER BY AVG(price_zar) DESC) AS rn
    FROM listings
    GROUP BY neighbourhood
) WHERE rn <= 5
UNION ALL
SELECT neighbourhood, avg_price_zar, price_tier
FROM (
    SELECT
        neighbourhood,
        ROUND(AVG(price_zar), 0)                    AS avg_price_zar,
        'Affordable'                                AS price_tier,
        ROW_NUMBER() OVER (ORDER BY AVG(price_zar) ASC) AS rn
    FROM listings
    GROUP BY neighbourhood
) WHERE rn <= 5
ORDER BY price_tier, avg_price_zar DESC;


-- Q6. Best value neighbourhoods
-- High rating + lower price = best value for guests
SELECT
    neighbourhood,
    ROUND(AVG(price_zar), 0)                        AS avg_price_zar,
    ROUND(AVG(review_score_rating), 2)              AS avg_rating,
    COUNT(*)                                        AS listings,
    ROUND(AVG(review_score_rating) / (AVG(price_zar) / 1000.0), 3) AS value_score
FROM listings
WHERE review_score_rating IS NOT NULL
  AND number_of_reviews >= 5
GROUP BY neighbourhood
HAVING listings >= 10
ORDER BY value_score DESC
LIMIT 10;


-- Q7. Price per bedroom by neighbourhood
-- Standardised pricing comparison across areas
SELECT
    neighbourhood,
    ROUND(AVG(price_zar / NULLIF(bedrooms, 0)), 0)  AS avg_price_per_bedroom,
    ROUND(AVG(price_zar), 0)                        AS avg_total_price,
    COUNT(*)                                        AS listings
FROM listings
WHERE bedrooms > 0
GROUP BY neighbourhood
ORDER BY avg_price_per_bedroom DESC;


-- ───────────────────────────────────────────────────────────────────────────
-- SECTION 3: HOST ANALYSIS
-- ───────────────────────────────────────────────────────────────────────────

-- Q8. Superhost vs regular host comparison
-- Do superhosts charge more? Are they rated better?
SELECT
    h.host_is_superhost,
    COUNT(DISTINCT h.host_id)                       AS total_hosts,
    COUNT(l.listing_id)                             AS total_listings,
    ROUND(AVG(l.price_zar), 0)                      AS avg_price_zar,
    ROUND(AVG(l.review_score_rating), 2)            AS avg_rating,
    ROUND(AVG(l.number_of_reviews), 1)              AS avg_reviews,
    ROUND(AVG(l.availability_365), 0)               AS avg_availability_days
FROM hosts h
JOIN listings l ON h.host_id = l.host_id
GROUP BY h.host_is_superhost;


-- Q9. Multi-listing hosts (potential commercial operators)
-- Hosts with 3+ listings may be commercial short-term rental operators
SELECT
    h.host_id,
    h.host_name,
    h.host_listings_count,
    h.host_is_superhost,
    COUNT(l.listing_id)                             AS actual_listings,
    ROUND(AVG(l.price_zar), 0)                      AS avg_price_zar,
    SUM(l.number_of_reviews)                        AS total_reviews
FROM hosts h
JOIN listings l ON h.host_id = l.host_id
GROUP BY h.host_id
HAVING actual_listings >= 3
ORDER BY actual_listings DESC
LIMIT 20;


-- Q10. Host tenure analysis
-- Do longer-serving hosts perform better?
SELECT
    CASE
        WHEN CAST(strftime('%Y', 'now') AS INT) - CAST(substr(host_since, 1, 4) AS INT) >= 7 THEN 'Veteran (7+ yrs)'
        WHEN CAST(strftime('%Y', 'now') AS INT) - CAST(substr(host_since, 1, 4) AS INT) >= 4 THEN 'Experienced (4-6 yrs)'
        WHEN CAST(strftime('%Y', 'now') AS INT) - CAST(substr(host_since, 1, 4) AS INT) >= 2 THEN 'Intermediate (2-3 yrs)'
        ELSE 'New (< 2 yrs)'
    END                                             AS host_tenure,
    COUNT(DISTINCT h.host_id)                       AS host_count,
    ROUND(AVG(l.review_score_rating), 2)            AS avg_rating,
    ROUND(AVG(l.price_zar), 0)                      AS avg_price_zar,
    ROUND(AVG(l.number_of_reviews), 1)              AS avg_reviews
FROM hosts h
JOIN listings l ON h.host_id = l.host_id
WHERE l.review_score_rating IS NOT NULL
GROUP BY host_tenure
ORDER BY avg_rating DESC;


-- Q11. Top 10 hosts by estimated annual revenue
-- Estimated revenue = price x (365 - availability_365)
SELECT
    h.host_id,
    h.host_name,
    h.host_is_superhost,
    COUNT(l.listing_id)                             AS listings,
    ROUND(SUM(l.price_zar * (365 - l.availability_365)), 0) AS est_annual_revenue_zar,
    ROUND(AVG(l.review_score_rating), 2)            AS avg_rating
FROM hosts h
JOIN listings l ON h.host_id = l.host_id
GROUP BY h.host_id
ORDER BY est_annual_revenue_zar DESC
LIMIT 10;


-- ───────────────────────────────────────────────────────────────────────────
-- SECTION 4: PRICING ANALYSIS
-- ───────────────────────────────────────────────────────────────────────────

-- Q12. Price distribution buckets
-- How are listings distributed across price ranges?
SELECT
    CASE
        WHEN price_zar < 500   THEN 'Under R500'
        WHEN price_zar < 1000  THEN 'R500 - R999'
        WHEN price_zar < 2000  THEN 'R1,000 - R1,999'
        WHEN price_zar < 3000  THEN 'R2,000 - R2,999'
        WHEN price_zar < 5000  THEN 'R3,000 - R4,999'
        ELSE                        'R5,000+'
    END                                             AS price_band,
    COUNT(*)                                        AS listings,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct_of_market,
    ROUND(AVG(review_score_rating), 2)              AS avg_rating
FROM listings
GROUP BY price_band
ORDER BY MIN(price_zar);


-- Q13. Price vs bedrooms relationship
-- How does price scale with bedroom count?
SELECT
    bedrooms,
    COUNT(*)                                        AS listings,
    ROUND(AVG(price_zar), 0)                        AS avg_price_zar,
    ROUND(MIN(price_zar), 0)                        AS min_price,
    ROUND(MAX(price_zar), 0)                        AS max_price,
    ROUND(AVG(review_score_rating), 2)              AS avg_rating
FROM listings
WHERE bedrooms BETWEEN 1 AND 6
GROUP BY bedrooms
ORDER BY bedrooms;


-- Q14. Seasonal pricing from calendar data
-- How does nightly price change month by month?
SELECT
    month,
    CASE month
        WHEN 1  THEN 'January'   WHEN 2  THEN 'February'
        WHEN 3  THEN 'March'     WHEN 4  THEN 'April'
        WHEN 5  THEN 'May'       WHEN 6  THEN 'June'
        WHEN 7  THEN 'July'      WHEN 8  THEN 'August'
        WHEN 9  THEN 'September' WHEN 10 THEN 'October'
        WHEN 11 THEN 'November'  WHEN 12 THEN 'December'
    END                                             AS month_name,
    COUNT(*)                                        AS data_points,
    ROUND(AVG(price_zar), 0)                        AS avg_nightly_price,
    ROUND(AVG(CASE WHEN available = 't' THEN 1.0 ELSE 0.0 END) * 100, 1) AS availability_pct
FROM calendar
GROUP BY month
ORDER BY month;


-- Q15. Peak season premium
-- How much more expensive is December vs the cheapest month?
WITH monthly AS (
    SELECT month, ROUND(AVG(price_zar), 0) AS avg_price
    FROM calendar
    GROUP BY month
)
SELECT
    m.month,
    m.avg_price,
    ROUND((m.avg_price - base.min_price) * 100.0 / base.min_price, 1) AS pct_above_cheapest_month
FROM monthly m
CROSS JOIN (SELECT MIN(avg_price) AS min_price FROM monthly) base
ORDER BY m.month;


-- ───────────────────────────────────────────────────────────────────────────
-- SECTION 5: AVAILABILITY & OCCUPANCY
-- ───────────────────────────────────────────────────────────────────────────

-- Q16. Occupancy rate by neighbourhood
-- Estimated occupancy = (365 - availability_365) / 365
SELECT
    neighbourhood,
    COUNT(*)                                        AS listings,
    ROUND(AVG(365 - availability_365), 0)           AS avg_booked_days,
    ROUND(AVG((365 - availability_365) / 365.0) * 100, 1) AS est_occupancy_pct,
    ROUND(AVG(price_zar), 0)                        AS avg_price_zar,
    ROUND(AVG(price_zar) * AVG(365 - availability_365), 0) AS est_annual_revenue_zar
FROM listings
GROUP BY neighbourhood
ORDER BY est_occupancy_pct DESC;


-- Q17. Instant bookable listings — do they perform better?
SELECT
    instant_bookable,
    COUNT(*)                                        AS listings,
    ROUND(AVG(price_zar), 0)                        AS avg_price_zar,
    ROUND(AVG(review_score_rating), 2)              AS avg_rating,
    ROUND(AVG(number_of_reviews), 1)                AS avg_reviews,
    ROUND(AVG((365 - availability_365) / 365.0) * 100, 1) AS est_occupancy_pct
FROM listings
GROUP BY instant_bookable;


-- Q18. Minimum nights impact on occupancy
-- Do shorter minimum stays attract more bookings?
SELECT
    CASE
        WHEN minimum_nights = 1 THEN '1 night'
        WHEN minimum_nights = 2 THEN '2 nights'
        WHEN minimum_nights BETWEEN 3 AND 6 THEN '3-6 nights'
        WHEN minimum_nights BETWEEN 7 AND 29 THEN '1-4 weeks'
        ELSE '30+ nights'
    END                                             AS min_stay,
    COUNT(*)                                        AS listings,
    ROUND(AVG(price_zar), 0)                        AS avg_price_zar,
    ROUND(AVG(number_of_reviews), 1)                AS avg_reviews,
    ROUND(AVG((365 - availability_365) / 365.0) * 100, 1) AS est_occupancy_pct
FROM listings
GROUP BY min_stay
ORDER BY MIN(minimum_nights);


-- ───────────────────────────────────────────────────────────────────────────
-- SECTION 6: REVIEW ANALYSIS
-- ───────────────────────────────────────────────────────────────────────────

-- Q19. Review volume by neighbourhood
-- Which areas generate the most guest feedback?
SELECT
    l.neighbourhood,
    COUNT(r.review_id)                              AS total_reviews,
    COUNT(DISTINCT r.listing_id)                    AS reviewed_listings,
    ROUND(COUNT(r.review_id) * 1.0 / COUNT(DISTINCT r.listing_id), 1) AS reviews_per_listing
FROM listings l
LEFT JOIN reviews r ON l.listing_id = r.listing_id
GROUP BY l.neighbourhood
ORDER BY total_reviews DESC;


-- Q20. Review trends over time
-- Is Airbnb activity growing or shrinking in Cape Town?
SELECT
    substr(date, 1, 7)                              AS year_month,
    COUNT(*)                                        AS review_count
FROM reviews
GROUP BY year_month
ORDER BY year_month;


-- Q21. Listings with high reviews but no recent activity
-- Identify potentially stale listings
SELECT
    listing_id,
    neighbourhood,
    price_zar,
    number_of_reviews,
    review_score_rating,
    last_review,
    availability_365
FROM listings
WHERE number_of_reviews > 20
  AND review_score_rating >= 4.5
  AND (last_review IS NULL OR last_review < '2023-01-01')
ORDER BY number_of_reviews DESC
LIMIT 15;


-- ───────────────────────────────────────────────────────────────────────────
-- SECTION 7: ADVANCED ANALYTICS
-- ───────────────────────────────────────────────────────────────────────────

-- Q22. Revenue ranking with window functions
-- Rank neighbourhoods by estimated annual revenue
SELECT
    neighbourhood,
    ROUND(AVG(price_zar), 0)                        AS avg_price,
    ROUND(AVG((365 - availability_365) / 365.0) * 100, 1) AS occupancy_pct,
    ROUND(AVG(price_zar) * AVG(365 - availability_365), 0) AS est_annual_revenue,
    RANK() OVER (ORDER BY AVG(price_zar) * AVG(365 - availability_365) DESC) AS revenue_rank,
    RANK() OVER (ORDER BY AVG(price_zar) DESC)       AS price_rank
FROM listings
GROUP BY neighbourhood;


-- Q23. Rolling 3-month review trend
-- Smoothed activity trend using window functions
WITH monthly_reviews AS (
    SELECT substr(date, 1, 7) AS ym, COUNT(*) AS monthly_count
    FROM reviews GROUP BY ym
)
SELECT
    ym,
    monthly_count,
    ROUND(AVG(monthly_count) OVER (ORDER BY ym ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS rolling_3m_avg
FROM monthly_reviews
ORDER BY ym;


-- Q24. Neighbourhood performance quadrants
-- Classify areas as: Star, Niche, Volume, or Struggling
WITH neighbourhood_stats AS (
    SELECT neighbourhood,
           ROUND(AVG(price_zar), 0)           AS avg_price,
           ROUND(AVG(review_score_rating), 2) AS avg_rating,
           COUNT(*)                           AS listings
    FROM listings WHERE review_score_rating IS NOT NULL
    GROUP BY neighbourhood
),
medians AS (
    SELECT AVG(avg_price) AS median_price, AVG(avg_rating) AS median_rating
    FROM neighbourhood_stats
)
SELECT
    n.neighbourhood, n.avg_price, n.avg_rating, n.listings,
    CASE
        WHEN n.avg_price >= m.median_price AND n.avg_rating >= m.median_rating THEN '⭐ Star (High Price + High Rating)'
        WHEN n.avg_price >= m.median_price AND n.avg_rating <  m.median_rating THEN '💰 Overpriced (High Price + Low Rating)'
        WHEN n.avg_price <  m.median_price AND n.avg_rating >= m.median_rating THEN '💎 Hidden Gem (Low Price + High Rating)'
        ELSE                                                                        '⚠️  Struggling (Low Price + Low Rating)'
    END AS market_quadrant
FROM neighbourhood_stats n CROSS JOIN medians m
ORDER BY n.avg_price DESC;


-- Q25. Correlation between review score and price premium
-- Do highly rated listings command a price premium?
SELECT
    CASE
        WHEN review_score_rating >= 4.9 THEN '4.9 - 5.0 (Exceptional)'
        WHEN review_score_rating >= 4.7 THEN '4.7 - 4.8 (Excellent)'
        WHEN review_score_rating >= 4.5 THEN '4.5 - 4.6 (Very Good)'
        WHEN review_score_rating >= 4.0 THEN '4.0 - 4.4 (Good)'
        ELSE                                 'Below 4.0'
    END                                             AS rating_band,
    COUNT(*)                                        AS listings,
    ROUND(AVG(price_zar), 0)                        AS avg_price_zar,
    ROUND(AVG(number_of_reviews), 0)                AS avg_reviews,
    ROUND(AVG((365 - availability_365) / 365.0) * 100, 1) AS est_occupancy_pct
FROM listings
WHERE review_score_rating IS NOT NULL
GROUP BY rating_band
ORDER BY MIN(review_score_rating) DESC;
