"""
Usage tracking module for recording and managing quantity history.
Provides data for ML-based predictions.
"""
from datetime import datetime
from typing import Optional
import json


# Maximum number of history entries to keep (90 days)
MAX_HISTORY_SIZE = 90


class UsageTracker:
    """
    Tracks usage history for items to enable ML-based predictions.
    """
    
    def add_quantity_record(
        self,
        current_history: Optional[str],
        old_qty: float,
        new_qty: float
    ) -> str:
        """
        Add a new quantity record to the history.
        
        Args:
            current_history: JSON string of existing history, or None
            old_qty: Previous quantity
            new_qty: New quantity
        
        Returns:
            Updated history as JSON string
        """
        # Parse existing history
        if current_history:
            try:
                history = json.loads(current_history)
            except json.JSONDecodeError:
                history = []
        else:
            history = []
        
        # Add new record
        record = {
            "date": datetime.utcnow().isoformat(),
            "quantity": new_qty,
            "change": new_qty - old_qty
        }
        history.append(record)
        
        # Trim to max size (keep most recent)
        if len(history) > MAX_HISTORY_SIZE:
            history = history[-MAX_HISTORY_SIZE:]
        
        return json.dumps(history)
    
    def get_history_as_list(self, history_json: Optional[str]) -> list:
        """
        Parse history JSON to list of dicts.
        
        Args:
            history_json: JSON string of history
        
        Returns:
            List of history records
        """
        if not history_json:
            return []
        
        try:
            return json.loads(history_json)
        except json.JSONDecodeError:
            return []
    
    def calculate_average_usage(self, history_json: Optional[str]) -> Optional[float]:
        """
        Calculate simple average daily usage from history.
        Fallback when ML prediction is not available.
        
        Args:
            history_json: JSON string of history
        
        Returns:
            Average daily usage, or None if insufficient data
        """
        history = self.get_history_as_list(history_json)
        
        if len(history) < 2:
            return None
        
        # Calculate time span
        try:
            first_date = datetime.fromisoformat(history[0]["date"].replace("Z", "+00:00"))
            last_date = datetime.fromisoformat(history[-1]["date"].replace("Z", "+00:00"))
            days = (last_date - first_date).days
            
            if days <= 0:
                return None
            
            # Calculate total consumption (only count decreases)
            total_consumed = 0.0
            for record in history:
                change = record.get("change", 0)
                if change < 0:  # Consumption (negative change)
                    total_consumed += abs(change)
            
            return total_consumed / days
        except Exception:
            return None
    
    def get_last_check_date(self, history_json: Optional[str]) -> Optional[datetime]:
        """
        Get the date of the last quantity check.
        
        Args:
            history_json: JSON string of history
        
        Returns:
            Datetime of last check, or None
        """
        history = self.get_history_as_list(history_json)
        
        if not history:
            return None
        
        try:
            last_entry = history[-1]
            return datetime.fromisoformat(last_entry["date"].replace("Z", "+00:00"))
        except Exception:
            return None
    
    def needs_check_reminder(
        self,
        history_json: Optional[str],
        days_threshold: int = 7
    ) -> bool:
        """
        Check if the item needs a quantity check reminder.
        
        Args:
            history_json: JSON string of history
            days_threshold: Days since last check to trigger reminder
        
        Returns:
            True if reminder should be sent
        """
        last_check = self.get_last_check_date(history_json)
        
        if not last_check:
            return True  # Never checked, needs check
        
        days_since_check = (datetime.utcnow() - last_check).days
        return days_since_check >= days_threshold
