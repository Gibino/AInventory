"""
ML-based usage prediction module using scikit-learn.
Provides accurate predictions for when items need to be purchased.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import json

try:
    from sklearn.linear_model import LinearRegression
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


# Buffer days based on acquisition difficulty
DIFFICULTY_BUFFER = {
    0: 2,   # Easy - 2 days buffer
    5: 5,   # Medium - 5 days buffer
    10: 10  # Hard - 10 days buffer
}

# Minimum data points required for ML prediction
MIN_DATA_POINTS = 5


def calculate_daily_usage(usage_rate: float, period: str) -> float:
    """
    Convert usage rate to daily usage.
    
    Args:
        usage_rate: Amount used per period
        period: One of 'daily', 'weekly', or 'monthly'
    
    Returns:
        Daily usage rate
    """
    period_days = {
        "daily": 1,
        "weekly": 7,
        "monthly": 30
    }
    divisor = period_days.get(period.lower(), 1)
    return usage_rate / divisor


def get_buffer_days(difficulty: int) -> int:
    """
    Get the buffer days based on acquisition difficulty.
    
    Args:
        difficulty: 0 (Easy), 5 (Medium), or 10 (Hard)
    
    Returns:
        Number of buffer days before depletion to trigger purchase alert
    """
    return DIFFICULTY_BUFFER.get(difficulty, 2)


def calculate_days_remaining(current_quantity: float, daily_usage: float) -> float:
    """
    Calculate how many days until the item is depleted.
    
    Args:
        current_quantity: Current stock level
        daily_usage: Amount used per day
    
    Returns:
        Days until depletion (infinity if no usage)
    """
    if current_quantity <= 0:
        return 0.0
    if daily_usage <= 0:
        return float('inf')
    return current_quantity / daily_usage


def calculate_purchase_date(
    current_quantity: float,
    daily_usage: float,
    difficulty: int
) -> datetime:
    """
    Calculate the date by which an item should be purchased.
    
    Args:
        current_quantity: Current stock level
        daily_usage: Amount used per day
        difficulty: Acquisition difficulty score
    
    Returns:
        Datetime when purchase should happen
    """
    days_remaining = calculate_days_remaining(current_quantity, daily_usage)
    buffer_days = get_buffer_days(difficulty)
    
    if days_remaining == float('inf'):
        # No usage, return far future date
        return datetime.utcnow() + timedelta(days=365)
    
    purchase_in_days = max(0, days_remaining - buffer_days)
    return datetime.utcnow() + timedelta(days=purchase_in_days)


class MLPredictor:
    """
    Machine Learning based usage predictor using Linear Regression.
    Learns from historical quantity data to predict daily usage rate.
    """
    
    def __init__(self):
        if ML_AVAILABLE:
            self.model = LinearRegression()
        else:
            self.model = None
    
    def predict_usage_rate(self, history: List[Dict]) -> Optional[float]:
        """
        Predict daily usage rate from historical data.
        
        Args:
            history: List of dicts with 'date' and 'quantity' keys
        
        Returns:
            Predicted daily usage rate, or None if insufficient data
        """
        if not ML_AVAILABLE or not history:
            return None
        
        if len(history) < MIN_DATA_POINTS:
            return None
        
        try:
            # Parse dates and quantities
            data_points = []
            base_date = None
            
            for entry in history:
                date_str = entry.get("date")
                quantity = entry.get("quantity")
                
                if date_str and quantity is not None:
                    try:
                        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        if isinstance(date, str):
                            date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                    except:
                        date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                    
                    if base_date is None:
                        base_date = date
                    
                    days_from_start = (date - base_date).days
                    data_points.append((days_from_start, quantity))
            
            if len(data_points) < MIN_DATA_POINTS:
                return None
            
            # Prepare data for sklearn
            X = np.array([[dp[0]] for dp in data_points])
            y = np.array([dp[1] for dp in data_points])
            
            # Fit linear regression
            self.model.fit(X, y)
            
            # The negative slope is the usage rate (quantity decreases over time)
            slope = self.model.coef_[0]
            
            # Usage rate is the negative of slope (positive value for consumption)
            usage_rate = -slope
            
            # Ensure non-negative usage rate
            return max(0.0, usage_rate)
        
        except Exception as e:
            print(f"ML prediction error: {e}")
            return None
    
    def get_prediction_confidence(self, history: List[Dict]) -> float:
        """
        Calculate confidence score for the prediction.
        Based on R² score and data quantity.
        
        Returns:
            Confidence score between 0 and 1
        """
        if not ML_AVAILABLE or not history or len(history) < MIN_DATA_POINTS:
            return 0.0
        
        try:
            # Same data preparation as predict_usage_rate
            data_points = []
            base_date = None
            
            for entry in history:
                date_str = entry.get("date")
                quantity = entry.get("quantity")
                
                if date_str and quantity is not None:
                    try:
                        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except:
                        date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                    
                    if base_date is None:
                        base_date = date
                    
                    days_from_start = (date - base_date).days
                    data_points.append((days_from_start, quantity))
            
            if len(data_points) < MIN_DATA_POINTS:
                return 0.0
            
            X = np.array([[dp[0]] for dp in data_points])
            y = np.array([dp[1] for dp in data_points])
            
            self.model.fit(X, y)
            r2_score = self.model.score(X, y)
            
            # Weight by data quantity (more data = higher confidence)
            data_factor = min(1.0, len(data_points) / 30)  # Max at 30 days of data
            
            return max(0.0, r2_score * data_factor)
        
        except Exception:
            return 0.0


def predict_purchase_urgency(
    current_quantity: float,
    daily_usage: float,
    difficulty: int
) -> str:
    """
    Determine the urgency level for purchasing an item.
    
    Returns:
        'critical', 'attention', or 'ok'
    """
    if current_quantity <= 0:
        return "critical"
    
    days_remaining = calculate_days_remaining(current_quantity, daily_usage)
    buffer_days = get_buffer_days(difficulty)
    
    if days_remaining <= buffer_days:
        return "critical"
    elif days_remaining <= buffer_days * 2:
        return "attention"
    else:
        return "ok"
