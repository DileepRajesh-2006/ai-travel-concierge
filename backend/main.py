# main.py
import os
import json
import psycopg2
from fastapi import FastAPI
from dotenv import load_dotenv
from upstash_redis import Redis

# ------------------------
# FastAPI app
# ------------------------
app = FastAPI()  # Mandatory for Render

# ------------------------
# Load environment variables
# ------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
UPSTASH_URL = os.getenv("UPSTASH_URL")
UPSTASH_TOKEN = os.getenv("UPSTASH_TOKEN")

SECRET_KEY = os.getenv("SECRET_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ------------------------
# Connect to PostgreSQL
# ------------------------
def init_db():
    try:
        # Fix DSN for psycopg2
        db_url = DATABASE_URL
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgres://", 1)
        
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # Create tables if not exist
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS trips (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            destination VARCHAR(255) NOT NULL,
            budget INTEGER NOT NULL,
            start_date DATE,
            end_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS trip_details (
            id SERIAL PRIMARY KEY,
            trip_id INTEGER UNIQUE REFERENCES trips(id) ON DELETE CASCADE,
            flight_data JSONB,
            hotel_data JSONB,
            itinerary TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            endpoint VARCHAR(255),
            latency_ms FLOAT,
            status_code INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ PostgreSQL: Schema is ready")
    except Exception as e:
        print(f"❌ PostgreSQL Error: {e}")

# Initialize DB
init_db()

# ------------------------
# Connect to Upstash Redis
# ------------------------
try:
    redis = Redis(url=UPSTASH_URL, token=UPSTASH_TOKEN)
    print("✅ Redis: Connected to Upstash")
except Exception as e:
    print(f"❌ Redis Error: {e}")

# ------------------------
# API Endpoints
# ------------------------
@app.get("/")
def health_check():
    """Health check endpoint"""
    return {
        "status": "online",
        "database": "connected" if DATABASE_URL else "not set",
        "cache": "connected" if redis else "not set"
    }

@app.get("/test-cache")
def test_cache():
    """Redis caching example"""
    query_key = "user123_trip_to_Paris"

    cached = redis.get(query_key)
    if cached:
        return {"source": "redis_cache", "data": json.loads(cached)}
    
    ai_response = {
        "flights": {"price": 400, "airline": "AirY"},
        "hotels": [{"name": "City Inn", "price_per_night": 100}],
        "budget": {"total": 1200}
    }

    redis.set(key=query_key, value=json.dumps(ai_response), ex=3600)
    return {"source": "ai_agent_simulated", "data": ai_response}