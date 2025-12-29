"""
Notification service for purchase reminders.
Initial implementation uses Apple Shortcuts URL scheme.
Designed to be extended for push notifications.
"""
from datetime import datetime
from typing import Optional, Dict, Any
import urllib.parse


class NotificationService:
    """
    Service for sending notifications about inventory items.
    Initial implementation supports Apple Shortcuts integration.
    """
    
    # Apple Shortcuts URL scheme format
    SHORTCUTS_URL_FORMAT = "shortcuts://run-shortcut?name={shortcut_name}&input=text&text={message}"
    
    def __init__(self, shortcut_name: str = "InventoryAlert"):
        """
        Initialize notification service.
        
        Args:
            shortcut_name: Name of the Apple Shortcut to trigger
        """
        self.shortcut_name = shortcut_name
    
    def generate_shortcut_url(self, item_name: str, message: str) -> str:
        """
        Generate Apple Shortcuts URL for notification.
        
        Args:
            item_name: Name of the item
            message: Notification message
        
        Returns:
            URL that can be opened to trigger the shortcut
        """
        full_message = f"🏠 Inventário: {item_name}\n{message}"
        encoded_message = urllib.parse.quote(full_message)
        encoded_shortcut = urllib.parse.quote(self.shortcut_name)
        
        return self.SHORTCUTS_URL_FORMAT.format(
            shortcut_name=encoded_shortcut,
            message=encoded_message
        )
    
    def create_low_stock_notification(
        self,
        item_name: str,
        current_quantity: float,
        unit: str,
        days_remaining: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Create notification data for low stock item.
        
        Args:
            item_name: Name of the item
            current_quantity: Current stock level
            unit: Unit of measurement
            days_remaining: Days until depletion (optional)
        
        Returns:
            Dict with notification data
        """
        if days_remaining is not None and days_remaining <= 2:
            urgency = "🔴 CRÍTICO"
            message = f"Acabando! Restam apenas {current_quantity} {unit}"
        elif days_remaining is not None and days_remaining <= 5:
            urgency = "🟡 ATENÇÃO"
            message = f"Estoque baixo: {current_quantity} {unit} (~{int(days_remaining)} dias)"
        else:
            urgency = "📝 LEMBRETE"
            message = f"Verificar estoque: {current_quantity} {unit}"
        
        if days_remaining:
            message += f"\nComprar em: {int(days_remaining)} dias"
        
        return {
            "type": "low_stock",
            "urgency": urgency,
            "item_name": item_name,
            "message": message,
            "shortcut_url": self.generate_shortcut_url(item_name, f"{urgency}: {message}"),
            "created_at": datetime.utcnow().isoformat()
        }
    
    def create_check_reminder_notification(
        self,
        item_name: str,
        last_check_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Create notification to remind user to check quantity.
        
        Args:
            item_name: Name of the item
            last_check_date: When the item was last checked
        
        Returns:
            Dict with notification data
        """
        if last_check_date:
            days_since = (datetime.utcnow() - last_check_date).days
            message = f"Faz {days_since} dias que não verificamos. Qual a quantidade atual?"
        else:
            message = "Nunca verificamos esse item. Qual a quantidade atual?"
        
        return {
            "type": "check_reminder",
            "urgency": "📋 VERIFICAR",
            "item_name": item_name,
            "message": message,
            "shortcut_url": self.generate_shortcut_url(item_name, message),
            "created_at": datetime.utcnow().isoformat()
        }
    
    def get_pending_notifications(
        self,
        items: list,
        usage_tracker: Any
    ) -> list:
        """
        Get all pending notifications for items.
        
        Args:
            items: List of item objects
            usage_tracker: UsageTracker instance
        
        Returns:
            List of notification dicts
        """
        notifications = []
        
        for item in items:
            # Check if low stock
            if item.current_quantity < item.minimum_quantity:
                # Calculate days remaining if possible
                from .ml_predictor import (
                    MLPredictor,
                    calculate_daily_usage,
                    calculate_days_remaining
                )
                
                history = usage_tracker.get_history_as_list(item.quantity_history)
                predictor = MLPredictor()
                ml_usage = predictor.predict_usage_rate(history)
                
                if ml_usage:
                    days = calculate_days_remaining(item.current_quantity, ml_usage)
                elif item.usage_rate:
                    daily = calculate_daily_usage(item.usage_rate, item.usage_period)
                    days = calculate_days_remaining(item.current_quantity, daily)
                else:
                    days = None
                
                notifications.append(
                    self.create_low_stock_notification(
                        item.name,
                        item.current_quantity,
                        item.unit,
                        days
                    )
                )
            
            # Check if needs verification
            elif usage_tracker.needs_check_reminder(item.quantity_history):
                last_check = usage_tracker.get_last_check_date(item.quantity_history)
                notifications.append(
                    self.create_check_reminder_notification(item.name, last_check)
                )
        
        return notifications


# Future: Push notification interface
class PushNotificationProvider:
    """
    Abstract base for push notification providers.
    Implement this for Firebase, APNs, or other services.
    """
    
    async def send(self, user_id: str, title: str, body: str, data: Dict) -> bool:
        """Send push notification. Override in implementations."""
        raise NotImplementedError
    
    async def register_device(self, user_id: str, device_token: str) -> bool:
        """Register device for push notifications. Override in implementations."""
        raise NotImplementedError
