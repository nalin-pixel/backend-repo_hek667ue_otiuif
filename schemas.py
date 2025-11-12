"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict

# Example schemas (you can keep or remove later):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# NutriFinder core schema
class Nutrient(BaseModel):
    name: str = Field(..., description="Nutrient name, e.g., Protein, Vitamin C")
    unit: str = Field(..., description="Unit of measurement, e.g., g, mg, mcg")
    amount: float = Field(..., ge=0, description="Amount per serving in given unit")

class FoodItem(BaseModel):
    """
    Food items and ingredients with nutrition and guidance
    Collection name: "fooditem"
    """
    name: str = Field(..., description="Common name of the food or ingredient")
    aliases: Optional[List[str]] = Field(default_factory=list, description="Alternate names")
    category: Optional[str] = Field(None, description="Category like fruit, legume, spice, dairy")
    serving_size: Optional[str] = Field(None, description="Serving size description, e.g., 100 g, 1 cup")

    calories: Optional[float] = Field(None, ge=0, description="Calories per serving")
    macros: Optional[Dict[str, float]] = Field(default_factory=dict, description="macros: protein(g), carbs(g), fat(g), fiber(g)")
    micronutrients: Optional[List[Nutrient]] = Field(default_factory=list, description="Key micronutrients per serving")

    glycemic_index: Optional[float] = Field(None, ge=0, le=100, description="GI value if applicable")

    best_time_to_eat: Optional[str] = Field(None, description="When to eat for most benefit, e.g., morning, post-workout")
    benefits: Optional[List[str]] = Field(default_factory=list, description="General benefits")
    conditions_helped: Optional[List[str]] = Field(default_factory=list, description="Sickness/conditions it may help")
    cautions: Optional[List[str]] = Field(default_factory=list, description="Who should be cautious or interactions")
    notes: Optional[str] = Field(None, description="Extra guidance or preparation tips")

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
