"""
SMS Service using Textbelt API
https://textbelt.com - 1 free SMS per day (no setup required)
For more SMS, get a paid key at textbelt.com
"""
import os
import httpx
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

TEXTBELT_KEY = os.getenv("TEXTBELT_KEY", "textbelt")  # "textbelt" = free tier
TEXTBELT_API_URL = "https://textbelt.com/text"

# Track sent messages to avoid spam (in-memory for simplicity)
# In production, use a database table
_sent_messages: dict[str, datetime] = {}


def can_send_sms(item_id: int) -> bool:
    """Check if we can send SMS for this item (1 per 24h per item)"""
    key = f"item_{item_id}"
    last_sent = _sent_messages.get(key)
    if last_sent and datetime.now() - last_sent < timedelta(hours=24):
        return False
    return True


def mark_sms_sent(item_id: int):
    """Mark that SMS was sent for this item"""
    _sent_messages[f"item_{item_id}"] = datetime.now()


async def send_sms(phone: str, message: str, item_id: Optional[int] = None) -> bool:
    """
    Send SMS via Textbelt API
    
    Args:
        phone: Recipient phone number (e.g., +5511999999999)
        message: SMS content
        item_id: Optional item ID for rate limiting
    
    Returns:
        True if SMS was sent successfully
    """
    if item_id and not can_send_sms(item_id):
        logger.info(f"SMS for item {item_id} already sent in last 24h, skipping")
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TEXTBELT_API_URL,
                data={
                    "phone": phone,
                    "message": message,
                    "key": TEXTBELT_KEY
                },
                timeout=30.0
            )
            
            result = response.json()
            
            if result.get("success"):
                logger.info(f"SMS sent successfully to {phone}")
                if item_id:
                    mark_sms_sent(item_id)
                return True
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"Failed to send SMS: {error}")
                return False
                
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        return False


def calculate_suggested_quantity(
    current_qty: float,
    min_qty: float,
    usage_rate: Optional[float],
    usage_period: str,
    acquisition_difficulty: int
) -> float:
    """
    Calculate suggested purchase quantity based on:
    - Current shortage
    - Usage rate/trend
    - Acquisition difficulty (buffer days)
    
    Returns suggested quantity to purchase
    """
    # Base: reach 150% of minimum for margin
    target_qty = min_qty * 1.5
    
    # Buffer days based on difficulty
    # Easy=3 days, Medium=7 days, Hard=14 days
    buffer_days = {0: 3, 5: 7, 10: 14}.get(acquisition_difficulty, 7)
    
    # Calculate daily usage
    daily_usage = 0.0
    if usage_rate:
        if usage_period == "daily":
            daily_usage = usage_rate
        elif usage_period == "weekly":
            daily_usage = usage_rate / 7
        elif usage_period == "monthly":
            daily_usage = usage_rate / 30
    
    # Add buffer based on usage and difficulty
    buffer_qty = daily_usage * buffer_days
    
    # Total needed
    suggested = (target_qty - current_qty) + buffer_qty
    
    # Round up to nearest unit
    return max(1, round(suggested, 1))


def format_low_stock_message(
    item_name: str,
    current_qty: float,
    min_qty: float,
    unit: str,
    suggested_qty: float,
    lang: str = "pt-BR"
) -> str:
    """Format the SMS message for low stock alert"""
    if lang.startswith("pt"):
        return (
            f"⚠️ AInventário: {item_name} está acabando!\n"
            f"Atual: {current_qty} {unit}\n"
            f"Mínimo: {min_qty} {unit}\n"
            f"Sugestão de compra: {suggested_qty} {unit}"
        )
    else:
        return (
            f"⚠️ AInventory: {item_name} is running low!\n"
            f"Current: {current_qty} {unit}\n"
            f"Minimum: {min_qty} {unit}\n"
            f"Suggested purchase: {suggested_qty} {unit}"
        )
