"""
waterDB Setup & Query Reference
================================
Database : waterDB
Collection: waterData

Run this script directly to:
  1. Create the DB + collection
  2. Insert a sample document
  3. Demonstrate fetch-all and filter-unsafe queries

Usage:
    python waterdb_setup.py
"""

from pymongo import MongoClient
from datetime import datetime

# ── Connect ────────────────────────────────────────────────────────────────────
client = MongoClient("mongodb://localhost:27017")
db         = client["waterDB"]
collection = db["waterData"]

print("✅ Connected to waterDB")

# ─────────────────────────────────────────────────────────────────────────────
# 1. SAMPLE INSERT QUERY
# ─────────────────────────────────────────────────────────────────────────────
sample_document = {
    "location": {
        "city":  "Salem",
        "state": "Tamil Nadu"
    },
    "ph":               7.2,
    "hardness":         180.5,    # mg/L
    "tds":              310.0,    # mg/L
    "chlorine":         1.8,      # mg/L
    "sulfate":          210.0,    # mg/L
    "conductivity":     620.0,    # μS/cm
    "organic_carbon":   1.5,      # mg/L
    "trihalomethanes":  55.0,     # μg/L
    "turbidity":        3.2,      # NTU
    "result":           "Safe",   # "Safe" or "Unsafe"
    "timestamp":        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

insert_result = collection.insert_one(sample_document)
print(f"✅ Inserted document ID: {insert_result.inserted_id}")

# Insert an unsafe sample so the filter query has something to return
unsafe_document = {
    "location": {
        "city":  "Chennai",
        "state": "Tamil Nadu"
    },
    "ph":               5.1,      # too low
    "hardness":         450.0,    # too high
    "tds":              520.0,    # too high
    "chlorine":         6.5,      # too high
    "sulfate":          310.0,    # too high
    "conductivity":     950.0,    # too high
    "organic_carbon":   4.8,      # too high
    "trihalomethanes":  95.0,     # too high
    "turbidity":        8.1,      # too high
    "result":           "Unsafe",
    "timestamp":        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

collection.insert_one(unsafe_document)
print("✅ Inserted unsafe sample document")

# ─────────────────────────────────────────────────────────────────────────────
# 2. FETCH ALL DATA
# ─────────────────────────────────────────────────────────────────────────────
print("\n── All water samples ──────────────────────────────────────────────────")
all_samples = list(collection.find({}, {"_id": 0}))   # exclude _id for clean output
for doc in all_samples:
    print(doc)

# ─────────────────────────────────────────────────────────────────────────────
# 3. FILTER ONLY UNSAFE LOCATIONS
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Unsafe water locations ─────────────────────────────────────────────")
unsafe_samples = list(collection.find({"result": "Unsafe"}, {"_id": 0}))
for doc in unsafe_samples:
    city  = doc.get("location", {}).get("city", "N/A")
    state = doc.get("location", {}).get("state", "N/A")
    print(f"  📍 {city}, {state}  |  pH: {doc['ph']}  |  TDS: {doc['tds']}  |  Result: {doc['result']}")

print(f"\nTotal unsafe locations found: {len(unsafe_samples)}")

client.close()
