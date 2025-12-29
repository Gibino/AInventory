from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from . import models, schemas, database, auth
from .database import engine, get_db
from .ml_predictor import (
    MLPredictor, 
    calculate_daily_usage, 
    get_buffer_days,
    calculate_days_remaining,
    calculate_purchase_date,
    predict_purchase_urgency
)
from .usage_tracker import UsageTracker

from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
import json

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AInventory")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# Initialize services
ml_predictor = MLPredictor()
usage_tracker = UsageTracker()

@app.get("/")
async def read_index():
    return RedirectResponse(url="/static/index.html")

# Seed initial categories if none exist
def seed_categories(db: Session):
    if db.query(models.Category).count() == 0:
        categories = [
            models.Category(name="Alimentos", icon="🍎", color="#FF5733"),
            models.Category(name="Limpeza", icon="🧹", color="#33FF57"),
            models.Category(name="Higiene", icon="🧼", color="#3357FF"),
            models.Category(name="Medicamentos", icon="💊", color="#F333FF"),
            models.Category(name="Pet", icon="🐕", color="#FFBD33"),
        ]
        db.add_all(categories)
        db.commit()

@app.on_event("startup")
def startup_event():
    db = next(get_db())
    seed_categories(db)
    
    # Seed Admin User
    if not db.query(models.User).filter(models.User.username == "admin").first():
        hashed_pw = auth.get_password_hash("admin")
        admin_user = models.User(
            username="admin", 
            hashed_password=hashed_pw,
            display_name="Administrator"
        )
        db.add(admin_user)
        db.commit()

# === Authentication Endpoint ===
@app.post("/token", response_model=auth.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.put("/users/me", response_model=schemas.User)
async def update_user_me(user_update: schemas.UserUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Update fields
    if user_update.display_name is not None:
        current_user.display_name = user_update.display_name
    if user_update.phone_number is not None:
        current_user.phone_number = user_update.phone_number
    if user_update.theme_preference is not None:
        current_user.theme_preference = user_update.theme_preference
    if user_update.language_preference is not None:
        current_user.language_preference = user_update.language_preference
    
    # Password update
    if user_update.password:
        current_user.hashed_password = auth.get_password_hash(user_update.password)
        
    db.commit()
    db.refresh(current_user)
    return current_user

# === Protected Endpoints ===

# Items Endpoints
@app.get("/items", response_model=List[schemas.Item])
def read_items(db: Session = Depends(get_db), current_user: auth.User = Depends(auth.get_current_user)):
    return db.query(models.Item).all()

@app.get("/items/{item_id}", response_model=schemas.Item)
def read_item(item_id: int, db: Session = Depends(get_db), current_user: auth.User = Depends(auth.get_current_user)):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.post("/items", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db), current_user: auth.User = Depends(auth.get_current_user)):
    db_item = models.Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.put("/items/{item_id}", response_model=schemas.Item)
async def update_item(item_id: int, item_update: schemas.ItemUpdate, db: Session = Depends(get_db), current_user: auth.User = Depends(auth.get_current_user)):
    from .sms_service import send_sms, calculate_suggested_quantity, format_low_stock_message
    
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_data = item_update.model_dump(exclude_unset=True)
    old_qty = db_item.current_quantity
    
    # Track quantity changes for ML learning
    if "current_quantity" in update_data:
        new_qty = update_data["current_quantity"]
        if old_qty != new_qty:
            db_item.quantity_history = usage_tracker.add_quantity_record(
                db_item.quantity_history,
                old_qty,
                new_qty
            )
    
    for key, value in update_data.items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    
    # Check if item dropped below minimum and send SMS
    new_qty = db_item.current_quantity
    if new_qty < db_item.minimum_quantity and old_qty >= db_item.minimum_quantity:
        # Item just dropped below minimum - check if we should send SMS
        user_phone = current_user.phone_number
        if user_phone:
            # Check if SMS was sent in last 24h for this item
            can_send = True
            if db_item.last_sms_sent_at:
                if datetime.utcnow() - db_item.last_sms_sent_at < timedelta(hours=24):
                    can_send = False
            
            if can_send:
                suggested_qty = calculate_suggested_quantity(
                    current_qty=new_qty,
                    min_qty=db_item.minimum_quantity,
                    usage_rate=db_item.usage_rate,
                    usage_period=db_item.usage_period or "daily",
                    acquisition_difficulty=db_item.acquisition_difficulty or 0
                )
                
                message = format_low_stock_message(
                    item_name=db_item.name,
                    current_qty=new_qty,
                    min_qty=db_item.minimum_quantity,
                    unit=db_item.unit,
                    suggested_qty=suggested_qty,
                    lang=current_user.language_preference or "pt-BR"
                )
                
                sms_sent = await send_sms(user_phone, message, item_id=db_item.id)
                if sms_sent:
                    db_item.last_sms_sent_at = datetime.utcnow()
                    db.commit()
    
    return db_item

@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db), current_user: auth.User = Depends(auth.get_current_user)):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted"}

# Categories Endpoints
@app.get("/categories", response_model=List[schemas.Category])
def read_categories(db: Session = Depends(get_db), current_user: auth.User = Depends(auth.get_current_user)):
    return db.query(models.Category).all()

@app.post("/categories", response_model=schemas.Category)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db), current_user: auth.User = Depends(auth.get_current_user)):
    # Check if exists
    if db.query(models.Category).filter(models.Category.name == category.name).first():
        raise HTTPException(status_code=400, detail="Category already exists")
    
    db_category = models.Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# Purchase Prediction Endpoint
@app.get("/items/{item_id}/purchase-prediction", response_model=schemas.PurchasePrediction)
def get_purchase_prediction(item_id: int, db: Session = Depends(get_db), current_user: auth.User = Depends(auth.get_current_user)):
    """Calculate when item needs to be purchased based on usage patterns."""
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Try ML prediction first
    history = usage_tracker.get_history_as_list(item.quantity_history)
    ml_usage_rate = ml_predictor.predict_usage_rate(history)
    confidence = ml_predictor.get_prediction_confidence(history)
    
    needs_tracking = ml_usage_rate is None and item.usage_rate is None
    
    # Use ML rate, fall back to user-provided rate
    if ml_usage_rate is not None:
        daily_usage = ml_usage_rate
    elif item.usage_rate is not None:
        daily_usage = calculate_daily_usage(item.usage_rate, item.usage_period)
        confidence = 0.5  # Medium confidence for user-provided data
    else:
        # No data available
        daily_usage = 0.0
        confidence = 0.0
    
    days_remaining = calculate_days_remaining(item.current_quantity, daily_usage)
    buffer_days = get_buffer_days(item.acquisition_difficulty)
    purchase_date = calculate_purchase_date(
        item.current_quantity,
        daily_usage,
        item.acquisition_difficulty
    )
    urgency = predict_purchase_urgency(
        item.current_quantity,
        daily_usage,
        item.acquisition_difficulty
    )
    
    return schemas.PurchasePrediction(
        item_id=item.id,
        item_name=item.name,
        days_remaining=round(days_remaining, 1) if days_remaining != float('inf') else 999,
        buffer_days=buffer_days,
        purchase_by=purchase_date.isoformat(),
        urgency=urgency,
        confidence=round(confidence, 2),
        needs_tracking=needs_tracking
    )

# Shopping List Endpoint
@app.get("/shopping-list", response_model=List[schemas.ShoppingListItem])
def get_shopping_list(db: Session = Depends(get_db), current_user: auth.User = Depends(auth.get_current_user)):
    items = db.query(models.Item).filter(models.Item.current_quantity < models.Item.minimum_quantity).all()
    shopping_list = []
    
    for item in items:
        # Get prediction data
        history = usage_tracker.get_history_as_list(item.quantity_history)
        ml_usage_rate = ml_predictor.predict_usage_rate(history)
        
        if ml_usage_rate is not None:
            daily_usage = ml_usage_rate
        elif item.usage_rate is not None:
            daily_usage = calculate_daily_usage(item.usage_rate, item.usage_period)
        else:
            daily_usage = 0.0
        
        days_remaining = calculate_days_remaining(item.current_quantity, daily_usage)
        purchase_date = calculate_purchase_date(
            item.current_quantity,
            daily_usage,
            item.acquisition_difficulty
        ) if daily_usage > 0 else None
        
        urgency = "critical" if item.current_quantity <= 0 else "attention"
        
        shopping_list.append({
            "id": item.id,
            "name": item.name,
            "current_quantity": item.current_quantity,
            "minimum_quantity": item.minimum_quantity,
            "unit": item.unit,
            "needed": item.minimum_quantity - item.current_quantity,
            "urgency": urgency,
            "acquisition_difficulty": item.acquisition_difficulty,
            "purchase_by": purchase_date.isoformat() if purchase_date else None,
            "days_remaining": round(days_remaining, 1) if days_remaining != float('inf') else None
        })
    
    return shopping_list

# Barcode identification endpoint 
@app.post("/barcode/identify", response_model=schemas.BarcodeIdentifyResponse)
async def identify_barcode(request: schemas.BarcodeIdentifyRequest, current_user: auth.User = Depends(auth.get_current_user)):
    """Identify product from barcode image using Gemini AI."""
    try:
        from .barcode_service import BarcodeService
        service = BarcodeService()
        result = await service.identify_product(request.image_base64)
        return result
    except ImportError:
        return schemas.BarcodeIdentifyResponse(
            success=False,
            error="Barcode service not configured. Please set GEMINI_API_KEY."
        )
    except Exception as e:
        return schemas.BarcodeIdentifyResponse(
            success=False,
            error=str(e)
        )

# Items needing attention (for notifications)
@app.get("/items/alerts/needed")
def get_items_needing_attention(db: Session = Depends(get_db), current_user: auth.User = Depends(auth.get_current_user)):
    """Get items that need quantity check or are running low."""
    items = db.query(models.Item).all()
    alerts = []
    
    for item in items:
        # Check if needs quantity update
        needs_check = usage_tracker.needs_check_reminder(item.quantity_history)
        
        # Check stock level
        is_low = item.current_quantity < item.minimum_quantity
        is_critical = item.current_quantity <= 0
        
        if needs_check or is_low:
            alerts.append({
                "id": item.id,
                "name": item.name,
                "needs_quantity_check": needs_check,
                "is_low_stock": is_low,
                "is_critical": is_critical,
                "current_quantity": item.current_quantity,
                "unit": item.unit
            })
    
    return alerts

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
