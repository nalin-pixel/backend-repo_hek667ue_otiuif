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
