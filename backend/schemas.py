from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class CategoryBase(BaseModel):
    name: str
    icon: str
    color: str

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True

class ItemBase(BaseModel):
    name: str
    category_id: int
    current_quantity: float
    minimum_quantity: float
    unit: str
    notes: Optional[str] = None
    barcode: Optional[str] = None
    acquisition_difficulty: int = 0  # 0=Easy, 5=Medium, 10=Hard
    usage_rate: Optional[float] = None
    usage_period: str = "daily"
    notification_enabled: bool = False
    phone_number: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    current_quantity: Optional[float] = None
    minimum_quantity: Optional[float] = None
    unit: Optional[str] = None
    notes: Optional[str] = None
    barcode: Optional[str] = None
    acquisition_difficulty: Optional[int] = None
    usage_rate: Optional[float] = None
    usage_period: Optional[str] = None
    notification_enabled: Optional[bool] = None
    phone_number: Optional[str] = None

class Item(ItemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    category: Optional[Category] = None
    quantity_history: Optional[str] = None

    class Config:
        from_attributes = True

class ShoppingListItem(BaseModel):
    id: int
    name: str
    current_quantity: float
    minimum_quantity: float
    unit: str
    needed: float
    urgency: str  # 'critical' (current <= 0), 'attention' (current < minimum), 'ok'
    acquisition_difficulty: int = 0
    purchase_by: Optional[str] = None  # ISO date string
    days_remaining: Optional[float] = None

class PurchasePrediction(BaseModel):
    item_id: int
    item_name: str
    days_remaining: float
    buffer_days: int
    purchase_by: str  # ISO date string
    urgency: str
    confidence: float  # 0-1 confidence score
    needs_tracking: bool  # True if insufficient data for ML prediction

class BarcodeIdentifyRequest(BaseModel):
    image_base64: str  # Base64 encoded image data

class BarcodeIdentifyResponse(BaseModel):
    success: bool
    product_name: Optional[str] = None
    suggested_category: Optional[str] = None
    suggested_unit: Optional[str] = None
    barcode: Optional[str] = None
    error: Optional[str] = None

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    phone_number: Optional[str] = None
    theme_preference: Optional[str] = None
    language_preference: Optional[str] = None
    password: Optional[str] = None # Optional password reset

class User(UserBase):
    id: int
    display_name: Optional[str] = None
    phone_number: Optional[str] = None
    theme_preference: Optional[str] = None
    language_preference: Optional[str] = None

    class Config:
        from_attributes = True
