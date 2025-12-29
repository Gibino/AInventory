from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    icon = Column(String) # Emoji or icon name
    color = Column(String) # Hex color

    items = relationship("Item", back_populates="category")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    current_quantity = Column(Float, default=0.0)
    minimum_quantity = Column(Float, default=1.0)
    unit = Column(String, default="un") # un, kg, L, g, ml, pacotes
    notes = Column(String, nullable=True)
    barcode = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Acquisition difficulty: 0 = Easy, 5 = Medium, 10 = Hard
    # Affects buffer days for purchase predictions
    acquisition_difficulty = Column(Integer, default=0)
    
    # Usage tracking for ML predictions
    usage_rate = Column(Float, nullable=True)  # User-provided consumption rate
    usage_period = Column(String, default="daily")  # daily, weekly, monthly
    
    # ML learning - JSON array of {date, quantity, change}
    quantity_history = Column(String, nullable=True)
    
    # Notification preferences
    notification_enabled = Column(Boolean, default=False)
    phone_number = Column(String, nullable=True)  # For SMS/notifications
    last_sms_sent_at = Column(DateTime, nullable=True)  # Track last SMS to prevent spam

    category = relationship("Category", back_populates="items")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    # Profile Info
    display_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    
    # Preferences
    theme_preference = Column(String, default="system")  # light, dark, system
    language_preference = Column(String, default="en-US") # pt-BR, en-US
