// MongoDB Playground
// Database : waterDB
// Collection: waterData

// ── 1. Switch to waterDB ───────────────────────────────────────────────────────
use("waterDB");

// ── 2. Create collection & insert a sample document ───────────────────────────
db.waterData.insertOne({
  location: {
    city:  "Salem",
    state: "Tamil Nadu"
  },
  ph:               7.2,
  hardness:         180.5,
  tds:              310.0,
  chlorine:         1.8,
  sulfate:          210.0,
  conductivity:     620.0,
  organic_carbon:   1.5,
  trihalomethanes:  55.0,
  turbidity:        3.2,
  result:           "Safe",
  timestamp:        new Date().toISOString()
});

// ── 3. Insert an unsafe sample ─────────────────────────────────────────────────
db.waterData.insertOne({
  location: {
    city:  "Chennai",
    state: "Tamil Nadu"
  },
  ph:               5.1,
  hardness:         450.0,
  tds:              520.0,
  chlorine:         6.5,
  sulfate:          310.0,
  conductivity:     950.0,
  organic_carbon:   4.8,
  trihalomethanes:  95.0,
  turbidity:        8.1,
  result:           "Unsafe",
  timestamp:        new Date().toISOString()
});

// ── 4. View ALL water quality data ─────────────────────────────────────────────
db.waterData.find({});

// ── 5. View ONLY unsafe water locations ────────────────────────────────────────
db.waterData.find({ result: "Unsafe" });
