"""
Unit tests for ML-based purchase prediction.
These tests will be expanded as the ML module is implemented.
"""
import pytest
from datetime import datetime, timedelta


class TestPredictionCalculations:
    """Test cases for prediction calculations."""
    
    def test_daily_usage_calculation(self):
        """Test converting various usage periods to daily usage."""
        from backend.ml_predictor import calculate_daily_usage
        
        # Daily usage stays the same
        assert calculate_daily_usage(1.0, "daily") == 1.0
        
        # Weekly usage divided by 7
        assert abs(calculate_daily_usage(7.0, "weekly") - 1.0) < 0.001
        
        # Monthly usage divided by 30
        assert abs(calculate_daily_usage(30.0, "monthly") - 1.0) < 0.001
    
    def test_buffer_days_by_difficulty(self):
        """Test buffer days based on acquisition difficulty."""
        from backend.ml_predictor import get_buffer_days
        
        assert get_buffer_days(0) == 2   # Easy
        assert get_buffer_days(5) == 5   # Medium
        assert get_buffer_days(10) == 10 # Hard
    
    def test_days_until_depletion(self):
        """Test calculation of days until item runs out."""
        from backend.ml_predictor import calculate_days_remaining
        
        # 10 units, using 2 per day = 5 days
        assert calculate_days_remaining(10.0, 2.0) == 5.0
        
        # Zero usage = infinite days
        assert calculate_days_remaining(10.0, 0.0) == float('inf')
        
        # Already empty
        assert calculate_days_remaining(0.0, 2.0) == 0.0
    
    def test_purchase_date_with_buffer(self):
        """Test purchase date calculation with difficulty buffer."""
        from backend.ml_predictor import calculate_purchase_date
        
        # 10 days remaining, difficulty easy (2 day buffer)
        # Should purchase in 8 days
        result = calculate_purchase_date(
            current_quantity=10.0,
            daily_usage=1.0,
            difficulty=0
        )
        
        expected_date = datetime.utcnow() + timedelta(days=8)
        # Allow 1 second tolerance
        assert abs((result - expected_date).total_seconds()) < 1


class TestMLModel:
    """Test cases for the ML prediction model."""
    
    def test_insufficient_data_returns_none(self):
        """Test that prediction returns None with insufficient history."""
        from backend.ml_predictor import MLPredictor
        
        predictor = MLPredictor()
        # Less than 5 data points
        history = [
            {"date": "2024-01-01", "quantity": 10.0},
            {"date": "2024-01-02", "quantity": 9.0},
        ]
        
        result = predictor.predict_usage_rate(history)
        assert result is None
    
    def test_linear_usage_prediction(self):
        """Test ML prediction with linear usage pattern."""
        from backend.ml_predictor import MLPredictor
        
        predictor = MLPredictor()
        # Linear decrease of 1 unit per day
        history = [
            {"date": "2024-01-01", "quantity": 10.0},
            {"date": "2024-01-02", "quantity": 9.0},
            {"date": "2024-01-03", "quantity": 8.0},
            {"date": "2024-01-04", "quantity": 7.0},
            {"date": "2024-01-05", "quantity": 6.0},
            {"date": "2024-01-06", "quantity": 5.0},
        ]
        
        result = predictor.predict_usage_rate(history)
        # Should predict approximately 1.0 units per day
        assert result is not None
        assert 0.9 <= result <= 1.1


class TestUsageTracking:
    """Test cases for usage history tracking."""
    
    def test_record_quantity_change(self):
        """Test recording a quantity change in history."""
        from backend.usage_tracker import UsageTracker
        import json
        
        tracker = UsageTracker()
        
        # Empty history
        current_history = None
        new_history = tracker.add_quantity_record(
            current_history,
            old_qty=10.0,
            new_qty=8.0
        )
        
        history_data = json.loads(new_history)
        assert len(history_data) == 1
        assert history_data[0]["quantity"] == 8.0
    
    def test_history_limit(self):
        """Test that history is limited to prevent unbounded growth."""
        from backend.usage_tracker import UsageTracker
        import json
        
        tracker = UsageTracker()
        
        # Create history with 100 entries
        history = json.dumps([
            {"date": f"2024-01-{i:02d}", "quantity": float(100 - i)}
            for i in range(1, 101)
        ])
        
        new_history = tracker.add_quantity_record(history, 5.0, 4.0)
        history_data = json.loads(new_history)
        
        # Should be capped at MAX_HISTORY_SIZE (e.g., 90 days)
        assert len(history_data) <= 90
