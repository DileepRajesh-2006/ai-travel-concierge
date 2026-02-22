# main.py
from dotenv import load_dotenv
import os
import psycopg2
import json
from upstash_redis import Redis

# ------------------------
# Load environment variables
# ------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

UPSTASH_URL = os.getenv("UPSTASH_URL")
UPSTASH_TOKEN = os.getenv("UPSTASH_TOKEN")

# ------------------------
# Connect to PostgreSQL
# ------------------------
try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    print("✅ Connected to PostgreSQL!")

    # Create tables if they don't exist
    cur.execute("""
    -- USERS TABLE
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- TRIPS TABLE
    CREATE TABLE IF NOT EXISTS trips (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        destination VARCHAR(255) NOT NULL,
        budget INTEGER NOT NULL,
        start_date DATE,
        end_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- TRIP DETAILS TABLE
    CREATE TABLE IF NOT EXISTS trip_details (
        id SERIAL PRIMARY KEY,
        trip_id INTEGER REFERENCES trips(id) ON DELETE CASCADE,
        flight_data JSONB,
        hotel_data JSONB,
        itinerary TEXT,
        budget_summary JSONB
    );

    -- LOGS TABLE
    CREATE TABLE IF NOT EXISTS logs (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        endpoint VARCHAR(255),
        response_time FLOAT,
        status_code INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    print("✅ PostgreSQL tables are ready!")

except Exception as e:
    print("❌ PostgreSQL connection failed:", e)

# ------------------------
# Connect to Upstash Redis
# ------------------------
try:
    redis = Redis(url=UPSTASH_URL, token=UPSTASH_TOKEN)
    print("✅ Connected to Upstash Redis!")
except Exception as e:
    print("❌ Redis connection failed:", e)

# ------------------------
# AI Response Caching Example
# ------------------------
query_key = "user123_trip_to_Paris"

# Example AI response
ai_response = {
    "flights": {"price": 400, "airline": "AirY"},
    "hotels": [{"name": "City Inn", "price_per_night": 100}],
    "budget": {"total": 1200}
}

# Check cache
cached = redis.get(query_key)
if cached:
    print("Using cached AI response:", json.loads(cached))
else:
    # Store in Redis for 1 hour
    redis.set(key=query_key, value=json.dumps(ai_response), ex=3600)
    print("Stored AI response in Redis!")