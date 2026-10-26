import pytest
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ingestion.camera_ingest import process_bronze_data

def test_bronze_ingestion_mock_dataframe():
    """Simple test to verify local bronze processing mock"""
    class MockSpark:
        def createDataFrame(self, data, schema):
            return "Mock DataFrame Result"
    
    result = process_bronze_data(MockSpark(), "test", "target_table")
    assert result == "Mock DataFrame Result"

def test_imports():
    """Test that all local modules can be imported without syntax errors"""
    import src.processing.image_processing
    import src.training.yolov8_training
    assert True
