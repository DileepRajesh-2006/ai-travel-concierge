import redis
import json

REDIS_URL = "rediss://:ARs5AAImcDI5NzE5MDJiOTk5NzA0MzVhOGU2OTZkYjQzNDM3NTg1M3AyNjk2OQ@tough-grizzly-6969.upstash.io:6379"

# Connect to Redis with decode_responses=True for strings
r = redis.from_url(REDIS_URL, decode_responses=True)

def get_cached_trip(query_key):
    cached = r.get(query_key)
    if cached:
        return json.loads(cached)
    return None

def cache_trip(query_key, data, ttl=3600):
    r.setex(query_key, ttl, json.dumps(data))

# Test caching
query = "user123_trip_to_Paris"
cached = get_cached_trip(query)
if cached:
    print("Using cached data:", cached)
else:
    ai_data = {"flights": {}, "hotels": {}, "budget": {}}
    cache_trip(query, ai_data)
    print("Stored AI response in Redis!")