import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI(title="NutriFinder API", description="Foods, nutrients, benefits, and guidance")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FoodItemCreate(BaseModel):
    name: str
    aliases: Optional[List[str]] = []
    category: Optional[str] = None
    serving_size: Optional[str] = None
    calories: Optional[float] = None
    macros: Optional[dict] = {}
    micronutrients: Optional[List[dict]] = []
    glycemic_index: Optional[float] = None
    best_time_to_eat: Optional[str] = None
    benefits: Optional[List[str]] = []
    conditions_helped: Optional[List[str]] = []
    cautions: Optional[List[str]] = []
    notes: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "NutriFinder API is running"}


@app.get("/schema")
async def read_schema():
    # Expose schemas for the GUI/DB viewer
    import schemas
    # Serialize BaseModel classes to basic dict structure
    def model_schema(model):
        return model.model_json_schema()

    return {
        "collections": {
            "user": model_schema(schemas.User),
            "product": model_schema(schemas.Product),
            "fooditem": model_schema(schemas.FoodItem),
        }
    }


@app.get("/api/foods")
async def list_foods(q: Optional[str] = Query(None, description="Search by name or alias"), category: Optional[str] = None, limit: int = 50):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    filter_q = {}
    if q:
        filter_q["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"aliases": {"$regex": q, "$options": "i"}},
        ]
    if category:
        filter_q["category"] = {"$regex": f"^{category}$", "$options": "i"}

    docs = get_documents("fooditem", filter_q, limit)
    # Convert ObjectIds
    for d in docs:
        if d.get("_id"):
            d["id"] = str(d.pop("_id"))
    return {"items": docs}


@app.post("/api/foods")
async def create_food(item: FoodItemCreate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    new_id = create_document("fooditem", item.model_dump())
    return {"id": new_id, "message": "Food item created"}


@app.get("/api/foods/{food_id}")
async def get_food(food_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        oid = ObjectId(food_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

    doc = db["fooditem"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.post("/api/foods/seed")
async def seed_foods():
    """Seed the database with a curated set of foods if they don't exist."""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    seed_data = [
        {
            "name": "Apple",
            "aliases": ["Malus domestica"],
            "category": "fruit",
            "serving_size": "1 medium (182 g)",
            "calories": 95,
            "macros": {"protein": 0.5, "carbs": 25, "fat": 0.3, "fiber": 4.4},
            "micronutrients": [
                {"name": "Vitamin C", "unit": "mg", "amount": 8.4},
                {"name": "Potassium", "unit": "mg", "amount": 195},
            ],
            "glycemic_index": 36,
            "best_time_to_eat": "Morning or as a snack",
            "benefits": ["Gut health", "Hydration", "Satiety"],
            "conditions_helped": ["Weight management", "Heart health"],
        },
        {
            "name": "Banana",
            "category": "fruit",
            "serving_size": "1 medium (118 g)",
            "calories": 105,
            "macros": {"protein": 1.3, "carbs": 27, "fat": 0.3, "fiber": 3.1},
            "micronutrients": [
                {"name": "Potassium", "unit": "mg", "amount": 422},
                {"name": "Vitamin B6", "unit": "mg", "amount": 0.4},
            ],
            "glycemic_index": 51,
            "best_time_to_eat": "Pre-workout or afternoon",
            "benefits": ["Energy", "Electrolyte balance"],
            "conditions_helped": ["Muscle cramps", "Digestion"],
        },
        {
            "name": "Oats",
            "category": "grain",
            "serving_size": "1/2 cup dry (40 g)",
            "calories": 154,
            "macros": {"protein": 5.3, "carbs": 27, "fat": 2.6, "fiber": 4},
            "micronutrients": [
                {"name": "Manganese", "unit": "mg", "amount": 1.7},
                {"name": "Iron", "unit": "mg", "amount": 1.7},
            ],
            "glycemic_index": 55,
            "best_time_to_eat": "Morning",
            "benefits": ["Cholesterol support", "Satiety"],
            "conditions_helped": ["Heart health", "Blood sugar"],
        },
        {
            "name": "Turmeric",
            "category": "spice",
            "serving_size": "1 tsp (3 g)",
            "calories": 9,
            "macros": {"protein": 0.3, "carbs": 2, "fat": 0.1, "fiber": 0.7},
            "micronutrients": [
                {"name": "Manganese", "unit": "mg", "amount": 0.2}
            ],
            "glycemic_index": 5,
            "best_time_to_eat": "With meals",
            "benefits": ["Anti-inflammatory", "Antioxidant"],
            "conditions_helped": ["Joint health", "Metabolic health"],
        },
        {
            "name": "Salmon",
            "category": "protein",
            "serving_size": "100 g cooked",
            "calories": 208,
            "macros": {"protein": 22, "carbs": 0, "fat": 13, "fiber": 0},
            "micronutrients": [
                {"name": "Vitamin D", "unit": "IU", "amount": 447},
                {"name": "Omega-3 (EPA+DHA)", "unit": "g", "amount": 1.8},
            ],
            "glycemic_index": 0,
            "best_time_to_eat": "Lunch or dinner",
            "benefits": ["Brain health", "Heart health"],
            "conditions_helped": ["Inflammation", "Triglycerides"],
        },
        {
            "name": "Greek Yogurt",
            "aliases": ["Yoghurt"],
            "category": "dairy",
            "serving_size": "170 g (6 oz)",
            "calories": 100,
            "macros": {"protein": 17, "carbs": 6, "fat": 0},
            "micronutrients": [
                {"name": "Calcium", "unit": "mg", "amount": 187},
                {"name": "Probiotics", "unit": "CFU", "amount": 0},
            ],
            "glycemic_index": 11,
            "best_time_to_eat": "Morning or snack",
            "benefits": ["Gut health", "Muscle repair"],
            "conditions_helped": ["Bone health", "Satiety"],
        },
        {
            "name": "Spinach",
            "category": "vegetable",
            "serving_size": "100 g raw",
            "calories": 23,
            "macros": {"protein": 2.9, "carbs": 3.6, "fat": 0.4, "fiber": 2.2},
            "micronutrients": [
                {"name": "Vitamin K", "unit": "mcg", "amount": 483},
                {"name": "Folate", "unit": "mcg", "amount": 194},
            ],
            "glycemic_index": 15,
            "best_time_to_eat": "Lunch or dinner",
            "benefits": ["Micronutrient dense", "Eye health"],
            "conditions_helped": ["Anemia", "Blood pressure"],
        },
        {
            "name": "Sweet Potato",
            "category": "vegetable",
            "serving_size": "1 medium (130 g)",
            "calories": 112,
            "macros": {"protein": 2, "carbs": 26, "fat": 0.1, "fiber": 3.9},
            "micronutrients": [
                {"name": "Vitamin A", "unit": "mcg", "amount": 944},
                {"name": "Potassium", "unit": "mg", "amount": 438},
            ],
            "glycemic_index": 54,
            "best_time_to_eat": "Lunch or post-workout",
            "benefits": ["Stable energy", "Eye health"],
            "conditions_helped": ["Blood sugar", "Immunity"],
        },
        {
            "name": "Almonds",
            "category": "nut",
            "serving_size": "28 g (23 almonds)",
            "calories": 164,
            "macros": {"protein": 6, "carbs": 6, "fat": 14, "fiber": 3.5},
            "micronutrients": [
                {"name": "Vitamin E", "unit": "mg", "amount": 7.3},
                {"name": "Magnesium", "unit": "mg", "amount": 76},
            ],
            "glycemic_index": 0,
            "best_time_to_eat": "Snack or with breakfast",
            "benefits": ["Satiety", "Heart health"],
            "conditions_helped": ["Cholesterol", "Blood sugar"],
        },
        {
            "name": "Lentils",
            "category": "legume",
            "serving_size": "1/2 cup cooked (99 g)",
            "calories": 115,
            "macros": {"protein": 9, "carbs": 20, "fat": 0.4, "fiber": 8},
            "micronutrients": [
                {"name": "Folate", "unit": "mcg", "amount": 179},
                {"name": "Iron", "unit": "mg", "amount": 3.3},
            ],
            "glycemic_index": 32,
            "best_time_to_eat": "Lunch or dinner",
            "benefits": ["Protein", "Gut health"],
            "conditions_helped": ["Blood sugar", "Heart health"],
        },
    ]

    inserted = 0
    for doc in seed_data:
        res = db["fooditem"].update_one({"name": doc["name"]}, {"$setOnInsert": doc}, upsert=True)
        # If upserted_id is not None, a new doc was inserted
        if res.upserted_id is not None:
            inserted += 1

    total = db["fooditem"].count_documents({})
    return {"inserted": inserted, "total": total}


@app.get("/test")
async def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
